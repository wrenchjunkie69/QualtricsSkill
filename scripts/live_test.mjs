// Explicit integration test. Creates/deletes one isolated draft only with the flag below.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { QualtricsClient, run, readJSON } from './qualtrics.mjs';

const args = process.argv.slice(2);
const lifecycle = args.includes('--test-lifecycle');
const reportArg = args.indexOf('--report');
if (reportArg < 0 || !args[reportArg + 1]) throw new Error('Supply --report FILE in a new test-output directory');
const reportPath = path.resolve(args[reportArg + 1]);
const profile = await readJSON(process.env.QUALTRICS_PROFILE || path.join(os.homedir(), '.config/qualtrics/profile.json'));
const client = new QualtricsClient(profile);
const report = { startedAt: new Date().toISOString(), checks: [], fixtureSurveyId: null, cleanupVerified: false };
const save = () => fs.writeFile(reportPath, JSON.stringify(client.redact(report), null, 2) + '\n');
const check = (name, details) => { report.checks.push({ name, ...details }); };
let fixtureName;
try {
  const identity = await client.request({ target: '/whoami' });
  check('authentication', { httpStatus: identity.status, brand: identity.data.result.brandId });
  const listed = await run({ command: 'paginate', path: '/surveys', query: ['pageSize=100'] }, client);
  check('survey-pagination', { count: listed.count });
  if (listed.elements.length) {
    const id = listed.elements[0].id;
    const definition = await client.request({ target: `/survey-definitions/${encodeURIComponent(id)}` });
    check('existing-definition-read', { httpStatus: definition.status, questions: Object.keys(definition.data.result.Questions || {}).length });
  }
  if (lifecycle) {
    fixtureName = `__QUALTRICS_SKILL_TEST_${Date.now()}`;
    const created = await client.request({ method: 'POST', target: '/survey-definitions',
      body: { SurveyName: fixtureName, Language: 'EN', ProjectCategory: 'CORE' } });
    const id = created.data.result.SurveyID;
    if (!/^SV_[A-Za-z0-9]+$/.test(id || '')) throw new Error('Creation did not return a usable survey ID');
    report.fixtureSurveyId = id;
    await save();
    check('create-draft', { httpStatus: created.status, surveyId: id });
    const definition = await client.request({ target: `/survey-definitions/${id}` });
    if (definition.data.result.SurveyName !== fixtureName) throw new Error('Fixture identity readback failed');
    check('read-draft', { httpStatus: definition.status, state: definition.data.result.SurveyStatus });
    const question = {
      QuestionText: 'Disposable API integration test: choose an option.',
      DataExportTag: 'SKILL_TEST', QuestionType: 'MC', Selector: 'SAVR', SubSelector: 'TX',
      Choices: { 1: { Display: 'Option A' }, 2: { Display: 'Option B' } },
      ChoiceOrder: ['1', '2'], Configuration: { QuestionDescriptionOption: 'UseText' },
      Validation: { Settings: { ForceResponse: 'OFF', Type: 'None' } }
    };
    const added = await client.request({ method: 'POST', target: `/survey-definitions/${id}/questions`, body: question });
    const qid = added.data.result.QuestionID;
    if (!/^QID[A-Za-z0-9]+$/.test(qid || '')) throw new Error('Question creation did not return its ID');
    check('create-question', { httpStatus: added.status, questionId: qid });
    const getQuestion = await client.request({ target: `/survey-definitions/${id}/questions/${qid}` });
    if (getQuestion.data.result.QuestionText !== question.QuestionText) throw new Error('Question readback mismatch');
    const updated = { ...getQuestion.data.result, QuestionText: 'Updated disposable API integration test.' };
    const changed = await client.request({ method: 'PUT', target: `/survey-definitions/${id}/questions/${qid}`, body: updated });
    const reread = await client.request({ target: `/survey-definitions/${id}/questions/${qid}` });
    if (reread.data.result.QuestionText !== updated.QuestionText) throw new Error('Question update readback mismatch');
    check('update-question-readback', { httpStatus: changed.status });
    const response = await client.request({ method: 'POST', target: `/surveys/${id}/responses`,
      body: { values: { [qid]: 1, finished: 1, progress: 100, userLanguage: 'EN' } } });
    const rid = response.data.result.responseId;
    if (!rid) throw new Error('Response creation did not return its ID');
    const retained = await client.request({ target: `/surveys/${id}/responses/${encodeURIComponent(rid)}` });
    if (retained.data.result.values[qid] !== 1) throw new Error('Test response readback mismatch');
    check('isolated-response-create-read', { httpStatus: response.status, responseId: rid });
    const exported = await run({ command: 'export', survey: id, format: 'csv', output: path.join(path.dirname(reportPath), 'fixture-responses.zip') }, client);
    check('export-job-poll-download', exported);
  }
} catch (error) {
  report.error = client.redact(error.message);
  process.exitCode = 1;
} finally {
  if (report.fixtureSurveyId) {
    try {
      const id = report.fixtureSurveyId;
      const read = await client.request({ target: `/survey-definitions/${id}` });
      if (read.data.result.SurveyName !== fixtureName || !fixtureName.startsWith('__QUALTRICS_SKILL_TEST_'))
        throw new Error('Cleanup guard refused an unexpected resource');
      const removed = await client.request({ method: 'DELETE', target: `/survey-definitions/${id}` });
      const remaining = await run({ command: 'paginate', path: '/surveys' }, client);
      report.cleanupVerified = !remaining.elements.some(s => s.id === id);
      check('delete-isolated-draft', { httpStatus: removed.status, absentFromList: report.cleanupVerified });
      if (!report.cleanupVerified) throw new Error('Fixture still listed after delete');
    } catch (error) {
      report.cleanupError = client.redact(error.message);
      process.exitCode = 1;
    }
  }
  report.finishedAt = new Date().toISOString();
  await save();
  console.log(JSON.stringify(client.redact(report), null, 2));
}
