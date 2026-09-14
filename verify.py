"""Reproduce every number in the paper from this repository and check it byte-for-byte.

1. Runs the worked-example checks in src/adli_letci.py.
2. Re-runs the Monte Carlo sensitivity analysis and the conformance/mutation analysis into a
   temporary directory and compares the
   SHA-256 of each output with the committed files in results/ (listed in results/SHA256SUMS).
Exit status 0 means the results reproduce exactly.
"""
import hashlib
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    subprocess.run([sys.executable, str(ROOT / "src" / "adli_letci.py")], check=True)

    expected = {}
    for line in (ROOT / "results" / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        expected[name.strip().lstrip("*")] = digest

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "src", work / "src")
        (work / "results").mkdir()
        subprocess.run([sys.executable, str(work / "src" / "sensitivity_analysis.py")], check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, str(work / "src" / "conformance.py")], check=True,
                       stdout=subprocess.DEVNULL, cwd=work / "src")
        failures = [n for n, d in expected.items() if sha(work / "results" / n) != d]

    if failures:
        print("NOT reproduced:", ", ".join(failures))
        return 1
    print(f"All {len(expected)} result files reproduced byte-for-byte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
