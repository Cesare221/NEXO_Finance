"""Check that Alembic has exactly one migration head."""
from pathlib import Path
import subprocess
import sys


def main():
    repo_root = Path(__file__).resolve().parents[1]
    api_dir = repo_root / "apps" / "api"
    result = subprocess.run(
        ["python", "-m", "alembic", "heads"],
        capture_output=True,
        text=True,
        cwd=api_dir,
    )
    output = result.stdout.strip()
    lines = [line.strip() for line in output.splitlines() if line.strip() and not line.startswith("Rev:")]
    heads = [line for line in lines if "(head)" in line]

    if len(heads) == 0:
        print("ERROR: No migration head found", file=sys.stderr)
        sys.exit(1)
    if len(heads) > 1:
        print(f"ERROR: Multiple migration heads found ({len(heads)}):", file=sys.stderr)
        for h in heads:
            print(f"  {h}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: Single migration head — {heads[0].split()[0]}")


if __name__ == "__main__":
    main()
