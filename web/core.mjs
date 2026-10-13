// Pure browser/Node calculations. Input units are consistent but arbitrary.
// H = offset I + z Z + x X, and |psi> = Ry(theta)|0>.
export function energy(theta, offset, z, x) {
  return offset + z * Math.cos(theta) + x * Math.sin(theta);
}
export function solveVqe(offset = -1, z = 0.5, x = 0.25) {
  if (![offset, z, x].every(v => typeof v === 'number' &&
      Number.isFinite(v) && Math.abs(v) <= 1e6)) {
    throw new Error('Coefficients must be finite real numbers within ±1,000,000.');
  }
  if (z === 0 && x === 0) {
    return {energy: offset, exact_energy: offset, absolute_error: 0,
      theta_radians: 0, evaluations: 1, converged: true};
  }
  const n = 72, spacing = 2 * Math.PI / n;
  let bestIndex = 0, best = Infinity;
  for (let i = 0; i < n; i++) {
    const val = energy(i * spacing, offset, z, x);
    if (val < best) { best = val; bestIndex = i; }
  }
  let left = bestIndex * spacing - spacing;
  let right = left + 2 * spacing;
  const ratio = (Math.sqrt(5) - 1) / 2;
  let p = right - ratio * (right - left);
  let q = left + ratio * (right - left);
  let fp = energy(p, offset, z, x);
  let fq = energy(q, offset, z, x);
  let evaluations = n + 2;
  for (let i = 0; i < 80 && right - left >= 1e-11; i++) {
    if (fp < fq) {
      right = q; q = p; fq = fp;
      p = right - ratio * (right - left); fp = energy(p, offset, z, x);
    } else {
      left = p; p = q; fp = fq;
      q = left + ratio * (right - left); fq = energy(q, offset, z, x);
    }
    evaluations++;
  }
  const theta = ((left + right) / 2 + 2 * Math.PI) % (2 * Math.PI);
  const resultEnergy = energy(theta, offset, z, x);
  const exact = offset - Math.hypot(z, x);
  const difference = Math.abs(resultEnergy - exact);
  return {energy: resultEnergy, exact_energy: exact,
    absolute_error: difference, theta_radians: theta,
    evaluations, converged: difference < 1e-8};
}
export function localAudit(p) {
  const flags = [];
  if (p.primary_metric > 25) flags.push('Primary metric exceeds reference bound (25.0)');
  if (p.secondary_metric > 12 || p.is_critical_flag) flags.push('Secondary metric or critical flag triggered');
  if (/DISCORDANT|ANOMALY|MUTANT|VIOLATION|FAIL|REJECT/i.test(p.status_descriptor)) {
    flags.push('Status descriptor indicates a protocol anomaly');
  }
  return {
    mode: 'LOCAL DEMONSTRATION — NOT A SIGNED AUDIT',
    task_id: p.task_id, target_identifier: p.target_identifier,
    overall_urgency: p.is_critical_flag ? 'CRITICAL_STAT_PANIC' :
      flags.length ? 'ELEVATED_RISK' : 'ROUTINE',
    total_alerts: flags.length,
    alerts: flags,
    note: 'Threshold simulation only. No server-side PHI controls or HMAC audit trail.'
  };
}
