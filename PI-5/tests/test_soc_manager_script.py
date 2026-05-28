import os
import unittest


SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'soc_manager.sh')
)


class TestSocManagerScript(unittest.TestCase):
    def test_api_model_choice_uses_gemini_3_flash_preview(self):
        with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
            script = f.read()

        self.assertIn('AI_MODEL="gemini-3-flash-preview"', script)

    def test_purge_logs_also_deletes_pending_ai_events(self):
        with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
            script = f.read()

        self.assertIn('DELETE FROM pending_ai_events', script)


if __name__ == '__main__':
    unittest.main()
