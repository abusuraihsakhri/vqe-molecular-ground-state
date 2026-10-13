import test from 'node:test';
import assert from 'node:assert/strict';
import {solveVqe, energy, localAudit} from '../web/core.mjs';

for (const [offset, z, x] of [[-1, .5, .25], [0, 1, 0], [0, 0, -2], [5, -.7, 1.2]]) {
  test('VQE matches exact 2x2 eigensystem', () => {
    const r = solveVqe(offset, z, x);
    assert.ok(r.converged);
    assert.ok(r.absolute_error < 1e-8);
    assert.ok(Math.abs(r.exact_energy - (offset - Math.hypot(z,x))) < 1e-12);
    assert.ok(Math.abs(r.energy - energy(r.theta_radians, offset, z, x)) < 1e-12);
  });
}
test('rejects NaN and infinity', () => {
  assert.throws(() => solveVqe(Infinity), /finite/);
  assert.throws(() => solveVqe(NaN), /finite/);
});
test('local audit is explicitly unsigned', () => {
  const r = localAudit({task_id:'A',target_identifier:'B',primary_metric:10,
    secondary_metric:1,status_descriptor:'NOMINAL',is_critical_flag:false});
  assert.equal(r.total_alerts, 0);
  assert.match(r.mode, /NOT A SIGNED AUDIT/);
  assert.ok(!('audit_hash' in r));
});
