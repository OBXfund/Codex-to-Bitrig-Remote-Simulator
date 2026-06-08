#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "bitrig-agent-project-bridge"
SKILL = PLUGIN / "skills" / "bitrig-agent-project-bridge"
BRIDGE = SKILL / "scripts" / "bitrig_agent_bridge.py"
PREPARE = SKILL / "scripts" / "prepare_bitrig_agent_prompt.py"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
RUNTIME_DIR = ROOT / ".bitrig-agent-bridge"


def fail(message: str) -> None:
    raise SystemExit(f"release check failed: {message}")


def run(command: list[str], cwd: Path = ROOT, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != expect:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        fail(f"{' '.join(command)} exited {result.returncode}, expected {expect}\n{output}")
    return result


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def check_marketplace() -> None:
    marketplace = load_json(MARKETPLACE)
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("marketplace must contain exactly one plugin entry")
    entry = plugins[0]
    if entry.get("name") != "bitrig-agent-project-bridge":
        fail("marketplace plugin name mismatch")
    source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
    if source.get("path") != "./plugins/bitrig-agent-project-bridge":
        fail("marketplace source.path must be relative to the marketplace root")
    policy = entry.get("policy") if isinstance(entry.get("policy"), dict) else {}
    if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
        fail("marketplace policy must be AVAILABLE and ON_INSTALL")


def check_plugin_manifest() -> None:
    manifest = load_json(PLUGIN_MANIFEST)
    if manifest.get("name") != "bitrig-agent-project-bridge":
        fail("plugin manifest name mismatch")
    if manifest.get("skills") != "./skills/":
        fail("plugin manifest must point skills to ./skills/")
    if not manifest.get("description"):
        fail("plugin manifest needs a description")
    interface = manifest.get("interface") if isinstance(manifest.get("interface"), dict) else {}
    if not interface.get("displayName") or not interface.get("defaultPrompt"):
        fail("plugin interface needs displayName and defaultPrompt")


def check_skill() -> None:
    skill_md = SKILL / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        fail("SKILL.md frontmatter is not closed")
    frontmatter = parts[1]
    if "\nname: bitrig-agent-project-bridge\n" not in f"\n{frontmatter}\n":
        fail("SKILL.md frontmatter missing expected name")
    if "\ndescription:" not in f"\n{frontmatter}\n":
        fail("SKILL.md frontmatter missing description")


def check_python() -> None:
    scripts = sorted((SKILL / "scripts").glob("*.py"))
    if not scripts:
        fail("no Python helper scripts found")
    run([sys.executable, "-m", "py_compile", *[str(script) for script in scripts]])


def write_sample_project(path: Path, name: str) -> Path:
    project = path / name
    project.mkdir(parents=True, exist_ok=True)
    (project / "ExampleApp.swift").write_text(
        'import SwiftUI\n@main struct ExampleApp: App { var body: some Scene { WindowGroup { Text("Example") } } }\n',
        encoding="utf-8",
    )
    return project


def check_runtime() -> None:
    if RUNTIME_DIR.exists():
        fail(".bitrig-agent-bridge must not be present before tests")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = write_sample_project(tmp_path, "ExampleApp")
        result = run([sys.executable, str(BRIDGE), "run", "--project", str(sample), "--dry-run", "--json"])
        payload = json.loads(result.stdout)
        if payload.get("status") != "dry_run_ready":
            fail("dry-run JSON status mismatch")
        if payload.get("prepared", {}).get("agentName") != "ExampleAppAgent":
            fail("dry-run did not derive ExampleAppAgent")
        if RUNTIME_DIR.exists():
            fail("dry-run must not write .bitrig-agent-bridge")

        generic = write_sample_project(tmp_path, "New Project")
        run([sys.executable, str(PREPARE), "--project", str(generic), "--json"], expect=1)


def iter_source_files() -> list[Path]:
    ignored_dirs = {".git", "__pycache__", ".bitrig-agent-bridge"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def check_scrub() -> None:
    forbidden_terms = [term.strip() for term in os.environ.get("RELEASE_FORBIDDEN_TERMS", "").split(",") if term.strip()]
    home_path = re.compile("/Us" + r"ers/[^\s\"')]+")
    for path in iter_source_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")
        home_match = home_path.search(text)
        if home_match:
            fail(f"hardcoded user home path in {rel}: {home_match.group(0)}")
        lower = text.lower()
        for term in forbidden_terms:
            if term.lower() in lower:
                fail(f"forbidden term found in {rel}")


def main() -> int:
    check_marketplace()
    check_plugin_manifest()
    check_skill()
    check_python()
    check_runtime()
    check_scrub()
    print("release checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
