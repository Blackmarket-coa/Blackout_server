# Copyright 2026 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

from pathlib import Path

from synapse.util.release_train import validate_release_train_artifacts

from tests.unittest import TestCase


class ReleaseTrainGateTestCase(TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def test_gate_passes_when_required_files_and_sections_exist(self) -> None:
        root = Path(self.mktemp())

        self._write(
            root,
            "release/train/checklist.md",
            "# Checklist\n## Upstream Diff Review\n## CVE Review\n## Backport Plan\n",
        )
        self._write(
            root,
            "release/train/changelog.md",
            "# Changelog\n## Fork Policy Changes\n## Runtime Defaults\n## Security Backports\n",
        )

        self.assertEqual(validate_release_train_artifacts(root), [])

    def test_gate_fails_when_checklist_is_missing(self) -> None:
        root = Path(self.mktemp())
        self._write(
            root,
            "release/train/changelog.md",
            "# Changelog\n## Fork Policy Changes\n## Runtime Defaults\n## Security Backports\n",
        )

        errors = validate_release_train_artifacts(root)
        self.assertIn(
            "Missing required release artifact: release/train/checklist.md", errors
        )

    def test_gate_fails_when_required_section_missing(self) -> None:
        root = Path(self.mktemp())
        self._write(
            root,
            "release/train/checklist.md",
            "# Checklist\n## Upstream Diff Review\n## Backport Plan\n",
        )
        self._write(
            root,
            "release/train/changelog.md",
            "# Changelog\n## Fork Policy Changes\n## Runtime Defaults\n",
        )

        errors = validate_release_train_artifacts(root)
        self.assertIn(
            "release/train/checklist.md missing section heading: ## CVE Review", errors
        )
        self.assertIn(
            "release/train/changelog.md missing section heading: ## Security Backports",
            errors,
        )
