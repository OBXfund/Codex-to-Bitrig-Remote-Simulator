#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
PREPARE_SCRIPT = SCRIPTS_DIR / "prepare_bitrig_agent_prompt.py"
VERIFY_SCRIPT = SCRIPTS_DIR / "verify_bitrig_agent_project.py"
HOME = Path.home()
BITRIG_APP = Path("/Applications/Bitrig.app")
BITRIG_LIBRARY = HOME / "Library" / "Bitrig"
DEFAULT_OUTPUT_DIR = Path.cwd() / ".bitrig-agent-bridge"


def run_command(command: list[str], timeout: float = 60.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout)


def print_step(title: str, message: str) -> None:
    print(f"[{title}] {message}")


def load_prepare_payload(args: argparse.Namespace, output_dir: Path | None = None) -> dict[str, Any]:
    command = [sys.executable, str(PREPARE_SCRIPT), "--project", args.project, "--json"]
    if getattr(args, "name", None):
        command.extend(["--name", args.name])
    if getattr(args, "agent_name", None):
        command.extend(["--agent-name", args.agent_name])
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        command.extend(["--output", str(output_dir / "agent-prompt.txt")])

    result = run_command(command)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "Preparation failed.")
    return json.loads(result.stdout)


def doctor_payload(project: str | None = None) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "macOS": platform.system() == "Darwin",
        "python3": shutil.which("python3") is not None or Path(sys.executable).exists(),
        "bitrigAppPresent": BITRIG_APP.exists(),
        "bitrigLibraryPresent": BITRIG_LIBRARY.exists(),
        "prepareScriptPresent": PREPARE_SCRIPT.exists(),
        "verifyScriptPresent": VERIFY_SCRIPT.exists(),
    }
    if project:
        source = Path(project).expanduser().resolve()
        checks["sourceProjectExists"] = source.exists()
        checks["sourceProjectIsDirectory"] = source.is_dir()

    required = ["macOS", "python3", "prepareScriptPresent", "verifyScriptPresent"]
    failed = [name for name in required if not checks.get(name)]
    status = "preflight_failed" if failed else "preflight_ready"
    return {
        "schemaVersion": "1.0",
        "status": status,
        "checks": checks,
        "failedRequiredChecks": failed,
        "notes": [
            "Bitrig.app is required before creating a native Agent project.",
            "Bitrig's user-library folder may not exist until Bitrig has been opened once.",
        ],
    }


def cmd_doctor(args: argparse.Namespace) -> int:
    payload = doctor_payload(args.project)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "preflight_ready" else 1

    print_step("Preflight", "Checking local prerequisites for a Bitrig Agent bridge run.")
    for key, value in payload["checks"].items():
        print(f"{key}: {'OK' if value else 'MISSING'}")
    if payload["failedRequiredChecks"]:
        print_step("Blocked", "Fix the missing required checks before continuing.")
        return 1
    if not payload["checks"].get("bitrigAppPresent"):
        print_step("Next", "Install or move Bitrig.app into Applications before running setup.")
    elif not payload["checks"].get("bitrigLibraryPresent"):
        print_step("Next", "Open Bitrig once so it can create its local library state.")
    else:
        print_step("Ready", "Preflight passed.")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser().resolve()
    prompt_path = output_dir / "agent-prompt.txt"
    payload = load_prepare_payload(args, output_dir)
    payload["promptPath"] = str(prompt_path)
    payload["status"] = "prepared"
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print_step("Project", f"Source project: {payload['sourceProjectName']} at {payload['projectPath']}")
    print_step("Project", f"Visible Bitrig Agent name: {payload['agentName']}")
    print_step("Prompt", f"Wrote Bitrig Agent prompt to {prompt_path}")
    print_step("Next", "Open Bitrig, choose Agent, create a new project, paste this prompt, and submit it.")
    return 0


def copy_prompt_to_clipboard(prompt_path: Path) -> bool:
    pbcopy = shutil.which("pbcopy")
    if not pbcopy:
        return False
    result = subprocess.run([pbcopy], input=prompt_path.read_text(encoding="utf-8"), text=True, check=False)
    return result.returncode == 0


def open_bitrig() -> bool:
    opener = shutil.which("open")
    if not opener:
        return False
    result = subprocess.run([opener, "-a", "Bitrig"], text=True, capture_output=True, check=False)
    return result.returncode == 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.json:
        print_step("Preflight", "Checking local prerequisites before setup.")
    preflight = doctor_payload(args.project)
    required_failed = preflight["failedRequiredChecks"]
    if required_failed:
        if args.json:
            print(json.dumps(preflight, indent=2, sort_keys=True))
        else:
            print_step("Blocked", "Missing required checks: " + ", ".join(required_failed))
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve()
    prompt_path = output_dir / "agent-prompt.txt"
    payload = load_prepare_payload(args, None if args.dry_run else output_dir)
    response: dict[str, Any] = {
        "schemaVersion": "1.0",
        "status": "dry_run_ready" if args.dry_run else "ready_for_bitrig_setup",
        "preflight": preflight,
        "prepared": payload,
        "promptPath": str(prompt_path),
        "userMustVerifyRemote": True,
        "remoteVerification": [
            "Open Bitrig Remote on iPhone.",
            "Refresh or reconnect to this Mac if needed.",
            "Open Agent, not Classic.",
            f"Confirm {payload['agentName']} appears and opens.",
        ],
    }
    if args.dry_run:
        if args.json:
            print(json.dumps(response, indent=2, sort_keys=True))
        else:
            print_step("Project", f"Resolved Agent name: {payload['agentName']}")
            print_step("Dry Run", f"Prompt would be written to {prompt_path}")
            print_step("Remote", "The user will need to confirm the Agent appears and opens in Bitrig Remote.")
        return 0

    clipboard = copy_prompt_to_clipboard(prompt_path)
    opened = False if args.no_open else open_bitrig()
    response["copiedPromptToClipboard"] = clipboard
    response["openedBitrig"] = opened

    if args.json:
        print(json.dumps(response, indent=2, sort_keys=True))
        return 0

    print_step("Project", f"Source project: {payload['sourceProjectName']} at {payload['projectPath']}")
    print_step("Project", f"Visible Bitrig Agent name: {payload['agentName']}")
    print_step("Prompt", f"Wrote Bitrig Agent prompt to {prompt_path}")
    print_step("Clipboard", "Prompt copied to clipboard." if clipboard else "Prompt was not copied; paste it from the prompt file.")
    print_step("Bitrig", "Bitrig was opened." if opened else "Open Bitrig manually, then choose Agent.")
    print_step("Bitrig", "Create a new Agent project, paste the prompt, submit it, and wait for Bitrig to finish.")
    print_step("Verify", f"After Bitrig finishes, run: python3 {Path(__file__).name} verify --name {payload['agentName']!r} --source-path {payload['projectPath']!r}")
    print_step("Remote", f"Finally, confirm {payload['agentName']} appears and opens in Bitrig Remote on iPhone.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    command = [sys.executable, str(VERIFY_SCRIPT), "--name", args.name]
    if args.source_path:
        command.extend(["--source-path", args.source_path])
    if args.json:
        command.append("--json")
    result = run_command(command, timeout=args.timeout)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr and not args.json:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode == 0 and not args.json:
        print_step("Remote", "Local Bitrig verification passed. The user still must confirm this Agent appears and opens in Bitrig Remote on iPhone.")
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and verify a native Bitrig Agent project for Bitrig Remote.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local prerequisites.")
    doctor.add_argument("--project", help="Optional source project path to include in checks.")
    doctor.add_argument("--json", action="store_true", help="Emit JSON.")
    doctor.set_defaults(func=cmd_doctor)

    prepare = subparsers.add_parser("prepare", help="Prepare the Agent prompt.")
    prepare.add_argument("--project", required=True, help="Local iOS project path.")
    prepare.add_argument("--name", help="Override the source project name.")
    prepare.add_argument("--agent-name", help="Override the visible Bitrig Agent name.")
    prepare.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated setup files.")
    prepare.add_argument("--json", action="store_true", help="Emit JSON.")
    prepare.set_defaults(func=cmd_prepare)

    run = subparsers.add_parser("run", help="Run preflight and prepare Bitrig setup.")
    run.add_argument("--project", required=True, help="Local iOS project path.")
    run.add_argument("--name", help="Override the source project name.")
    run.add_argument("--agent-name", help="Override the visible Bitrig Agent name.")
    run.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated setup files.")
    run.add_argument("--dry-run", action="store_true", help="Show setup without opening Bitrig or using the clipboard.")
    run.add_argument("--no-open", action="store_true", help="Do not open Bitrig.")
    run.add_argument("--json", action="store_true", help="Emit JSON.")
    run.set_defaults(func=cmd_run)

    verify = subparsers.add_parser("verify", help="Verify the local Bitrig Agent evidence.")
    verify.add_argument("--name", required=True, help="Visible Bitrig Agent project name.")
    verify.add_argument("--source-path", help="Expected local source project path.")
    verify.add_argument("--timeout", type=float, default=60.0, help="Verification timeout in seconds.")
    verify.add_argument("--json", action="store_true", help="Emit JSON.")
    verify.set_defaults(func=cmd_verify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
