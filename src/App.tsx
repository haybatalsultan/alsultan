import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { StorefrontPage } from './pages/StorefrontPage';
import { ProductDetailPage } from './pages/ProductDetailPage';

// Code Splitting & Lazy-loading for Admin ERP & B2B Portals
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const QuickSalePOSPage = lazy(() => import('./pages/QuickSalePOSPage').then(m => ({ default: m.QuickSalePOSPage })));
const InventoryPage = lazy(() => import('./pages/InventoryPage').then(m => ({ default: m.InventoryPage })));
const CustodyPage = lazy(() => import('./pages/CustodyPage').then(m => ({ default: m.CustodyPage })));
const WorkshopPage = lazy(() => import('./pages/WorkshopPage').then(m => ({ default: m.WorkshopPage })));
const OrdersPage = lazy(() => import('./pages/OrdersPage').then(m => ({ default: m.OrdersPage })));
const AccountantPage = lazy(() => import('./pages/AccountantPage').then(m => ({ default: m.AccountantPage })));
const AmbassadorsPage = lazy(() => import('./pages/AmbassadorsPage').then(m => ({ default: m.AmbassadorsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const UsersPage = lazy(() => import('./pages/UsersPage').then(m => ({ default: m.UsersPage })));
const AdminLoginPage = lazy(() => import('./pages/AdminLoginPage').then(m => ({ default: m.AdminLoginPage })));
const B2BWholesalePage = lazy(() => import('./pages/B2BWholesalePage').then(m => ({ default: m.B2BWholesalePage })));

// Modals
import { ProductModal } from './components/ProductModal';
import { CustodyModal } from './components/CustodyModal';
import { BeadAdjustmentModal } from './components/BeadAdjustmentModal';
import { QuickSaleModal } from './components/QuickSaleModal';
import { InvoiceModal } from './components/InvoiceModal';
import { CustomerAuthModal } from './components/CustomerAuthModal';
import { CustomerOrdersModal } from './components/CustomerOrdersModal';
import { CheckoutModal } from './components/CheckoutModal';
import { RoyalNotifications } from './components/RoyalNotifications';
import { toast } from './utils/toast';
import { Clock, ShoppingBag, MessageCircle, X } from 'lucide-react';

import { Product, Order, Category, Material, User } from './types';
import { api, socket } from './lib/api';

const LazyLoadingSpinner = () => (
  <div className="min-h-[300px] flex items-center justify-center p-8 text-[#9A6817]">
    <div className="w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin" />
  </div>
);

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
  const [pendingReserveProduct, setPendingReserveProduct] = useState<Product | null>(null);
  const [storefrontFilterCategory, setStorefrontFilterCategory] = useState<string>('all');

  // Cart & 15-Minute Reservation State (Persisted across pages and navigation)
  const [cartItem, setCartItem] = useState<Product | null>(() => {
    try {
      const savedExpiry = localStorage.getItem('haybat_reservation_expiry');
      const savedItem = localStorage.getItem('haybat_reserved_item');
      if (savedExpiry && savedItem) {
        const remaining = Math.floor((Number(savedExpiry) - Date.now()) / 1000);
        if (remaining > 0) {
          return JSON.parse(savedItem);
        }
      }
    } catch {}
    return null;
  });

  const [reservationRemaining, setReservationRemaining] = useState<number>(() => {
    try {
      const savedExpiry = localStorage.getItem('haybat_reservation_expiry');
      if (savedExpiry) {
        const remaining = Math.floor((Number(savedExpiry) - Date.now()) / 1000);
        if (remaining > 0) return remaining;
      }
    } catch {}
    return 0;
  });

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Global 15-Minute Reservation Countdown Timer
  useEffect(() => {
    let interval: any = null;
    if (cartItem && reservationRemaining > 0) {
      interval = setInterval(() => {
        setReservationRemaining((prev) => {
          if (prev <= 1) {
            // Reservation expired after 15 minutes!
            if (cartItem?.id) {
              api.unreserveProduct(cartItem.id).catch(() => {});
            }
            localStorage.removeItem('haybat_reservation_expiry');
            localStorage.removeItem('haybat_reserved_item');
            setCartItem(null);
            toast.warning(
              'انتهت مهلة حجز المسبحة (15 دقيقة) وتمت إعادتها للمخزون العام حمايةً للحصرية ومنعاً للاحتكار.',
              'انتهاء مهلة الحجز'
            );
            setRefreshTrigger((n) => n + 1);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [cartItem, reservationRemaining]);

  const handleReserveProduct = async (product: Product, durationMinutes = 15, userOverride?: any) => {
    const userToUse = userOverride || customerUser;
    if (!userToUse) {
      setPendingReserveProduct(product);
      setIsCustomerAuthOpen(true);
      toast.warning(
        'لحجز هذه القطعة الحصرية وتوثيق مهلة الـ 15 دقيقة حصرياً باسمك، يجب تسجيل الدخول أو إنشاء حساب أولاً.',
        'تسجيل الدخول مطلوب للحجز'
      );
      return;
    }

    try {
      const userIdentifier = userToUse.phone || userToUse.username || `user_${userToUse.id}`;
      await api.reserveProduct(product.id, userIdentifier, durationMinutes);
      const totalSeconds = durationMinutes * 60;
      const expiry = Date.now() + totalSeconds * 1000;
      localStorage.setItem('haybat_reservation_expiry', String(expiry));
      localStorage.setItem('haybat_reserved_item', JSON.stringify(product));
      setCartItem(product);
      setReservationRemaining(totalSeconds);
      toast.success(
        `تم توثيق حجز المسبحة (${product.name_ar}) باسمك (${userToUse.full_name || userToUse.username}) لمدة 15 دقيقة حصرياً! لن يتمكن أي عميل أو معرض آخر من شرائها.`,
        'حجز مسبحة حصرية'
      );
      setRefreshTrigger((n) => n + 1);
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر حجز المسبحة');
    }
  };

  const handleCancelReservation = async () => {
    if (!cartItem) return;
    const confirmed = await toast.confirm({
      title: 'إلغاء حجز المسبحة',
      message: `هل ترغب بإلغاء حجز (${cartItem.name_ar}) وإتاحتها فوراً لعملاء وزوار المتجر الآخرين؟`,
      confirmText: 'نعم، إلغاء الحجز',
      cancelText: 'تراجع',
      type: 'warning'
    });
    if (!confirmed) return;

    try {
      await api.unreserveProduct(cartItem.id);
    } catch {}
    localStorage.removeItem('haybat_reservation_expiry');
    localStorage.removeItem('haybat_reserved_item');
    setCartItem(null);
    setReservationRemaining(0);
    toast.info('تم إلغاء الحجز بنجاح وأصبحت القطعة متاحة للجميع');
    setRefreshTrigger((n) => n + 1);
  };

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

  const handleSelectStorefrontMenuItem = (itemId: string) => {
    // 1. If currently viewing a product detail page or other portal, switch to storefront immediately!
    if (portal !== 'storefront') {
      navigatePortal('storefront');
    }

    // 2. Set the category filter and scroll appropriately
    if (itemId === 'home') {
      setStorefrontFilterCategory('all');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (itemId === 'rare') {
      setStorefrontFilterCategory('rare');
      setTimeout(() => {
        const el = document.getElementById('products-section') || document.getElementById('products');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 120);
    } else if (itemId === 'rosaries') {
      setStorefrontFilterCategory('all');
      setTimeout(() => {
        const el = document.getElementById('products-section') || document.getElementById('products');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 120);
    } else if (itemId === 'gemstones') {
      setStorefrontFilterCategory('gemstones');
      setTimeout(() => {
        const el = document.getElementById('products-section') || document.getElementById('products');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 120);
    } else if (itemId === 'gifts') {
      setStorefrontFilterCategory('gifts');
      setTimeout(() => {
        const el = document.getElementById('products-section') || document.getElementById('products');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 120);
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

  const handleStaffLogout = async () => {
    const confirmed = await toast.confirm({
      title: 'تسجيل الخروج',
      message: 'هل ترغب بتسجيل الخروج من لوحة الإدارة؟',
      confirmText: 'تسجيل الخروج',
      cancelText: 'إلغاء',
      type: 'warning'
    });
    if (confirmed) {
      localStorage.removeItem('haybat_staff_token');
      localStorage.removeItem('haybat_staff_user');
      setStaffUser(null);
      toast.info('تم تسجيل الخروج بنجاح');
    }
  };

  const handleCustomerLogout = () => {
    localStorage.removeItem('haybat_customer_token');
    localStorage.removeItem('haybat_customer_user');
    setCustomerUser(null);
    if (cartItem?.id) {
      api.unreserveProduct(cartItem.id).catch(() => {});
      localStorage.removeItem('haybat_reservation_expiry');
      localStorage.removeItem('haybat_reserved_item');
      setCartItem(null);
      setReservationRemaining(0);
    }
  };

  // -------------------------------------------------------------
  // 1. ADMIN PORTAL ROUTE (/admin)
  // -------------------------------------------------------------
  if (portal === 'admin') {
    // If not authenticated as staff, show the dedicated Admin Login Page
    if (!staffUser) {
      return (
        <Suspense fallback={<LazyLoadingSpinner />}>
          <AdminLoginPage
            onSuccess={(loggedUser) => setStaffUser(loggedUser)}
            onBackToStore={() => navigatePortal('storefront')}
          />
        </Suspense>
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
            <Suspense fallback={<LazyLoadingSpinner />}>
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
                onViewProduct={(p) => handleViewProduct(p)}
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
                onViewProduct={(p) => handleViewProduct(p)}
                customerUser={customerUser}
                cartItem={cartItem}
                setCartItem={setCartItem}
              />
            )}

            {currentTab === 'settings' && (
              <SettingsPage key={refreshTrigger} />
            )}
            </Suspense>
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
          <Suspense fallback={<LazyLoadingSpinner />}>
            <B2BWholesalePage
              currentUser={customerUser}
              onUserLoginSuccess={(u) => setCustomerUser(u)}
              onNavigateHome={() => navigatePortal('storefront')}
            />
          </Suspense>
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
        onSelectMenuItem={handleSelectStorefrontMenuItem}
        activeMenuItem={storefrontFilterCategory}
      />

      {/* Global 15-Minute Reservation Countdown Bar */}
      {cartItem && reservationRemaining > 0 && (
        <div className="sticky top-0 z-40 bg-gradient-to-r from-[#17140F] via-[#26221C] to-[#17140F] text-white px-4 py-3 shadow-2xl border-b-2 border-[#C9972B] animate-in slide-in-from-top-4 duration-300">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#C9972B]/20 border border-[#C9972B]/50 flex items-center justify-center shrink-0">
                <Clock className="w-5 h-5 text-[#E2B84B] animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-extrabold text-[#F8F4EB]">
                    القطعة محجوزة حصرياً باسمك لمدة 15 دقيقة:
                  </span>
                  <span className="text-[#E2B84B] font-bold">
                    {cartItem.name_ar}
                  </span>
                  <span className="text-[11px] font-mono bg-white/10 px-2 py-0.5 rounded border border-white/15">
                    #{cartItem.sku}
                  </span>
                </div>
                <p className="text-[11px] text-[#C8BCAB] mt-0.5">
                  لن يتمكن أي عميل أو معرض آخر من حجزها أو شرائها حتى انتهاء المهلة وتصبح حرة.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 w-full md:w-auto justify-between md:justify-end">
              {/* Live Countdown Badge */}
              <div className="flex items-center gap-1.5 bg-[#0E0D0B] border border-[#C9972B]/60 px-3.5 py-1.5 rounded-xl shadow-inner">
                <span className="text-[11px] text-[#A69B8D]">الوقت المتبقي:</span>
                <span className="text-base font-black font-mono text-[#E2B84B] tracking-wider min-w-[50px] text-center">
                  {Math.floor(reservationRemaining / 60)}:
                  {String(reservationRemaining % 60).padStart(2, '0')}
                </span>
                <span className="text-[10px] text-[#A69B8D]">دقيقة</span>
              </div>

              {/* Checkout Button */}
              <button
                type="button"
                onClick={() => setCheckoutProduct(cartItem)}
                className="px-4 py-2 bg-gradient-to-r from-[#9A6817] via-[#C9972B] to-[#E2B84B] hover:brightness-110 text-[#12100D] font-black rounded-xl text-xs transition shadow-md flex items-center gap-1.5 active:scale-95 cursor-pointer"
              >
                <ShoppingBag className="w-4 h-4 text-[#12100D]" />
                <span>إتمام الاقتناء</span>
              </button>

              {/* Cancel Reservation Button */}
              <button
                type="button"
                onClick={handleCancelReservation}
                className="px-3 py-2 bg-white/10 hover:bg-rose-950/40 hover:border-rose-400/50 text-[#C8BCAB] hover:text-rose-300 border border-white/15 rounded-xl text-xs font-semibold transition cursor-pointer"
                title="إلغاء الحجز وإتاحة القطعة فوراً للآخرين"
              >
                إلغاء الحجز
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Storefront Body / Dedicated Product Detail Page */}
      <main className="flex-1">
        {portal === 'product' && viewingProduct ? (
          <ProductDetailPage
            key={viewingProduct.id}
            product={viewingProduct}
            allProducts={allStoreProducts}
            onBackToStore={() => handleSelectStorefrontMenuItem('home')}
            onNavigateHome={() => handleSelectStorefrontMenuItem('home')}
            onNavigateRare={() => handleSelectStorefrontMenuItem('rare')}
            currentUser={staffUser || customerUser}
            onOpenCheckout={(product) => setCheckoutProduct(product)}
            onReserveProduct={handleReserveProduct}
            cartItem={cartItem}
            reservationRemaining={reservationRemaining}
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
            reservationRemaining={reservationRemaining}
            onReserveProduct={handleReserveProduct}
            activeCategoryFilter={storefrontFilterCategory}
            onCategoryFilterChange={setStorefrontFilterCategory}
          />
        )}
      </main>

      {/* Customer Modals */}
      <CustomerAuthModal
        isOpen={isCustomerAuthOpen}
        onClose={() => {
          setIsCustomerAuthOpen(false);
          setPendingReserveProduct(null);
        }}
        onSuccess={(u) => {
          setCustomerUser(u);
          if (pendingReserveProduct) {
            const prod = pendingReserveProduct;
            setPendingReserveProduct(null);
            handleReserveProduct(prod, 15, u);
          }
        }}
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
          localStorage.removeItem('haybat_reservation_expiry');
          localStorage.removeItem('haybat_reserved_item');
          setCheckoutProduct(null);
          setCartItem(null);
          setReservationRemaining(0);
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

      {/* Royal Toast & Confirm Notifications */}
      <RoyalNotifications />
    </div>
  );
};
