import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "slave/pixel/registry.json"
PIXEL_TASK = ROOT / "slave/tasks/pixel_task.py"


class HiNuServoModeAliasesTest(unittest.TestCase):
    def test_servo_ids_keep_blue_and_black_contract_aligned(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        aliases = {
            (entry["mode_type"], entry["mode_id"]): entry["local_mode_id"]
            for entry in registry["remote_mode_aliases"]
        }
        self.assertEqual(
            aliases,
            {
                (2, 0): None,
                (2, 1): None,
                (2, 2): 3,
                (2, 3): 2,
            },
        )

    def test_runtime_applies_alias_without_rewriting_reported_remote_id(self):
        source = PIXEL_TASK.read_text(encoding="utf-8")
        self.assertIn("self._remote_mode_aliases", source)
        self.assertIn("remote_mode_id = int(rid)", source)
        self.assertIn("local_mode_id = self._remote_mode_aliases.get", source)
        self.assertIn("self._modes.get(local_mode_id)", source)


if __name__ == "__main__":
    unittest.main()
