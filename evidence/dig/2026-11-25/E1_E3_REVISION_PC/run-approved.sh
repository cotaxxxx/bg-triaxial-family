#!/bin/bash
set -u
cd /home/daybreak/equator-revision-20261125/work || exit 1
(
  set -C
  {
    printf 'started_at=%s\n' "$(date -Is)"
    run_status=0
    timeout --verbose --signal=TERM --kill-after=30s 6000s \
      python3 src/run_intervals.py --workers 6 &
    timeout_pid=$!
    printf 'timeout_pid=%s\n' "$timeout_pid"
    wait "$timeout_pid" || run_status=$?
    printf 'finished_at=%s\nexit_status=%s\n' "$(date -Is)" "$run_status"
    printf 'remaining_process_group_members:\n'
    ps -eo pid,ppid,pgid,stat,args | awk -v g="$timeout_pid" '$3==g'
    printf 'remaining_kernel_or_runner_processes:\n'
    ps -eo pid,ppid,pgid,stat,args | awk -v k="$(pwd)/kernel" '$5==k || ($5 ~ /python/ && $6=="src/run_intervals.py" && $7=="--workers" && $8=="6")'
    exit "$run_status"
  } > interval-run.log 2>&1
)
rc=$?
printf 'finished_at=%s\nexit_status=%s\n' "$(date -Is)" "$rc" > ../records/exit-status.txt
exit "$rc"
