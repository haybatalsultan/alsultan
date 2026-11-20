import axios from 'axios';
import { io } from 'socket.io-client';

const API_BASE = '/api';

// Automatically inject JWT bearer tokens for customer and staff requests
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('haybat_customer_token') || localStorage.getItem('haybat_staff_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const socket = io({
  transports: ['websocket', 'polling'],
  autoConnect: true
});

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const res = await axios.post(`${API_BASE}/auth/login`, { username, password });
    return res.data;
  },
  customerRegister: async (data: { username: string; password: string; full_name: string; phone?: string; email?: string }) => {
    const res = await axios.post(`${API_BASE}/auth/customer/register`, data);
    return res.data;
  },
  customerLogin: async (identifier: string, password: string) => {
    const res = await axios.post(`${API_BASE}/auth/customer/login`, { identifier, password });
    return res.data;
  },
  adminLogin: async (username: string, password: string) => {
    const res = await axios.post(`${API_BASE}/auth/admin/login`, { username, password });
    return res.data;
  },
  getCustomerOrders: async (params: { phone?: string; email?: string }) => {
    const res = await axios.get(`${API_BASE}/customer/my-orders`, { params });
    return res.data;
  },
  checkoutOnline: async (data: any) => {
    const res = await axios.post(`${API_BASE}/orders/checkout`, data);
    return res.data;
  },

  // B2B Wholesale Authentication & Portal
  b2bRegister: async (data: {
    company_name: string;
    commercial_register: string;
    tax_id?: string;
    full_name: string;
    email: string;
    phone: string;
    password: string;
    website_hp?: string;
  }) => {
    const res = await axios.post(`${API_BASE}/auth/b2b/register`, data);
    return res.data;
  },
  getB2BProducts: async (params?: { search?: string; category?: string | number }) => {
    const res = await axios.get(`${API_BASE}/b2b/products`, { params });
    return res.data;
  },
  b2bCheckout: async (data: {
    items: { product_id: number | string; quantity: number }[];
    company_name: string;
    commercial_register: string;
    tax_id?: string;
    contact_name: string;
    phone: string;
    email?: string;
    shipping_address?: string;
    city?: string;
    payment_method: 'BANK_TRANSFER' | 'CHEQUE' | 'CREDIT_TERMS';
    notes?: string;
  }) => {
    const res = await axios.post(`${API_BASE}/b2b/checkout`, data);
    return res.data;
  },
  getB2BMerchants: async () => {
    const res = await axios.get(`${API_BASE}/admin/b2b/merchants`);
    return res.data;
  },
  approveB2BMerchant: async (id: number | string, actor_name?: string) => {
    const res = await axios.post(`${API_BASE}/admin/b2b/approve/${id}`, { actor_name });
    return res.data;
  },
  rejectB2BMerchant: async (id: number | string, actor_name?: string) => {
    const res = await axios.post(`${API_BASE}/admin/b2b/reject/${id}`, { actor_name });
    return res.data;
  },

  // Products
  getProducts: async (params?: Record<string, any>) => {
    const res = await axios.get(`${API_BASE}/products`, { params });
    return res.data;
  },
  getProduct: async (id: string | number) => {
    const res = await axios.get(`${API_BASE}/products/${id}`);
    return res.data;
  },
  createProduct: async (data: any) => {
    const res = await axios.post(`${API_BASE}/products`, data);
    return res.data;
  },
  updateProduct: async (id: number, data: any) => {
    const res = await axios.put(`${API_BASE}/products/${id}`, data);
    return res.data;
  },
  deleteProduct: async (id: number, actor_name?: string) => {
    const res = await axios.delete(`${API_BASE}/products/${id}`, { params: { actor_name } });
    return res.data;
  },
  reserveProduct: async (id: number, cart_id?: string, minutes?: number) => {
    const res = await axios.post(`${API_BASE}/products/${id}/reserve`, { cart_id, minutes });
    return res.data;
  },

  // Categories & Materials
  getCategories: async () => {
    const res = await axios.get(`${API_BASE}/categories`);
    return res.data;
  },
  createCategory: async (data: { name_ar: string; name_en?: string; slug?: string; sort_order?: number }) => {
    const res = await axios.post(`${API_BASE}/categories`, data);
    return res.data;
  },
  updateCategory: async (id: number, data: { name_ar: string; name_en?: string; slug?: string; sort_order?: number }) => {
    const res = await axios.put(`${API_BASE}/categories/${id}`, data);
    return res.data;
  },
  deleteCategory: async (id: number) => {
    const res = await axios.delete(`${API_BASE}/categories/${id}`);
    return res.data;
  },
  getMaterials: async () => {
    const res = await axios.get(`${API_BASE}/materials`);
    return res.data;
  },

  // Quick Sale POS
  quickSale: async (data: any) => {
    const res = await axios.post(`${API_BASE}/quick-sale`, data);
    return res.data;
  },

  // Custody
  getCustody: async (productId: number) => {
    const res = await axios.get(`${API_BASE}/products/${productId}/custody`);
    return res.data;
  },
  assignCustody: async (productId: number, data: any) => {
    const res = await axios.post(`${API_BASE}/products/${productId}/custody`, data);
    return res.data;
  },

  // Bead Adjustment Workshop
  getBeadAdjustments: async () => {
    const res = await axios.get(`${API_BASE}/bead-adjustments`);
    return res.data;
  },
  createBeadAdjustment: async (data: any) => {
    const res = await axios.post(`${API_BASE}/bead-adjustments`, data);
    return res.data;
  },
  updateBeadStatus: async (id: number, status: string, actor_name?: string) => {
    const res = await axios.patch(`${API_BASE}/bead-adjustments/${id}/status`, { status, actor_name });
    return res.data;
  },

  // Orders
  getOrders: async (params?: Record<string, any>) => {
    const res = await axios.get(`${API_BASE}/orders`, { params });
    return res.data;
  },
  getOrder: async (id: string | number) => {
    const res = await axios.get(`${API_BASE}/orders/${id}`);
    return res.data;
  },

  // Smart Accountant & Receivables
  getAccountantReport: async (period: string, start?: string, end?: string) => {
    const res = await axios.get(`${API_BASE}/accountant/report`, { params: { period, start, end } });
    return res.data;
  },
  getReceivables: async () => {
    const res = await axios.get(`${API_BASE}/receivables`);
    return res.data;
  },
  payReceivable: async (orderId: number, data: any) => {
    const res = await axios.post(`${API_BASE}/receivables/${orderId}/payment`, data);
    return res.data;
  },

  // Expenses
  getExpenses: async () => {
    const res = await axios.get(`${API_BASE}/expenses`);
    return res.data;
  },
  createExpense: async (data: any) => {
    const res = await axios.post(`${API_BASE}/expenses`, data);
    return res.data;
  },
  voidExpense: async (id: number, reason: string, actor_name?: string) => {
    const res = await axios.post(`${API_BASE}/expenses/${id}/void`, { reason, actor_name });
    return res.data;
  },

  // Ambassadors
  getAmbassadors: async () => {
    const res = await axios.get(`${API_BASE}/ambassadors`);
    return res.data;
  },
  createAmbassador: async (data: any) => {
    const res = await axios.post(`${API_BASE}/ambassadors`, data);
    return res.data;
  },

  // Settings & License
  getSettings: async () => {
    const res = await axios.get(`${API_BASE}/settings`);
    return res.data;
  },
  updateSettings: async (data: any) => {
    const res = await axios.put(`${API_BASE}/settings`, data);
    return res.data;
  },
  getLicenseStatus: async () => {
    const res = await axios.get(`${API_BASE}/license/status`);
    return res.data;
  },
  activateLicense: async (key: string) => {
    const res = await axios.post(`${API_BASE}/license/activate`, { key });
    return res.data;
  },

  // Users & Permissions Management
  getUsers: async (params?: { role?: string; include_customers?: boolean }) => {
    const res = await axios.get(`${API_BASE}/users`, { params });
    return res.data;
  },
  createUser: async (data: any) => {
    const res = await axios.post(`${API_BASE}/users`, data);
    return res.data;
  },
  updateUser: async (id: number, data: any) => {
    const res = await axios.put(`${API_BASE}/users/${id}`, data);
    return res.data;
  },
  deleteUser: async (id: number, actor_name?: string) => {
    const res = await axios.delete(`${API_BASE}/users/${id}`, { params: { actor_name } });
    return res.data;
  },

  // Audit Logs
  getAuditLogs: async () => {
    const res = await axios.get(`${API_BASE}/audit`);
    return res.data;
  }
};
