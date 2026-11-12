from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.verify_guard import git_blob_sha1, verify_repository


class ProtectedRepositoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".guard").mkdir()
        (self.root / "src").mkdir()
        self.protected = self.root / "src" / "stable.py"
        self.protected.write_text("VALUE = 7\n", encoding="utf-8")
        self.manifest_path = self.root / ".guard" / "manifest.json"
        self._write_manifest()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "guard-test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Guard Test"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial guard fixture"], cwd=self.root, check=True)

    def tearDown(self):
        self.temp.cleanup()

    def _write_manifest(self):
        payload = {
            "schema": "spectral-core.guard.v1",
            "files": {"src/stable.py": git_blob_sha1(self.protected.read_bytes())},
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_approved_baseline_passes(self):
        self.assertEqual(verify_repository(self.root), [])

    def test_modified_protected_file_fails(self):
        self.protected.write_text("VALUE = 8\n", encoding="utf-8")
        errors = verify_repository(self.root)
        self.assertTrue(any("protected file changed: src/stable.py" in item for item in errors))

    def test_new_tracked_file_fails_until_registered(self):
        extra = self.root / "src" / "new.py"
        extra.write_text("NEW = True\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/new.py"], cwd=self.root, check=True)
        errors = verify_repository(self.root)
        self.assertTrue(any("absent from the approved baseline: src/new.py" in item for item in errors))

    def test_missing_protected_file_fails(self):
        self.protected.unlink()
        errors = verify_repository(self.root)
        self.assertTrue(any("protected file is missing" in item for item in errors))

    def test_symbolic_link_is_rejected(self):
        self.protected.unlink()
        self.protected.symlink_to("missing-target")
        errors = verify_repository(self.root)
        self.assertTrue(any("symbolic links are not allowed" in item for item in errors))

    def test_manifest_cannot_hash_itself(self):
        payload = {
            "schema": "spectral-core.guard.v1",
            "files": {
                "src/stable.py": git_blob_sha1(self.protected.read_bytes()),
                ".guard/manifest.json": "0" * 40,
            },
        }
        self.manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertTrue(any("cannot include its own hash" in item for item in verify_repository(self.root)))

    def test_invalid_digest_fails(self):
        self.manifest_path.write_text(
            json.dumps({"schema": "spectral-core.guard.v1", "files": {"src/stable.py": "bad"}}),
            encoding="utf-8",
        )
        self.assertTrue(any("invalid Git blob SHA-1" in item for item in verify_repository(self.root)))


if __name__ == "__main__":
    unittest.main()
