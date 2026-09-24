from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "team-mode"


class TeamModeSkillContractTests(unittest.TestCase):
    def test_routing_and_fresh_context(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for role in ("Explorer", "Executor", "Reviewer", "ExpertAdvisor"):
            self.assertIn(f"`{role}`", skill)
        self.assertIn('`fork_turns="none"`', skill)
        self.assertIn("Always use it for `Reviewer` and `ExpertAdvisor`", skill)
        self.assertIn("An `Executor` may inherit a small number of recent parent turns", skill)
        self.assertIn("Use the smallest useful positive `fork_turns` value", skill)
        self.assertIn("not a fixed diagnosis or checklist", skill)
        self.assertIn("large codebase", skill)
        self.assertIn("repeated attempts", skill)
        self.assertIn("Team Mode does not require it", skill)
        self.assertIn("Other configured roles and models are allowed", skill)
        self.assertNotIn("Every `spawn_agent` call must explicitly pass `agent_type` as exactly one of", skill)
        self.assertNotIn("one concrete `Unresolved risk`", skill)
        self.assertLess(len(skill.splitlines()), 100)

    def test_profile_reference_matches_runtime_contract(self) -> None:
        reference = (SKILL / "references" / "custom-agents.md").read_text(encoding="utf-8")
        self.assertIn("optional `default.toml` sentinel", reference)
        self.assertIn("custom profile's fixed model and effort", reference)
        self.assertIn("all** local tasks", reference)
        self.assertIn("gpt-6-sol", reference)
        self.assertIn("gpt-6-luna", reference)
        self.assertIn("ExpertAdvisor.toml", reference)
        self.assertTrue((SKILL / "scripts" / "current_model.py").exists())

    def test_public_readmes_keep_visual_and_updated_roles(self) -> None:
        for filename in ("README.md", "README.zh-CN.md"):
            readme = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("./assets/readme/agent-map.webp", readme)
            self.assertIn("ExpertAdvisor", readme)
            self.assertIn("GPT-6 Sol High", readme)
        self.assertTrue((ROOT / "assets" / "readme" / "agent-map.webp").is_file())


if __name__ == "__main__":
    unittest.main()
