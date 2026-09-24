from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "team-mode"


class TeamModeResourceTests(unittest.TestCase):
    def test_skill_local_resources_exist(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        references = set(re.findall(r"\]\((references/[^)#]+)\)", skill))
        scripts = set(re.findall(r"scripts/[a-z_]+\.py", skill))
        self.assertTrue(references)
        for target in references | scripts:
            with self.subTest(target=target):
                self.assertTrue((SKILL / target).is_file())


if __name__ == "__main__":
    unittest.main()
