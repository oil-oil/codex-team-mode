from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
PROFILES = {
    "Explorer.toml": ("Explorer", "gpt-6-luna", "medium", "read-only"),
    "Executor.toml": ("Executor", "gpt-6-luna", "xhigh", "workspace-write"),
    "Reviewer.toml": ("Reviewer", "gpt-6-sol", "high", "workspace-write"),
    "default.toml": ("default", "gpt-6-luna", "low", "read-only"),
}


class AgentProfileTests(unittest.TestCase):
    def profile(self, name: str) -> dict:
        return tomllib.loads((ROOT / "agents" / name).read_text(encoding="utf-8"))

    def test_fixed_profile_boundaries(self) -> None:
        for filename, expected in PROFILES.items():
            with self.subTest(filename=filename):
                data = self.profile(filename)
                self.assertEqual(
                    (data["name"], data["model"], data["model_reasoning_effort"], data["sandbox_mode"]),
                    expected,
                )
                self.assertTrue(data["developer_instructions"].isascii())
                self.assertLess(len(data["developer_instructions"].split()), 75)

    def test_advisor_is_writable_and_model_free(self) -> None:
        data = self.profile("ExpertAdvisor.toml")
        self.assertEqual(data["name"], "ExpertAdvisor")
        self.assertEqual(data["sandbox_mode"], "workspace-write")
        self.assertNotIn("model", data)
        self.assertNotIn("model_reasoning_effort", data)
        self.assertTrue(data["developer_instructions"].isascii())
        self.assertLess(len(data["developer_instructions"].split()), 75)

    def test_roles_stay_bounded(self) -> None:
        for filename in ("Explorer.toml", "Executor.toml", "Reviewer.toml", "ExpertAdvisor.toml"):
            with self.subTest(filename=filename):
                instructions = self.profile(filename)["developer_instructions"]
                self.assertRegex(instructions.lower(), r"do not (?:edit or )?spawn subagents")
        self.assertIn("large codebase", self.profile("Explorer.toml")["developer_instructions"])
        self.assertIn("material", self.profile("Reviewer.toml")["developer_instructions"])
        self.assertIn("DISPATCH BLOCKED", self.profile("default.toml")["developer_instructions"])


if __name__ == "__main__":
    unittest.main()
