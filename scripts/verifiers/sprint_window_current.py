"""Assert a sprint folder covers today's date.

CLAUDE.md session-start rule: if today falls outside every sprint window,
the next one must be scaffolded before work. A day with no covering
sprint-<m>-<yy>-<dd>-<dd> folder is the counterexample.
"""
import datetime
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "Today falls within some docs/sprint-<m>-<yy>-<dd>-<dd> window."
METHOD = "static"
OWNER = "pm/program-tracker"
SPRINT_RE = re.compile(r"sprint-(\d{1,2})-(\d{2})-(\d{1,2})-(\d{1,2})$")


def check():
    _lib.in_repo_root()
    today = datetime.date.today()
    windows = []
    for d in glob.glob("docs/sprint-*/"):
        m = SPRINT_RE.search(d.rstrip("/"))
        if not m:
            continue
        month, yy, d1, d2 = (int(x) for x in m.groups())
        year = 2000 + yy
        try:
            start = datetime.date(year, month, d1)
            end = datetime.date(year, month, d2)
        except ValueError:
            continue
        windows.append((d.rstrip("/"), start, end))
        if start <= today <= end:
            return _lib.PASS, f"{today} covered by {d.rstrip('/')}"
    if not windows:
        return _lib.FAIL, "no parseable sprint folders found"
    latest = max(windows, key=lambda w: w[2])
    return (_lib.FAIL,
            f"{today} not in any sprint window (latest ends {latest[2]} "
            f"in {latest[0]}) — scaffold the next sprint")


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
