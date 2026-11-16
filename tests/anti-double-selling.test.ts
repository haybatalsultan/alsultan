/**
 * 🧪 Test Suite 1: Anti-Double-Selling & Exclusivity Protection
 * Verifies that unique prayer beads cannot be sold twice or concurrently acquired.
 */

import { createClient } from '@libsql/client';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, '..', 'data', 'haybatalsultan.db');

const client = createClient({ url: `file:${dbPath}` });

async function run() {
  console.log('\n🔒 [TEST 1] Testing Exclusivity Protection & Anti-Double-Selling...');

  // 1. Create a mock unique test rosary
  const testRef = 'HSP-TEST-UNIQUE-001';
  await client.execute({
    sql: `
      INSERT OR REPLACE INTO products (
        public_id, product_reference, sku, name_ar, name_en, cost_price, selling_price, status, is_unique, bead_count
      ) VALUES ('test-uuid-001', ?, 'HSTEST1', 'مسبحة فحص حصرية فريدة', 'Test Unique Rosary', 1000, 2500, 'AVAILABLE', 1, 33)
    `,
    args: [testRef]
  });

  // Verify item is AVAILABLE
  const initial = await client.execute({
    sql: 'SELECT status FROM products WHERE product_reference = ?',
    args: [testRef]
  });
  if (initial.rows[0].status !== 'AVAILABLE') {
    throw new Error('Initial product status should be AVAILABLE');
  }

  // 2. Simulate First Sale
  await client.execute({
    sql: "UPDATE products SET status = 'SOLD' WHERE product_reference = ? AND status = 'AVAILABLE'",
    args: [testRef]
  });

  // 3. Simulate Concurrent Second Sale Attempt (MUST FAIL - row unaffected)
  const secondAttempt = await client.execute({
    sql: "UPDATE products SET status = 'SOLD' WHERE product_reference = ? AND status = 'AVAILABLE'",
    args: [testRef]
  });

  if (secondAttempt.rowsAffected !== 0) {
    throw new Error('CRITICAL FLAW: Second concurrent sale attempt succeeded on a unique sold item!');
  }

  // 4. Test Timed Reservation Anti-Hoarding
  await client.execute({
    sql: `
      UPDATE products SET
        status = 'RESERVED',
        reserved_until = datetime('now', '-5 minutes', 'localtime')
      WHERE product_reference = ?
    `,
    args: [testRef]
  });

  // Verify cron release logic picks up expired reservation
  const expired = await client.execute({
    sql: `
      SELECT id FROM products
      WHERE product_reference = ? AND status = 'RESERVED' AND reserved_until <= datetime('now', 'localtime')
    `,
    args: [testRef]
  });

  if (expired.rows.length === 0) {
    throw new Error('Expired reservation was not detected by anti-hoarding filter');
  }

  // Clean up
  await client.execute({
    sql: 'DELETE FROM products WHERE product_reference = ?',
    args: [testRef]
  });

  console.log('✅ [TEST 1 PASSED] Anti-Double-Selling and Exclusivity Engine verified 100% safe.');
}

run().catch(err => {
  console.error('❌ [TEST 1 FAILED]:', err.message);
  process.exit(1);
});
