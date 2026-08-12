from __future__ import annotations

import unittest

from github_service.client import GitHubClient


class GitHubClientHelpersTests(unittest.TestCase):
    def test_accepts_repository_relative_paths(self):
        self.assertEqual(GitHubClient.normalize_file_path("notes.md"), "notes.md")
        self.assertEqual(
            GitHubClient.normalize_file_path(".github/workflows/test.yml"),
            ".github/workflows/test.yml",
        )
        self.assertEqual(
            GitHubClient.normalize_file_path(r"docs\notes.txt"),
            "docs/notes.txt",
        )

    def test_rejects_unsafe_paths(self):
        for path in ("", "/etc/passwd", "../secret", "a/../secret", "a//b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                GitHubClient.normalize_file_path(path)

    def test_append_text_does_not_add_leading_blank_line(self):
        self.assertEqual(GitHubClient.append_text("", "first"), "first")

    def test_append_text_respects_existing_newline(self):
        self.assertEqual(GitHubClient.append_text("first", "second"), "first\nsecond")
        self.assertEqual(GitHubClient.append_text("first\n", "second"), "first\nsecond")

    def test_only_main_branch_is_allowed(self):
        with self.assertRaisesRegex(ValueError, "main"):
            GitHubClient("token", "owner/repo", branch="feature", github=object())


if __name__ == "__main__":
    unittest.main()
