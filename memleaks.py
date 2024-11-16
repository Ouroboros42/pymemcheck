import linecache
import os
import tracemalloc
from tracemalloc import start, take_snapshot, Filter

__all__ = ['start', 'take_snapshot', 'display_top_diffs']

TRACE_FILTER = (
    Filter(False, "<frozen importlib._bootstrap>"),
    Filter(False, "<frozen importlib._bootstrap_external>"),
    Filter(False, "<unknown>"),
    Filter(False, linecache.__file__),
    Filter(False, tracemalloc.__file__),
    Filter(False, __file__)
)

last_snap = None

def init():
    start()
    global last_snap
    last_snap = take_snapshot()

def display_top_diffs(new_snap=None, old_snap=None, key_type='lineno', limit=10):
    if new_snap is None:
        new_snap = take_snapshot()

    if old_snap is None:
        global last_snap
        
        old_snap = last_snap
        last_snap = new_snap

        if old_snap is None:
            return

    full_diff = new_snap.compare_to(old_snap, key_type)

    filter_old_snap = old_snap.filter_traces(TRACE_FILTER)
    filter_new_snap = new_snap.filter_traces(TRACE_FILTER)

    top_diffs = filter_new_snap.compare_to(filter_old_snap, key_type)

    print(f"=== MemLeak Diff ===\n Top {limit} lines")
    for index, stat in enumerate(top_diffs[:limit], 1):
        frame = stat.traceback[0]
        print(f"  #{index}: {frame.filename}:{frame.lineno}: {(stat.size_diff/1024):.1f} KiB")
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f"    {line}")

    other = top_diffs[limit:]
    if other:
        size = sum(stat.size_diff for stat in other)
        print(f" {len(other)} others: {size/1024:.1f} KiB")

    total = sum(stat.size_diff for stat in top_diffs)
    full_total = sum(stat.size_diff for stat in full_diff)


    print(f" Total allocated size diff: {full_total/1024:.1f} KiB\n  ({(full_total - total)/1024:.1f} KiB hidden sources)")
