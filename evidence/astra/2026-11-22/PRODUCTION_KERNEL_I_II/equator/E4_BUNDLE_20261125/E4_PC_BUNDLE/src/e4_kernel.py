"""Advance the fixed angular kernel one stage at a time and log its enclosures."""

import json
import os
import select
import subprocess
import tempfile
import time
from fractions import Fraction as F

from e4_support import AXES, STAGES, box_json, norm_bounds_squared
from run_intervals import add, arr, encode, intersect, ivjson, mul, ri, rounded, unpack
from samples import deg, middle


class EvaluationStopped(Exception):
    def __init__(self, state, detail):
        super().__init__(detail)
        self.state = state
        self.detail = detail


class Clock:
    def __init__(self, start_ns, budget_ns, stop_requested, sample_memory):
        self.start_ns = start_ns
        self.end_ns = start_ns + budget_ns
        self.stop_requested = stop_requested
        self.sample_memory = sample_memory

    def poll(self):
        if self.stop_requested():
            raise EvaluationStopped("PARTIAL", "operator stop")
        remaining_ns = self.end_ns - time.monotonic_ns()
        if remaining_ns <= 0:
            raise EvaluationStopped("BUDGET", "monotonic wall-clock limit reached")
        self.sample_memory()
        return min(0.25, remaining_ns / 1_000_000_000)


class StagedIntegral:
    """Keep the kernel's angle tree between stages while one integral per case runs."""

    def __init__(self, kernel, stage_io, args):
        self.args = args
        self.stage = 0
        self.waiting = False
        self.previous_calls = 0
        self.buffer = b""
        self.errors = tempfile.TemporaryFile()
        read_fd, self.permit = os.pipe()
        try:
            env = dict(os.environ, E4_STAGE_FD=str(read_fd), LD_PRELOAD=str(stage_io),
                       LC_ALL="C")
            self.process = subprocess.Popen(
                [str(kernel), *args], stdout=subprocess.PIPE, stderr=self.errors,
                pass_fds=(read_fd,), env=env,
            )
        except BaseException:
            os.close(self.permit)
            self.errors.close()
            raise
        finally:
            os.close(read_fd)

    def failure(self):
        self.errors.seek(0)
        message = self.errors.read().decode("utf-8", errors="replace").strip()
        state = "INCONSISTENT" if "INCONSISTENT" in message else "PARTIAL"
        return EvaluationStopped(state, f"kernel rc={self.process.poll()}: {message}")

    def advance(self, panels, clock):
        clock.poll()
        if panels != STAGES[self.stage]:
            raise ValueError("integral advanced out of order")
        if self.waiting:
            os.write(self.permit, b"+")
            self.waiting = False
        fd = self.process.stdout.fileno()
        while b"\n" not in self.buffer:
            ready, _, _ = select.select([fd], [], [], clock.poll())
            if ready:
                data = os.read(fd, 16384)
                if not data:
                    raise self.failure()
                self.buffer += data
        line, self.buffer = self.buffer.split(b"\n", 1)
        if self.buffer:
            raise EvaluationStopped("PARTIAL", "kernel emitted an unrequested stage")
        clock.poll()
        self.waiting = True
        raw = json.loads(line)
        record = self.validate(raw, panels)
        self.stage += 1
        if panels == STAGES[-1]:
            os.write(self.permit, b"+")
            self.waiting = False
            while self.process.poll() is None:
                try:
                    self.process.wait(timeout=clock.poll())
                except subprocess.TimeoutExpired:
                    continue
            if self.process.returncode or os.read(fd, 1):
                raise self.failure()
        return record

    def validate(self, raw, panels):
        if raw["panels"] != panels:
            raise ValueError("kernel returned an unexpected angular stage")
        interval = read_interval(raw["interval"])
        outer = read_interval(raw["outer"])
        legacy = read_interval(raw["legacy_outer"])
        if not legacy[0] <= outer[0] <= outer[1] <= legacy[1]:
            raise EvaluationStopped("INCONSISTENT", f"outer inclusion failed: {raw}")
        grids = raw["grids"]
        contact = "cap" in raw
        expected_calls = (32 + 4 * ((panels - 32) // 3)) * (1 if contact else 5)
        if (set(grids) != {"contact", "1x4", "2x2", "4x1"}
                or any(type(n) is not int or n < 0 for n in grids.values())
                or sum(grids.values()) != panels
                or grids["contact"] != (panels if contact else 0)
                or raw["panel_calls"] != expected_calls
                or (self.args[0] == "0" and contact)
                or (self.args[0] == "2" and not contact)
                or (not contact and interval != outer)):
            raise ValueError("invalid stage counters, contact mode or interval")
        if any(read_number(raw[k]) < 0 for k in ("coarse_2R_sum", "composite_2R_sum")):
            raise ValueError("negative remainder width")
        if contact:
            for key in ("cap", "rho", "eta", "delta"):
                read_interval(raw[key])
        calls = raw["panel_calls"] - self.previous_calls
        self.previous_calls = raw["panel_calls"]
        return dict(raw, args=self.args, width=width(interval), natural_only_cells=False,
                    new_panel_calls=calls, new_gauss_nodes=4 * calls,
                    new_integrand_calls=7 * calls)

    def close(self):
        os.close(self.permit)
        try:
            if not self.waiting and self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        finally:
            self.process.stdout.close()
            self.errors.close()


def read_number(raw):
    if (not isinstance(raw, list) or len(raw) != 2
            or type(raw[0]) is not str or type(raw[1]) is not int):
        raise ValueError("expected exact two-part binary endpoint")
    return F(int(raw[0])) * F(2) ** raw[1]


def read_interval(raw):
    lo, hi = map(read_number, raw)
    if lo > hi:
        raise EvaluationStopped("INCONSISTENT", f"reversed interval: {raw}")
    return lo, hi


def width(interval):
    return encode(rounded(interval[1] - interval[0], True))


class BoxEvaluation:
    def __init__(self, kernel, stage_io, box, watch_pid):
        self.kernel = kernel
        self.stage_io = stage_io
        self.box = box
        self.watch_pid = watch_pid
        self.contact = norm_bounds_squared(box)[1] >= 1
        self.jobs = {}
        self.processes = {}
        self.records = {}
        self.active = None
        self.add_job("D", box, 2, mode=2 if self.contact else 0)
        if not self.contact:
            self.add_job("I0", tuple(deg(middle(p)) for p in box), 2)
            self.add_job("base", box[:4] + (deg(0),), 2)
            if box[4][1]:
                tube = box[:4] + ((F(0), box[4][1]),)
                if norm_bounds_squared(tube)[1] >= 1:
                    raise EvaluationStopped("PARTIAL", "even-formula tube meets the boundary")
                self.add_job("Haa", tube, 4)
            for i, name in enumerate(AXES):
                if box[i][0] < box[i][1]:
                    if i < 4:
                        self.add_job("I_" + name, box, 2, i)
                    else:
                        self.add_job("I_a", box, 3)

    def add_job(self, key, box, order, axis=-1, mode=0):
        self.jobs[key] = tuple([str(mode), str(order), str(axis), *arr(box)])

    def advance(self, panels, previous, clock):
        self.records = {}
        aliases = {}
        for name, spec in self.jobs.items():
            if spec in aliases:
                self.records[name] = {"same_as": aliases[spec]}
                continue
            self.active = name
            clock.poll()
            if spec not in self.processes:
                integral = StagedIntegral(self.kernel, self.stage_io, list(spec))
                self.processes[spec] = integral
                self.watch_pid(integral.process.pid)
            self.records[name] = self.processes[spec].advance(panels, clock)
            aliases[spec] = name
        self.active = None

        direct = self.value("D")
        if self.contact:
            raw = {"direct": direct}
            r2 = {
                "status": "NOT_APPLICABLE", "axis_order": AXES,
                "parameter_widths": ["NOT_APPLICABLE"] * 5,
                "angle_width": "NOT_APPLICABLE", "outside": self.records["D"]["outer"],
                "outside_width": width(read_interval(self.records["D"]["outer"])),
                "cap": self.records["D"]["cap"],
            }
        else:
            center = self.value("I0")
            terms = []
            for axis, (lo, hi) in zip(AXES, self.box):
                term = (F(0), F(0))
                if lo < hi:
                    mid = (lo + hi) / 2
                    term = mul(ri(lo - mid, hi - mid), self.value("I_" + axis))
                    center = add(center, term)
                terms.append(term)
            alo, ahi = self.box[4]
            correction = (F(0), F(0))
            if ahi:
                correction = mul(ri(alo ** 2 / 2, ahi ** 2 / 2), self.value("Haa"))
            raw = {"direct": direct, "center": center, "even": add(self.value("base"), correction)}
            r2 = {
                "status": "MEASURED", "axis_order": AXES,
                "parameter_widths": [width(iv) for iv in terms],
                "parameter_terms": [ivjson(iv) for iv in terms],
                "angle_width": width(self.value("I0")),
                "center_width_before_intersection": width(center),
                "omitted_zero_width_axes": [a for a in AXES if "I_" + a not in self.jobs],
            }
        components = {name: ivjson(iv) for name, iv in raw.items()}
        try:
            within_stage = intersect(*raw.values())
            result = intersect(previous, within_stage) if previous is not None else within_stage
        except RuntimeError as exc:
            prior = None if previous is None else ivjson(previous)
            raise EvaluationStopped("INCONSISTENT", f"{exc}; {components=}; {prior=}") from exc
        clock.poll()
        r2["intersection_width"] = width(result)
        return result, {
            "box": box_json(self.box), "contact": self.contact, "R2": r2,
            "components": components, "stage_interval": ivjson(within_stage),
            "interval": ivjson(result), "integrals": self.records,
        }

    def value(self, name):
        entry = self.records[name]
        if "same_as" in entry:
            entry = self.records[entry["same_as"]]
        return unpack(entry["interval"])

    def close(self):
        for integral in self.processes.values():
            integral.close()
