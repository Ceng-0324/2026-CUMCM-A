"""Audit inputs or reproduce the A-problem results without Make or shell scripts."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def prepare_inputs(source: Path | None):
    summary = json.loads((ROOT / "results/q1/summary.json").read_text(encoding="utf-8"))
    hashes = summary["provenance"]["input_sha256"]
    entries = [{"path": path, "sha256": digest} for path, digest in hashes.items()]
    source = source or ROOT / "problemA"
    source = source.resolve()
    # Existing input files are never overwritten.
    pending = []
    for entry in entries:
        relative = Path(entry["path"])
        origin = source / relative.relative_to("problemA")
        destination = ROOT / relative
        if not origin.is_file():
            raise FileNotFoundError(f"Missing original input: {origin}")
        if sha256(origin.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Original input hash mismatch: {origin}")
        if destination.exists():
            if sha256(destination.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Existing input differs; refusing to overwrite: {destination}")
        else:
            pending.append((origin, destination))
    for origin, destination in pending:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, destination)


def run(command, env):
    subprocess.run([sys.executable, "-B", *command], cwd=ROOT, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="audit",
                        choices=("audit", "q1", "q2", "q3", "q4"))
    parser.add_argument("--input-dir", type=Path,
                        help="Original problemA directory; copied and verified on first use")
    args = parser.parse_args()
    source = args.input_dir
    if source is None and os.environ.get("PROBLEM_A_DIR"):
        source = Path(os.environ["PROBLEM_A_DIR"])
    if source is None and not (ROOT / "problemA").exists() and (ROOT.parent / "problemA").is_dir():
        source = ROOT.parent / "problemA"

    cache = ROOT / ".mpl-cache"
    cache.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLCONFIGDIR=str(cache),
               XDG_CACHE_HOME=str(cache), MPLBACKEND="Agg")
    env.pop("PYTHONPATH", None)
    prepare_inputs(source)
    run(["code/common/audit.py"], env)
    if args.action == "audit":
        return

    question = args.action
    output = ROOT / "reproduced/results" / question
    figures = ROOT / "reproduced/figures" / question
    command = [f"code/{question}/problem{question[-1]}.py", "--output-dir", str(output),
               "--figures-dir", str(figures)]
    run(command, env)
    import numpy as np
    with np.load(output / "fields.npz") as actual, np.load(ROOT / "results" / question / "fields.npz") as expected:
        for key in ("times_s", "temperature_C", "moisture", "surface_moisture"):
            if key not in expected:
                continue
            tolerance = 1.0 if key == "times_s" and question in ("q3", "q4") else 3e-7
            np.testing.assert_allclose(actual[key], expected[key], rtol=0, atol=tolerance,
                                       equal_nan=True, err_msg=f"{question}: {key}")
    print(f"{question}: reproduced fields match the supplied reference results")


if __name__ == "__main__":
    main()
