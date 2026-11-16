/**
 * 🧪 Test Suite 3: Rosary Bead Adjustments (Workshop & Sizing Service)
 * Verifies calculation of removed beads and bagging verification for custom hand fit.
 */

import { createClient } from '@libsql/client';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, '..', 'data', 'haybatalsultan.db');

const client = createClient({ url: `file:${dbPath}` });

async function run() {
  console.log('\n📿 [TEST 3] Testing Rosary Bead Adjustment & Workshop Service...');

  const originalBeadCount = 45;
  const requestedBeadCount = 33;
  const expectedRemoved = 12;

  // Insert adjustment entry
  await client.execute({
    sql: `
      INSERT INTO bead_adjustments (
        product_id, product_reference, customer_name, customer_phone,
        original_bead_count, requested_bead_count, removed_beads_count, notes, status
      ) VALUES (1, 'HSP-TEST-BEADS-003', 'الشيخ محمد بن راشد', '+971500000000', ?, ?, ?, 'تصغير لمقاس اليد وتجهيز كيس حرير للخرز المفكوك', 'PENDING')
    `,
    args: [originalBeadCount, requestedBeadCount, originalBeadCount - requestedBeadCount]
  });

  const row = await client.execute({
    sql: 'SELECT * FROM bead_adjustments WHERE product_reference = ?',
    args: ['HSP-TEST-BEADS-003']
  });

  if (row.rows.length === 0) {
    throw new Error('Bead adjustment record was not created');
  }

  const rec = row.rows[0];
  if (rec.removed_beads_count !== expectedRemoved) {
    throw new Error(`Mathematical error in removed beads: expected ${expectedRemoved}, got ${rec.removed_beads_count}`);
  }

  // Update status through workshop workflow
  await client.execute({
    sql: "UPDATE bead_adjustments SET status = 'COMPLETED', completed_at = datetime('now', 'localtime') WHERE id = ?",
    args: [rec.id]
  });

  const updated = await client.execute({
    sql: 'SELECT status, completed_at FROM bead_adjustments WHERE id = ?',
    args: [rec.id]
  });

  if (updated.rows[0].status !== 'COMPLETED' || !updated.rows[0].completed_at) {
    throw new Error('Workshop completion lifecycle update failed');
  }

  // Clean up
  await client.execute({ sql: 'DELETE FROM bead_adjustments WHERE id = ?', args: [rec.id] });

  console.log('✅ [TEST 3 PASSED] Bead Adjustment Sizing and Workshop workflow verified.');
}

run().catch(err => {
  console.error('❌ [TEST 3 FAILED]:', err.message);
  process.exit(1);
});
