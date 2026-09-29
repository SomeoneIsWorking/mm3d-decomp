#!/usr/bin/env python3
"""Run MM3D's source-file attribution and enforce its control at the PROCESS level.

Why this exists: Ghidra's `analyzeHeadless` swallows a Jython `SystemExit(1)`, so a postScript that
"exits non-zero" on a zero match still leaves the headless process exiting 0. Verified on
ghidra_12.0.4: with `MM3D_ATTR_REQUIRE` pointed at a file that does not exist, the script printed
`CONTROL FAILED: ... exiting non-zero` and `analyzeHeadless` still returned 0. A control whose
failure cannot fail the build is decoration.

So the control is enforced here instead, on the captured output, and this runner is what returns a
real exit status. It scans for the marker lines, requires a NON-ZERO match count, and requires the
control to have passed for the file named in `--require`. A zero match fails.

Usage:
    run_source_attribution.py [--require FILE] [--project DIR] [--program NAME] [--script FILE]

Defaults run against the attribution copy of the Ghidra project (the pristine project under the
repo-root build/ is not a directory this tool will analyze, so it cannot perturb it).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = REPO / "mm3d-decomp" / "build" / "ghidra-mm3d-attrib"
DEFAULT_SCRIPT = REPO / "mm3d-decomp" / "tools" / "FunctionSourceAttribution.py"
TOOL_DIR = REPO / "mm3d-decomp" / "tools"

# `MATCH functions_attributed=136 of 12054` -- the count the whole exercise exists to produce.
MATCH_RE = re.compile(r"MATCH functions_attributed=(\d+) of (\d+)")


def run(project: pathlib.Path, program: str, script: pathlib.Path, require: str,
        timeout: int) -> int:
    env = dict(os.environ)
    env["MM3D_ATTR_REQUIRE"] = require
    cmd = [
        "analyzeHeadless", str(project), program,
        "-process", "-noanalysis",
        "-scriptPath", str(TOOL_DIR),
        "-postScript", script.name,
    ]
    print("RUN " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, env=env, cwd=str(REPO), timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    # Print the tool's own scan/match/control lines verbatim: raw Ghidra banner is noise, but the
    # control output must be seen as emitted, not as this runner's summary of it.
    for line in out.splitlines():
        if re.match(r"^(SCAN|MATCH|UNATTRIBUTED|REJECTED|CONTROL|wrote) ", line):
            print(line, flush=True)

    failures = []
    if proc.returncode != 0:
        failures.append("analyzeHeadless returned %d" % proc.returncode)
    if "Traceback" in out:
        failures.append("script raised an exception (Traceback in output)")

    m = MATCH_RE.search(out)
    if not m:
        failures.append("no 'MATCH functions_attributed=N of M' line: the scan never reported a count")
    elif int(m.group(1)) == 0:
        failures.append("matched 0 functions: every string was left unattributed")

    if "CONTROL OK %s " % require not in out:
        failures.append("control for %r did not report OK" % require)
    if "CONTROL PASSED" not in out:
        failures.append("script did not report CONTROL PASSED")

    if failures:
        for f in failures:
            print("CONTROL FAILED: %s" % f, file=sys.stderr)
        return 1
    print("CONTROL OK: %d/%s functions attributed; control for %r confirmed"
          % (int(m.group(1)), m.group(2), require))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=pathlib.Path, default=DEFAULT_PROJECT)
    ap.add_argument("--program", default="mm3d")
    ap.add_argument("--script", type=pathlib.Path, default=DEFAULT_SCRIPT)
    ap.add_argument("--require", default="z_kankyo.cpp",
                    help="source file the control must positively attribute (default: z_kankyo.cpp)")
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    if not args.project.is_dir():
        print("no such Ghidra project: %s" % args.project, file=sys.stderr)
        return 2
    return run(args.project, args.program, args.script, args.require, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
