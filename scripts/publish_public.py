#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BRANCH = "main"
DEFAULT_FORBIDDEN_TERMS = [
    "lo" + "nnie",
    "lo" + "nniejordan",
    "Lo" + "nnie Jordan",
]


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        raise SystemExit(f"command failed: {' '.join(command)}\n{output}")
    return result


def current_remote(name: str) -> str | None:
    result = subprocess.run(["git", "remote", "get-url", name], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def ensure_clean_worktree() -> None:
    result = run(["git", "status", "--porcelain"])
    if result.stdout.strip():
        raise SystemExit("worktree is not clean; commit or stash changes before publishing")


def ensure_remote(remote: str, url: str) -> None:
    existing = current_remote(remote)
    if existing and existing != url:
        raise SystemExit(f"remote {remote!r} already points to {existing!r}; refusing to replace it")
    if not existing:
        run(["git", "remote", "add", remote, url])


def forbidden_terms(args: argparse.Namespace) -> list[str]:
    terms = list(args.forbidden_term)
    return terms if terms else DEFAULT_FORBIDDEN_TERMS


def release_env(terms: list[str]) -> dict[str, str]:
    env = os.environ.copy()
    env["RELEASE_FORBIDDEN_TERMS"] = ",".join(terms)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the marketplace repo to a public remote and verify Codex install.")
    parser.add_argument("remote_url", help="Public Git repository URL, GitHub shorthand, HTTPS Git URL, or SSH Git URL.")
    parser.add_argument("--remote", default="origin", help="Git remote name to create or use.")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Branch to push and verify.")
    parser.add_argument(
        "--forbidden-term",
        action="append",
        default=[],
        help="Private term to reject during release and install verification. Repeat as needed.",
    )
    parser.add_argument("--no-push", action="store_true", help="Run checks and remote setup without pushing.")
    parser.add_argument("--skip-remote-verify", action="store_true", help="Skip clean Codex install verification from the remote URL.")
    args = parser.parse_args()
    private_terms = forbidden_terms(args)

    print("[Preflight] Checking worktree and release gates.")
    ensure_clean_worktree()
    run([sys.executable, str(ROOT / "scripts" / "release_check.py")], env=release_env(private_terms))
    local_verify = [sys.executable, str(ROOT / "scripts" / "verify_clean_codex_install.py")]
    for term in private_terms:
        local_verify.extend(["--forbidden-term", term])
    run(local_verify)

    print(f"[Remote] Ensuring {args.remote} points to the requested public source.")
    ensure_remote(args.remote, args.remote_url)

    if args.no_push:
        print("[Publish] Skipped push because --no-push was supplied.")
    else:
        print(f"[Publish] Pushing {args.branch} to {args.remote}.")
        run(["git", "push", "-u", args.remote, args.branch])

    if args.skip_remote_verify:
        print("[Verify] Skipped remote install verification.")
    else:
        print("[Verify] Installing from the published marketplace source in a clean Codex profile.")
        remote_verify = [
            sys.executable,
            str(ROOT / "scripts" / "verify_clean_codex_install.py"),
            "--source",
            args.remote_url,
            "--ref",
            args.branch,
        ]
        for term in private_terms:
            remote_verify.extend(["--forbidden-term", term])
        run(remote_verify)

    print("[Done] Public marketplace publication flow completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
