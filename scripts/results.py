"""Retrieve requested Qualtrics results and metadata. No automatic modeling.

Python 3.10+ standard library; uses the Node API client for authenticated requests.
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def api(arguments):
    process = subprocess.Popen(['node', str(ROOT / 'scripts/qualtrics.mjs')] + [str(v) for v in arguments],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    stdout = []
    reader = threading.Thread(target=lambda: stdout.append(process.stdout.read()), daemon=True)
    reader.start()
    try:
        for line in process.stderr:
            try:
                item = json.loads(line)
                if arguments and arguments[0] == 'export' and '--output' in arguments and isinstance(item.get('progressId'), str) and isinstance(item.get('pollPath'), str):
                    job = {'progressId': item['progressId'], 'pollPath': item['pollPath']}
                    file = Path(arguments[arguments.index('--output') + 1]).parent / 'export-job.json'
                    file.write_text(json.dumps(job, indent=2) + '\n', encoding='utf-8')
            except (ValueError, AttributeError):
                pass
        process.wait()
        reader.join()
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()
    if process.returncode:
        raise RuntimeError('Qualtrics API operation failed. Check the private profile/key, API error and saved job state; do not blindly recreate a write/export job')
    try:
        return json.loads(''.join(stdout))
    except ValueError:
        raise RuntimeError('API helper did not return structured JSON; inspect the client installation without displaying credentials') from None


def unpack_csv(downloaded, output, max_bytes=1024 * 1024 * 1024):
    downloaded, output = Path(downloaded), Path(output)
    if output.exists():
        raise ValueError('CSV output already exists')
    if zipfile.is_zipfile(downloaded):
        with zipfile.ZipFile(downloaded) as archive:
            candidates = [entry for entry in archive.infolist() if not entry.is_dir() and entry.filename.lower().endswith('.csv')]
            if len(candidates) != 1 or candidates[0].file_size > max_bytes:
                raise ValueError('Expected exactly one CSV under the configured size limit; inspect the archive separately')
            # Do not extract archive paths: stream the selected CSV to one fixed output path.
            with archive.open(candidates[0]) as source, output.open('xb') as destination:
                copied = 0
                while chunk := source.read(1024 * 1024):
                    copied += len(chunk)
                    if copied > max_bytes:
                        raise ValueError('CSV exceeded the configured size limit')
                    destination.write(chunk)
    else:
        if downloaded.stat().st_size > max_bytes:
            raise ValueError('CSV exceeded the configured size limit')
        with downloaded.open('rb') as source, output.open('xb') as destination:
            shutil.copyfileobj(source, destination)


def build_codebook(file, definition, output):
    with Path(file).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        header = next(reader)
        second = next(reader, [])
        third = next(reader, [])
        imports = []
        for value in third:
            try:
                item = json.loads(value)
                imports.append(item.get('ImportId') if isinstance(item, dict) else None)
            except ValueError:
                imports.append(None)
        three = len(third) == len(header) and any(imports)
        row_count = sum(1 for row in reader if row) + (0 if three else int(bool(second)) + int(bool(third)))
    questions = definition.get('Questions', {})
    rows = []
    for index, column in enumerate(header):
        import_id = imports[index] if three else None
        matches = [qid for qid in questions if import_id == qid or (import_id and import_id.startswith(qid + '_'))]
        qid = max(matches, key=len) if matches else next((q for q, value in questions.items() if value.get('DataExportTag') == column), None)
        question = questions.get(qid, {})
        rows.append({'export_column': column, 'label': second[index] if three and index < len(second) else '',
                     'import_id': import_id or '', 'question_id': qid or '', 'question_type': question.get('QuestionType', ''),
                     'selector': question.get('Selector', ''), 'measurement_note': 'Confirm measurement scale, units and coding from the research plan before analysis'})
    with Path(output).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {'dataRows': row_count, 'columns': len(header), 'headerRecords': 3 if three else 1}


def fetch_results(survey, output, options=None, profile=None, client=api):
    import re
    if not re.fullmatch(r'SV_[A-Za-z0-9]+', survey):
        raise ValueError('Use a real survey ID from the API survey list')
    output = Path(output).expanduser().resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Save research results outside the public skill/repository directory')
    if output.exists():
        raise ValueError('Output directory already exists; choose a new export directory')
    options = dict(options or {'format': 'csv', 'compress': True, 'useLabels': False})
    if options.get('format') != 'csv':
        raise ValueError('This retrieval/codebook helper needs CSV; use the generic API export for other formats')
    common = ['--profile', str(profile)] if profile else []
    # Resolve permissions/resource before starting a new export job.
    response = client(['request', '--path', '/survey-definitions/' + survey] + common)
    definition = response['data']['result']
    output.mkdir(parents=True)
    (output / 'definition.json').write_text(json.dumps(definition, indent=2) + '\n', encoding='utf-8')
    parameters = output / 'export-options.json'
    parameters.write_text(json.dumps(options, indent=2) + '\n', encoding='utf-8')
    archive = output / 'responses-download.zip'
    client(['export', '--survey', survey, '--json-file', str(parameters), '--output', str(archive)] + common)
    data = output / 'responses.csv'
    unpack_csv(archive, data)
    counts = build_codebook(data, definition, output / 'codebook.csv')
    manifest = {'surveyId': survey, 'retrievedAtUTC': datetime.now(timezone.utc).isoformat(), 'exportOptions': options,
                **counts, 'responses': str(data), 'definition': str(output / 'definition.json'), 'codebook': str(output / 'codebook.csv'),
                'sha256': hashlib.sha256(data.read_bytes()).hexdigest(), 'modelingPerformed': False,
                'notes': ['Count describes the returned export under its options, not a population count.',
                          'Definition and responses are separate API reads; ongoing survey edits/collection are not an atomic snapshot.'],
                'nextStep': 'Provide the saved locations and export scope to the student. Ask whether they want to inspect or analyze it; do not start optional modeling.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch'])
    parser.add_argument('--survey', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--options', type=Path, help='Complete documented CSV export request body')
    parser.add_argument('--profile', type=Path)
    args = parser.parse_args()
    try:
        options = json.loads(args.options.read_text(encoding='utf-8-sig')) if args.options else None
        print(json.dumps(fetch_results(args.survey, args.out, options, args.profile), indent=2))
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None
