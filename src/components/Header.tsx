import React, { useState, useEffect } from 'react';
import {
  Search,
  User as UserIcon,
  Heart,
  ShoppingBag,
  Globe,
  Truck,
  Sparkles,
  Gift,
  RefreshCw,
  LogOut,
  ShieldCheck,
  ExternalLink,
  ChevronDown,
  Building2,
  ArrowRight
} from 'lucide-react';
import { socket } from '../lib/api';

interface HeaderProps {
  portalMode: 'storefront' | 'admin' | 'wholesale';
  currentTab?: string;
  setCurrentTab?: (tab: string) => void;
  onRefresh?: () => void;
  staffUser?: any;
  customerUser?: any;
  onStaffLogout?: () => void;
  onCustomerLogout?: () => void;
  onOpenCustomerAuth?: () => void;
  onOpenCustomerOrders?: () => void;
  onOpenCheckout?: () => void;
  onNavigatePortal: (portal: 'storefront' | 'admin' | 'wholesale') => void;
  cartCount?: number;
  onSelectMenuItem?: (itemId: string) => void;
  activeMenuItem?: string;
}

export const Header: React.FC<HeaderProps> = ({
  portalMode,
  currentTab = 'storefront',
  setCurrentTab,
  onRefresh,
  staffUser,
  customerUser,
  onStaffLogout,
  onCustomerLogout,
  onOpenCustomerAuth,
  onOpenCustomerOrders,
  onOpenCheckout,
  onNavigatePortal,
  cartCount = 0,
  onSelectMenuItem,
  activeMenuItem = 'all'
}) => {
  const [isSocketConnected, setIsSocketConnected] = useState(socket.connected);
  const [customerMenuOpen, setCustomerMenuOpen] = useState(false);

  useEffect(() => {
    function onConnect() { setIsSocketConnected(true); }
    function onDisconnect() { setIsSocketConnected(false); }
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, []);

  const storefrontMenuItems = [
    { id: 'home', label: 'الرئيسية', icon: '🏠', targetSection: 'hero' },
    { id: 'rosaries', label: 'المسابيح', icon: '📿', targetSection: 'products' },
    { id: 'rare', label: 'النوادر', icon: '🏺', targetSection: 'products' },
    { id: 'gemstones', label: 'الأحجار الكريمة', icon: '💎', targetSection: 'products' },
    { id: 'gifts', label: 'الهدايا', icon: '🎁', targetSection: 'products' },
    { id: 'b2b', label: 'مبيعات الجملة B2B', icon: '🏛️', action: () => onNavigatePortal('wholesale') },
    { id: 'contact', label: 'تواصل معنا', icon: '📞', action: () => window.open('https://wa.me/971504084006', '_blank') },
  ];

  const handleMenuItemClick = (item: typeof storefrontMenuItems[0]) => {
    if (item.action) {
      item.action();
      return;
    }

    if (onSelectMenuItem) {
      onSelectMenuItem(item.id);
      return;
    }

    // Fallback: Return to storefront and scroll
    onNavigatePortal('storefront');
    if (item.id === 'home') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setTimeout(() => {
        const el = document.getElementById(item.targetSection || 'products-section') || document.getElementById('products');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#EBE3D5] shadow-[0_2px_15px_rgba(70,45,15,0.04)] selection:bg-[#C9972B]/20">
      {/* Top Language & Currency Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-1 flex items-center justify-between text-[11px] text-[#746A5D] border-b border-[#F5EFE6]">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-semibold text-[#4B4338]">
            <Globe className="w-3.5 h-3.5 text-[#C9972B]" />
            <span>العربية</span>
          </span>
          <span className="text-[#D8D0C4]">|</span>
          <span className="font-mono text-[#4B4338]">AED</span>

          {/* Quick switch between Retail & Wholesale Portal */}
          {portalMode === 'storefront' && (
            <>
              <span className="text-[#D8D0C4]">|</span>
              <button
                onClick={() => onNavigatePortal('wholesale')}
                className="flex items-center gap-1 font-bold text-[#9A6817] hover:text-[#C9972B] hover:underline cursor-pointer"
              >
                <Building2 className="w-3.5 h-3.5 text-[#C9972B]" />
                <span>بوابة تجار الجملة (B2B)</span>
              </button>
            </>
          )}

          {portalMode === 'wholesale' && (
            <>
              <span className="text-[#D8D0C4]">|</span>
              <button
                onClick={() => onNavigatePortal('storefront')}
                className="flex items-center gap-1 font-bold text-[#26221C] hover:text-[#9A6817] hover:underline cursor-pointer"
              >
                <ArrowRight className="w-3.5 h-3.5 text-[#C9972B]" />
                <span>العودة لمتجر التجزئة (قطاعي)</span>
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isSocketConnected ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            <span className="text-[10px] text-[#746A5D]">
              {isSocketConnected ? 'المخزون متزامن لحظياً' : 'وضع عدم الاتصال'}
            </span>
          </span>

          {portalMode === 'admin' && onRefresh && (
            <button
              onClick={onRefresh}
              title="تحديث البيانات"
              className="p-1 hover:text-[#C9972B] transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Quick link to Storefront when inside Admin */}
          {portalMode === 'admin' && (
            <button
              onClick={() => onNavigatePortal('storefront')}
              className="flex items-center gap-1 text-[11px] font-bold text-[#9A6817] hover:underline cursor-pointer"
            >
              <span>معاينة المتجر الخارجي</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* 3. Main Header Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2.5 flex items-center justify-between gap-4">
        {/* Right: Golden Logo */}
        <div
          onClick={() => {
            if (portalMode === 'admin' && setCurrentTab) {
              setCurrentTab('dashboard');
            } else {
              onNavigatePortal('storefront');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }
          }}
          className="cursor-pointer flex items-center shrink-0"
        >
          <img
            src="/branding/logo-header.png"
            alt="هيبة السلطان - HAYBAT ALSULTAN"
            width={200}
            height={64}
            decoding="async"
            className="h-12 sm:h-16 w-auto object-contain hover:opacity-95 transition"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>

        {/* Center: Nav Links based on portal */}
        {portalMode === 'storefront' ? (
          <nav className="hidden lg:flex items-center gap-3 text-[13px] font-semibold text-[#3D352E]">
            {storefrontMenuItems.map((item) => {
              const isActive = activeMenuItem === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleMenuItemClick(item)}
                  className={`flex items-center gap-1.5 py-1.5 px-3 rounded-full transition group cursor-pointer ${
                    isActive
                      ? 'bg-[#26221C] text-[#E2B84B] shadow-xs font-bold'
                      : item.id === 'b2b'
                      ? 'text-[#9A6817] bg-[#FAF4E8] hover:bg-[#F3E7CE] border border-[#E4D5B8] font-bold'
                      : 'text-[#4B4338] hover:text-[#C9972B] hover:bg-[#FBF8F2]'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full text-[11px] flex items-center justify-center border transition ${
                    isActive
                      ? 'bg-[#1C1814] border-[#E2B84B]/40'
                      : 'bg-[#F4EEE3] border-[#EADBCE] group-hover:border-[#C9972B]'
                  }`}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        ) : portalMode === 'wholesale' ? (
          <div className="hidden md:flex items-center gap-2 text-xs font-bold text-[#9A6817] bg-[#FAF4E8] px-4 py-2 rounded-2xl border border-[#E4D5B8]">
            <Building2 className="w-4 h-4 text-[#C9972B]" />
            <span>بوابة التوريد والشراء بالجملة لكبار التجار (B2B Private Portal)</span>
          </div>
        ) : (
          <div className="hidden md:flex items-center gap-2 text-xs font-bold text-[#8C8275] bg-[#F7EFE3] px-3 py-1.5 rounded-xl border border-[#EADBCE]">
            <ShieldCheck className="w-4 h-4 text-[#C9972B]" />
            <span>لوحة الإدارة المركزية — هيبة السلطان</span>
          </div>
        )}

        {/* Left: Customer/Admin Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {portalMode !== 'admin' ? (
            <>
              {portalMode === 'storefront' && (
                <button
                  onClick={() => {
                    const el = document.getElementById('products');
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="w-9 h-9 rounded-full hover:bg-[#F4EEE3] text-[#2B241B] hover:text-[#C9972B] flex items-center justify-center transition border border-transparent hover:border-[#EADBCE]"
                  title="البحث في المسابيح"
                >
                  <Search className="w-4 h-4" />
                </button>
              )}

              {/* Customer / Merchant Account Button */}
              <div className="relative">
                {customerUser ? (
                  <div>
                    <button
                      onClick={() => setCustomerMenuOpen(!customerMenuOpen)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#FAF4E8] text-[#9A6817] hover:bg-[#F3E7CE] border border-[#E4D5B8] transition text-xs font-bold"
                    >
                      <UserIcon className="w-3.5 h-3.5" />
                      <span className="max-w-[120px] truncate">
                        {customerUser.company_name || customerUser.full_name || 'حسابي'}
                      </span>
                      <ChevronDown className="w-3 h-3" />
                    </button>

                    {customerMenuOpen && (
                      <div className="absolute left-0 mt-2 w-52 bg-white border border-[#EBE3D5] rounded-2xl shadow-xl py-2 z-50 animate-in fade-in zoom-in-95">
                        <div className="px-4 py-2 border-b border-[#F5EFE6]">
                          {customerUser.company_name && (
                            <p className="text-[10px] text-[#9A6817] font-bold">🏛️ {customerUser.company_name}</p>
                          )}
                          <p className="text-xs font-bold text-[#26221C] truncate">{customerUser.full_name}</p>
                          <p className="text-[10px] text-[#8C8275] truncate">{customerUser.phone || customerUser.email}</p>
                        </div>

                        {portalMode === 'storefront' ? (
                          <button
                            onClick={() => {
                              setCustomerMenuOpen(false);
                              onNavigatePortal('wholesale');
                            }}
                            className="w-full text-right px-4 py-2 text-xs font-medium text-[#9A6817] hover:bg-[#FAF4E8] flex items-center gap-2"
                          >
                            <Building2 className="w-3.5 h-3.5" />
                            <span>بوابة طلبات الجملة</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              setCustomerMenuOpen(false);
                              onNavigatePortal('storefront');
                            }}
                            className="w-full text-right px-4 py-2 text-xs font-medium text-[#4B4338] hover:bg-[#FAF4E8] flex items-center gap-2"
                          >
                            <ShoppingBag className="w-3.5 h-3.5" />
                            <span>المتجر الخارجي (قطاعي)</span>
                          </button>
                        )}

                        <button
                          onClick={() => {
                            setCustomerMenuOpen(false);
                            if (onOpenCustomerOrders) onOpenCustomerOrders();
                          }}
                          className="w-full text-right px-4 py-2 text-xs font-medium text-[#4B4338] hover:bg-[#FAF4E8] flex items-center gap-2"
                        >
                          <ShoppingBag className="w-3.5 h-3.5" />
                          <span>سجل الطلبات والمشتريات</span>
                        </button>

                        <button
                          onClick={() => {
                            setCustomerMenuOpen(false);
                            if (onCustomerLogout) onCustomerLogout();
                          }}
                          className="w-full text-right px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 flex items-center gap-2 border-t border-[#F5EFE6]"
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          <span>تسجيل الخروج</span>
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={onOpenCustomerAuth}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full hover:bg-[#F4EEE3] text-[#2B241B] hover:text-[#C9972B] border border-[#EADBCE] transition text-xs font-bold"
                    title="تسجيل الدخول / حساب عميل"
                  >
                    <UserIcon className="w-3.5 h-3.5" />
                    <span>دخول / حساب</span>
                  </button>
                )}
              </div>

              {portalMode === 'storefront' && (
                <>
                  <button
                    onClick={() => {
                      const el = document.getElementById('products');
                      if (el) el.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="w-9 h-9 rounded-full hover:bg-[#F4EEE3] text-[#2B241B] hover:text-[#C9972B] flex items-center justify-center transition border border-transparent hover:border-[#EADBCE]"
                    title="المفضلة"
                  >
                    <Heart className="w-4 h-4" />
                  </button>

                  <button
                    onClick={onOpenCheckout}
                    className="w-9 h-9 rounded-full bg-[#FAF4E8] text-[#9A6817] hover:bg-[#C9972B] hover:text-white flex items-center justify-center transition border border-[#EADBCE] relative"
                    title="سلة التسوق"
                  >
                    <ShoppingBag className="w-4 h-4" />
                    {cartCount > 0 && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#C9972B] text-white text-[10px] font-bold flex items-center justify-center border border-white">
                        {cartCount}
                      </span>
                    )}
                  </button>
                </>
              )}
            </>
          ) : (
            /* Staff/Admin User Profile Info & Logout */
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-xs font-bold text-[#26221C] leading-tight">{staffUser?.full_name || 'الموظف'}</p>
                <span className="text-[10px] bg-[#FAF4E8] text-[#9A6817] px-2 py-0.5 rounded-md font-bold border border-[#E4D5B8]">
                  {staffUser?.role === 'OWNER'
                    ? 'مالك المتجر'
                    : staffUser?.role === 'SUPERVISOR'
                    ? 'مشرف عام'
                    : staffUser?.role === 'SALES'
                    ? 'نقطة البيع'
                    : staffUser?.role === 'ACCOUNTANT'
                    ? 'محاسب'
                    : staffUser?.role === 'WORKSHOP'
                    ? 'فني الورشة'
                    : 'موظف مصرح'}
                </span>
              </div>

              {onStaffLogout && (
                <button
                  onClick={onStaffLogout}
                  title="تسجيل خروج من الإدارة"
                  className="p-2 rounded-xl text-rose-600 hover:bg-rose-50 border border-rose-200 transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile & Tablet Quick Navigation Strip */}
      {portalMode === 'storefront' && (
        <div className="lg:hidden flex items-center gap-2 px-3 py-1.5 border-t border-[#F5EFE6] bg-[#FAF7F2] overflow-x-auto no-scrollbar scroll-smooth">
          {storefrontMenuItems.map((item) => {
            const isActive = activeMenuItem === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleMenuItemClick(item)}
                className={`flex items-center gap-1.5 py-1 px-3 rounded-full text-xs font-bold shrink-0 transition cursor-pointer ${
                  isActive
                    ? 'bg-[#26221C] text-[#E2B84B] shadow-xs'
                    : item.id === 'b2b'
                    ? 'text-[#9A6817] bg-[#FAF4E8] border border-[#E4D5B8]'
                    : 'text-[#4B4338] hover:text-[#C9972B] bg-white border border-[#EBE3D5]'
                }`}
              >
                <span className="text-[11px]">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
