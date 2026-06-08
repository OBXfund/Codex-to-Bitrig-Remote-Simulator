#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "dist"
PACKAGE_NAME = "bitrig-agent-project-bridge-marketplace"


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(f"command failed: {' '.join(command)}\n{output}")
    return result


def tracked_files() -> list[Path]:
    result = run(["git", "ls-files", "-z"])
    files = [ROOT / item for item in result.stdout.split("\0") if item]
    if not files:
        raise SystemExit("no tracked files found; commit the marketplace source before packaging")
    return files


def copy_tracked_files(target: Path) -> None:
    for source in tracked_files():
        relative = source.relative_to(ROOT)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def make_archive(staging_root: Path, output_dir: Path, version: str | None) -> Path:
    suffix = f"-{version}" if version else ""
    archive_base = output_dir / f"{PACKAGE_NAME}{suffix}"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = shutil.make_archive(str(archive_base), "zip", staging_root)
    return Path(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a clean source archive for public Codex marketplace publication.")
    parser.add_argument("--output-dir", default=str(DEFAULT_DIST), help="Directory for the generated zip archive.")
    parser.add_argument("--version", help="Optional version suffix for the archive filename.")
    parser.add_argument("--skip-check", action="store_true", help="Skip release_check.py before packaging.")
    args = parser.parse_args()

    if not args.skip_check:
        run([sys.executable, str(ROOT / "scripts" / "release_check.py")], cwd=ROOT)

    with tempfile.TemporaryDirectory() as tmp:
        staging_root = Path(tmp) / PACKAGE_NAME
        staging_root.mkdir(parents=True)
        copy_tracked_files(staging_root)
        archive = make_archive(staging_root, Path(args.output_dir).expanduser().resolve(), args.version)

    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
