import React from 'react';
import {
  Gem,
  LayoutDashboard,
  ShoppingBag,
  Sparkles,
  ShieldCheck,
  Scissors,
  Receipt,
  Calculator,
  Users,
  Settings,
  Store,
  UserCheck,
  PanelRightClose
} from 'lucide-react';
import { User } from '../types';
import { hasPermission } from '../lib/permissions';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  currentUser?: User;
  isOpen?: boolean;
  onToggle?: () => void;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  currentUser,
  isOpen = true,
  onToggle,
  onClose
}) => {
  const allNavItems = [
    { id: 'storefront', label: 'المتجر والواجهة', icon: Store, badge: 'رئيسي', perm: null },
    { id: 'pos', label: 'البيع السريع (POS)', icon: ShoppingBag, badge: 'فوري', perm: 'pos.view' },
    { id: 'inventory', label: 'المسابيح الفاخرة', icon: Gem, perm: 'inventory.view' },
    { id: 'custody', label: 'سجل العهدة والمعارض', icon: ShieldCheck, perm: 'custody.view' },
    { id: 'workshop', label: 'ورشة تعديل الخرز', icon: Scissors, perm: 'workshop.view' },
    { id: 'orders', label: 'سجلات المبيعات', icon: Receipt, perm: 'orders.view' },
    { id: 'accountant', label: 'المحاسب الذكي', icon: Calculator, badge: 'مالي', perm: 'accountant.view' },
    { id: 'dashboard', label: 'لوحة التحكم والمؤشرات', icon: LayoutDashboard, perm: 'dashboard.view' },
    { id: 'ambassadors', label: 'برنامج السفراء', icon: Users, perm: 'ambassadors.view' },
    { id: 'users', label: 'المستخدمون والصلاحيات', icon: UserCheck, badge: 'أمان', perm: 'users.view' },
    { id: 'settings', label: 'الإعدادات والترخيص', icon: Settings, perm: 'settings.view' },
  ];

  // Filter based on user permissions
  const navItems = allNavItems.filter(item => {
    if (!item.perm) return true;
    if (!currentUser) return true;
    return hasPermission(currentUser, item.perm);
  });

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 md:hidden transition-opacity duration-300"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Aside */}
      <aside
        className={`
          fixed md:static inset-y-0 right-0 z-50 shrink-0
          bg-[#FDFBF7] border-l border-[#EBE3D5] flex flex-col justify-between select-none
          shadow-[2px_0_15px_rgba(70,45,15,0.02)] transition-all duration-300 ease-in-out
          ${
            isOpen
              ? 'w-64 min-w-[16rem] translate-x-0 opacity-100'
              : 'w-0 min-w-0 max-w-0 translate-x-full md:translate-x-0 opacity-0 overflow-hidden border-none pointer-events-none'
          }
        `}
      >
        <div className={`w-64 flex flex-col justify-between h-full transition-opacity duration-200 ${isOpen ? 'min-w-[16rem] opacity-100' : 'min-w-0 opacity-0 pointer-events-none'}`}>
          <div>
            {/* Brand Header */}
            <div className="p-4 border-b border-[#EBE3D5] flex items-center justify-between bg-gradient-to-b from-[#FFFDF8] to-[#FBF8F2]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#C9972B] to-[#E2B84B] flex items-center justify-center shadow-md shadow-[#C9972B]/20 text-white font-black overflow-hidden p-1 shrink-0">
                  <img
                    src="/branding/brand-symbol.png"
                    alt="هيبة السلطان"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="truncate">
                  <h1 className="font-extrabold text-sm text-[#26221C] tracking-wide">هيبة السلطان</h1>
                  <p className="text-[10px] font-semibold text-[#9A6817]">نظام المسابيح الفاخرة PRO</p>
                </div>
              </div>

              {/* Close / Hide Sidebar Button */}
              {onToggle && (
                <button
                  type="button"
                  onClick={onToggle}
                  className="px-2 py-1 rounded-xl text-[#746A5D] hover:text-[#9A6817] hover:bg-[#F2ECE1] transition border border-[#EADBCE] hover:border-[#C9972B] cursor-pointer flex items-center gap-1 shadow-2xs active:scale-95"
                  title="إخفاء القائمة الجانبية لتوسيع الشاشة"
                >
                  <PanelRightClose className="w-4 h-4 text-[#9A6817]" />
                  <span className="text-[11px] font-bold text-[#746A5D]">إخفاء</span>
                </button>
              )}
            </div>

            {/* Navigation Items */}
            <nav className="p-3 space-y-1.5 overflow-y-auto max-h-[calc(100vh-140px)]">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-gradient-to-r from-[#FAF3E4] to-[#FFFDF8] text-[#9A6817] border border-[#E2B84B]/40 shadow-xs font-bold'
                        : 'text-[#4F463B] hover:bg-[#F8F4EC] hover:text-[#9A6817]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={`w-7 h-7 rounded-lg flex items-center justify-center transition ${
                        isActive ? 'bg-[#C9972B] text-white shadow-xs' : 'bg-[#F4EEE3] text-[#746A5D]'
                      }`}>
                        <Icon className="w-4 h-4" />
                      </span>
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        isActive
                          ? 'bg-[#C9972B] text-white'
                          : 'bg-[#F4EEE3] text-[#9A6817] border border-[#EADBCE]'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Footer Status Card */}
          <div className="p-3.5 border-t border-[#EBE3D5] bg-[#F7F2E7]/80 text-xs text-[#554C41]">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold block text-[11px] text-[#26221C]">{currentUser?.full_name || 'المستخدم'}</span>
                <span className="text-[10px] text-[#8C8275]">
                  {currentUser?.role === 'OWNER' ? '👑 مالك المتجر' : currentUser?.role || 'موظف مصرح'}
                </span>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm" title="متصل" />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
