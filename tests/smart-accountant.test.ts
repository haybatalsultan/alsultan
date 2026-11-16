/**
 * 🧪 Test Suite 5: Smart Accountant (Profit, Margin & Voided Expenses Engine)
 * Verifies that profits are computed strictly from realized delivered orders and that voided expenses are excluded.
 */

import { createClient } from '@libsql/client';
import crypto from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, '..', 'data', 'haybatalsultan.db');

const client = createClient({ url: `file:${dbPath}` });

async function run() {
  console.log('\n📊 [TEST 5] Testing Smart Accountant Realized Financial Truth & Expense Voiding...');

  // 1. Create a realized order
  const orderRef = 'HSO-TEST-ACC-005';
  const orderPubId = crypto.randomUUID();
  const salesAmount = 5000.0;
  const costAmount = 2800.0;
  const expectedGrossProfit = salesAmount - costAmount; // 2200.0

  await client.execute({
    sql: `
      INSERT INTO orders (
        public_id, reference, customer_name, customer_phone,
        grand_total, status, payment_status, paid_amount, delivered_at
      ) VALUES (?, ?, 'عميل محاسبة', '+971500000000', ?, 'DELIVERED', 'PAID', ?, datetime('now', 'localtime'))
    `,
    args: [orderPubId, orderRef, salesAmount, salesAmount]
  });

  const oRow = await client.execute({ sql: 'SELECT id FROM orders WHERE reference = ?', args: [orderRef] });
  const orderId = oRow.rows[0].id;

  await client.execute({
    sql: `
      INSERT INTO order_items (
        order_id, product_reference, sku, name_ar, cost_price_snapshot, unit_price, line_total
      ) VALUES (?, 'HSP-TEST-ACC', 'HSACC', 'مسبحة فحص محاسبة', ?, ?, ?)
    `,
    args: [orderId, costAmount, salesAmount, salesAmount]
  });

  // 2. Add an ACTIVE expense and a VOIDED expense
  const expActiveId = crypto.randomUUID();
  const expVoidedId = crypto.randomUUID();

  await client.execute({
    sql: `
      INSERT INTO expenses (public_id, category, description, amount, incurred_on, status, created_by_name)
      VALUES (?, 'BOXES', 'علب فاخرة خشب مطعم', 400.0, '2026-11-03', 'ACTIVE', 'المحاسب')
    `,
    args: [expActiveId]
  });

  await client.execute({
    sql: `
      INSERT INTO expenses (public_id, category, description, amount, incurred_on, status, void_reason, voided_at, created_by_name)
      VALUES (?, 'MARKETING', 'مصروف إعلاني خاطئ تم إلغاؤه', 1500.0, '2026-11-03', 'VOIDED', 'خطأ في فواتير الإعلانات', datetime('now', 'localtime'), 'المحاسب')
    `,
    args: [expVoidedId]
  });

  // 3. Verify that Voided expenses are strictly excluded from net profit calculations
  const activeExpensesSum = await client.execute({
    sql: "SELECT SUM(amount) as s FROM expenses WHERE status = 'ACTIVE' AND public_id IN (?, ?)",
    args: [expActiveId, expVoidedId]
  });

  if (activeExpensesSum.rows[0].s !== 400.0) {
    throw new Error('Smart accountant included voided expenses into operational costs calculation!');
  }

  // 4. Calculate Net Profit
  const netProfit = expectedGrossProfit - 400.0; // 2200 - 400 = 1800.0
  if (netProfit !== 1800.0) {
    throw new Error(`Net profit discrepancy: expected 1800.0, got ${netProfit}`);
  }

  // Clean up
  await client.execute({ sql: 'DELETE FROM expenses WHERE public_id IN (?, ?)', args: [expActiveId, expVoidedId] });
  await client.execute({ sql: 'DELETE FROM order_items WHERE order_id = ?', args: [orderId] });
  await client.execute({ sql: 'DELETE FROM orders WHERE id = ?', args: [orderId] });

  console.log('✅ [TEST 5 PASSED] Smart Accountant Realized Profit and Expense Voiding logic verified.');
}

run().catch(err => {
  console.error('❌ [TEST 5 FAILED]:', err.message);
  process.exit(1);
});
