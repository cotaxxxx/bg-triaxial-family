"""Run an unmodified script (a runner, a self-test) with the tape log switched on.
Usage: run_with_log.py LOG.jsonl READER_DIR SCRIPT [script arguments...]"""
import runpy, sys
from pathlib import Path
log, reader, script = sys.argv[1:4]
sys.path.insert(0, reader); sys.path.insert(0, str(Path(__file__).resolve().parent))
import tape_log
tape_log.install(log)
sys.argv = [script] + sys.argv[4:]; sys.path.insert(0, str(Path(script).resolve().parent))
runpy.run_path(script, run_name="__main__")
