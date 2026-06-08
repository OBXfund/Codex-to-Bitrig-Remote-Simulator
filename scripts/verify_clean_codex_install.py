#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = "bitrig-agent-project-bridge-marketplace"
PLUGIN = "bitrig-agent-project-bridge"
VERSION = "0.2.0"


def fail(message: str) -> None:
    raise SystemExit(f"clean install verification failed: {message}")


def run(command: list[str], home: Path, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        fail(f"{' '.join(command)} exited {result.returncode}\n{output}")
    return result


def codex_binary() -> str:
    codex = shutil.which("codex")
    if not codex:
        fail("codex CLI was not found on PATH")
    return codex


def cache_root(home: Path) -> Path:
    return home / ".codex" / "plugins" / "cache" / MARKETPLACE / PLUGIN / VERSION


def load_manifest(root: Path) -> dict:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        fail(f"installed manifest missing at {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def scan_installed_cache(root: Path, forbidden_terms: list[str]) -> None:
    home_path = re.compile("/Us" + r"ers/[^\s\"')]+")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = home_path.search(text)
        if match:
            fail(f"hardcoded user home path in installed cache: {path.relative_to(root)}")
        lower = text.lower()
        for term in forbidden_terms:
            if term.lower() in lower:
                fail(f"forbidden term in installed cache: {path.relative_to(root)}")


def source_supports_ref(source: str) -> bool:
    if source.startswith(("http://", "https://", "ssh://", "git@")):
        return True
    return not Path(source).expanduser().exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the marketplace installs into a clean Codex home.")
    parser.add_argument(
        "--source",
        default=str(ROOT),
        help="Marketplace source to add. Use a local path, owner/repo, HTTPS Git URL, or SSH Git URL.",
    )
    parser.add_argument("--ref", help="Optional Git ref to pass to codex plugin marketplace add.")
    parser.add_argument(
        "--forbidden-term",
        action="append",
        default=[],
        help="Private term that must not appear in the installed plugin cache. Repeat as needed.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args()

    codex = codex_binary()
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        marketplace_command = [codex, "plugin", "marketplace", "add", args.source]
        if args.ref and source_supports_ref(args.source):
            marketplace_command.extend(["--ref", args.ref])
        run(marketplace_command, home=home)
        run([codex, "plugin", "add", f"{PLUGIN}@{MARKETPLACE}"], home=home)
        listing = run([codex, "plugin", "list"], home=home).stdout

        installed = cache_root(home)
        if not installed.exists():
            fail(f"installed plugin cache missing at {installed}")
        manifest = load_manifest(installed)
        if manifest.get("name") != PLUGIN:
            fail("installed manifest plugin name mismatch")
        if manifest.get("version") != VERSION:
            fail("installed manifest version mismatch")
        if f"{PLUGIN}@{MARKETPLACE}" not in listing:
            fail("codex plugin list did not include installed marketplace plugin")

        scan_installed_cache(installed, args.forbidden_term)

        payload = {
            "status": "clean_install_verified",
            "source": args.source,
            "ref": args.ref,
            "marketplace": MARKETPLACE,
            "plugin": PLUGIN,
            "version": VERSION,
            "cacheFiles": sorted(str(path.relative_to(installed)) for path in installed.rglob("*") if path.is_file()),
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("clean install verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
