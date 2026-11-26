export type ProductStatus = 'AVAILABLE' | 'RESERVED' | 'SOLD' | 'IN_CUSTODY' | 'IN_WORKSHOP' | 'ARCHIVED';
export type VerificationStatus = 'NONE' | 'INSPECTED' | 'CERTIFIED';
export type PaymentMethod = 'CASH' | 'POS' | 'BANK_TRANSFER' | 'DEFERRED' | 'STRIPE' | 'MANUAL';
export type PaymentStatus = 'UNPAID' | 'PAID' | 'PARTIALLY_PAID' | 'REFUNDED';
export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'PREPARING' | 'READY' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';

export interface Category {
  id: number;
  public_id: string;
  name_ar: string;
  name_en: string;
  slug: string;
  sort_order: number;
  is_active: number;
}

export interface Material {
  id: number;
  public_id: string;
  name_ar: string;
  name_en: string;
  slug: string;
  sort_order: number;
  is_active: number;
}

export interface Country {
  id: number;
  name_ar: string;
  name_en?: string;
  code?: string;
  phone_code?: string;
  currency?: string;
  sort_order: number;
  is_active: number;
  is_system?: number;
}

export interface Product {
  id: number;
  public_id: string;
  product_reference: string;
  sku: string;
  name_ar: string;
  name_en: string;
  description_ar: string;
  description_en: string;
  category_id?: number;
  material_id?: number;
  category_name_ar?: string;
  category_name_en?: string;
  material_name_ar?: string;
  material_name_en?: string;
  origin: string;
  color: string;
  bead_count: number;
  bead_size_mm: string | number;
  weight_g: number;
  shape: string;
  tassel_type: string;
  condition: string;
  cost_price: number;
  selling_price: number;
  discount_price?: number | null;
  status: ProductStatus;
  is_unique: number;
  quantity: number;
  reserved_until?: string | null;
  reserved_by_cart?: string | null;
  verification_status: VerificationStatus;
  certificate_number?: string;
  image_url: string;
  secondary_images?: string;
  sales_channel?: 'b2c' | 'b2b' | 'both';
  price_b2c?: number;
  price_b2b?: number;
  b2b_moq?: number;
  stock_quantity?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CustodyRecord {
  id: number;
  product_id: number;
  holder_name: string;
  location_name: string;
  placed_on: string;
  note: string;
  recorded_by_name: string;
  created_at: string;
}

export interface BeadAdjustment {
  id: number;
  order_id?: number;
  product_id: number;
  product_reference: string;
  product_name_ar?: string;
  product_image_url?: string;
  customer_name: string;
  customer_phone: string;
  original_bead_count: number;
  requested_bead_count: number;
  removed_beads_count: number;
  bag_labeled: number;
  status: 'PENDING' | 'IN_WORKSHOP' | 'COMPLETED' | 'DELIVERED';
  notes: string;
  created_at: string;
  completed_at?: string | null;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id?: number;
  product_reference: string;
  sku: string;
  name_ar: string;
  cost_price_snapshot: number;
  unit_price: number;
  discount: number;
  line_total: number;
  original_bead_count?: number;
  requested_bead_count?: number;
  image_url: string;
}

export interface Order {
  id: number;
  public_id: string;
  reference: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  country: string;
  city?: string;
  area?: string;
  subtotal: number;
  discount_total: number;
  tax_total: number;
  grand_total: number;
  currency: string;
  sale_channel: 'DIRECT' | 'ONLINE';
  delivery_method: 'HAND_TO_HAND' | 'SHIPPING';
  status: OrderStatus;
  payment_status: PaymentStatus;
  payment_method: PaymentMethod;
  payment_due_date?: string | null;
  paid_amount: number;
  outstanding_amount: number;
  hand_to_hand_by?: string;
  additional_notes?: string;
  delivered_at?: string | null;
  created_at: string;
  items?: OrderItem[];
  payments?: any[];
}

export interface Expense {
  id: number;
  public_id: string;
  category: string;
  description: string;
  amount: number;
  incurred_on: string;
  supplier?: string;
  status: 'ACTIVE' | 'VOIDED';
  void_reason?: string;
  voided_at?: string | null;
  created_by_name: string;
  created_at: string;
}

export interface Ambassador {
  id: number;
  name: string;
  phone: string;
  email: string;
  code: string;
  points_balance: number;
  total_earned: number;
  is_active: number;
  created_at: string;
}

export interface AccountantReport {
  period: string;
  orderCount: number;
  totalSales: number;
  totalDiscounts: number;
  totalCostOfGoodsSold: number;
  grossProfit: number;
  totalExpenses: number;
  netProfit: number;
  profitMargin: string;
  totalReceivables: number;
  countReceivables: number;
}

export interface StoreSettings {
  store_name_ar: string;
  store_name_en: string;
  phone: string;
  email: string;
  address: string;
  currency: string;
  tax_rate: number;
  shipping_fee: number;
  reservation_minutes: number;
  invoice_thank_you: string;
  whatsapp_number: string;
}

export interface User {
  id: number;
  public_id: string;
  username: string;
  full_name: string;
  role: 'OWNER' | 'SUPERVISOR' | 'SALES' | 'ACCOUNTANT' | 'WORKSHOP' | 'CUSTOMER' | 'b2c_user' | 'b2b_pending' | 'b2b_approved' | 'admin';
  phone?: string;
  email?: string;
  company_name?: string;
  commercial_register?: string;
  tax_id?: string;
  approved_at?: string;
  approved_by?: string;
  permissions?: Record<string, boolean>;
  is_active?: number;
  created_at?: string;
}
