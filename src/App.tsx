import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { QuickSalePOSPage } from './pages/QuickSalePOSPage';
import { InventoryPage } from './pages/InventoryPage';
import { CustodyPage } from './pages/CustodyPage';
import { WorkshopPage } from './pages/WorkshopPage';
import { OrdersPage } from './pages/OrdersPage';
import { AccountantPage } from './pages/AccountantPage';
import { StorefrontPage } from './pages/StorefrontPage';
import { AmbassadorsPage } from './pages/AmbassadorsPage';
import { SettingsPage } from './pages/SettingsPage';
import { UsersPage } from './pages/UsersPage';
import { AdminLoginPage } from './pages/AdminLoginPage';
import { B2BWholesalePage } from './pages/B2BWholesalePage';
import { ProductDetailPage } from './pages/ProductDetailPage';

// Modals
import { ProductModal } from './components/ProductModal';
import { CustodyModal } from './components/CustodyModal';
import { BeadAdjustmentModal } from './components/BeadAdjustmentModal';
import { QuickSaleModal } from './components/QuickSaleModal';
import { InvoiceModal } from './components/InvoiceModal';
import { CustomerAuthModal } from './components/CustomerAuthModal';
import { CustomerOrdersModal } from './components/CustomerOrdersModal';
import { CheckoutModal } from './components/CheckoutModal';

import { Product, Order, Category, Material, User } from './types';
import { api, socket } from './lib/api';

export const App: React.FC = () => {
  // Determine initial portal: '/admin' vs '/wholesale' vs '/p/:id' vs Storefront '/'
  const getInitialPortal = (): 'storefront' | 'admin' | 'wholesale' | 'product' => {
    const path = window.location.pathname.toLowerCase();
    const search = window.location.search.toLowerCase();
    if (path.startsWith('/admin') || search.includes('portal=admin')) {
      return 'admin';
    }
    if (path.startsWith('/wholesale') || search.includes('portal=wholesale')) {
      return 'wholesale';
    }
    if (path.startsWith('/product/') || path.startsWith('/p/')) {
      return 'product';
    }
    return 'storefront';
  };

  const [portal, setPortal] = useState<'storefront' | 'admin' | 'wholesale' | 'product'>(getInitialPortal);
  const [currentTab, setCurrentTab] = useState('dashboard');

  // Single Product Viewing State
  const [viewingProduct, setViewingProduct] = useState<Product | null>(null);
  const [allStoreProducts, setAllStoreProducts] = useState<Product[]>([]);

  // Staff User Session
  const [staffUser, setStaffUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('haybat_staff_user');
      if (saved) {
        const u = JSON.parse(saved);
        if (u && u.role !== 'CUSTOMER') return u;
      }
    } catch (e) {
      console.error(e);
    }
    return null;
  });

  // Customer User Session
  const [customerUser, setCustomerUser] = useState<any | null>(() => {
    try {
      const saved = localStorage.getItem('haybat_customer_user');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return null;
  });

  // Global Categories & Materials
  const [categories, setCategories] = useState<Category[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);

  // Modals state
  const [productModalItem, setProductModalItem] = useState<{ open: boolean; item: Product | null }>({ open: false, item: null });
  const [custodyModalItem, setCustodyModalItem] = useState<{ open: boolean; item: Product | null }>({ open: false, item: null });
  const [beadModalItem, setBeadModalItem] = useState<{ open: boolean; item: Product | null }>({ open: false, item: null });
  const [quickSaleModalItem, setQuickSaleModalItem] = useState<{ open: boolean; item: Product | null }>({ open: false, item: null });
  const [invoiceModalItem, setInvoiceModalItem] = useState<{ open: boolean; order: Order | null }>({ open: false, order: null });

  // Storefront Modals
  const [isCustomerAuthOpen, setIsCustomerAuthOpen] = useState(false);
  const [isCustomerOrdersOpen, setIsCustomerOrdersOpen] = useState(false);
  const [checkoutProduct, setCheckoutProduct] = useState<Product | null>(null);
  const [cartItem, setCartItem] = useState<Product | null>(null);

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Helper: Resolve product by unpredictable UUID, SKU, Reference or ID
  const resolveProductFromPath = async (pathname: string, prods: Product[]) => {
    let token = '';
    const lower = pathname.toLowerCase();
    if (lower.startsWith('/p/')) {
      token = pathname.slice(3).split('/')[0]?.trim();
    } else if (lower.startsWith('/product/')) {
      token = pathname.slice(9).split('/')[0]?.trim();
    }
    if (!token) return;

    // First check in-memory catalog
    let found = prods.find((p: Product) =>
      p.public_id === token ||
      p.product_reference === token ||
      p.sku.toLowerCase() === token.toLowerCase() ||
      String(p.id) === token
    );

    // If not found in-memory, fetch directly from backend API
    if (!found) {
      try {
        found = await api.getProduct(token);
      } catch (e) {
        console.warn('Could not load product for token:', token);
      }
    }

    if (found) {
      setViewingProduct(found);
      setPortal('product');
    }
  };

  // Sync browser URL & Back/Forward button history
  useEffect(() => {
    const handlePopState = () => {
      const initPortal = getInitialPortal();
      setPortal(initPortal);
      if (initPortal === 'product') {
        resolveProductFromPath(window.location.pathname, allStoreProducts);
      } else {
        setViewingProduct(null);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [allStoreProducts]);

  const navigatePortal = (newPortal: 'storefront' | 'admin' | 'wholesale') => {
    setPortal(newPortal);
    setViewingProduct(null);
    let targetPath = '/';
    if (newPortal === 'admin') targetPath = '/admin';
    else if (newPortal === 'wholesale') targetPath = '/wholesale';

    if (window.location.pathname !== targetPath) {
      window.history.pushState({}, '', targetPath);
    }
  };

  const handleViewProduct = (prod: Product) => {
    setViewingProduct(prod);
    setPortal('product');
    // Unpredictable URL token: public_id (UUID)
    const targetPath = `/p/${prod.public_id || prod.id}`;
    if (window.location.pathname !== targetPath) {
      window.history.pushState({}, '', targetPath);
    }
  };

  useEffect(() => {
    loadBaseData();

    socket.on('product:created', () => setRefreshTrigger(n => n + 1));
    socket.on('product:updated', () => setRefreshTrigger(n => n + 1));
    socket.on('product:reserved', () => setRefreshTrigger(n => n + 1));
    socket.on('product:status_changed', () => setRefreshTrigger(n => n + 1));
    socket.on('order:created', () => setRefreshTrigger(n => n + 1));

    return () => {
      socket.off('product:created');
      socket.off('product:updated');
      socket.off('product:reserved');
      socket.off('product:status_changed');
      socket.off('order:created');
    };
  }, [refreshTrigger]);

  const loadBaseData = async () => {
    try {
      const [cats, mats, prods] = await Promise.all([
        api.getCategories(),
        api.getMaterials(),
        api.getProducts({ status: 'AVAILABLE' })
      ]);
      setCategories(cats);
      setMaterials(mats);
      setAllStoreProducts(prods || []);

      // If initial path is /p/:token or /product/:token, open that product
      const path = window.location.pathname;
      if (path.startsWith('/p/') || path.startsWith('/product/')) {
        resolveProductFromPath(path, prods || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRefresh = () => {
    setRefreshTrigger(n => n + 1);
  };

  const handleStaffLogout = () => {
    if (confirm('هل ترغب بتسجيل الخروج من لوحة الإدارة؟')) {
      localStorage.removeItem('haybat_staff_token');
      localStorage.removeItem('haybat_staff_user');
      setStaffUser(null);
    }
  };

  const handleCustomerLogout = () => {
    localStorage.removeItem('haybat_customer_token');
    localStorage.removeItem('haybat_customer_user');
    setCustomerUser(null);
  };

  // -------------------------------------------------------------
  // 1. ADMIN PORTAL ROUTE (/admin)
  // -------------------------------------------------------------
  if (portal === 'admin') {
    // If not authenticated as staff, show the dedicated Admin Login Page
    if (!staffUser) {
      return (
        <AdminLoginPage
          onSuccess={(loggedUser) => setStaffUser(loggedUser)}
          onBackToStore={() => navigatePortal('storefront')}
        />
      );
    }

    // Authenticated Staff Dashboard View
    return (
      <div className="flex h-screen bg-[#FAF7F2] text-[#26221C] overflow-hidden font-sans" dir="rtl">
        {/* Staff Sidebar Navigation */}
        <Sidebar
          currentTab={currentTab}
          setCurrentTab={setCurrentTab}
          currentUser={staffUser}
        />

        {/* Main App Content Viewport */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header
            portalMode="admin"
            currentTab={currentTab}
            setCurrentTab={setCurrentTab}
            onRefresh={handleRefresh}
            staffUser={staffUser}
            onStaffLogout={handleStaffLogout}
            onNavigatePortal={navigatePortal}
          />

          <main className="flex-1 overflow-y-auto">
            {currentTab === 'dashboard' && (
              <DashboardPage
                key={refreshTrigger}
                onNavigate={setCurrentTab}
                onOpenQuickSale={(p) => setQuickSaleModalItem({ open: true, item: p })}
                currentUser={staffUser}
              />
            )}

            {currentTab === 'pos' && (
              <QuickSalePOSPage
                key={refreshTrigger}
                userName={staffUser.full_name}
                currentUser={staffUser}
                onSaleComplete={(ord) => setInvoiceModalItem({ open: true, order: ord })}
              />
            )}

            {currentTab === 'inventory' && (
              <InventoryPage
                key={refreshTrigger}
                currentUser={staffUser}
                onOpenProductModal={(p) => setProductModalItem({ open: true, item: p })}
                onOpenCustodyModal={(p) => setCustodyModalItem({ open: true, item: p })}
                onOpenBeadModal={(p) => setBeadModalItem({ open: true, item: p })}
                onOpenQuickSaleModal={(p) => setQuickSaleModalItem({ open: true, item: p })}
              />
            )}

            {currentTab === 'custody' && (
              <CustodyPage
                key={refreshTrigger}
                onOpenCustodyModal={(p) => setCustodyModalItem({ open: true, item: p })}
              />
            )}

            {currentTab === 'workshop' && (
              <WorkshopPage key={refreshTrigger} />
            )}

            {currentTab === 'orders' && (
              <OrdersPage
                key={refreshTrigger}
                onViewInvoice={(ord) => setInvoiceModalItem({ open: true, order: ord })}
              />
            )}

            {currentTab === 'accountant' && (
              <AccountantPage key={refreshTrigger} />
            )}

            {currentTab === 'ambassadors' && (
              <AmbassadorsPage key={refreshTrigger} />
            )}

            {currentTab === 'users' && (
              <UsersPage key={refreshTrigger} currentUser={staffUser} />
            )}

            {currentTab === 'storefront' && (
              <StorefrontPage
                key={refreshTrigger}
                onOpenCheckout={(p) => setCheckoutProduct(p)}
                onOpenCustomerAuth={() => setIsCustomerAuthOpen(true)}
                onOpenCustomerOrders={() => setIsCustomerOrdersOpen(true)}
                customerUser={customerUser}
                cartItem={cartItem}
                setCartItem={setCartItem}
              />
            )}

            {currentTab === 'settings' && (
              <SettingsPage key={refreshTrigger} />
            )}
          </main>
        </div>

        {/* Global Staff Modals */}
        {productModalItem.open && (
          <ProductModal
            product={productModalItem.item}
            categories={categories}
            materials={materials}
            userName={staffUser.full_name}
            onClose={() => setProductModalItem({ open: false, item: null })}
            onSuccess={() => {
              setProductModalItem({ open: false, item: null });
              setRefreshTrigger(n => n + 1);
            }}
          />
        )}

        {custodyModalItem.open && custodyModalItem.item && (
          <CustodyModal
            product={custodyModalItem.item}
            userName={staffUser.full_name}
            onClose={() => setCustodyModalItem({ open: false, item: null })}
            onSuccess={() => setRefreshTrigger(n => n + 1)}
          />
        )}

        {beadModalItem.open && beadModalItem.item && (
          <BeadAdjustmentModal
            product={beadModalItem.item}
            userName={staffUser.full_name}
            onClose={() => setBeadModalItem({ open: false, item: null })}
            onSuccess={() => setRefreshTrigger(n => n + 1)}
          />
        )}

        {quickSaleModalItem.open && quickSaleModalItem.item && (
          <QuickSaleModal
            product={quickSaleModalItem.item}
            userName={staffUser.full_name}
            onClose={() => setQuickSaleModalItem({ open: false, item: null })}
            onSuccess={(ord) => {
              setQuickSaleModalItem({ open: false, item: null });
              setInvoiceModalItem({ open: true, order: ord });
              setRefreshTrigger(n => n + 1);
            }}
          />
        )}

        {invoiceModalItem.open && invoiceModalItem.order && (
          <InvoiceModal
            order={invoiceModalItem.order}
            onClose={() => setInvoiceModalItem({ open: false, order: null })}
          />
        )}
      </div>
    );
  }

  // -------------------------------------------------------------
  // 2. B2B WHOLESALE PRIVATE PORTAL (/wholesale)
  // -------------------------------------------------------------
  if (portal === 'wholesale') {
    return (
      <div className="min-h-screen bg-[#FAF7F2] text-[#26221C] flex flex-col font-sans" dir="rtl">
        <Header
          portalMode="wholesale"
          customerUser={customerUser}
          onOpenCustomerOrders={() => setIsCustomerOrdersOpen(true)}
          onCustomerLogout={handleCustomerLogout}
          onNavigatePortal={navigatePortal}
        />

        <main className="flex-1">
          <B2BWholesalePage
            currentUser={customerUser}
            onUserLoginSuccess={(u) => setCustomerUser(u)}
            onNavigateHome={() => navigatePortal('storefront')}
          />
        </main>

        <CustomerOrdersModal
          isOpen={isCustomerOrdersOpen}
          onClose={() => setIsCustomerOrdersOpen(false)}
          customerUser={customerUser}
          onViewInvoice={(ord) => setInvoiceModalItem({ open: true, order: ord })}
          onLogoutCustomer={handleCustomerLogout}
        />

        {invoiceModalItem.open && invoiceModalItem.order && (
          <InvoiceModal
            order={invoiceModalItem.order}
            onClose={() => setInvoiceModalItem({ open: false, order: null })}
          />
        )}
      </div>
    );
  }

  // -------------------------------------------------------------
  // 3. PUBLIC STOREFRONT PORTAL (/)
  // -------------------------------------------------------------
  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#26221C] flex flex-col font-sans" dir="rtl">
      {/* Storefront Header */}
      <Header
        portalMode="storefront"
        customerUser={customerUser}
        cartCount={cartItem ? 1 : 0}
        onOpenCustomerAuth={() => setIsCustomerAuthOpen(true)}
        onOpenCustomerOrders={() => setIsCustomerOrdersOpen(true)}
        onOpenCheckout={() => {
          if (cartItem) {
            setCheckoutProduct(cartItem);
          } else {
            const el = document.getElementById('products-section');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }
        }}
        onCustomerLogout={handleCustomerLogout}
        onNavigatePortal={navigatePortal}
      />

      {/* Main Storefront Body / Dedicated Product Detail Page */}
      <main className="flex-1">
        {portal === 'product' && viewingProduct ? (
          <ProductDetailPage
            key={viewingProduct.id}
            product={viewingProduct}
            allProducts={allStoreProducts}
            onBackToStore={() => navigatePortal('storefront')}
            currentUser={staffUser || customerUser}
          />
        ) : (
          <StorefrontPage
            key={refreshTrigger}
            onOpenCheckout={(product) => setCheckoutProduct(product)}
            onOpenCustomerAuth={() => setIsCustomerAuthOpen(true)}
            onOpenCustomerOrders={() => setIsCustomerOrdersOpen(true)}
            onViewProduct={(product) => handleViewProduct(product)}
            customerUser={customerUser}
            cartItem={cartItem}
            setCartItem={setCartItem}
          />
        )}
      </main>

      {/* Customer Modals */}
      <CustomerAuthModal
        isOpen={isCustomerAuthOpen}
        onClose={() => setIsCustomerAuthOpen(false)}
        onSuccess={(u) => setCustomerUser(u)}
      />

      <CustomerOrdersModal
        isOpen={isCustomerOrdersOpen}
        onClose={() => setIsCustomerOrdersOpen(false)}
        customerUser={customerUser}
        onViewInvoice={(ord) => setInvoiceModalItem({ open: true, order: ord })}
        onLogoutCustomer={handleCustomerLogout}
      />

      <CheckoutModal
        product={checkoutProduct}
        customerUser={customerUser}
        onClose={() => setCheckoutProduct(null)}
        onSuccess={(ord) => {
          setCheckoutProduct(null);
          setCartItem(null);
          setInvoiceModalItem({ open: true, order: ord });
          setRefreshTrigger(n => n + 1);
        }}
      />

      {/* Invoice Viewer Modal */}
      {invoiceModalItem.open && invoiceModalItem.order && (
        <InvoiceModal
          order={invoiceModalItem.order}
          onClose={() => setInvoiceModalItem({ open: false, order: null })}
        />
      )}
    </div>
  );
};
