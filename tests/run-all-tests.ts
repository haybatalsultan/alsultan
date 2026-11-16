/**
 * 🚀 Haybat Al Sultan PRO - Master Test Runner
 * Executes all financial, security, exclusivity, and custody verification suites.
 */

import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const suites = [
  { name: 'Anti-Double-Selling & Exclusivity Engine', file: 'anti-double-selling.test.ts' },
  { name: 'Product Custody Append-Only Audit Trail', file: 'custody-immutable.test.ts' },
  { name: 'Rosary Bead Adjustment & Workshop Sizing', file: 'bead-adjustment.test.ts' },
  { name: 'Quick Sale POS & Receivables Reconciliation', file: 'quick-sale-pos.test.ts' },
  { name: 'Smart Accountant Realized Profit & Expense Voiding', file: 'smart-accountant.test.ts' },
  { name: 'Multi-Role RBAC & Audit Log Immutability', file: 'security-rbac.test.ts' }
];

console.log(`
==============================================================================
🧪 HAYBAT AL SULTAN PRO - COMPREHENSIVE VERIFICATION SUITE
==============================================================================
Running ${suites.length} automated test suites...
`);

let passed = 0;
let failed = 0;

const tsxBin = `"${path.join(__dirname, '..', 'node_modules', '.bin', 'tsx.cmd')}"`;

for (const suite of suites) {
  const testPath = `"${path.join(__dirname, suite.file)}"`;
  const result = spawnSync(`${tsxBin} ${testPath}`, {
    stdio: 'inherit',
    shell: true
  });

  if (result.status === 0) {
    passed++;
  } else {
    failed++;
    console.error(`\x1b[31m❌ [FAILED] Suite: ${suite.name}\x1b[0m`);
  }
}

console.log(`
==============================================================================
📊 TEST SUMMARY
==============================================================================
Total Suites:  ${suites.length}
Passed:        \x1b[32m${passed}\x1b[0m
Failed:        \x1b[31m${failed}\x1b[0m
Status:        ${failed === 0 ? '\x1b[32mALL PRODUCTION TESTS PASSED (100% SUCCESS)\x1b[0m' : '\x1b[31mFAILURES DETECTED\x1b[0m'}
==============================================================================
`);

if (failed > 0) {
  process.exit(1);
}
