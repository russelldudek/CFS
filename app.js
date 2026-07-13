const scenarios = {
  focused: {
    state: 'Focused', data: 'Definitions aligned', authority: 'Authority explicit', evidence: 'Evidence instrumented',
    text: '<strong>Focused:</strong> a named workflow owner, aligned definitions, explicit authority, and outcome evidence allow AI to assist safely.'
  },
  conflict: {
    state: 'Distorted', data: 'CRM definitions conflict', authority: 'Owner must reconcile', evidence: 'Do not automate ambiguity',
    text: '<strong>CRM conflict:</strong> pause automation, reconcile definitions and ownership, then create a reusable canonical view.'
  },
  unowned: {
    state: 'Unreliable', data: 'Document authority unclear', authority: 'No accountable steward', evidence: 'Quarantine from AI use',
    text: '<strong>Unowned documents:</strong> identify authoritative sources, freshness rules, access, and review responsibility before retrieval or generation.'
  },
  premature: {
    state: 'Premature', data: 'Data quality not bounded', authority: 'Human decision right vague', evidence: 'Run a constrained test',
    text: '<strong>AI before readiness:</strong> narrow the use case, state human authority, expose the missing controls, and test the smallest useful intervention.'
  }
};

document.querySelectorAll('.scenario-btn').forEach((button) => {
  button.addEventListener('click', () => {
    const scenario = scenarios[button.dataset.scenario];
    document.querySelectorAll('.scenario-btn').forEach((b) => b.setAttribute('aria-pressed', String(b === button)));
    document.getElementById('lensState').textContent = scenario.state;
    document.getElementById('lensData').textContent = scenario.data;
    document.getElementById('lensAuthority').textContent = scenario.authority;
    document.getElementById('lensEvidence').textContent = scenario.evidence;
    document.getElementById('scenarioReadout').innerHTML = scenario.text;
    const stage = document.querySelector('.lens-stage');
    stage.dataset.state = button.dataset.scenario;
  });
});
