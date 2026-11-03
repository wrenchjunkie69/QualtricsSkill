import csv
import io
import json
import tempfile
import subprocess
import sys
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from results import api, fetch_results, unpack_csv


class ResultsTests(unittest.TestCase):
    def test_fetch_is_export_only_preserves_options_and_builds_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            calls = []
            stream = io.StringIO(newline='')
            csv.writer(stream).writerows([['ResponseId', 'Q1'], ['Response ID', 'How satisfied?'],
                                         ['{"ImportId":"_recordId"}', '{"ImportId":"QID1"}'], ['R_TEST', '5']])
            def fake(arguments):
                calls.append(arguments)
                if arguments[0] == 'request':
                    return {'data': {'result': {'Questions': {'QID1': {'DataExportTag': 'Q1', 'QuestionType': 'MC', 'Selector': 'SAVR'}}}}}
                self.assertEqual(arguments[0], 'export')
                options_file = Path(arguments[arguments.index('--json-file') + 1])
                self.assertEqual(json.loads(options_file.read_text())['useLabels'], True)
                output_file = Path(arguments[arguments.index('--output') + 1])
                with zipfile.ZipFile(output_file, 'w') as archive:
                    archive.writestr('../../not-extracted.csv', stream.getvalue())
                return {'status': 200}
            output = Path(folder) / 'export'
            manifest = fetch_results('SV_Test', output, {'format': 'csv', 'useLabels': True}, client=fake)
            self.assertEqual(manifest['dataRows'], 1)
            self.assertEqual(manifest['headerRecords'], 3)
            self.assertFalse(manifest['modelingPerformed'])
            self.assertEqual([call[0] for call in calls], ['request', 'export'])
            self.assertFalse((Path(folder) / 'not-extracted.csv').exists())
            with (output / 'codebook.csv').open(newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[1]['question_id'], 'QID1')
            self.assertEqual(rows[1]['question_type'], 'MC')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                fetch_results('SV_Test', output, client=fake)

    def test_csv_download_without_zip_and_single_header(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            download = folder / 'download'
            download.write_text('id,value\na,1\nb,2\n')
            def fake(arguments):
                if arguments[0] == 'request':
                    return {'data': {'result': {'Questions': {}}}}
                target = Path(arguments[arguments.index('--output') + 1])
                target.write_bytes(download.read_bytes())
                return {}
            manifest = fetch_results('SV_Test', folder / 'result', client=fake)
            self.assertEqual(manifest['dataRows'], 2)
            self.assertEqual(manifest['headerRecords'], 1)

    def test_invalid_survey_and_non_csv_options_do_not_call_client(self):
        def fake(_):
            self.fail('must not contact API')
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'survey ID'):
                fetch_results('../bad', Path(folder) / 'result', client=fake)
            with self.assertRaisesRegex(ValueError, 'needs CSV'):
                fetch_results('SV_Test', Path(folder) / 'result', {'format': 'json'}, client=fake)

    def test_archive_multiple_csv_or_size_limit_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            archive = folder / 'download.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('a.csv', 'data')
                handle.writestr('b.csv', 'data')
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                unpack_csv(archive, folder / 'result.csv')
            archive.write_text('x' * 100)
            with self.assertRaisesRegex(ValueError, 'size limit'):
                unpack_csv(archive, folder / 'result.csv', max_bytes=10)

    def test_export_job_is_saved_while_child_is_still_polling(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            release = folder / 'release'
            child = ('import json,sys,time; from pathlib import Path; '
                     'print(json.dumps({"progressId":"ES_inert","pollPath":"/surveys/SV_Test/export-responses/ES_inert"}),file=sys.stderr,flush=True); '
                     'p=Path(sys.argv[1]);\nwhile not p.exists(): time.sleep(0.02)\n'
                     'print(json.dumps({"status":200}))')
            real_popen = subprocess.Popen
            results, errors = [], []
            def inert_process(_arguments, **kwargs):
                return real_popen([sys.executable, '-c', child, str(release)], **kwargs)
            def retrieve():
                try:
                    results.append(api(['export', '--output', str(folder / 'download.zip')]))
                except Exception as error:
                    errors.append(error)
            with patch('results.subprocess.Popen', inert_process):
                thread = threading.Thread(target=retrieve)
                thread.start()
                deadline = time.time() + 5
                while not (folder / 'export-job.json').exists() and time.time() < deadline:
                    time.sleep(0.02)
                saved_while_polling = (folder / 'export-job.json').exists() and thread.is_alive()
                release.touch()
                thread.join(timeout=5)
            self.assertTrue(saved_while_polling)
            self.assertFalse(errors)
            self.assertEqual(results[0]['status'], 200)


if __name__ == '__main__':
    unittest.main()
