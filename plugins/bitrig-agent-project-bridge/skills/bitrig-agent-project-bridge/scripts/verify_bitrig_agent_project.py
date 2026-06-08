#!/usr/bin/env python3
import argparse
import json
import plistlib
from pathlib import Path


HOME = Path.home()
BITRIG = HOME / "Library" / "Bitrig"
PROJECTS_JSON = BITRIG / "Projects.json"
PREFS = HOME / "Library" / "Preferences" / "app.bitrig.bitrigapp.plist"
PROJECT_INDEX_KEY = "app.bitrig.AppIntents.ProjectIndex"


def load_projects() -> dict:
    if not PROJECTS_JSON.exists():
        return {}
    return json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))


def load_project_index() -> list[dict]:
    if not PREFS.exists():
        return []
    with PREFS.open("rb") as fh:
        prefs = plistlib.load(fh)
    raw = prefs.get(PROJECT_INDEX_KEY, b"[]")
    if isinstance(raw, bytes):
        return json.loads(raw.decode("utf-8"))
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def newest_named_project(projects: dict, name: str):
    matches = [(pid, data) for pid, data in projects.items() if data.get("name") == name]
    if not matches:
        return None, None
    matches.sort(key=lambda item: item[1].get("updatedAt") or item[1].get("createdAt") or "", reverse=True)
    return matches[0]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def project_json_has_ios_app(project_json: dict) -> bool:
    targets = project_json.get("targets") or {}
    for target in targets.values():
        if target.get("platform") == "iOS" and target.get("type") == "application":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a native Bitrig Agent project by name.")
    parser.add_argument("--name", required=True, help="Bitrig project name to verify")
    parser.add_argument("--source-path", help="Expected Codex source checkout path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    projects = load_projects()
    index = load_project_index()
    project_id, project_data = newest_named_project(projects, args.name)
    if not project_id:
        raise SystemExit(f"No Bitrig project named {args.name!r} found in {PROJECTS_JSON}")

    project_root = BITRIG / "Projects" / project_id
    project_json_path = project_root / "Project.json"
    agent_json_path = project_root / "BitrigAgent.json"
    project_json = load_json(project_json_path)
    agent_json = load_json(agent_json_path)
    index_entries = [entry for entry in index if entry.get("id") == project_id]

    checks = {
        "projectsJsonEntry": True,
        "iPhoneEnabled": bool((project_data.get("supportedPlatforms") or {}).get("iPhone")),
        "projectFolderExists": project_root.exists(),
        "projectJsonExists": project_json_path.exists(),
        "projectJsonHasIosApp": project_json_has_ios_app(project_json),
        "bitrigAgentJsonExists": agent_json_path.exists(),
        "indexHasAgentEntry": any(entry.get("source") == "agent" for entry in index_entries),
    }
    if args.source_path:
        expected = str(Path(args.source_path).expanduser().resolve())
        actual = agent_json.get("sourceProjectPath") or agent_json.get("codexCheckoutPath")
        checks["sourcePathMatches"] = actual == expected

    result = {
        "projectId": project_id,
        "name": args.name,
        "projectRoot": str(project_root),
        "checks": checks,
        "indexEntries": index_entries,
        "agentMetadata": agent_json,
    }

    failed = [key for key, value in checks.items() if not value]
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"projectId: {project_id}")
        print(f"projectRoot: {project_root}")
        for key, value in checks.items():
            print(f"{key}: {'OK' if value else 'MISSING'}")
        if agent_json:
            print("agentMetadata: " + json.dumps(agent_json, sort_keys=True))

    if failed:
        raise SystemExit("Verification failed: " + ", ".join(failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
