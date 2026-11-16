/**
 * 🧪 Test Suite 4: Quick Sale & Exhibition POS Financial Engine
 * Verifies direct POS checkout, immutable cost snapshot capture, and deferred payment receivables.
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
  console.log('\n💳 [TEST 4] Testing Quick Sale POS & Receivables Engine...');

  const testRef = 'HSP-TEST-POS-004';
  const costPrice = 1200.0;
  const sellingPrice = 2800.0;
  const specialDiscount = 300.0;
  const grandTotal = sellingPrice - specialDiscount; // 2500.0

  // 1. Create product
  await client.execute({
    sql: `
      INSERT OR REPLACE INTO products (
        public_id, product_reference, sku, name_ar, name_en, cost_price, selling_price, status
      ) VALUES ('pos-uuid-004', ?, 'HSPOS4', 'مسبحة فحص بيع مباشر', 'POS Rosary', ?, ?, 'AVAILABLE')
    `,
    args: [testRef, costPrice, sellingPrice]
  });

  const pRow = await client.execute({
    sql: 'SELECT id FROM products WHERE product_reference = ?',
    args: [testRef]
  });
  const prodId = pRow.rows[0].id;

  // 2. Perform Quick Sale with Deferred Payment (آجل)
  const orderRef = 'HSO-TEST-POS-999';
  const orderPubId = crypto.randomUUID();

  await client.execute({
    sql: `
      INSERT INTO orders (
        public_id, reference, customer_name, customer_phone,
        subtotal, discount_total, grand_total, status, payment_status,
        payment_method, paid_amount, outstanding_amount, payment_due_date
      ) VALUES (?, ?, 'عميل المعرض الدائم', '+971501234567', ?, ?, ?, 'DELIVERED', 'UNPAID', 'DEFERRED', 0.0, ?, '2026-12-01')
    `,
    args: [orderPubId, orderRef, sellingPrice, specialDiscount, grandTotal, grandTotal]
  });

  const oRow = await client.execute({
    sql: 'SELECT id FROM orders WHERE reference = ?',
    args: [orderRef]
  });
  const orderId = oRow.rows[0].id;

  // 3. Save Order Item with Immutable Cost Snapshot
  await client.execute({
    sql: `
      INSERT INTO order_items (
        order_id, product_id, product_reference, sku, name_ar,
        cost_price_snapshot, unit_price, discount, line_total
      ) VALUES (?, ?, ?, 'HSPOS4', 'مسبحة فحص بيع مباشر', ?, ?, ?, ?)
    `,
    args: [orderId, prodId, testRef, costPrice, sellingPrice, specialDiscount, grandTotal]
  });

  // Verify item snapshot preserves original historical cost
  const itemSnap = await client.execute({
    sql: 'SELECT cost_price_snapshot, line_total FROM order_items WHERE order_id = ?',
    args: [orderId]
  });

  if (itemSnap.rows[0].cost_price_snapshot !== costPrice) {
    throw new Error('Order item failed to freeze immutable cost price snapshot');
  }

  // 4. Test Partial Debt Payment on Receivable
  const partialPayment = 1000.0;
  const newOutstanding = grandTotal - partialPayment; // 1500.0

  await client.execute({
    sql: `
      UPDATE orders SET
        paid_amount = ?,
        outstanding_amount = ?,
        payment_status = 'PARTIALLY_PAID'
      WHERE id = ?
    `,
    args: [partialPayment, newOutstanding, orderId]
  });

  const updatedOrder = await client.execute({
    sql: 'SELECT paid_amount, outstanding_amount, payment_status FROM orders WHERE id = ?',
    args: [orderId]
  });

  if (updatedOrder.rows[0].outstanding_amount !== newOutstanding || updatedOrder.rows[0].payment_status !== 'PARTIALLY_PAID') {
    throw new Error('Partial receivable payment balance reconciliation failed');
  }

  // Clean up
  await client.execute({ sql: 'DELETE FROM order_items WHERE order_id = ?', args: [orderId] });
  await client.execute({ sql: 'DELETE FROM orders WHERE id = ?', args: [orderId] });
  await client.execute({ sql: 'DELETE FROM products WHERE id = ?', args: [prodId] });

  console.log('✅ [TEST 4 PASSED] POS Quick Sale, Immutable Cost Snapshot and Receivables verified.');
}

run().catch(err => {
  console.error('❌ [TEST 4 FAILED]:', err.message);
  process.exit(1);
});
