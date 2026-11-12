#!/usr/bin/env python3
"""Verify the approved tracked-file baseline for Spectral Core.

The baseline uses Git blob SHA-1 values so it matches the object identifiers
reported by GitHub. This is a change-detection mechanism, not a signature.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_MANIFEST = ".guard/manifest.json"
SCHEMA = "spectral-core.guard.v1"
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class GuardError(Exception):
    """Raised when the repository baseline cannot be validated."""


def git_blob_sha1(content: bytes) -> str:
    """Return the SHA-1 of content using Git's blob object framing."""
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()


def _tracked_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GuardError("cannot enumerate tracked files with git ls-files: " + detail)
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise GuardError("manifest contains an empty or non-string file path")
    if "\\" in value:
        raise GuardError("manifest paths must use forward slashes: " + value)
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise GuardError("unsafe manifest path: " + value)
    if path.as_posix() != value:
        raise GuardError("non-canonical manifest path: " + value)
    return value


def _reject_symlink_path(root: Path, relative_path: str) -> bool:
    current = root
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _read_manifest(root: Path, manifest_rel: str) -> dict[str, str]:
    if _reject_symlink_path(root, manifest_rel):
        raise GuardError("guard manifest path contains a symbolic link: " + manifest_rel)
    manifest_path = root.joinpath(*PurePosixPath(manifest_rel).parts)
    if not manifest_path.is_file():
        raise GuardError("guard manifest is missing: " + manifest_rel)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GuardError("cannot read guard manifest: " + str(exc)) from exc

    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise GuardError("unsupported or missing guard manifest schema")
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise GuardError("manifest 'files' must be a non-empty object")

    normalized: dict[str, str] = {}
    for raw_path, digest in files.items():
        path = _safe_relative_path(raw_path)
        if path == manifest_rel:
            raise GuardError("the manifest cannot include its own hash")
        if not isinstance(digest, str) or not _SHA1_RE.fullmatch(digest):
            raise GuardError("invalid Git blob SHA-1 for " + path)
        normalized[path] = digest
    return normalized


def verify_repository(
    root: str | Path,
    manifest_rel: str = DEFAULT_MANIFEST,
) -> list[str]:
    """Return validation errors; an empty list means the guard passed."""
    root_path = Path(root).resolve()
    try:
        manifest_rel = _safe_relative_path(manifest_rel)
        expected = _read_manifest(root_path, manifest_rel)
        actual = _tracked_files(root_path)
    except GuardError as exc:
        return [str(exc)]

    expected_paths = set(expected) | {manifest_rel}
    errors: list[str] = []

    for path in sorted(expected_paths - actual):
        errors.append("expected tracked file is not tracked: " + path)
    for path in sorted(actual - expected_paths):
        errors.append("tracked file is absent from the approved baseline: " + path)

    for relative_path, expected_sha in sorted(expected.items()):
        if _reject_symlink_path(root_path, relative_path):
            errors.append("symbolic links are not allowed in protected paths: " + relative_path)
            continue
        candidate = root_path.joinpath(*PurePosixPath(relative_path).parts)
        if not candidate.is_file():
            errors.append("protected file is missing or not a regular file: " + relative_path)
            continue
        try:
            actual_sha = git_blob_sha1(candidate.read_bytes())
        except OSError as exc:
            errors.append("cannot read protected file " + relative_path + ": " + str(exc))
            continue
        if actual_sha != expected_sha:
            errors.append(
                "protected file changed: "
                + relative_path
                + " (expected "
                + expected_sha
                + ", got "
                + actual_sha
                + ")"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)

    errors = verify_repository(args.root, args.manifest)
    if errors:
        print("GUARD FAIL")
        for error in errors:
            print(" - " + error)
        return 1

    manifest = Path(args.root).resolve().joinpath(*PurePosixPath(args.manifest).parts)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print("GUARD PASS: verified " + str(len(payload["files"])) + " protected files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
