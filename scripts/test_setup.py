"""Installer tests use inert tokens and temporary directories, never a real profile."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

spec = importlib.util.spec_from_file_location('qualtrics_setup', Path(__file__).with_name('setup.py'))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class SetupTests(unittest.TestCase):
    def test_private_template_is_blank_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            config = installer.initialize_private(Path(folder) / 'private')
            self.assertEqual((config / '.env').read_text(), 'APIKEY=\n')
            installer.atomic_write(config / '.env', 'APIKEY=inert-fixture-token\n', private=True)
            installer.initialize_private(config)
            self.assertEqual((config / '.env').read_text(), 'APIKEY=inert-fixture-token\n')

    def test_config_imports_private_token_without_output_or_repo_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            key = folder / 'token.txt'
            marker = 'inert-import-fixture-token'
            key.write_text(marker)
            args = Namespace(config_dir=folder / 'private', base_url=None, datacenter='iad1', import_key_file=key,
                             prompt_key=False, replace_key=False)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = installer.configure(args)
            self.assertTrue(result['keyPresent'])
            self.assertNotIn(marker, json.dumps(result) + output.getvalue())
            profile = json.loads((args.config_dir / 'profile.json').read_text())
            self.assertEqual(profile['baseURL'], 'https://iad1.qualtrics.com/API/v3/')
            self.assertNotIn(marker, json.dumps(profile))
            self.assertEqual((args.config_dir / '.env').read_text(), 'APIKEY=' + marker + '\n')
            self.assertEqual(key.read_text(), marker)

    def test_existing_key_changes_are_explicit_and_newlines_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            key = folder / 'token.txt'
            key.write_text('inert-first-token')
            args = Namespace(config_dir=folder / 'private', base_url=None, datacenter='iad1', import_key_file=key,
                             prompt_key=False, replace_key=False)
            installer.configure(args)
            key.write_text('inert-second-token')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                installer.configure(args)
            args.replace_key = True
            installer.configure(args)
            key.write_text('invalid\nnewline')
            with self.assertRaisesRegex(ValueError, 'single API token'):
                installer.configure(args)

    def test_private_config_cannot_be_inside_source(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            installer.initialize_private(installer.ROOT / 'private')

    def test_runtime_copy_excludes_credentials_and_updates_with_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'source'
            source.mkdir()
            (source / 'SKILL.md').write_text('old skill')
            (source / '.env').write_text('APIKEY=\n')
            (source / 'private.env').write_text('not a real credential')
            for name in ['agents', 'references', 'scripts']:
                (source / name).mkdir()
            destination = folder / 'hosts/codex/qualtrics'
            config = folder / 'private'
            result = installer.install_files(destination, config, source=source)
            self.assertEqual(result['status'], 'installed')
            self.assertFalse((destination / '.env').exists())
            self.assertFalse((destination / 'private.env').exists())
            self.assertEqual(installer.install_files(destination, config, source=source)['status'], 'current')
            (source / 'SKILL.md').write_text('new skill')
            with self.assertRaisesRegex(ValueError, '--update'):
                installer.install_files(destination, config, source=source)
            updated = installer.install_files(destination, config, update=True, source=source)
            self.assertEqual((destination / 'SKILL.md').read_text(), 'new skill')
            self.assertEqual((Path(updated['backup']) / 'SKILL.md').read_text(), 'old skill')

    def test_api_base_rejects_url_credentials_and_non_https(self):
        with tempfile.TemporaryDirectory() as folder:
            for base in ['http://example.org/API/v3/', 'https://name:password@example.org/API/v3/']:
                args = Namespace(config_dir=Path(folder) / 'private', base_url=base, datacenter=None,
                                 import_key_file=None, prompt_key=False, replace_key=False)
                with self.assertRaisesRegex(ValueError, 'HTTPS'):
                    installer.configure(args)

    def test_datacenter_only_update_preserves_existing_credential_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for mode in ['keyFile', 'envFile', 'bearerTokenFile']:
                config = installer.initialize_private(folder / mode)
                credential = folder / (mode + '.txt')
                credential.write_text('APIKEY=inert-token\n' if mode == 'envFile' else 'inert-token')
                (config / 'profile.json').write_text(json.dumps({'datacenter': 'iad1', mode: str(credential)}))
                args = Namespace(config_dir=config, base_url=None, datacenter='pdx1', import_key_file=None, prompt_key=False, replace_key=False)
                installer.configure(args)
                profile = json.loads((config / 'profile.json').read_text())
                self.assertEqual(profile[mode], str(credential))
                self.assertEqual(profile['baseURL'], 'https://pdx1.qualtrics.com/API/v3/')
                self.assertNotIn('inert-token', json.dumps(profile))

    def test_normal_ancestor_symlink_does_not_block_install_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            real = folder / 'real'; real.mkdir()
            alias = folder / 'alias'
            try:
                alias.symlink_to(real, target_is_directory=True)
            except OSError:
                self.skipTest('Directory symlinks unavailable in this test account')
            source = real / 'source'; source.mkdir()
            (source / 'SKILL.md').write_text('version one')
            destination = alias / 'installed'
            installer.install_files(destination, folder / 'private', source=source)
            (source / 'SKILL.md').write_text('version two')
            installer.install_files(destination, folder / 'private', source=source, update=True)
            self.assertEqual((destination / 'SKILL.md').read_text(), 'version two')

    @unittest.skipUnless(os.name == 'nt', 'Windows DACL regression')
    def test_explicit_everyone_acl_is_removed_from_directory_and_existing_env(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'private'
            config.mkdir()
            (config / '.env').write_text('APIKEY=inert-token\n')
            installer.execute(['icacls', config, '/grant', '*S-1-1-0:(OI)(CI)R'])
            installer.execute(['icacls', config / '.env', '/grant', '*S-1-1-0:R'])
            installer.initialize_private(config)
            for file in [config, config / '.env']:
                acl = installer.execute(['icacls', file])
                self.assertNotIn('Everyone:', acl)
                self.assertNotIn('S-1-1-0:', acl)
            self.assertEqual((config / '.env').read_text(), 'APIKEY=inert-token\n')


if __name__ == '__main__':
    unittest.main()
