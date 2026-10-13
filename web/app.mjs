import {energy, solveVqe, localAudit} from './core.mjs';

const byId = id => document.getElementById(id);
const numeric = id => {
  const value = byId(id).value.trim();
  if (!value) throw new Error('Missing value: ' + id);
  const num = Number(value);
  if (!Number.isFinite(num)) throw new Error('Invalid numeric input: ' + id);
  return num;
};
const fmt = x => Number(x).toFixed(9);

function plot(offset, z, x, theta) {
  const canvas = byId('energy-plot');
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const w = canvas.width, h = canvas.height, pad = 38;
  ctx.clearRect(0, 0, w, h);
  const n = 181, values = [];
  for (let i = 0; i < n; i++) {
    values.push(energy(2 * Math.PI * i / (n - 1), offset, z, x));
  }
  const min = Math.min(...values), max = Math.max(...values);
  const spread = Math.max(max - min, 1e-8);
  const xy = (i, value) => [
    pad + (w - 2 * pad) * i / (n - 1),
    h - pad - (h - 2 * pad) * (value - min + 0.08 * spread) / (1.16 * spread)
  ];
  ctx.strokeStyle = '#7187a3'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, pad / 2); ctx.lineTo(pad, h - pad);
  ctx.lineTo(w - pad / 2, h - pad); ctx.stroke();
  ctx.strokeStyle = '#74b0ff'; ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, i) => {
    const p = xy(i, value);
    if (i === 0) ctx.moveTo(p[0], p[1]);
    else ctx.lineTo(p[0], p[1]);
  });
  ctx.stroke();
  const p = xy(theta / (2 * Math.PI) * (n - 1), energy(theta, offset, z, x));
  ctx.fillStyle = '#f1c96f';
  ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, 2 * Math.PI); ctx.fill();
  ctx.fillStyle = '#d3e1ee'; ctx.font = '14px system-ui';
  ctx.fillText('0', pad, h - 12);
  ctx.fillText('2π', w - pad - 20, h - 12);
  ctx.fillText('θ (radians)', w / 2 - 36, h - 12);
  ctx.fillText('Energy', 6, 18);
}

byId('vqe-form').addEventListener('submit', event => {
  event.preventDefault();
  try {
    const offset = numeric('offset'), z = numeric('z'), x = numeric('x');
    const result = solveVqe(offset, z, x);
    byId('vqe-energy').textContent = fmt(result.energy);
    byId('vqe-exact').textContent = fmt(result.exact_energy);
    byId('vqe-error').textContent = result.absolute_error.toExponential(3);
    byId('vqe-detail').textContent =
      'Optimal θ = ' + result.theta_radians.toFixed(7) + ' radians; ' +
      result.evaluations + ' energy evaluations; converged: ' + result.converged;
    plot(offset, z, x, result.theta_radians);
  } catch (err) {
    byId('vqe-detail').textContent = String(err.message || err);
    for (const id of ['vqe-energy', 'vqe-exact', 'vqe-error']) byId(id).textContent = '—';
  }
});

const likelyPhi = text => /\b\d{3}-\d{2}-\d{4}\b|\bMRN[\s:#-]*\d{4,}\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/i.test(text);

let audits = 0;
byId('audit-form').addEventListener('submit', async event => {
  event.preventDefault();
  const output = byId('audit-output');
  const button = byId('audit-button');
  button.disabled = true;
  try {
    const payload = {
      task_id: byId('task_id').value.trim(),
      target_identifier: byId('target_id').value.trim(),
      primary_metric: numeric('primary_metric'),
      secondary_metric: numeric('secondary_metric'),
      status_descriptor: byId('status_descriptor').value.trim(),
      is_critical_flag: byId('is_critical').checked
    };
    if ([payload.task_id, payload.target_identifier, payload.status_descriptor].some(likelyPhi)) {
      throw new Error('Potential sensitive identifier detected. Use synthetic IDs only.');
    }
    if ([payload.primary_metric, payload.secondary_metric].some(x => Math.abs(x) > 1e6)) {
      throw new Error('Metric exceeds the supported magnitude (1,000,000).');
    }
    let data, mode;
    const staticSite = location.protocol === 'file:' || location.hostname.endsWith('.github.io');
    if (!staticSite) {
      try {
        const response = await fetch('./api/audit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        if (response.status === 404) {
          mode = 'LOCAL DEMO';
        } else {
          const body = await response.json();
          if (!response.ok) throw new Error(body.detail || 'API returned HTTP ' + response.status);
          data = body;
          mode = 'PYTHON BACKEND — HMAC CHAIN';
        }
      } catch (err) {
        if (mode !== 'LOCAL DEMO' && !(err instanceof TypeError)) throw err;
        mode = 'LOCAL DEMO';
      }
    } else {
      mode = 'LOCAL DEMO';
    }
    if (!data) data = localAudit(payload);
    byId('connection-label').textContent = mode === 'LOCAL DEMO'
      ? 'Unsigned browser simulation — no server audit trail.'
      : 'Backend evaluation — audit trail generated on Python server.';
    output.textContent = JSON.stringify(data, null, 2);
    byId('audit-count').textContent = String(++audits);
  } catch (err) {
    output.textContent = 'Evaluation failed: ' + String(err.message || err);
    byId('connection-label').textContent = 'No completed evaluation.';
  } finally {
    button.disabled = false;
  }
});

byId('vqe-form').requestSubmit();
