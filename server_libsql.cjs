/**
 * ==============================================================================
 * 📿 HAYBAT AL SULTAN PRO - Backend Engine & libSQL Architecture
 * ==============================================================================
 * Luxury Rosary (المسابيح الفاخرة) Store, Exhibition POS, Custody & Workshop ERP
 * Offline-First + Embedded libSQL SQLite + Turso Cloud Sync + Socket.IO Realtime
 * Built with SmartCut Architecture Standards
 * ==============================================================================
 */

const express = require('express');
const http = require('http');
const { Server: SocketIOServer } = require('socket.io');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { createClient } = require('@libsql/client');
const crypto = require('crypto');
const cron = require('node-cron');
const zlib = require('zlib');
require('dotenv').config();

function hashPassword(pwd) {
  return crypto.createHash('sha256').update(String(pwd) + '_haybat_salt_2026').digest('hex');
}
function comparePassword(pwd, hash) {
  return hashPassword(pwd) === hash || pwd === hash;
}

const cloudConfig = require('./cloudConfig.cjs');
let licenseHelper;
try {
  licenseHelper = require('./license.cjs');
} catch (e) {
  console.warn('⚠️ license.cjs could not be loaded:', e.message);
}

const app = express();
const httpServer = http.createServer(app);
const io = new SocketIOServer(httpServer, {
  cors: { origin: '*', methods: ['GET', 'POST', 'PUT', 'DELETE'] }
});

const PORT = parseInt(process.env.PORT || process.env.SERVER_PORT || '3001', 10);
const HOST = '0.0.0.0';

// Global Middlewares
app.use(cors({ origin: '*', methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'] }));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// High-Performance Built-in GZIP Compression Middleware
app.use((req, res, next) => {
  const enc = req.headers['accept-encoding'] || '';
  if (!enc.includes('gzip')) return next();

  const originalSend = res.send;
  res.send = function (body) {
    if (res.headersSent || !body) return originalSend.apply(this, arguments);

    const cType = String(res.getHeader('Content-Type') || '');
    const isCompressible = typeof body === 'string' || Buffer.isBuffer(body);
    const shouldCompress = /text|json|javascript|css|xml|svg/i.test(cType) || (cType === '' && typeof body === 'string');

    if (isCompressible && shouldCompress && Buffer.byteLength(body) > 1024) {
      res.removeHeader('Content-Length');
      res.setHeader('Content-Encoding', 'gzip');
      res.setHeader('Vary', 'Accept-Encoding');
      zlib.gzip(body, (err, compressed) => {
        if (err) return originalSend.apply(this, arguments);
        res.setHeader('Content-Length', compressed.length);
        originalSend.call(this, compressed);
      });
      return this;
    }
    return originalSend.apply(this, arguments);
  };
  next();
});

// Automatic API route prefix rewrites (supports both /products and /api/products)
app.use((req, res, next) => {
  if (!req.path.startsWith('/api') && !req.path.startsWith('/assets') && !req.path.includes('.')) {
    const knownPrefixes = [
      '/auth', '/products', '/categories', '/materials', '/orders',
      '/quick-sale', '/custody', '/bead-adjustments', '/expenses',
      '/receivables', '/accountant', '/ambassadors', '/audit',
      '/settings', '/license', '/cloud', '/database', '/health', '/upload', '/countries'
    ];
    if (knownPrefixes.some(p => req.path === p || req.path.startsWith(p + '/'))) {
      req.url = '/api' + req.url;
    }
  }
  next();
});

// Paths & Data Directory
function getDataDir() {
  if (process.env.HAYBAT_DATA_DIR) {
    return process.env.HAYBAT_DATA_DIR;
  }
  if (__dirname.includes('app.asar')) {
    const appData = process.env.APPDATA || (process.platform === 'darwin' ? process.env.HOME + '/Library/Application Support' : '/var/local');
    return path.join(appData, 'haybatalsultan-pro', 'data');
  }
  return path.join(__dirname, 'data');
}

const DATA_DIR = getDataDir();
if (!fs.existsSync(DATA_DIR)) {
  try { fs.mkdirSync(DATA_DIR, { recursive: true }); } catch (e) {}
}

const UPLOADS_DIR = path.join(DATA_DIR, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) {
  try { fs.mkdirSync(UPLOADS_DIR, { recursive: true }); } catch (e) {}
}

// Serve uploaded luxury rosary images with long-term cache headers
app.use('/uploads', express.static(UPLOADS_DIR, {
  maxAge: '30d',
  etag: true,
  lastModified: true
}));

const DB_PATH = path.join(DATA_DIR, 'haybatalsultan.db');
const client = createClient({
  url: `file:${DB_PATH}`
});

// Helper for LibSQL queries
async function query(sql, args = []) {
  try {
    const res = await client.execute({ sql, args });
    return res.rows || [];
  } catch (err) {
    console.error(`❌ SQL Error [${sql}]:`, err.message);
    throw err;
  }
}

async function queryOne(sql, args = []) {
  const rows = await query(sql, args);
  return rows[0] || null;
}

// In-Memory Mutex for Atomic Exclusivity & Anti-Double-Selling
const productLocks = new Set();
async function acquireProductLock(productId) {
  const idStr = String(productId);
  if (productLocks.has(idStr)) return false;
  productLocks.add(idStr);
  return true;
}
function releaseProductLock(productId) {
  productLocks.delete(String(productId));
}

// Helper: Record Immutable Audit Log
async function recordAudit(actorName, actorRole, action, category, details = {}, ip = '127.0.0.1') {
  try {
    await query(`
      INSERT INTO audit_logs (actor_name, actor_role, action, category, details, ip_address, created_at)
      VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    `, [actorName || 'System', actorRole || 'SYSTEM', action, category, JSON.stringify(details), ip]);
  } catch (e) {
    console.error('Failed to write audit log:', e.message);
  }
}

// Initialize Database Schema & Seed Data
async function initDatabase() {
  console.log('🔄 [DB] Initializing Haybat Al Sultan PRO Schema...');

  try {
    await query('PRAGMA journal_mode = WAL;');
    await query('PRAGMA busy_timeout = 5000;');
  } catch (e) {}

  await query(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'CUSTOMER', -- OWNER, SUPERVISOR, SALES, CUSTOMER
      phone TEXT DEFAULT '',
      email TEXT DEFAULT '',
      permissions TEXT DEFAULT '{}', -- JSON flags for supervisors
      is_active INTEGER DEFAULT 1,
      mfa_secret TEXT DEFAULT '',
      mfa_enabled INTEGER DEFAULT 0,
      country TEXT DEFAULT 'الإمارات العربية المتحدة',
      address TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  try { await query('ALTER TABLE users ADD COLUMN country TEXT DEFAULT "الإمارات العربية المتحدة"'); } catch (e) {}
  try { await query('ALTER TABLE users ADD COLUMN address TEXT DEFAULT ""'); } catch (e) {}

  await query(`
    CREATE TABLE IF NOT EXISTS countries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name_ar TEXT NOT NULL UNIQUE,
      name_en TEXT DEFAULT '',
      code TEXT DEFAULT '',
      phone_code TEXT DEFAULT '',
      currency TEXT DEFAULT 'AED',
      sort_order INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1,
      is_system INTEGER DEFAULT 0
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      name_ar TEXT NOT NULL,
      name_en TEXT NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      sort_order INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS materials (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      name_ar TEXT NOT NULL,
      name_en TEXT NOT NULL,
      slug TEXT UNIQUE NOT NULL,
      sort_order INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      product_reference TEXT UNIQUE NOT NULL,
      sku TEXT UNIQUE NOT NULL,
      name_ar TEXT NOT NULL,
      name_en TEXT NOT NULL,
      description_ar TEXT DEFAULT '',
      description_en TEXT DEFAULT '',
      category_id INTEGER REFERENCES categories(id),
      material_id INTEGER REFERENCES materials(id),
      origin TEXT DEFAULT '',
      color TEXT DEFAULT '',
      bead_count INTEGER DEFAULT 33,
      bead_size_mm REAL DEFAULT 10.0,
      weight_g REAL DEFAULT 45.0,
      shape TEXT DEFAULT 'برميلي',
      tassel_type TEXT DEFAULT 'فضة كازازية عيار 1000',
      condition TEXT DEFAULT 'جديد فاخر',
      cost_price REAL NOT NULL DEFAULT 0.0,
      selling_price REAL NOT NULL DEFAULT 0.0,
      discount_price REAL DEFAULT NULL,
      status TEXT NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, RESERVED, SOLD, IN_CUSTODY, IN_WORKSHOP, ARCHIVED
      is_unique INTEGER DEFAULT 1,
      quantity INTEGER DEFAULT 1,
      reserved_until TEXT DEFAULT NULL,
      reserved_by_cart TEXT DEFAULT NULL,
      verification_status TEXT DEFAULT 'CERTIFIED', -- NONE, INSPECTED, CERTIFIED
      certificate_number TEXT DEFAULT '',
      image_url TEXT DEFAULT '',
      secondary_images TEXT DEFAULT '[]',
      created_at TEXT DEFAULT (datetime('now', 'localtime')),
      updated_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS custody_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      product_id INTEGER NOT NULL REFERENCES products(id),
      holder_name TEXT NOT NULL,
      location_name TEXT NOT NULL,
      placed_on TEXT NOT NULL,
      note TEXT DEFAULT '',
      recorded_by_name TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS bead_adjustments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER REFERENCES orders(id),
      product_id INTEGER NOT NULL REFERENCES products(id),
      product_reference TEXT NOT NULL,
      customer_name TEXT NOT NULL,
      customer_phone TEXT DEFAULT '',
      original_bead_count INTEGER NOT NULL,
      requested_bead_count INTEGER NOT NULL,
      removed_beads_count INTEGER NOT NULL,
      bag_labeled INTEGER DEFAULT 1,
      status TEXT DEFAULT 'PENDING', -- PENDING, IN_WORKSHOP, COMPLETED, DELIVERED
      notes TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now', 'localtime')),
      completed_at TEXT DEFAULT NULL
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      reference TEXT UNIQUE NOT NULL,
      customer_name TEXT NOT NULL,
      customer_phone TEXT NOT NULL,
      customer_email TEXT DEFAULT '',
      country TEXT DEFAULT 'AE',
      city TEXT DEFAULT '',
      area TEXT DEFAULT '',
      subtotal REAL NOT NULL DEFAULT 0.0,
      discount_total REAL NOT NULL DEFAULT 0.0,
      tax_total REAL NOT NULL DEFAULT 0.0,
      grand_total REAL NOT NULL DEFAULT 0.0,
      currency TEXT DEFAULT 'AED',
      sale_channel TEXT DEFAULT 'DIRECT', -- DIRECT, ONLINE
      delivery_method TEXT DEFAULT 'HAND_TO_HAND', -- HAND_TO_HAND, SHIPPING
      status TEXT DEFAULT 'CONFIRMED', -- PENDING, CONFIRMED, PREPARING, READY, SHIPPED, DELIVERED, CANCELLED
      payment_status TEXT DEFAULT 'PAID', -- UNPAID, PAID, PARTIALLY_PAID, REFUNDED
      payment_method TEXT DEFAULT 'CASH', -- CASH, POS, BANK_TRANSFER, DEFERRED, STRIPE, MANUAL
      payment_due_date TEXT DEFAULT NULL,
      paid_amount REAL DEFAULT 0.0,
      outstanding_amount REAL DEFAULT 0.0,
      hand_to_hand_by TEXT DEFAULT '',
      additional_notes TEXT DEFAULT '',
      delivered_at TEXT DEFAULT NULL,
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL REFERENCES orders(id),
      product_id INTEGER REFERENCES products(id),
      product_reference TEXT NOT NULL,
      sku TEXT NOT NULL,
      name_ar TEXT NOT NULL,
      cost_price_snapshot REAL NOT NULL DEFAULT 0.0,
      unit_price REAL NOT NULL DEFAULT 0.0,
      discount REAL DEFAULT 0.0,
      line_total REAL NOT NULL DEFAULT 0.0,
      original_bead_count INTEGER DEFAULT NULL,
      requested_bead_count INTEGER DEFAULT NULL,
      image_url TEXT DEFAULT ''
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS direct_payments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL REFERENCES orders(id),
      amount REAL NOT NULL,
      payment_method TEXT NOT NULL,
      note TEXT DEFAULT '',
      received_by_name TEXT NOT NULL,
      received_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      public_id TEXT UNIQUE NOT NULL,
      category TEXT NOT NULL, -- BOXES, BAGS, PACKAGING, MARKETING, SHIPPING, OPERATIONS, OTHER
      description TEXT NOT NULL,
      amount REAL NOT NULL,
      incurred_on TEXT NOT NULL,
      supplier TEXT DEFAULT '',
      status TEXT DEFAULT 'ACTIVE', -- ACTIVE, VOIDED
      void_reason TEXT DEFAULT '',
      voided_at TEXT DEFAULT NULL,
      created_by_name TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS ambassadors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT NOT NULL,
      email TEXT DEFAULT '',
      code TEXT UNIQUE NOT NULL,
      points_balance INTEGER DEFAULT 0,
      total_earned INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS ambassador_ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ambassador_id INTEGER NOT NULL REFERENCES ambassadors(id),
      order_id INTEGER REFERENCES orders(id),
      kind TEXT NOT NULL, -- EARN, REDEEM, EXPIRE, ADJUST
      points INTEGER NOT NULL,
      note TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      actor_name TEXT NOT NULL,
      actor_role TEXT NOT NULL,
      action TEXT NOT NULL,
      category TEXT NOT NULL,
      details TEXT DEFAULT '{}',
      ip_address TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS store_settings (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      store_name_ar TEXT DEFAULT 'هيبة السلطان للمسابيح الفاخرة',
      store_name_en TEXT DEFAULT 'Haybat Al Sultan Luxury Rosaries',
      phone TEXT DEFAULT '+971 50 408 4006',
      email TEXT DEFAULT 'info@haybatalsultan.com',
      address TEXT DEFAULT 'أبوظبي، الإمارات العربية المتحدة',
      currency TEXT DEFAULT 'AED',
      tax_rate REAL DEFAULT 0.0,
      shipping_fee REAL DEFAULT 0.0,
      reservation_minutes INTEGER DEFAULT 15,
      invoice_thank_you TEXT DEFAULT 'شكرًا لاختياركم هيبة السلطان - عنوان الفخامة والقطع النادرة',
      whatsapp_number TEXT DEFAULT '+971504084006'
    );
  `);

  // Ensure Single Store Settings Row
  await query(`
    INSERT OR IGNORE INTO store_settings (id) VALUES (1);
  `);

  // Seed default Owner User
  const ownerExists = await queryOne('SELECT id FROM users WHERE role = ?', ['OWNER']);
  if (!ownerExists) {
    await query(`
      INSERT INTO users (public_id, username, password_hash, full_name, role, phone, email, is_active)
      VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    `, [
      crypto.randomUUID(),
      'owner',
      hashPassword('Haybat@2026!Master'),
      'مالك المتجر - هيبة السلطان',
      'OWNER',
      '+971504084006',
      'owner@haybatalsultan.com'
    ]);
    console.log('✅ [Seed] Default Owner account created: user=owner, pass=Haybat@2026!Master');
  }

  // Seed Categories
  const catCount = await queryOne('SELECT COUNT(*) as c FROM categories');
  if (catCount && catCount.c === 0) {
    const defaultCategories = [
      ['مسابيح بكلايت', 'Bakelite Rosaries', 'bakelite', 1],
      ['فاتوران ألماني وأنتيك', 'German Faturan Antique', 'faturan', 2],
      ['كهرمان بلطيقي طبيعي', 'Natural Baltic Amber', 'amber', 3],
      ['سندلوس ومستكة فاخرة', 'Sandaloos & Mastic', 'sandaloos', 4],
      ['أحجار كريمة وعقيق وفيروز', 'Gemstones & Agate', 'gemstones', 5],
      ['أخشاب نادرة (كوك وصندل)', 'Rare Woods (Kuk & Sandalwood)', 'rare-woods', 6],
      ['تحف وهدايا ملكية', 'Royal Gifts & Antiques', 'royal-gifts', 7]
    ];
    for (const [ar, en, slug, order] of defaultCategories) {
      await query(`
        INSERT INTO categories (public_id, name_ar, name_en, slug, sort_order)
        VALUES (?, ?, ?, ?, ?)
      `, [crypto.randomUUID(), ar, en, slug, order]);
    }
    console.log('✅ [Seed] Default Categories inserted.');
  }

  // Seed Materials
  const matCount = await queryOne('SELECT COUNT(*) as c FROM materials');
  if (matCount && matCount.c === 0) {
    const defaultMaterials = [
      ['بكلايت بلجيكي مخرط يدوي', 'Belgian Hand-cut Bakelite', 'belgian-bakelite', 1],
      ['فاتوران ألماني صب قديم', 'Old German Cast Faturan', 'old-german-faturan', 2],
      ['كهرمان حر بولندي مضغوط', 'Polish Natural Amber', 'polish-amber', 3],
      ['سندلوس ألماني مسكي', 'German Sandaloos', 'german-sandaloos', 4],
      ['فيروز نيشابوري طبيعي', 'Natural Nishapur Turquoise', 'nishapur-turquoise', 5],
      ['خشب الكوك البرازيلي', 'Brazilian Kuk Wood', 'brazilian-kuk', 6],
      ['عقيق يماني كبدي أصلي', 'Authentic Yemeni Agate', 'yemeni-agate', 7]
    ];
    for (const [ar, en, slug, order] of defaultMaterials) {
      await query(`
        INSERT INTO materials (public_id, name_ar, name_en, slug, sort_order)
        VALUES (?, ?, ?, ?, ?)
      `, [crypto.randomUUID(), ar, en, slug, order]);
    }
    console.log('✅ [Seed] Default Materials inserted.');
  }

  // Seed All 22 Arab Countries (if countries table is empty)
  const countryCount = await queryOne('SELECT COUNT(*) as c FROM countries');
  if (countryCount && countryCount.c === 0) {
    const arabCountries = [
      ['الإمارات العربية المتحدة', 'United Arab Emirates', 'AE', '+971', 'AED', 1, 1],
      ['المملكة العربية السعودية', 'Saudi Arabia', 'SA', '+966', 'SAR', 2, 1],
      ['دولة الكويت', 'Kuwait', 'KW', '+965', 'KWD', 3, 1],
      ['دولة قطر', 'Qatar', 'QA', '+974', 'QAR', 4, 1],
      ['سلطنة عمان', 'Oman', 'OM', '+968', 'OMR', 5, 1],
      ['مملكة البحرين', 'Bahrain', 'BH', '+973', 'BHD', 6, 1],
      ['جمهورية مصر العربية', 'Egypt', 'EG', '+20', 'EGP', 7, 1],
      ['المملكة الأردنية الهاشمية', 'Jordan', 'JO', '+962', 'JOD', 8, 1],
      ['جمهورية العراق', 'Iraq', 'IQ', '+964', 'IQD', 9, 1],
      ['الجمهورية اللبنانية', 'Lebanon', 'LB', '+961', 'USD', 10, 1],
      ['دولة فلسطين', 'Palestine', 'PS', '+970', 'USD', 11, 1],
      ['الجمهورية العربية السورية', 'Syria', 'SY', '+963', 'SYP', 12, 1],
      ['الجمهورية اليمنية', 'Yemen', 'YE', '+967', 'YER', 13, 1],
      ['دولة ليبيا', 'Libya', 'LY', '+218', 'LYD', 14, 1],
      ['الجمهورية التونسية', 'Tunisia', 'TN', '+216', 'TND', 15, 1],
      ['الجمهورية الجزائرية', 'Algeria', 'DZ', '+213', 'DZD', 16, 1],
      ['المملكة المغربية', 'Morocco', 'MA', '+212', 'MAD', 17, 1],
      ['جمهورية السودان', 'Sudan', 'SD', '+249', 'SDG', 18, 1],
      ['جمهورية الصومال', 'Somalia', 'SO', '+252', 'SOS', 19, 1],
      ['الجمهورية الإسلامية الموريتانية', 'Mauritania', 'MR', '+222', 'MRU', 20, 1],
      ['جمهورية جيبوتي', 'Djibouti', 'DJ', '+253', 'DJF', 21, 1],
      ['جزر القمر', 'Comoros', 'KM', '+269', 'KMF', 22, 1]
    ];
    for (const [ar, en, code, phone, cur, sort, sys] of arabCountries) {
      await query(`
        INSERT INTO countries (name_ar, name_en, code, phone_code, currency, sort_order, is_active, is_system)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
      `, [ar, en, code, phone, cur, sort, sys]);
    }
    console.log('✅ [Seed] All 22 Arab Countries seeded successfully.');
  }

  // Seed Initial Rare Rosary Products (if empty)
  const prodCount = await queryOne('SELECT COUNT(*) as c FROM products');
  if (prodCount && prodCount.c === 0) {
    const initialItems = [
      {
        ref: 'HSP-261103-AK8912B',
        sku: 'HS00001',
        name_ar: 'مسبحة كهرمان بلطيقي ملكي أصفر معرق - كركوشة فضة 1000',
        name_en: 'Royal Marbled Yellow Baltic Amber Rosary - Pure Silver Tassel',
        cat_slug: 'amber',
        mat_slug: 'polish-amber',
        origin: 'بولندا / بحر البلطيق',
        color: 'أصفر زبدي معرق',
        bead_count: 33,
        bead_size_mm: 11.5,
        weight_g: 48.5,
        shape: 'برميلي متناسق',
        tassel_type: 'فضة كازازية عيار 1000 شغل يدوي فاخر',
        cost_price: 1800.0,
        selling_price: 3200.0,
        status: 'AVAILABLE',
        verification_status: 'CERTIFIED',
        certificate_number: 'AMB-PL-2026-9901',
        image_url: 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=800'
      },
      {
        ref: 'HSP-261103-BF4410C',
        sku: 'HS00002',
        name_ar: 'مسبحة فاتوران ألماني أنتيك أحمر كبدي شفاف مخرطة أسطى',
        name_en: 'Antique Deep Cherry German Faturan Rosary - Master Lathed',
        cat_slug: 'faturan',
        mat_slug: 'old-german-faturan',
        origin: 'ألمانيا - خامات قديمة',
        color: 'أحمر كبدي دم الغزال شفاف',
        bead_count: 45,
        bead_size_mm: 12.0,
        weight_g: 62.0,
        shape: 'ذروي صنوبري فاخر',
        tassel_type: 'طربزونة فضة عيار 925 مطلية بالروديوم',
        cost_price: 2400.0,
        selling_price: 4500.0,
        status: 'AVAILABLE',
        verification_status: 'CERTIFIED',
        certificate_number: 'FAT-DE-2026-4402',
        image_url: 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800'
      },
      {
        ref: 'HSP-261103-CK1299A',
        sku: 'HS00003',
        name_ar: 'مسبحة بكلايت بلجيكي زيتوني عسلي بنقشة شجري نادرة',
        name_en: 'Belgian Olive Honey Dendritic Bakelite Rosary',
        cat_slug: 'bakelite',
        mat_slug: 'belgian-bakelite',
        origin: 'بلجيكا',
        color: 'زيتوني متدرج مع عسلي',
        bead_count: 33,
        bead_size_mm: 10.5,
        weight_g: 41.2,
        shape: 'كروي دائري مضبوط',
        tassel_type: 'كركوشة حرير طبيعي تركي مع تفصيل يدوي',
        cost_price: 750.0,
        selling_price: 1650.0,
        status: 'AVAILABLE',
        verification_status: 'INSPECTED',
        certificate_number: 'BAK-BE-2026-1108',
        image_url: 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800'
      },
      {
        ref: 'HSP-261103-DY8831X',
        sku: 'HS00004',
        name_ar: 'مسبحة فيروز نيشابوري إيراني طبيعي غير معالج شذر أزرق صافي',
        name_en: 'Natural Iranian Nishapur Turquoise Rosary - Pure Azure',
        cat_slug: 'gemstones',
        mat_slug: 'nishapur-turquoise',
        origin: 'نيشابور - إيران',
        color: 'أزرق سماوي فيروزي صافي',
        bead_count: 33,
        bead_size_mm: 9.8,
        weight_g: 54.0,
        shape: 'بيضاوي تفاحي رائع',
        tassel_type: 'شاهد وفواصل وفضة إيطالية عيار 925 مطعمة',
        cost_price: 3100.0,
        selling_price: 5800.0,
        status: 'AVAILABLE',
        verification_status: 'CERTIFIED',
        certificate_number: 'TUR-IR-2026-3390',
        image_url: 'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=800'
      }
    ];

    for (const item of initialItems) {
      const cat = await queryOne('SELECT id FROM categories WHERE slug = ?', [item.cat_slug]);
      const mat = await queryOne('SELECT id FROM materials WHERE slug = ?', [item.mat_slug]);
      await query(`
        INSERT INTO products (
          public_id, product_reference, sku, name_ar, name_en,
          category_id, material_id, origin, color, bead_count,
          bead_size_mm, weight_g, shape, tassel_type, cost_price,
          selling_price, status, verification_status, certificate_number, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        crypto.randomUUID(), item.ref, item.sku, item.name_ar, item.name_en,
        cat ? cat.id : null, mat ? mat.id : null, item.origin, item.color, item.bead_count,
        item.bead_size_mm, item.weight_g, item.shape, item.tassel_type, item.cost_price,
        item.selling_price, item.status, item.verification_status, item.certificate_number, item.image_url
      ]);
    }
    console.log('✅ [Seed] Rare Rosaries Seeded successfully.');
  }

  // B2B & Hybrid Schema Migrations (SQLite / libSQL)
  try {
    const userCols = await query('PRAGMA table_info(users)');
    const userColNames = userCols.map(c => c.name);
    if (!userColNames.includes('company_name')) await query("ALTER TABLE users ADD COLUMN company_name TEXT DEFAULT ''");
    if (!userColNames.includes('commercial_register')) await query("ALTER TABLE users ADD COLUMN commercial_register TEXT DEFAULT ''");
    if (!userColNames.includes('tax_id')) await query("ALTER TABLE users ADD COLUMN tax_id TEXT DEFAULT ''");
    if (!userColNames.includes('approved_at')) await query("ALTER TABLE users ADD COLUMN approved_at TEXT DEFAULT NULL");
    if (!userColNames.includes('approved_by')) await query("ALTER TABLE users ADD COLUMN approved_by TEXT DEFAULT NULL");

    const prodCols = await query('PRAGMA table_info(products)');
    const prodColNames = prodCols.map(c => c.name);
    if (!prodColNames.includes('sales_channel')) await query("ALTER TABLE products ADD COLUMN sales_channel TEXT DEFAULT 'both'");
    if (!prodColNames.includes('price_b2c')) {
      await query("ALTER TABLE products ADD COLUMN price_b2c REAL DEFAULT 0.0");
      await query("UPDATE products SET price_b2c = selling_price WHERE price_b2c = 0.0");
    }
    if (!prodColNames.includes('price_b2b')) {
      await query("ALTER TABLE products ADD COLUMN price_b2b REAL DEFAULT 0.0");
      await query("UPDATE products SET price_b2b = ROUND(selling_price * 0.70, 0) WHERE price_b2b = 0.0");
    }
    if (!prodColNames.includes('b2b_moq')) await query("ALTER TABLE products ADD COLUMN b2b_moq INTEGER DEFAULT 5");
    if (!prodColNames.includes('stock_quantity')) await query("ALTER TABLE products ADD COLUMN stock_quantity INTEGER DEFAULT 50");

    const orderCols = await query('PRAGMA table_info(orders)');
    const orderColNames = orderCols.map(c => c.name);
    if (!orderColNames.includes('order_type')) await query("ALTER TABLE orders ADD COLUMN order_type TEXT DEFAULT 'B2C'");
    if (!orderColNames.includes('company_name')) await query("ALTER TABLE orders ADD COLUMN company_name TEXT DEFAULT ''");
    if (!orderColNames.includes('tax_id')) await query("ALTER TABLE orders ADD COLUMN tax_id TEXT DEFAULT ''");
    if (!orderColNames.includes('commercial_register')) await query("ALTER TABLE orders ADD COLUMN commercial_register TEXT DEFAULT ''");

    const orderItemCols = await query('PRAGMA table_info(order_items)');
    const orderItemColNames = orderItemCols.map(c => c.name);
    if (!orderItemColNames.includes('quantity')) await query("ALTER TABLE order_items ADD COLUMN quantity INTEGER DEFAULT 1");
  } catch (mErr) {
    console.warn('⚠️ Migration note:', mErr.message);
  }

  console.log('🚀 [DB] Database Schema Ready.');
}

// Background Cron: Auto-release expired reservations every 60 seconds
cron.schedule('* * * * *', async () => {
  try {
    const expiredRows = await query(`
      SELECT id, product_reference, name_ar FROM products
      WHERE status = 'RESERVED' AND reserved_until IS NOT NULL AND reserved_until <= datetime('now', 'localtime')
    `);
    if (expiredRows.length > 0) {
      for (const row of expiredRows) {
        await query(`
          UPDATE products
          SET status = 'AVAILABLE', reserved_until = NULL, reserved_by_cart = NULL, updated_at = datetime('now', 'localtime')
          WHERE id = ?
        `, [row.id]);
        console.log(`🔓 [Anti-Hoarding] Reservation expired and released: ${row.product_reference} - ${row.name_ar}`);
      }
      io.emit('product:status_changed', { event: 'reservations_released', count: expiredRows.length });
    }
  } catch (err) {
    console.error('Error in reservation release cron:', err.message);
  }
});

// ==============================================================================
// 🔐 REST API ENDPOINTS
// ==============================================================================

// 1. Health & System Info
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    app: 'Haybat Al Sultan PRO',
    version: '1.0.0',
    time: new Date().toISOString(),
    engine: 'libSQL + SQLite'
  });
});

// 2. Authentication & Users
const activeSessions = new Map(); // token -> { id, username, role }

async function getUserFromReq(req) {
  const auth = req.headers['authorization'];
  if (!auth) return null;
  const token = auth.replace(/^Bearer\s+/i, '').trim();
  const sess = activeSessions.get(token);
  if (!sess) return null;
  const user = await queryOne('SELECT id, username, role, full_name, company_name, commercial_register, tax_id, is_active FROM users WHERE id = ?', [sess.id]);
  return user || null;
}

// A) General / Legacy Login
app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'اسم المستخدم وكلمة المرور مطلوبان' });
  }

  try {
    const user = await queryOne('SELECT * FROM users WHERE (LOWER(username) = ? OR LOWER(email) = ?) AND is_active = 1', [
      username.trim().toLowerCase(),
      username.trim().toLowerCase()
    ]);
    if (!user || !comparePassword(password, user.password_hash)) {
      await recordAudit(username, 'ANONYMOUS', 'LOGIN_FAILED', 'AUTH', { reason: 'Invalid credentials' }, req.ip);
      return res.status(401).json({ error: 'اسم المستخدم أو كلمة المرور غير صحيحة' });
    }

    await recordAudit(user.full_name, user.role, 'LOGIN_SUCCESS', 'AUTH', { userId: user.id }, req.ip);
    
    const token = 'haybat_jwt_' + crypto.randomBytes(16).toString('hex');
    activeSessions.set(token, { id: user.id, username: user.username, role: user.role });

    // Return sanitized user object
    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        public_id: user.public_id,
        username: user.username,
        full_name: user.full_name,
        role: user.role,
        phone: user.phone,
        email: user.email,
        permissions: JSON.parse(user.permissions || '{}')
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// B) Customer Registration (Storefront)
app.post('/api/auth/customer/register', async (req, res) => {
  const { username, password, full_name, phone, email, country, address } = req.body;
  if (!username || !password || !full_name) {
    return res.status(400).json({ error: 'الاسم، اسم المستخدم، وكلمة المرور مطلوبة' });
  }

  try {
    const existing = await queryOne(
      "SELECT id FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?)",
      [username.trim().toLowerCase(), (email || '').trim().toLowerCase()]
    );
    if (existing) {
      return res.status(400).json({ error: 'اسم المستخدم أو البريد الإلكتروني مسجل مسبقاً' });
    }

    const publicId = crypto.randomUUID();
    const passwordHash = hashPassword(password);

    await query(`
      INSERT INTO users (public_id, username, password_hash, full_name, role, phone, email, country, address, is_active)
      VALUES (?, ?, ?, ?, 'CUSTOMER', ?, ?, ?, ?, 1)
    `, [
      publicId,
      username.trim().toLowerCase(),
      passwordHash,
      full_name.trim(),
      (phone || '').trim(),
      (email || '').trim().toLowerCase(),
      (country || 'الإمارات العربية المتحدة').trim(),
      (address || '').trim()
    ]);

    const newUser = await queryOne('SELECT * FROM users WHERE public_id = ?', [publicId]);
    await recordAudit(newUser.full_name, 'CUSTOMER', 'CUSTOMER_REGISTER', 'AUTH', { userId: newUser.id }, req.ip);

    res.status(201).json({
      success: true,
      token: 'haybat_cust_' + crypto.randomBytes(16).toString('hex'),
      user: {
        id: newUser.id,
        public_id: newUser.public_id,
        username: newUser.username,
        full_name: newUser.full_name,
        role: 'CUSTOMER',
        phone: newUser.phone,
        email: newUser.email,
        country: newUser.country,
        address: newUser.address
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// C) Customer Login (Storefront)
app.post('/api/auth/customer/login', async (req, res) => {
  const { identifier, password } = req.body;
  if (!identifier || !password) {
    return res.status(400).json({ error: 'يرجى إدخال اسم المستخدم / البريد / الهاتف وكلمة المرور' });
  }

  try {
    const cleanId = identifier.trim().toLowerCase();
    const user = await queryOne(
      'SELECT * FROM users WHERE (LOWER(username) = ? OR LOWER(email) = ? OR phone = ?) AND is_active = 1',
      [cleanId, cleanId, identifier.trim()]
    );

    if (!user || !comparePassword(password, user.password_hash)) {
      return res.status(401).json({ error: 'بيانات الدخول غير صحيحة، يرجى التأكد من البيانات' });
    }

    await recordAudit(user.full_name, user.role, 'CUSTOMER_LOGIN', 'AUTH', { userId: user.id }, req.ip);

    const token = 'haybat_cust_' + crypto.randomBytes(16).toString('hex');
    activeSessions.set(token, { id: user.id, username: user.username, role: user.role });

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        public_id: user.public_id,
        username: user.username,
        full_name: user.full_name,
        role: user.role,
        phone: user.phone,
        email: user.email,
        company_name: user.company_name,
        commercial_register: user.commercial_register,
        tax_id: user.tax_id
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// C2) Wholesale B2B Registration (Honeypot + Anti-Bot Sliding Window Limiter)
const b2bRateLimitMap = new Map();
function checkB2BRateLimit(ip) {
  const now = Date.now();
  const windowMs = 15 * 60 * 1000;
  const maxRequests = 5;
  const history = b2bRateLimitMap.get(ip) || [];
  const recent = history.filter(ts => now - ts < windowMs);
  if (recent.length >= maxRequests) return false;
  recent.push(now);
  b2bRateLimitMap.set(ip, recent);
  return true;
}

app.post('/api/auth/b2b/register', async (req, res) => {
  const {
    company_name,
    commercial_register,
    tax_id,
    full_name,
    email,
    phone,
    password,
    website_hp // Honeypot trap
  } = req.body;

  // 1. Silent rejection for automated bot scrapers
  if (website_hp && String(website_hp).trim().length > 0) {
    return res.status(201).json({
      success: true,
      status: 'b2b_pending',
      message: 'تم استلام طلب اعتماد حساب التاجر بنجاح وسيتم مراجعته.'
    });
  }

  // 2. Sliding window anti-spam rate limiter
  if (!checkB2BRateLimit(req.ip)) {
    return res.status(429).json({
      error: 'تم تجاوز الحد المسموح به لطلبات تسجيل الجملة من عنوانك. يرجى المحاولة بعد قليل.'
    });
  }

  // 3. Strict Verification
  if (!company_name || !commercial_register || !email || !password || !phone) {
    return res.status(400).json({
      error: 'يرجى استيفاء جميع البيانات القانونية للمنشأة (اسم الشركة، السجل التجاري، البريد، ورقم الهاتف).'
    });
  }

  try {
    const cleanEmail = email.trim().toLowerCase();
    const existing = await queryOne(
      "SELECT id FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?",
      [cleanEmail, cleanEmail]
    );
    if (existing) {
      return res.status(400).json({ error: 'البريد الإلكتروني مسجل مسبقاً في النظام.' });
    }

    const publicId = crypto.randomUUID();
    const passwordHash = hashPassword(password);

    await query(`
      INSERT INTO users (
        public_id, username, password_hash, full_name, role, phone, email,
        company_name, commercial_register, tax_id, is_active
      ) VALUES (?, ?, ?, ?, 'b2b_pending', ?, ?, ?, ?, ?, 1)
    `, [
      publicId,
      cleanEmail,
      passwordHash,
      full_name.trim(),
      phone.trim(),
      cleanEmail,
      company_name.trim(),
      commercial_register.trim(),
      (tax_id || '').trim()
    ]);

    await recordAudit(company_name, 'B2B_PENDING', 'B2B_APPLICATION_SUBMITTED', 'WHOLESALE', {
      email: cleanEmail,
      cr: commercial_register
    }, req.ip);

    res.status(201).json({
      success: true,
      status: 'b2b_pending',
      message: 'تم استلام طلب انضمامكم لشبكة تجار الجملة بنجاح. حسابكم قيد التدقيق وسيتم تفعيله بعد التحقق من السجل التجاري.'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// D) Strict Admin & Staff Login (/admin)
app.post('/api/auth/admin/login', async (req, res) => {
  const loginId = (req.body.username || req.body.identifier || '').trim();
  const { password } = req.body;
  if (!loginId || !password) {
    return res.status(400).json({ error: 'اسم المستخدم وكلمة المرور مطلوبان' });
  }

  try {
    const cleanId = loginId.toLowerCase();
    const aliasUsername = cleanId === 'admin' ? 'owner' : cleanId;
    const user = await queryOne(
      'SELECT * FROM users WHERE (LOWER(username) = ? OR LOWER(username) = ? OR LOWER(email) = ? OR phone = ?) AND is_active = 1',
      [cleanId, aliasUsername, cleanId, loginId]
    );

    if (!user || !comparePassword(password, user.password_hash)) {
      await recordAudit(loginId, 'ANONYMOUS', 'ADMIN_LOGIN_FAILED', 'SECURITY', { reason: 'Bad credentials' }, req.ip);
      return res.status(401).json({ error: 'اسم المستخدم أو كلمة المرور غير صحيحة' });
    }

    // STRICT CHECK: Reject customers and wholesale buyers attempting to login to admin portal!
    if (user.role === 'CUSTOMER' || user.role === 'b2c_user' || user.role === 'b2b_pending' || user.role === 'b2b_approved') {
      await recordAudit(user.full_name, user.role, 'ADMIN_ACCESS_BLOCKED', 'SECURITY', { userId: user.id, username: user.username }, req.ip);
      return res.status(403).json({
        error: 'عذراً، هذا الحساب مخصص للمتجر وبوابة الجملة فقط، ولا يملك أي صلاحيات لدخول لوحة الإدارة أو نقاط البيع.'
      });
    }

    await recordAudit(user.full_name, user.role, 'ADMIN_LOGIN_SUCCESS', 'AUTH', { userId: user.id, role: user.role }, req.ip);

    const token = 'haybat_admin_' + crypto.randomBytes(16).toString('hex');
    activeSessions.set(token, { id: user.id, username: user.username, role: user.role });

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        public_id: user.public_id,
        username: user.username,
        full_name: user.full_name,
        role: user.role,
        phone: user.phone,
        email: user.email,
        permissions: JSON.parse(user.permissions || '{}')
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// E) Customer My-Orders
app.get('/api/customer/my-orders', async (req, res) => {
  try {
    const { phone, email } = req.query;
    if (!phone && !email) {
      return res.json([]);
    }
    const orders = await query(`
      SELECT * FROM orders
      WHERE (customer_phone IS NOT NULL AND customer_phone != '' AND customer_phone = ?) OR (customer_email IS NOT NULL AND customer_email != '' AND customer_email = ?)
      ORDER BY id DESC
    `, [phone || '', email || '']);

    for (const ord of orders) {
      ord.items = await query('SELECT * FROM order_items WHERE order_id = ?', [ord.id]);
    }

    res.json(orders);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// G) Users & Granular Permissions Management
app.get('/api/users', async (req, res) => {
  try {
    const { role, include_customers } = req.query;
    let sql = 'SELECT id, public_id, username, full_name, role, phone, email, permissions, is_active, created_at FROM users WHERE 1=1';
    const args = [];
    if (!include_customers) {
      sql += " AND role != 'CUSTOMER'";
    }
    if (role && role !== 'ALL') {
      sql += ' AND role = ?';
      args.push(role);
    }
    sql += ' ORDER BY id ASC';
    const users = await query(sql, args);
    const parsed = users.map(u => ({
      ...u,
      permissions: JSON.parse(u.permissions || '{}')
    }));
    res.json(parsed);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/users', async (req, res) => {
  const { username, password, full_name, role, phone, email, permissions, is_active, actor_name } = req.body;
  if (!username || !password || !full_name || !role) {
    return res.status(400).json({ error: 'اسم المستخدم، كلمة المرور، الاسم الكامل والدور الوظيفي حقول مطلوبة' });
  }

  try {
    const existing = await queryOne(
      "SELECT id FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?)",
      [username.trim().toLowerCase(), (email || '').trim().toLowerCase()]
    );
    if (existing) {
      return res.status(400).json({ error: 'اسم المستخدم أو البريد الإلكتروني مسجل مسبقاً لمستخدم آخر' });
    }

    const publicId = crypto.randomUUID();
    const passwordHash = hashPassword(password);
    const permissionsJson = typeof permissions === 'object' ? JSON.stringify(permissions) : '{}';

    await query(`
      INSERT INTO users (public_id, username, password_hash, full_name, role, phone, email, permissions, is_active)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      publicId,
      username.trim().toLowerCase(),
      passwordHash,
      full_name.trim(),
      role,
      (phone || '').trim(),
      (email || '').trim().toLowerCase(),
      permissionsJson,
      is_active !== undefined ? (is_active ? 1 : 0) : 1
    ]);

    const created = await queryOne(
      'SELECT id, public_id, username, full_name, role, phone, email, permissions, is_active, created_at FROM users WHERE public_id = ?',
      [publicId]
    );

    await recordAudit(actor_name || 'Admin', 'OWNER', 'CREATE_USER', 'USERS', {
      created_username: username,
      role
    });

    res.status(201).json({
      ...created,
      permissions: JSON.parse(created.permissions || '{}')
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/users/:id', async (req, res) => {
  const { full_name, role, phone, email, password, permissions, is_active, actor_name } = req.body;
  const userId = req.params.id;

  try {
    const existing = await queryOne('SELECT * FROM users WHERE id = ?', [userId]);
    if (!existing) {
      return res.status(404).json({ error: 'المستخدم غير موجود' });
    }

    // Safety: Protect primary owner from being demoted or deactivated
    if (existing.username === 'owner' && ((role && role !== 'OWNER') || is_active === 0 || is_active === false)) {
      return res.status(400).json({ error: 'لا يمكن إلغاء تنشيط أو تغيير دور الحساب الرئيسي للمالك (owner)' });
    }

    let passwordHash = existing.password_hash;
    if (password && password.trim()) {
      passwordHash = hashPassword(password.trim());
    }

    const permissionsJson = permissions !== undefined
      ? (typeof permissions === 'object' ? JSON.stringify(permissions) : permissions)
      : existing.permissions;

    await query(`
      UPDATE users SET
        full_name = ?,
        role = ?,
        phone = ?,
        email = ?,
        password_hash = ?,
        permissions = ?,
        is_active = ?
      WHERE id = ?
    `, [
      full_name !== undefined ? full_name.trim() : existing.full_name,
      role || existing.role,
      phone !== undefined ? phone.trim() : existing.phone,
      email !== undefined ? email.trim().toLowerCase() : existing.email,
      passwordHash,
      permissionsJson,
      is_active !== undefined ? (is_active ? 1 : 0) : existing.is_active,
      userId
    ]);

    const updated = await queryOne(
      'SELECT id, public_id, username, full_name, role, phone, email, permissions, is_active, created_at FROM users WHERE id = ?',
      [userId]
    );

    await recordAudit(actor_name || 'Admin', 'OWNER', 'UPDATE_USER', 'USERS', {
      target_user: existing.username,
      updated_fields: Object.keys(req.body)
    });

    res.json({
      ...updated,
      permissions: JSON.parse(updated.permissions || '{}')
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/users/:id', async (req, res) => {
  const userId = req.params.id;
  const actorName = req.query.actor_name || 'Admin';

  try {
    const existing = await queryOne('SELECT * FROM users WHERE id = ?', [userId]);
    if (!existing) {
      return res.status(404).json({ error: 'المستخدم غير موجود' });
    }

    if (existing.username === 'owner' || existing.id === 1) {
      return res.status(403).json({ error: 'حظر أمني: لا يمكن حذف الحساب الرئيسي لمالك المتجر إطلاقاً' });
    }

    await query('DELETE FROM users WHERE id = ?', [userId]);

    await recordAudit(actorName, 'OWNER', 'DELETE_USER', 'USERS', {
      deleted_username: existing.username,
      deleted_role: existing.role
    });

    res.json({ success: true, message: `تم حذف المستخدم (${existing.username}) بنجاح` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// F) Online Store Checkout (Customer Order Placement)
app.post('/api/orders/checkout', async (req, res) => {
  const {
    product_id,
    customer_name,
    customer_phone,
    customer_email,
    country,
    city,
    address,
    notes,
    payment_method
  } = req.body;

  if (!product_id || !customer_name || !customer_phone) {
    return res.status(400).json({ error: 'بيانات المسبحة واسم العميل ورقم الهاتف مطلوبة' });
  }

  const lockAcquired = await acquireProductLock(product_id);
  if (!lockAcquired) {
    return res.status(409).json({ error: 'القطعة قيد المعالجة من قبل عميل آخر حالياً' });
  }

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [product_id]);
    if (!product) {
      releaseProductLock(product_id);
      return res.status(404).json({ error: 'المسبحة غير متوفرة' });
    }

    if (product.status === 'SOLD') {
      releaseProductLock(product_id);
      return res.status(400).json({ error: 'نعتذر، تم اقتناء هذه المسبحة الفريدة بالفعل من قبل عميل آخر' });
    }

    const price = Number(product.selling_price);
    const datePart = new Date().toISOString().slice(2, 10).replace(/-/g, '');
    const randPart = crypto.randomBytes(3).toString('hex').toUpperCase();
    const orderRef = `WEB-${datePart}-${randPart}`;
    const orderPublicId = crypto.randomUUID();

    // 1. Create order with full country and shipping destination
    await query(`
      INSERT INTO orders (
        public_id, reference, customer_name, customer_phone, customer_email,
        country, city, area, subtotal, discount_total, tax_total, grand_total,
        currency, sale_channel, delivery_method, status, payment_status,
        payment_method, paid_amount, outstanding_amount, additional_notes, delivered_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, ?, 'AED', 'ONLINE', 'COURIER', 'PENDING', 'UNPAID', ?, 0.0, ?, ?, datetime('now', 'localtime'))
    `, [
      orderPublicId, orderRef, customer_name.trim(), customer_phone.trim(), (customer_email || '').trim(),
      (country || 'الإمارات العربية المتحدة').trim(), (city || 'أبوظبي').trim(), (address || 'توصيل منزلي فاخر').trim(), price, price,
      payment_method || 'CASH_ON_DELIVERY', price, notes || ''
    ]);

    const order = await queryOne('SELECT * FROM orders WHERE public_id = ?', [orderPublicId]);

    // 2. Order Item
    await query(`
      INSERT INTO order_items (
        order_id, product_id, product_reference, sku, name_ar,
        cost_price_snapshot, unit_price, discount, line_total, original_bead_count, image_url
      ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?)
    `, [
      order.id, product.id, product.product_reference, product.sku, product.name_ar,
      product.cost_price, price, price, product.bead_count, product.image_url
    ]);

    // 3. Mark product as SOLD
    await query('UPDATE products SET status = ?, reserved_until = NULL, reserved_by_cart = NULL WHERE id = ?', ['SOLD', product.id]);

    releaseProductLock(product_id);

    io.emit('order:created', { id: order.id, reference: order.reference });
    io.emit('product:status_changed', { id: product.id, status: 'SOLD' });

    res.status(201).json({
      success: true,
      message: 'تم استلام طلب الاقتناء بنجاح وتوثيق الحصرية',
      order: {
        id: order.id,
        reference: order.reference,
        grand_total: order.grand_total,
        customer_name: order.customer_name
      }
    });
  } catch (err) {
    releaseProductLock(product_id);
    res.status(500).json({ error: err.message });
  }
});

// 3. Products & Luxury Rosary Catalog (B2C & General)
app.get('/api/products', async (req, res) => {
  try {
    const { status, category, material, search, channel, min_price, max_price } = req.query;
    let sql = `
      SELECT p.*, c.name_ar as category_name_ar, c.name_en as category_name_en,
             m.name_ar as material_name_ar, m.name_en as material_name_en
      FROM products p
      LEFT JOIN categories c ON p.category_id = c.id
      LEFT JOIN materials m ON p.material_id = m.id
      WHERE 1=1
    `;
    const args = [];

    // Sales channel isolation: retail clients only see b2c / both
    if (channel === 'b2b') {
      sql += " AND (p.sales_channel IS NULL OR p.sales_channel IN ('b2b', 'both'))";
    } else if (channel !== 'all_channels') {
      // Default to B2C Retail isolation
      sql += " AND (p.sales_channel IS NULL OR p.sales_channel IN ('b2c', 'both'))";
    }

    if (status && status !== 'ALL') {
      sql += ' AND p.status = ?';
      args.push(status);
    }
    if (category) {
      sql += ' AND p.category_id = ?';
      args.push(category);
    }
    if (material) {
      sql += ' AND p.material_id = ?';
      args.push(material);
    }
    if (min_price && !isNaN(Number(min_price))) {
      sql += ' AND p.selling_price >= ?';
      args.push(Number(min_price));
    }
    if (max_price && !isNaN(Number(max_price))) {
      sql += ' AND p.selling_price <= ?';
      args.push(Number(max_price));
    }
    if (search) {
      sql += ' AND (p.name_ar LIKE ? OR p.name_en LIKE ? OR p.product_reference LIKE ? OR p.sku LIKE ? OR p.origin LIKE ?)';
      const s = `%${search}%`;
      args.push(s, s, s, s, s);
    }

    sql += ' ORDER BY p.id DESC';
    const products = await query(sql, args);

    // Data Protection: Strip wholesale margins and internal cost from retail queries
    if (channel !== 'all_channels') {
      products.forEach(p => {
        delete p.price_b2b;
        delete p.cost_price;
      });
    }

    res.json(products);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3.B) Wholesale B2B Dedicated Quick Order Catalog
app.get('/api/b2b/products', async (req, res) => {
  try {
    const user = await getUserFromReq(req);
    if (!user || !['b2b_approved', 'admin', 'OWNER', 'SUPERVISOR'].includes(user.role)) {
      return res.status(403).json({
        error: 'غير مصرح بالاطلاع على كتالوج وأسعار الجملة. يتطلب حساب تاجر معتمد نشط (b2b_approved).'
      });
    }

    const { search, category, min_price, max_price } = req.query;
    let sql = `
      SELECT p.id, p.public_id, p.product_reference, p.sku, p.name_ar, p.name_en,
             COALESCE(p.price_b2b, ROUND(p.selling_price * 0.70, 0)) as price_b2b,
             COALESCE(p.price_b2c, p.selling_price) as price_b2c,
             COALESCE(p.b2b_moq, 5) as b2b_moq,
             COALESCE(p.stock_quantity, 50) as stock_quantity,
             p.image_url, p.bead_count, p.bead_size_mm, p.weight_g, p.shape, p.tassel_type,
             p.origin, p.color, p.status, p.verification_status, p.certificate_number,
             c.name_ar as category_name_ar, m.name_ar as material_name_ar
      FROM products p
      LEFT JOIN categories c ON p.category_id = c.id
      LEFT JOIN materials m ON p.material_id = m.id
      WHERE p.status = 'AVAILABLE' AND (p.sales_channel IS NULL OR p.sales_channel IN ('b2b', 'both'))
    `;
    const args = [];

    if (category) {
      sql += ' AND p.category_id = ?';
      args.push(category);
    }
    if (min_price && !isNaN(Number(min_price))) {
      sql += ' AND COALESCE(p.price_b2b, ROUND(p.selling_price * 0.70, 0)) >= ?';
      args.push(Number(min_price));
    }
    if (max_price && !isNaN(Number(max_price))) {
      sql += ' AND COALESCE(p.price_b2b, ROUND(p.selling_price * 0.70, 0)) <= ?';
      args.push(Number(max_price));
    }
    if (search) {
      sql += ' AND (p.name_ar LIKE ? OR p.sku LIKE ? OR p.product_reference LIKE ? OR p.origin LIKE ?)';
      const s = `%${search}%`;
      args.push(s, s, s, s);
    }

    sql += ' ORDER BY p.id DESC';
    const products = await query(sql, args);
    res.json(products);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3.C) Wholesale B2B Purchase Order Checkout
app.post('/api/b2b/checkout', async (req, res) => {
  const user = await getUserFromReq(req);
  if (!user || !['b2b_approved', 'admin', 'OWNER', 'SUPERVISOR'].includes(user.role)) {
    return res.status(403).json({
      error: 'عذراً، لا يمكن إتمام طلبيات الشراء بالجملة إلا بعد اعتماد حساب التاجر رسمياً من قبل الإدارة.'
    });
  }

  const {
    items, // [{ product_id, quantity }]
    company_name,
    commercial_register,
    tax_id,
    contact_name,
    phone,
    email,
    shipping_address,
    city,
    payment_method, // 'BANK_TRANSFER' | 'CHEQUE' | 'CREDIT_TERMS'
    notes
  } = req.body;

  if (!items || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'سلة طلب الجملة فارغة، يرجى اختيار الأصناف والكميات.' });
  }
  if (!company_name || !phone || !contact_name) {
    return res.status(400).json({ error: 'اسم المنشأة، اسم جهة الاتصال، ورقم الهاتف حقول إلزامية.' });
  }

  // 1. Verify every item, check MOQ and stock
  let grandTotal = 0;
  const verifiedItems = [];

  for (const item of items) {
    const productId = item.product_id || item.id;
    const prod = await queryOne('SELECT * FROM products WHERE id = ?', [productId]);
    if (!prod) {
      return res.status(404).json({ error: `الصنف ذو المعرف (${productId}) غير موجود.` });
    }

    const requestedQty = Number(item.quantity) || 0;
    const moq = Number(prod.b2b_moq || 1);

    if (requestedQty < moq) {
      return res.status(400).json({
        error: `الكمية المطلوبة للمسبحة (${prod.name_ar} - SKU: ${prod.sku}) هي ${requestedQty}، وهي أقل من الحد الأدنى للطلب (${moq} قطع).`
      });
    }

    const unitPrice = Number(prod.price_b2b || (prod.selling_price * 0.70));
    const lineTotal = unitPrice * requestedQty;
    grandTotal += lineTotal;

    verifiedItems.push({
      product: prod,
      quantity: requestedQty,
      unitPrice,
      lineTotal
    });
  }

  try {
    const datePart = new Date().toISOString().slice(2, 10).replace(/-/g, '');
    const randPart = crypto.randomBytes(3).toString('hex').toUpperCase();
    const poReference = `PO-${datePart}-${randPart}`;
    const orderPublicId = crypto.randomUUID();

    // 2. Insert Wholesale Purchase Order
    await query(`
      INSERT INTO orders (
        public_id, reference, customer_name, customer_phone, customer_email,
        company_name, tax_id, country, city, area, subtotal, discount_total,
        tax_total, grand_total, currency, sale_channel, delivery_method,
        status, payment_status, payment_method, order_type, additional_notes, delivered_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, 'AE', ?, ?, ?, 0.0, 0.0, ?, 'AED', 'B2B_WHOLESALE', 'FREIGHT_LOGISTICS', 'CONFIRMED', 'UNPAID', ?, 'B2B', ?, datetime('now', 'localtime'))
    `, [
      orderPublicId,
      poReference,
      contact_name.trim(),
      phone.trim(),
      (email || '').trim(),
      company_name.trim(),
      (tax_id || '').trim(),
      city || 'أبوظبي',
      shipping_address || 'المقر التجاري للمنشأة',
      grandTotal,
      grandTotal,
      payment_method || 'BANK_TRANSFER',
      notes || `أمر شراء وتوريد جملة - س.ت: ${commercial_register || 'معتمد'}`
    ]);

    const order = await queryOne('SELECT * FROM orders WHERE public_id = ?', [orderPublicId]);

    // 3. Insert line items & update stock
    for (const v of verifiedItems) {
      await query(`
        INSERT INTO order_items (
          order_id, product_id, product_reference, sku, name_ar,
          cost_price_snapshot, unit_price, quantity, discount, line_total, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?)
      `, [
        order.id,
        v.product.id,
        v.product.product_reference,
        v.product.sku,
        v.product.name_ar,
        v.product.cost_price,
        v.unitPrice,
        v.quantity,
        v.lineTotal,
        v.product.image_url
      ]);

      // Deduct stock
      await query(`
        UPDATE products
        SET stock_quantity = MAX(0, COALESCE(stock_quantity, 50) - ?)
        WHERE id = ?
      `, [v.quantity, v.product.id]);
    }

    await recordAudit(
      company_name,
      'B2B_APPROVED',
      'B2B_PO_CREATED',
      'WHOLESALE',
      { reference: poReference, itemsCount: verifiedItems.length, grandTotal }
    );

    io.emit('order:created', { id: order.id, reference: poReference, type: 'B2B' });

    res.status(201).json({
      success: true,
      message: 'تم إصدار أمر الشراء والفاتورة المبدئية للجملة بنجاح.',
      order: {
        id: order.id,
        reference: poReference,
        order_number: poReference,
        company_name,
        grand_total: grandTotal,
        total_amount: grandTotal,
        items_count: verifiedItems.length,
        payment_method: payment_method || 'BANK_TRANSFER',
        status: 'CONFIRMED'
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3.D) Admin B2B Merchant Review Endpoints
app.get('/api/admin/b2b/merchants', async (req, res) => {
  try {
    const merchants = await query(`
      SELECT id, public_id, username, full_name, role, phone, email,
             company_name, commercial_register, tax_id, approved_at, is_active, created_at
      FROM users
      WHERE role IN ('b2b_pending', 'b2b_approved')
      ORDER BY id DESC
    `);
    res.json(merchants);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/admin/b2b/approve/:id', async (req, res) => {
  const merchantId = req.params.id;
  const actorName = req.body.actor_name || 'Admin';

  try {
    const merchant = await queryOne('SELECT * FROM users WHERE id = ?', [merchantId]);
    if (!merchant) return res.status(404).json({ error: 'حساب المنشأة غير موجود.' });

    await query(`
      UPDATE users SET
        role = 'b2b_approved',
        approved_at = datetime('now', 'localtime'),
        approved_by = ?
      WHERE id = ?
    `, [actorName, merchantId]);

    await recordAudit(actorName, 'OWNER', 'B2B_MERCHANT_APPROVED', 'WHOLESALE', {
      merchantId,
      company: merchant.company_name
    });

    res.json({
      success: true,
      message: `تم اعتماد المنشأة (${merchant.company_name}) رسمياً كتاجر جملة معتمد.`
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/admin/b2b/reject/:id', async (req, res) => {
  const merchantId = req.params.id;
  const actorName = req.body.actor_name || 'Admin';

  try {
    const merchant = await queryOne('SELECT * FROM users WHERE id = ?', [merchantId]);
    if (!merchant) return res.status(404).json({ error: 'حساب المنشأة غير موجود.' });

    await query("UPDATE users SET is_active = 0, role = 'CUSTOMER' WHERE id = ?", [merchantId]);

    await recordAudit(actorName, 'OWNER', 'B2B_MERCHANT_REJECTED', 'WHOLESALE', {
      merchantId,
      company: merchant.company_name
    });

    res.json({
      success: true,
      message: `تم رفض وتجميد طلب المنشأة (${merchant.company_name}).`
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/products/:id', async (req, res) => {
  try {
    const product = await queryOne(`
      SELECT p.*, c.name_ar as category_name_ar, m.name_ar as material_name_ar
      FROM products p
      LEFT JOIN categories c ON p.category_id = c.id
      LEFT JOIN materials m ON p.material_id = m.id
      WHERE p.id = ? OR p.public_id = ? OR p.product_reference = ? OR p.sku = ?
    `, [req.params.id, req.params.id, req.params.id, req.params.id]);

    if (!product) return res.status(404).json({ error: 'المسبحة غير موجودة' });
    res.json(product);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Upload and store rosary image (supports compressed base64 webp/jpeg/png)
app.post('/api/upload', (req, res) => {
  try {
    const { dataUrl, filename } = req.body;
    if (!dataUrl || typeof dataUrl !== 'string') {
      return res.status(400).json({ error: 'لم يتم توفير بيانات الصورة' });
    }

    const matches = dataUrl.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
    if (!matches || matches.length !== 3) {
      return res.status(400).json({ error: 'صيغة الصورة غير صالحة أو غير مدعومة' });
    }

    const mimeType = matches[1].toLowerCase();
    const base64Data = matches[2];
    const buffer = Buffer.from(base64Data, 'base64');

    if (buffer.length > 15 * 1024 * 1024) {
      return res.status(400).json({ error: 'حجم الصورة كبير جداً (الحد الأقصى 15 ميجابايت)' });
    }

    let ext = 'webp';
    if (mimeType.includes('jpeg') || mimeType.includes('jpg')) ext = 'jpg';
    else if (mimeType.includes('png')) ext = 'png';
    else if (mimeType.includes('webp')) ext = 'webp';
    else if (mimeType.includes('gif')) ext = 'gif';

    const safeRand = crypto.randomBytes(6).toString('hex');
    const safeFilename = `rosary_${Date.now()}_${safeRand}.${ext}`;
    const filePath = path.join(UPLOADS_DIR, safeFilename);

    fs.writeFileSync(filePath, buffer);

    const publicUrl = `/uploads/${safeFilename}`;
    res.json({
      success: true,
      url: publicUrl,
      size: buffer.length,
      filename: safeFilename
    });
  } catch (err) {
    console.error('❌ Upload error:', err);
    res.status(500).json({ error: 'حدث خطأ أثناء رفع وحفظ الصورة: ' + err.message });
  }
});

app.post('/api/products', async (req, res) => {
  try {
    const b = req.body;
    if (!b.name_ar || b.selling_price === undefined) {
      return res.status(400).json({ error: 'اسم المسبحة وسعر البيع مطلوبان' });
    }

    const publicId = crypto.randomUUID();
    const datePart = new Date().toISOString().slice(2, 10).replace(/-/g, '');
    const randPart = crypto.randomBytes(4).toString('hex').toUpperCase();
    const productReference = `HSP-${datePart}-${randPart}`;

    // Concurrency-safe automatic SKU generation
    const maxRow = await queryOne('SELECT MAX(id) as maxId FROM products');
    const nextId = (maxRow?.maxId || 0) + 1;
    const sku = `HS${String(nextId).padStart(5, '0')}`;

    let secImagesJson = '[]';
    if (Array.isArray(b.secondary_images)) {
      secImagesJson = JSON.stringify(b.secondary_images);
    } else if (typeof b.secondary_images === 'string') {
      secImagesJson = b.secondary_images;
    }

    await query(`
      INSERT INTO products (
        public_id, product_reference, sku, name_ar, name_en, description_ar, description_en,
        category_id, material_id, origin, color, bead_count, bead_size_mm, weight_g,
        shape, tassel_type, condition, cost_price, selling_price, discount_price,
        status, is_unique, verification_status, certificate_number, image_url, secondary_images
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      publicId, productReference, sku, b.name_ar, b.name_en || '', b.description_ar || '', b.description_en || '',
      b.category_id || null, b.material_id || null, b.origin || '', b.color || '', b.bead_count || 33,
      b.bead_size_mm || 10.0, b.weight_g || 40.0, b.shape || 'برميلي', b.tassel_type || 'فضة',
      b.condition || 'جديد فاخر', Number(b.cost_price || 0), Number(b.selling_price), b.discount_price ? Number(b.discount_price) : null,
      b.status || 'AVAILABLE', b.is_unique !== undefined ? b.is_unique : 1, b.verification_status || 'CERTIFIED',
      b.certificate_number || '', b.image_url || '', secImagesJson
    ]);

    const created = await queryOne('SELECT * FROM products WHERE public_id = ?', [publicId]);
    await recordAudit(req.body.actor_name || 'Admin', 'OWNER', 'CREATE_PRODUCT', 'CATALOG', { sku, ref: productReference });
    
    io.emit('product:created', created);
    res.status(201).json(created);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/products/:id', async (req, res) => {
  try {
    const b = req.body;
    const existing = await queryOne('SELECT * FROM products WHERE id = ?', [req.params.id]);
    if (!existing) return res.status(404).json({ error: 'المسبحة غير موجودة' });

    let secImagesToSave = existing.secondary_images;
    if (b.secondary_images !== undefined) {
      if (Array.isArray(b.secondary_images)) {
        secImagesToSave = JSON.stringify(b.secondary_images);
      } else if (typeof b.secondary_images === 'string') {
        secImagesToSave = b.secondary_images;
      }
    }

    await query(`
      UPDATE products SET
        name_ar = ?, name_en = ?, description_ar = ?, description_en = ?,
        category_id = ?, material_id = ?, origin = ?, color = ?,
        bead_count = ?, bead_size_mm = ?, weight_g = ?, shape = ?,
        tassel_type = ?, condition = ?, cost_price = ?, selling_price = ?,
        discount_price = ?, status = ?, verification_status = ?, certificate_number = ?,
        image_url = ?, secondary_images = ?, updated_at = datetime('now', 'localtime')
      WHERE id = ?
    `, [
      b.name_ar ?? existing.name_ar, b.name_en ?? existing.name_en,
      b.description_ar ?? existing.description_ar, b.description_en ?? existing.description_en,
      b.category_id ?? existing.category_id, b.material_id ?? existing.material_id,
      b.origin ?? existing.origin, b.color ?? existing.color,
      b.bead_count ?? existing.bead_count, b.bead_size_mm ?? existing.bead_size_mm,
      b.weight_g ?? existing.weight_g, b.shape ?? existing.shape,
      b.tassel_type ?? existing.tassel_type, b.condition ?? existing.condition,
      b.cost_price ?? existing.cost_price, b.selling_price ?? existing.selling_price,
      b.discount_price !== undefined ? b.discount_price : existing.discount_price,
      b.status ?? existing.status, b.verification_status ?? existing.verification_status,
      b.certificate_number ?? existing.certificate_number,
      b.image_url ?? existing.image_url,
      secImagesToSave,
      req.params.id
    ]);

    const updated = await queryOne('SELECT * FROM products WHERE id = ?', [req.params.id]);
    await recordAudit(req.body.actor_name || 'Admin', 'OWNER', 'UPDATE_PRODUCT', 'CATALOG', { id: req.params.id });
    
    io.emit('product:updated', updated);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/products/:id', async (req, res) => {
  const productId = req.params.id;
  const actorName = req.query.actor_name || req.body?.actor_name || 'Admin';

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [productId]);
    if (!product) {
      return res.status(404).json({ error: 'المسبحة غير موجودة' });
    }

    // Check if product is tied to any finalized order
    const orderItems = await query('SELECT id FROM order_items WHERE product_id = ?', [productId]);
    if (orderItems.length > 0) {
      // Safe Archive rather than breaking financial history
      await query("UPDATE products SET status = 'ARCHIVED', updated_at = datetime('now', 'localtime') WHERE id = ?", [productId]);
      await recordAudit(actorName, 'OWNER', 'ARCHIVE_PRODUCT', 'CATALOG', { id: productId, reason: 'Tied to customer order history' });
      io.emit('product:status_changed', { id: productId, status: 'ARCHIVED' });
      return res.json({ success: true, message: 'تمت أرشفة المسبحة بنجاح لحماية السجلات المالية للفواتير' });
    }

    await query('DELETE FROM custody_records WHERE product_id = ?', [productId]);
    await query('DELETE FROM bead_adjustments WHERE product_id = ?', [productId]);
    await query('DELETE FROM products WHERE id = ?', [productId]);

    await recordAudit(actorName, 'OWNER', 'DELETE_PRODUCT', 'CATALOG', { id: productId, sku: product.sku, name: product.name_ar });
    io.emit('product:deleted', { id: productId });

    res.json({ success: true, message: 'تم حذف المسبحة من المخزون بنجاح' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 4. Categories & Materials
app.get('/api/categories', async (req, res) => {
  try {
    const list = await query('SELECT * FROM categories ORDER BY sort_order ASC, id ASC');
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Add new category
app.post('/api/categories', async (req, res) => {
  const { name_ar, name_en, slug, sort_order, is_active } = req.body;
  if (!name_ar || !name_ar.trim()) {
    return res.status(400).json({ error: 'اسم التصنيف بالعربية مطلوب' });
  }

  try {
    const publicId = crypto.randomUUID();
    const cleanNameAr = name_ar.trim();
    const cleanNameEn = (name_en || '').trim();
    let cleanSlug = (slug || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    if (!cleanSlug) {
      cleanSlug = 'cat-' + Date.now();
    }

    const existing = await queryOne('SELECT id FROM categories WHERE slug = ?', [cleanSlug]);
    if (existing) {
      cleanSlug = `${cleanSlug}-${Math.floor(Math.random() * 1000)}`;
    }

    const order = parseInt(sort_order, 10) || 0;
    const active = is_active !== undefined ? (is_active ? 1 : 0) : 1;

    await query(`
      INSERT INTO categories (public_id, name_ar, name_en, slug, sort_order, is_active)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [publicId, cleanNameAr, cleanNameEn, cleanSlug, order, active]);

    const created = await queryOne('SELECT * FROM categories WHERE public_id = ?', [publicId]);
    await recordAudit('Admin', 'OWNER', 'CREATE_CATEGORY', 'CATALOG', { name_ar: cleanNameAr, id: created.id });
    io.emit('category:created', created);
    res.status(201).json(created);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update category
app.put('/api/categories/:id', async (req, res) => {
  const categoryId = req.params.id;
  const { name_ar, name_en, slug, sort_order, is_active } = req.body;
  if (!name_ar || !name_ar.trim()) {
    return res.status(400).json({ error: 'اسم التصنيف بالعربية مطلوب' });
  }

  try {
    const existing = await queryOne('SELECT * FROM categories WHERE id = ?', [categoryId]);
    if (!existing) return res.status(404).json({ error: 'التصنيف غير موجود' });

    const cleanNameAr = name_ar.trim();
    const cleanNameEn = (name_en || '').trim();
    const cleanSlug = (slug || existing.slug).trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    const order = sort_order !== undefined ? parseInt(sort_order, 10) : existing.sort_order;
    const active = is_active !== undefined ? (is_active ? 1 : 0) : existing.is_active;

    await query(`
      UPDATE categories
      SET name_ar = ?, name_en = ?, slug = ?, sort_order = ?, is_active = ?
      WHERE id = ?
    `, [cleanNameAr, cleanNameEn, cleanSlug, order, active, categoryId]);

    const updated = await queryOne('SELECT * FROM categories WHERE id = ?', [categoryId]);
    await recordAudit('Admin', 'OWNER', 'UPDATE_CATEGORY', 'CATALOG', { name_ar: cleanNameAr, id: categoryId });
    io.emit('category:updated', updated);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete category
app.delete('/api/categories/:id', async (req, res) => {
  const categoryId = req.params.id;
  try {
    const existing = await queryOne('SELECT * FROM categories WHERE id = ?', [categoryId]);
    if (!existing) return res.status(404).json({ error: 'التصنيف غير موجود' });

    const linked = await queryOne('SELECT COUNT(*) as count FROM products WHERE category_id = ?', [categoryId]);
    if (linked && linked.count > 0) {
      return res.status(400).json({
        error: `لا يمكن حذف التصنيف لوجود ${linked.count} مسبحة مرتبطة به حالياً. يرجى تعديل تصنيف المسابيح أولاً قبل الحذف.`
      });
    }

    await query('DELETE FROM categories WHERE id = ?', [categoryId]);
    await recordAudit('Admin', 'OWNER', 'DELETE_CATEGORY', 'CATALOG', { name_ar: existing.name_ar, id: categoryId });
    io.emit('category:deleted', { id: categoryId });
    res.json({ success: true, message: 'تم حذف التصنيف بنجاح' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/materials', async (req, res) => {
  try {
    const list = await query('SELECT * FROM materials ORDER BY sort_order ASC, id ASC');
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Countries & Shipping Destinations API
app.get('/api/countries', async (req, res) => {
  try {
    const { all } = req.query;
    let sql = 'SELECT * FROM countries';
    if (!all) {
      sql += ' WHERE is_active = 1';
    }
    sql += ' ORDER BY sort_order ASC, name_ar ASC';
    const list = await query(sql);
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/countries', async (req, res) => {
  const { name_ar, name_en, code, phone_code, currency, sort_order } = req.body;
  if (!name_ar || !name_ar.trim()) {
    return res.status(400).json({ error: 'اسم الدولة بالعربية مطلوب' });
  }

  try {
    const cleanNameAr = name_ar.trim();
    const existing = await queryOne('SELECT id FROM countries WHERE LOWER(name_ar) = ?', [cleanNameAr.toLowerCase()]);
    if (existing) {
      return res.status(400).json({ error: 'الدولة مسجلة مسبقاً في النظام' });
    }

    const nextOrder = parseInt(sort_order, 10) || 50;
    await query(`
      INSERT INTO countries (name_ar, name_en, code, phone_code, currency, sort_order, is_active, is_system)
      VALUES (?, ?, ?, ?, ?, ?, 1, 0)
    `, [
      cleanNameAr,
      (name_en || '').trim(),
      (code || '').trim().toUpperCase(),
      (phone_code || '').trim(),
      (currency || 'AED').trim().toUpperCase(),
      nextOrder
    ]);

    const created = await queryOne('SELECT * FROM countries WHERE name_ar = ?', [cleanNameAr]);
    await recordAudit(req.body.actor_name || 'Admin', 'OWNER', 'CREATE_COUNTRY', 'SETTINGS', { name: cleanNameAr, id: created.id });
    io.emit('country:created', created);
    res.status(201).json(created);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/countries/:id', async (req, res) => {
  const countryId = req.params.id;
  const { name_ar, name_en, code, phone_code, currency, sort_order, is_active } = req.body;

  try {
    const existing = await queryOne('SELECT * FROM countries WHERE id = ?', [countryId]);
    if (!existing) return res.status(404).json({ error: 'الدولة غير موجودة' });

    await query(`
      UPDATE countries SET
        name_ar = ?, name_en = ?, code = ?, phone_code = ?,
        currency = ?, sort_order = ?, is_active = ?
      WHERE id = ?
    `, [
      name_ar ? name_ar.trim() : existing.name_ar,
      name_en !== undefined ? name_en.trim() : existing.name_en,
      code !== undefined ? code.trim().toUpperCase() : existing.code,
      phone_code !== undefined ? phone_code.trim() : existing.phone_code,
      currency !== undefined ? currency.trim().toUpperCase() : existing.currency,
      sort_order !== undefined ? Number(sort_order) : existing.sort_order,
      is_active !== undefined ? Number(is_active) : existing.is_active,
      countryId
    ]);

    const updated = await queryOne('SELECT * FROM countries WHERE id = ?', [countryId]);
    await recordAudit(req.body.actor_name || 'Admin', 'OWNER', 'UPDATE_COUNTRY', 'SETTINGS', { name: updated.name_ar, id: countryId });
    io.emit('country:updated', updated);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/countries/:id', async (req, res) => {
  const countryId = req.params.id;
  try {
    const existing = await queryOne('SELECT * FROM countries WHERE id = ?', [countryId]);
    if (!existing) return res.status(404).json({ error: 'الدولة غير موجودة' });

    if (existing.is_system) {
      return res.status(400).json({ error: 'لا يمكن حذف الدول العربية الأساسية المدمجة بالنظام. يمكنك تعطيل تفعيلها بدلاً من ذلك.' });
    }

    await query('DELETE FROM countries WHERE id = ?', [countryId]);
    await recordAudit('Admin', 'OWNER', 'DELETE_COUNTRY', 'SETTINGS', { name: existing.name_ar, id: countryId });
    io.emit('country:deleted', { id: countryId });
    res.json({ success: true, message: 'تم حذف الدولة بنجاح' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 5. Exclusivity & Anti-Double-Selling: Atomically Reserve a Rosary
app.post('/api/products/:id/reserve', async (req, res) => {
  const productId = req.params.id;
  const { cart_id, minutes } = req.body;
  const lockAcquired = await acquireProductLock(productId);
  if (!lockAcquired) {
    return res.status(409).json({ error: 'القطعة قيد المعالجة حالياً من قبل عميل آخر' });
  }

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [productId]);
    if (!product) {
      releaseProductLock(productId);
      return res.status(404).json({ error: 'المسبحة غير موجودة' });
    }

    if (product.status === 'SOLD') {
      releaseProductLock(productId);
      return res.status(400).json({ error: 'عذراً، هذه المسبحة الفريدة تم بيعها واقتناؤها مسبقاً' });
    }

    // Check existing active reservation
    if (product.status === 'RESERVED' && product.reserved_by_cart !== cart_id) {
      const now = new Date();
      const expiry = product.reserved_until ? new Date(product.reserved_until) : null;
      if (expiry && expiry > now) {
        releaseProductLock(productId);
        const remainingMinutes = Math.ceil((expiry.getTime() - now.getTime()) / 60000);
        return res.status(409).json({
          error: `المسبحة محجوزة مؤقتاً لعميل آخر. متبقي ${remainingMinutes} دقيقة على انتهاء مهلة الحجز.`
        });
      }
    }

    const duration = minutes || 15;
    await query(`
      UPDATE products SET
        status = 'RESERVED',
        reserved_until = datetime('now', 'localtime', '+' || ? || ' minutes'),
        reserved_by_cart = ?,
        updated_at = datetime('now', 'localtime')
      WHERE id = ?
    `, [duration, cart_id || 'guest', productId]);

    const updated = await queryOne('SELECT * FROM products WHERE id = ?', [productId]);
    releaseProductLock(productId);
    
    io.emit('product:reserved', updated);
    res.json({ success: true, product: updated });
  } catch (err) {
    releaseProductLock(productId);
    res.status(500).json({ error: err.message });
  }
});

// 6. Quick Sale & Exhibition POS (Strict Financial Truth & Double-Selling Prevention)
app.post('/api/quick-sale', async (req, res) => {
  const {
    product_id,
    customer_name,
    customer_phone,
    customer_email,
    payment_method, // CASH, POS, BANK_TRANSFER, DEFERRED
    special_discount,
    payment_due_date,
    notes,
    actor_name
  } = req.body;

  if (!product_id || !payment_method) {
    return res.status(400).json({ error: 'معرف المسبحة وطريقة الدفع مطلوبان' });
  }

  const lockAcquired = await acquireProductLock(product_id);
  if (!lockAcquired) {
    return res.status(409).json({ error: 'عملية البيع قيد التنفيذ حالياً لهذه القطعة' });
  }

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [product_id]);
    if (!product) {
      releaseProductLock(product_id);
      return res.status(404).json({ error: 'المسبحة غير موجودة' });
    }

    if (product.status === 'SOLD') {
      releaseProductLock(product_id);
      return res.status(400).json({ error: 'المسبحة مباعة بالفعل ولا يمكن بيعها مرتين (حماية حصرية القطع)' });
    }

    const basePrice = Number(product.selling_price);
    const discount = Number(special_discount || 0);
    if (discount >= basePrice) {
      releaseProductLock(product_id);
      return res.status(400).json({ error: 'قيمة الخصم يجب أن تكون أقل من سعر البيع' });
    }

    const grandTotal = basePrice - discount;
    const isDeferred = payment_method === 'DEFERRED';
    const paymentStatus = isDeferred ? 'UNPAID' : 'PAID';
    const paidAmount = isDeferred ? 0.0 : grandTotal;
    const outstandingAmount = isDeferred ? grandTotal : 0.0;

    const datePart = new Date().toISOString().slice(2, 10).replace(/-/g, '');
    const randPart = crypto.randomBytes(3).toString('hex').toUpperCase();
    const orderRef = `HSO-${datePart}-${randPart}`;
    const orderPublicId = crypto.randomUUID();

    // 1. Create Order
    await query(`
      INSERT INTO orders (
        public_id, reference, customer_name, customer_phone, customer_email,
        country, city, area, subtotal, discount_total, tax_total, grand_total,
        currency, sale_channel, delivery_method, status, payment_status,
        payment_method, payment_due_date, paid_amount, outstanding_amount,
        hand_to_hand_by, additional_notes, delivered_at
      ) VALUES (?, ?, ?, ?, ?, 'AE', 'المعرض الرئيسي', 'بيع مباشر', ?, ?, 0.0, ?, 'AED', 'DIRECT', 'HAND_TO_HAND', 'DELIVERED', ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    `, [
      orderPublicId, orderRef, customer_name || 'عميل مباشر', customer_phone || '', customer_email || '',
      basePrice, discount, grandTotal, paymentStatus, payment_method,
      isDeferred ? payment_due_date : null, paidAmount, outstandingAmount,
      actor_name || 'الكاشير', notes || ''
    ]);

    const order = await queryOne('SELECT * FROM orders WHERE public_id = ?', [orderPublicId]);

    // 2. Create Order Item with Immutable Financial Cost Snapshot
    await query(`
      INSERT INTO order_items (
        order_id, product_id, product_reference, sku, name_ar,
        cost_price_snapshot, unit_price, discount, line_total, original_bead_count, image_url
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      order.id, product.id, product.product_reference, product.sku, product.name_ar,
      Number(product.cost_price), basePrice, discount, grandTotal, product.bead_count, product.image_url
    ]);

    // 3. Mark Product as Sold and Clear any Reservation
    await query(`
      UPDATE products SET
        status = 'SOLD',
        reserved_until = NULL,
        reserved_by_cart = NULL,
        updated_at = datetime('now', 'localtime')
      WHERE id = ?
    `, [product.id]);

    // 4. If Paid, Record Direct Payment Receipt
    if (!isDeferred) {
      await query(`
        INSERT INTO direct_payments (order_id, amount, payment_method, note, received_by_name)
        VALUES (?, ?, ?, 'سداد فوري بنقطة البيع', ?)
      `, [order.id, grandTotal, payment_method, actor_name || 'الكاشير']);
    }

    // 5. Immutable Audit Log
    await recordAudit(
      actor_name || 'الكاشير',
      'SALES',
      'QUICK_SALE_COMPLETED',
      'ORDERS',
      { orderRef, sku: product.sku, grandTotal, isDeferred }
    );

    releaseProductLock(product_id);
    io.emit('order:created', order);
    io.emit('product:status_changed', { id: product.id, status: 'SOLD' });

    res.status(201).json({
      success: true,
      order,
      product_reference: product.product_reference,
      sku: product.sku
    });
  } catch (err) {
    releaseProductLock(product_id);
    res.status(500).json({ error: err.message });
  }
});

// 7. Rosary Custody Management (Append-Only Immutable Records)
app.get('/api/products/:id/custody', async (req, res) => {
  try {
    const history = await query(`
      SELECT * FROM custody_history WHERE product_id = ? ORDER BY id DESC
    `, [req.params.id]);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/products/:id/custody', async (req, res) => {
  const { holder_name, location_name, placed_on, note, actor_name } = req.body;
  if (!holder_name || !location_name) {
    return res.status(400).json({ error: 'اسم الحائز وموقع العهدة مطلوبان' });
  }

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [req.params.id]);
    if (!product) return res.status(404).json({ error: 'المسبحة غير موجودة' });

    // Append-only entry
    await query(`
      INSERT INTO custody_history (product_id, holder_name, location_name, placed_on, note, recorded_by_name)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [
      product.id, holder_name, location_name, placed_on || new Date().toISOString().slice(0, 10),
      note || '', actor_name || 'المشرف'
    ]);

    // Update product status to IN_CUSTODY if available
    if (product.status === 'AVAILABLE') {
      await query("UPDATE products SET status = 'IN_CUSTODY', updated_at = datetime('now', 'localtime') WHERE id = ?", [product.id]);
    }

    await recordAudit(actor_name || 'المشرف', 'SUPERVISOR', 'CUSTODY_ASSIGNED', 'CUSTODY', {
      sku: product.sku, holder_name, location_name
    });

    res.status(201).json({ success: true, message: 'تم قيد سجل العهدة بنجاح' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 8. Custom Rosary Bead Adjustments (Workshop & Sizing)
app.get('/api/bead-adjustments', async (req, res) => {
  try {
    const list = await query(`
      SELECT b.*, p.name_ar as product_name_ar, p.image_url as product_image_url
      FROM bead_adjustments b
      LEFT JOIN products p ON b.product_id = p.id
      ORDER BY b.id DESC
    `);
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/bead-adjustments', async (req, res) => {
  const {
    order_id,
    product_id,
    customer_name,
    customer_phone,
    requested_bead_count,
    notes,
    actor_name
  } = req.body;

  try {
    const product = await queryOne('SELECT * FROM products WHERE id = ?', [product_id]);
    if (!product) return res.status(404).json({ error: 'المسبحة غير موجودة' });

    const orig = Number(product.bead_count);
    const reqCount = Number(requested_bead_count);
    if (reqCount >= orig) {
      return res.status(400).json({ error: 'العدد المطلوب يجب أن يكون أقل من عدد الخرز الأصلي لتصغير المسبحة' });
    }

    const removed = orig - reqCount;

    await query(`
      INSERT INTO bead_adjustments (
        order_id, product_id, product_reference, customer_name, customer_phone,
        original_bead_count, requested_bead_count, removed_beads_count, notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      order_id || null, product.id, product.product_reference, customer_name || 'عميل', customer_phone || '',
      orig, reqCount, removed, notes || ''
    ]);

    await recordAudit(actor_name || 'ورشة', 'WORKSHOP', 'BEAD_ADJUSTMENT_REQUESTED', 'SERVICES', {
      sku: product.sku, original: orig, requested: reqCount, removed
    });

    res.status(201).json({
      success: true,
      message: `تم قيد طلب تعديل المسبحة وتجهيز كيس حفظ لعدد (${removed}) خرزات مفكوكة`
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.patch('/api/bead-adjustments/:id/status', async (req, res) => {
  const { status, actor_name } = req.body;
  try {
    const completedAt = status === 'COMPLETED' ? new Date().toISOString() : null;
    await query(`
      UPDATE bead_adjustments SET status = ?, completed_at = ? WHERE id = ?
    `, [status, completedAt, req.params.id]);

    res.json({ success: true, status });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 9. Orders & Invoices
app.get('/api/orders', async (req, res) => {
  try {
    const { status, payment_status, search } = req.query;
    let sql = 'SELECT * FROM orders WHERE 1=1';
    const args = [];

    if (status && status !== 'ALL') {
      sql += ' AND status = ?';
      args.push(status);
    }
    if (payment_status && payment_status !== 'ALL') {
      sql += ' AND payment_status = ?';
      args.push(payment_status);
    }
    if (search) {
      sql += ' AND (reference LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)';
      const s = `%${search}%`;
      args.push(s, s, s);
    }

    sql += ' ORDER BY id DESC';
    const orders = await query(sql, args);
    res.json(orders);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/orders/:id', async (req, res) => {
  try {
    const order = await queryOne('SELECT * FROM orders WHERE id = ? OR public_id = ? OR reference = ?', [
      req.params.id, req.params.id, req.params.id
    ]);
    if (!order) return res.status(404).json({ error: 'الطلب غير موجود' });

    const items = await query('SELECT * FROM order_items WHERE order_id = ?', [order.id]);
    const payments = await query('SELECT * FROM direct_payments WHERE order_id = ? ORDER BY id DESC', [order.id]);

    res.json({ ...order, items, payments });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10. Smart Accountant & Financial Truth Engine
app.get('/api/accountant/report', async (req, res) => {
  try {
    const { period, start, end } = req.query;
    let dateFilter = '1=1';
    const args = [];

    if (period === 'today') {
      dateFilter = "date(delivered_at) = date('now', 'localtime')";
    } else if (period === 'week') {
      dateFilter = "delivered_at >= datetime('now', '-7 days', 'localtime')";
    } else if (period === 'month' || !period) {
      dateFilter = "strftime('%Y-%m', delivered_at) = strftime('%Y-%m', 'now', 'localtime')";
    } else if (period === 'year') {
      dateFilter = "strftime('%Y', delivered_at) = strftime('%Y', 'now', 'localtime')";
    } else if (period === 'custom' && start && end) {
      dateFilter = 'date(delivered_at) BETWEEN date(?) AND date(?)';
      args.push(start, end);
    }

    // Realized figures: Only delivered and paid orders
    const realizedOrders = await query(`
      SELECT * FROM orders
      WHERE status = 'DELIVERED' AND payment_status = 'PAID' AND ${dateFilter}
    `, args);

    let totalSales = 0.0;
    let totalDiscounts = 0.0;
    let orderIds = [];

    for (const ord of realizedOrders) {
      totalSales += Number(ord.grand_total);
      totalDiscounts += Number(ord.discount_total || 0);
      orderIds.push(ord.id);
    }

    let totalCostOfGoodsSold = 0.0;
    if (orderIds.length > 0) {
      const placeholders = orderIds.map(() => '?').join(',');
      const itemRows = await query(`
        SELECT SUM(cost_price_snapshot) as totalCost FROM order_items
        WHERE order_id IN (${placeholders})
      `, orderIds);
      totalCostOfGoodsSold = Number(itemRows[0]?.totalCost || 0);
    }

    // Active Operational Expenses
    const expenseRows = await query(`
      SELECT SUM(amount) as totalExpenses FROM expenses
      WHERE status = 'ACTIVE'
    `);
    const totalExpenses = Number(expenseRows[0]?.totalExpenses || 0);

    const grossProfit = totalSales - totalCostOfGoodsSold;
    const netProfit = grossProfit - totalExpenses;
    const profitMargin = totalSales > 0 ? (grossProfit / totalSales) * 100 : 0.0;

    // Receivables (Unpaid Deferred Sales)
    const receivablesRows = await query(`
      SELECT SUM(outstanding_amount) as totalReceivables, COUNT(*) as countReceivables
      FROM orders WHERE payment_status != 'PAID' AND outstanding_amount > 0
    `);
    const totalReceivables = Number(receivablesRows[0]?.totalReceivables || 0);
    const countReceivables = Number(receivablesRows[0]?.countReceivables || 0);

    res.json({
      period: period || 'month',
      orderCount: realizedOrders.length,
      totalSales,
      totalDiscounts,
      totalCostOfGoodsSold,
      grossProfit,
      totalExpenses,
      netProfit,
      profitMargin: profitMargin.toFixed(2),
      totalReceivables,
      countReceivables
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Receivables List
app.get('/api/receivables', async (req, res) => {
  try {
    const list = await query(`
      SELECT * FROM orders
      WHERE payment_status != 'PAID' AND outstanding_amount > 0
      ORDER BY payment_due_date ASC, id DESC
    `);
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Pay towards Receivable
app.post('/api/receivables/:id/payment', async (req, res) => {
  const { amount, payment_method, note, actor_name } = req.body;
  const payAmt = Number(amount);
  if (!payAmt || payAmt <= 0) {
    return res.status(400).json({ error: 'مبلغ السداد يجب أن يكون أكبر من صفر' });
  }

  try {
    const order = await queryOne('SELECT * FROM orders WHERE id = ?', [req.params.id]);
    if (!order) return res.status(404).json({ error: 'الطلب غير موجود' });

    const outstanding = Number(order.outstanding_amount);
    if (payAmt > outstanding) {
      return res.status(400).json({ error: `المبلغ المدفوع يتجاوز الرصيد المتبقي (${outstanding} درهم)` });
    }

    const newOutstanding = outstanding - payAmt;
    const newPaid = Number(order.paid_amount) + payAmt;
    const newStatus = newOutstanding === 0 ? 'PAID' : 'PARTIALLY_PAID';

    await query(`
      UPDATE orders SET
        outstanding_amount = ?,
        paid_amount = ?,
        payment_status = ?
      WHERE id = ?
    `, [newOutstanding, newPaid, newStatus, order.id]);

    await query(`
      INSERT INTO direct_payments (order_id, amount, payment_method, note, received_by_name)
      VALUES (?, ?, ?, ?, ?)
    `, [order.id, payAmt, payment_method || 'CASH', note || 'سداد آجل', actor_name || 'الكاشير']);

    await recordAudit(actor_name || 'الكاشير', 'SALES', 'RECEIVABLE_PAYMENT_COLLECTED', 'FINANCE', {
      orderRef: order.reference, amount: payAmt, remaining: newOutstanding
    });

    res.json({ success: true, newOutstanding, paymentStatus: newStatus });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 11. Operational Expenses (Packaging, Bags, Shipping)
app.get('/api/expenses', async (req, res) => {
  try {
    const expenses = await query('SELECT * FROM expenses ORDER BY incurred_on DESC, id DESC');
    res.json(expenses);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/expenses', async (req, res) => {
  const { category, description, amount, incurred_on, supplier, actor_name } = req.body;
  if (!description || !amount) {
    return res.status(400).json({ error: 'وصف المصروف والمبلغ مطلوبان' });
  }

  try {
    const publicId = crypto.randomUUID();
    await query(`
      INSERT INTO expenses (public_id, category, description, amount, incurred_on, supplier, created_by_name)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `, [
      publicId, category || 'BOXES', description, Number(amount),
      incurred_on || new Date().toISOString().slice(0, 10), supplier || '', actor_name || 'المحاسب'
    ]);

    await recordAudit(actor_name || 'المحاسب', 'ACCOUNTANT', 'CREATE_EXPENSE', 'FINANCE', { description, amount });
    res.status(201).json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/expenses/:id/void', async (req, res) => {
  const { reason, actor_name } = req.body;
  if (!reason || !reason.trim()) {
    return res.status(400).json({ error: 'سبب الإلغاء إلزامي ولا يمكن حذف المصاريف مباشرة' });
  }

  try {
    await query(`
      UPDATE expenses SET
        status = 'VOIDED',
        void_reason = ?,
        voided_at = datetime('now', 'localtime')
      WHERE id = ?
    `, [reason.trim(), req.params.id]);

    await recordAudit(actor_name || 'المحاسب', 'ACCOUNTANT', 'VOID_EXPENSE', 'FINANCE', { id: req.params.id, reason });
    res.json({ success: true, message: 'تم إلغاء المصروف وتوثيقه محاسبياً' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 12. Ambassador Program & Affiliates
app.get('/api/ambassadors', async (req, res) => {
  try {
    const list = await query('SELECT * FROM ambassadors ORDER BY id DESC');
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/ambassadors', async (req, res) => {
  const { name, phone, email } = req.body;
  if (!name || !phone) return res.status(400).json({ error: 'الاسم ورقم الهاتف مطلوبان' });

  try {
    const code = 'HSA-' + crypto.randomBytes(4).toString('hex').toUpperCase();
    await query(`
      INSERT INTO ambassadors (name, phone, email, code) VALUES (?, ?, ?, ?)
    `, [name, phone, email || '', code]);

    res.status(201).json({ success: true, code });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 13. Audit Trail Records
app.get('/api/audit', async (req, res) => {
  try {
    const logs = await query('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200');
    res.json(logs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 14. Store Settings
app.get('/api/settings', async (req, res) => {
  try {
    const settings = await queryOne('SELECT * FROM store_settings WHERE id = 1');
    res.json(settings || {});
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/settings', async (req, res) => {
  const b = req.body;
  try {
    await query(`
      UPDATE store_settings SET
        store_name_ar = ?, store_name_en = ?, phone = ?, email = ?,
        address = ?, currency = ?, tax_rate = ?, shipping_fee = ?,
        reservation_minutes = ?, invoice_thank_you = ?, whatsapp_number = ?
      WHERE id = 1
    `, [
      b.store_name_ar, b.store_name_en, b.phone, b.email,
      b.address, b.currency, b.tax_rate, b.shipping_fee,
      b.reservation_minutes, b.invoice_thank_you, b.whatsapp_number
    ]);

    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 15. License & Hardware ID Management
app.get('/api/license/status', (req, res) => {
  if (licenseHelper) {
    res.json(licenseHelper.checkLicenseStatus());
  } else {
    res.json({ isActivated: true, type: 'dev', message: 'مفتاح المطور النشط' });
  }
});

app.post('/api/license/activate', (req, res) => {
  const { key } = req.body;
  if (!key) return res.status(400).json({ error: 'مفتاح الترخيص مطلوب' });
  if (licenseHelper) {
    res.json(licenseHelper.activateLicense(key));
  } else {
    res.json({ success: true, message: 'تم التفعيل' });
  }
});

// 16. Cloud Configuration & Database Sync
app.get('/api/cloud/config', (req, res) => {
  res.json(cloudConfig.getCloudConfig());
});

app.post('/api/cloud/config', (req, res) => {
  res.json(cloudConfig.saveCloudConfig(req.body));
});

// Production Static Serving with Caching
const distPath = path.join(__dirname, 'dist');
if (fs.existsSync(distPath)) {
  console.log(`✅ [Static] Serving luxury storefront and dashboard from: ${distPath}`);
  
  app.use(express.static(distPath, {
    maxAge: '7d',
    etag: true,
    lastModified: true,
    setHeaders: (res, filePath) => {
      // Immutable long-term caching for hashed JS/CSS assets and fonts
      if (filePath.includes(path.sep + 'assets' + path.sep) || filePath.includes(path.sep + 'fonts' + path.sep)) {
        res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
      } else if (filePath.endsWith('.html')) {
        res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
      } else {
        // Branding images, etc.
        res.setHeader('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400');
      }
    }
  }));

  app.get('*', (req, res) => {
    if (!req.path.startsWith('/api')) {
      res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
      res.sendFile(path.join(distPath, 'index.html'));
    }
  });
} else {
  console.warn(`⚠️ [Static] "dist" folder not found at: ${distPath}`);
  app.get('/', (req, res) => {
    res.status(200).send(`
      <!DOCTYPE html>
      <html dir="rtl" lang="ar">
      <head>
        <meta charset="utf-8">
        <title>خادم هيبة السلطان - بانتظار ملفات الواجهة</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f17; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }
          .card { background: #131b2e; border: 1px solid #d4af37; border-radius: 16px; padding: 40px; max-width: 600px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
          h1 { color: #d4af37; margin-bottom: 12px; font-size: 24px; }
          p { color: #94a3b8; line-height: 1.6; }
          code { background: #1e293b; color: #38bdf8; padding: 4px 8px; border-radius: 6px; }
          .badge { display: inline-block; padding: 6px 14px; background: rgba(212,175,55,0.15); color: #d4af37; border: 1px solid rgba(212,175,55,0.3); border-radius: 999px; font-size: 13px; margin-bottom: 16px; }
        </style>
      </head>
      <body>
        <div class="card">
          <div class="badge">هيبة السلطان - Haybat Al Sultan PRO</div>
          <h1>الخادم الخلفي يعمل بنجاح ✅</h1>
          <p>تم تشغيل محرك الخادم وقاعدة البيانات بنجاح، لكن مجلد واجهة المتجر <code>dist</code> لم يتم العثور عليه في الحاوية.</p>
          <p>قم ببناء الواجهة محلياً عبر <code>npm run build</code> ثم رفع مجلد <code>dist</code> إلى GitHub وإعادة النشر على Easypanel.</p>
        </div>
      </body>
      </html>
    `);
  });
}

// Socket.IO Events
io.on('connection', (socket) => {
  console.log(`🔌 [Socket.IO] Client connected: ${socket.id}`);
  socket.on('disconnect', () => {
    console.log(`🔌 [Socket.IO] Client disconnected: ${socket.id}`);
  });
});

// Start Server
async function start() {
  await initDatabase();
  httpServer.listen(PORT, HOST, () => {
    console.log(`
==============================================================================
📿 HAYBAT AL SULTAN PRO - ENGINE ONLINE
==============================================================================
🚀 Server listening on: http://${HOST}:${PORT}
🗄️ Database path: ${DB_PATH}
🛡️ Exclusivity Engine: Active (Double-selling Prevention)
⏰ Background Cron: Active (Reservations Auto-Release)
==============================================================================
    `);
  });
}

start().catch(err => {
  console.error('❌ Failed to start Haybat Al Sultan PRO Server:', err);
});
