import React from 'react';
import { Home, Gem, Search, ShoppingBag, User as UserIcon } from 'lucide-react';
import { Product } from '../types';

interface MobileBottomNavProps {
  activeTab: string; // 'all' | 'rare' | 'gemstones' | 'gifts' | 'cart' | 'orders'
  onSelectTab: (tabId: string) => void;
  cartItem?: Product | null;
  reservationRemaining?: number;
  onOpenCheckout: () => void;
  onOpenAccount: () => void;
  customerUser?: any;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  activeTab,
  onSelectTab,
  cartItem,
  reservationRemaining = 0,
  onOpenCheckout,
  onOpenAccount,
  customerUser
}) => {
  const isReserved = Boolean(cartItem && reservationRemaining > 0);

  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-40 bg-[#FAF7F2]/95 backdrop-blur-xl border-t border-[#E8DEC9] shadow-[0_-5px_25px_rgba(38,34,28,0.08)] md:hidden pb-[max(0.35rem,env(safe-area-inset-bottom,0px))] transition-transform"
      aria-label="قائمة التنقل السفلية لتطبيق الجوال"
    >
      <div className="grid grid-cols-5 h-14 max-w-md mx-auto px-1 items-center text-center">
        {/* 1. الرئيسية (Home) */}
        <button
          type="button"
          onClick={() => onSelectTab('home')}
          className={`flex flex-col items-center justify-center gap-0.5 py-1 transition-all active:scale-90 cursor-pointer ${
            activeTab === 'home' || activeTab === 'all'
              ? 'text-[#9A6817] font-black'
              : 'text-[#746A5D] hover:text-[#26221C]'
          }`}
        >
          <div className={`p-1 rounded-xl transition ${activeTab === 'home' || activeTab === 'all' ? 'bg-[#FAF4E8] text-[#C9972B]' : ''}`}>
            <Home className="w-5 h-5" />
          </div>
          <span className="text-[10px] leading-none">الرئيسية</span>
        </button>

        {/* 2. النوادر (Rare) */}
        <button
          type="button"
          onClick={() => onSelectTab('rare')}
          className={`flex flex-col items-center justify-center gap-0.5 py-1 transition-all active:scale-90 cursor-pointer ${
            activeTab === 'rare'
              ? 'text-[#9A6817] font-black'
              : 'text-[#746A5D] hover:text-[#26221C]'
          }`}
        >
          <div className={`p-1 rounded-xl transition ${activeTab === 'rare' ? 'bg-[#FAF4E8] text-[#C9972B]' : ''}`}>
            <Gem className="w-5 h-5" />
          </div>
          <span className="text-[10px] leading-none">النوادر</span>
        </button>

        {/* 3. البحث (Search) */}
        <button
          type="button"
          onClick={() => onSelectTab('search')}
          className={`flex flex-col items-center justify-center gap-0.5 py-1 transition-all active:scale-90 cursor-pointer ${
            activeTab === 'search'
              ? 'text-[#9A6817] font-black'
              : 'text-[#746A5D] hover:text-[#26221C]'
          }`}
        >
          <div className={`p-1 rounded-xl transition ${activeTab === 'search' ? 'bg-[#FAF4E8] text-[#C9972B]' : ''}`}>
            <Search className="w-5 h-5" />
          </div>
          <span className="text-[10px] leading-none">البحث</span>
        </button>

        {/* 4. السلة والحجز (Cart / Reserved) */}
        <button
          type="button"
          onClick={onOpenCheckout}
          className={`flex flex-col items-center justify-center gap-0.5 py-1 transition-all active:scale-90 cursor-pointer relative ${
            isReserved
              ? 'text-[#9A6817] font-black'
              : cartItem
              ? 'text-[#C9972B] font-bold'
              : 'text-[#746A5D] hover:text-[#26221C]'
          }`}
        >
          <div className={`p-1 rounded-xl relative transition ${isReserved || cartItem ? 'bg-[#FAF4E8]' : ''}`}>
            <ShoppingBag className="w-5 h-5" />
            {isReserved ? (
              <span className="absolute -top-1.5 -right-2 bg-gradient-to-r from-[#9A6817] to-[#C9972B] text-white text-[9px] font-mono font-bold px-1 py-0.2 rounded-full border border-white animate-pulse">
                {Math.floor(reservationRemaining / 60)}:{String(reservationRemaining % 60).padStart(2, '0')}
              </span>
            ) : cartItem ? (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#C9972B] border border-white" />
            ) : null}
          </div>
          <span className="text-[10px] leading-none">{isReserved ? 'حجزي' : 'السلة'}</span>
        </button>

        {/* 5. حسابي (Account / Orders) */}
        <button
          type="button"
          onClick={onOpenAccount}
          className="flex flex-col items-center justify-center gap-0.5 py-1 text-[#746A5D] hover:text-[#26221C] transition-all active:scale-90 cursor-pointer"
        >
          <div className="p-1 rounded-xl">
            <UserIcon className="w-5 h-5" />
          </div>
          <span className="text-[10px] leading-none truncate max-w-[55px]">
            {customerUser ? (customerUser.full_name?.split(' ')[0] || 'حسابي') : 'دخول'}
          </span>
        </button>
      </div>
    </nav>
  );
};
