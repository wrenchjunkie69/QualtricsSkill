import subprocess
import tempfile
import unittest
from pathlib import Path

from public_check import check


class PublicCheckTests(unittest.TestCase):
    def test_blank_template_passes_and_filled_template_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.env').write_bytes(b'APIKEY=\n')
            (root / 'README.md').write_text('Portable instructions')
            self.assertTrue(check(root)['ok'])
            (root / '.env').write_text('APIKEY=inert-private-fixture\n')
            with self.assertRaisesRegex(ValueError, 'no value'):
                check(root)

    def test_staged_secret_is_rejected_when_worktree_template_was_cleared(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', str(root)], check=True, capture_output=True)
            (root / '.env').write_text('APIKEY=inert-index-fixture\n')
            subprocess.run(['git', '-C', str(root), 'add', '.env'], check=True, capture_output=True)
            (root / '.env').write_bytes(b'APIKEY=\n')
            with self.assertRaisesRegex(ValueError, 'staged/index'):
                check(root)

    def test_private_account_artifact_is_not_publishable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.env').write_bytes(b'APIKEY=\n')
            (root / 'profile.json').write_text('{"envFile":"private"}')
            with self.assertRaisesRegex(ValueError, 'Private credential'):
                check(root)


if __name__ == '__main__':
    unittest.main()
