import React, { useState, useEffect } from 'react';
import {
  Gem,
  Award,
  Clock,
  ShoppingCart,
  MessageCircle,
  Sparkles,
  Truck,
  Gift,
  Headphones,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Search,
  Lock,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  SlidersHorizontal,
  ArrowUpDown,
  RotateCcw,
  Coins,
  X,
  Filter,
  Check
} from 'lucide-react';
import { api } from '../lib/api';
import { Product, Banner } from '../types';
import { toast } from '../utils/toast';
import { HeroBannerSlider } from '../components/HeroBannerSlider';

interface StorefrontPageProps {
  onOpenCheckout: (product: Product) => void;
  onOpenCustomerAuth: () => void;
  onOpenCustomerOrders: () => void;
  onViewProduct?: (product: Product) => void;
  customerUser?: any;
  cartItem?: Product | null;
  reservationRemaining?: number;
  onReserveProduct?: (product: Product, durationMinutes?: number) => void;
  activeCategoryFilter?: string;
  onCategoryFilterChange?: (cat: string) => void;
}

export const StorefrontPage: React.FC<StorefrontPageProps> = ({
  onOpenCheckout,
  onOpenCustomerAuth,
  onOpenCustomerOrders,
  onViewProduct,
  customerUser,
  cartItem,
  reservationRemaining = 0,
  onReserveProduct,
  activeCategoryFilter = 'all',
  onCategoryFilterChange
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [banners, setBanners] = useState<Banner[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Price Range & Sorting Filters
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [selectedPreset, setSelectedPreset] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'featured' | 'price_asc' | 'price_desc'>('featured');

  const pricePresets = [
    { id: 'all', label: 'كافة الأسعار', min: '', max: '' },
    { id: 'under_3000', label: 'أقل من 3,000 د.إ', min: '', max: '3000' },
    { id: '3000_6000', label: '3,000 - 6,000 د.إ', min: '3000', max: '6000' },
    { id: '6000_12000', label: '6,000 - 12,000 د.إ', min: '6000', max: '12000' },
    { id: 'above_12000', label: 'أكثر من 12,000 د.إ (نوادر ملكية)', min: '12000', max: '' },
  ];

  const handleSelectPreset = (preset: typeof pricePresets[0]) => {
    setSelectedPreset(preset.id);
    setMinPrice(preset.min);
    setMaxPrice(preset.max);
  };

  const handleCustomMinChange = (val: string) => {
    setMinPrice(val);
    setSelectedPreset('custom');
  };

  const handleCustomMaxChange = (val: string) => {
    setMaxPrice(val);
    setSelectedPreset('custom');
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setMinPrice('');
    setMaxPrice('');
    setSelectedPreset('all');
    setSortBy('featured');
    if (onCategoryFilterChange) onCategoryFilterChange('all');
  };

  const hasActiveFilter = Boolean(
    searchQuery.trim() || minPrice !== '' || maxPrice !== '' || sortBy !== 'featured' || (activeCategoryFilter && activeCategoryFilter !== 'all')
  );

  useEffect(() => {
    loadStore();
  }, []);

  const loadStore = async () => {
    setLoading(true);
    try {
      const [prods, bData] = await Promise.all([
        api.getProducts({ status: 'AVAILABLE' }),
        api.getBanners().catch(() => [])
      ]);
      setProducts(prods);
      setBanners(bData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleReserve = async (product: Product) => {
    if (onReserveProduct) {
      onReserveProduct(product, 15);
      return;
    }
    if (!customerUser) {
      if (onOpenCustomerAuth) onOpenCustomerAuth();
      toast.warning('لحجز هذه القطعة الحصرية، يجب تسجيل الدخول أو إنشاء حساب أولاً.', 'تسجيل الدخول مطلوب للحجز');
      return;
    }
    try {
      const userIdentifier = customerUser.phone || customerUser.username || `user_${customerUser.id}`;
      await api.reserveProduct(product.id, userIdentifier, 15);
      toast.success(`تم حجز المسبحة (${product.name_ar}) باسمك لمدة 15 دقيقة حصرياً! لن يتمكن أي عميل أو معرض آخر من شرائها.`, 'حجز مسبحة حصرية');
      await loadStore();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر حجز المسبحة');
    }
  };

  const handleWhatsAppOrder = (product: Product) => {
    const text = encodeURIComponent(
      `السلام عليكم ورحمة الله وبركاته،\nأود اقتناء هذه القطعة الفريدة من هيبة السلطان:\n\n• الاسم: ${product.name_ar}\n• الرمز المرجعي: ${product.product_reference}\n• الـ SKU: ${product.sku}\n• السعر: ${product.selling_price} AED\n\nيرجى تأكيد التوافر وإجراءات الاستلام/التوصيل.`
    );
    window.open(`https://wa.me/971504084006?text=${text}`, '_blank');
  };

  const filteredProducts = products.filter((p) => {
    // 0. Active category filter (النوادر / الأحجار الكريمة / الهدايا / الكل)
    if (activeCategoryFilter === 'rare') {
      const isRare =
        Boolean((p as any).is_rare) ||
        p.name_ar.includes('نادر') ||
        p.name_ar.includes('نوادر') ||
        p.name_ar.includes('أنتيك') ||
        p.name_ar.includes('ملكي') ||
        p.name_ar.includes('فاتوران') ||
        p.name_ar.includes('كهرمان') ||
        Number(p.selling_price) >= 4000 ||
        (p.category_name_ar && (p.category_name_ar.includes('نادر') || p.category_name_ar.includes('أنتيك') || p.category_name_ar.includes('فاتوران')));
      if (!isRare) return false;
    } else if (activeCategoryFilter === 'gemstones') {
      const isGem =
        (p.category_name_ar && p.category_name_ar.includes('أحجار')) ||
        p.name_ar.includes('فيروز') ||
        p.name_ar.includes('عقيق') ||
        p.name_ar.includes('حجر') ||
        p.name_ar.includes('نيشابوري') ||
        (p.material_name_ar && (p.material_name_ar.includes('فيروز') || p.material_name_ar.includes('عقيق')));
      if (!isGem) return false;
    } else if (activeCategoryFilter === 'gifts') {
      const isGift =
        (p.category_name_ar && p.category_name_ar.includes('هدايا')) ||
        p.name_ar.includes('هدية') ||
        p.name_ar.includes('تحف') ||
        p.name_ar.includes('طقم');
      if (!isGift) return false;
    }

    // 1. Keyword search (Name, SKU, Reference, Shape, Origin, Category, Material)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        p.name_ar.toLowerCase().includes(q) ||
        p.sku.toLowerCase().includes(q) ||
        p.product_reference.toLowerCase().includes(q) ||
        (p.shape && p.shape.toLowerCase().includes(q)) ||
        (p.origin && p.origin.toLowerCase().includes(q)) ||
        (p.category_name_ar && p.category_name_ar.toLowerCase().includes(q)) ||
        (p.material_name_ar && p.material_name_ar.toLowerCase().includes(q));
      if (!match) return false;
    }

    // 2. Price Range Filter: Min & Max
    const price = Number(p.selling_price) || 0;
    if (minPrice !== '' && !isNaN(Number(minPrice))) {
      if (price < Number(minPrice)) return false;
    }
    if (maxPrice !== '' && !isNaN(Number(maxPrice))) {
      if (price > Number(maxPrice)) return false;
    }

    return true;
  }).sort((a, b) => {
    if (sortBy === 'price_asc') return a.selling_price - b.selling_price;
    if (sortBy === 'price_desc') return b.selling_price - a.selling_price;
    return b.id - a.id;
  });

  return (
    <div className="min-h-full bg-[#FAF7F2] text-[#26221C] flex flex-col justify-between selection:bg-[#C9972B]/20">
      {/* 1. Panoramic Hero Section (Desktop Web: Luxury Slider with Permanent Base Image) */}
      <section id="hero" className="hidden md:block relative w-full bg-[#EFE8DC] overflow-hidden border-b border-[#EBE3D5]">
        {/* Dynamic Hero Slider */}
        <HeroBannerSlider banners={banners} />

        {/* 2. 4-Column Benefit Strip (Exact Match to User Attached Screenshot) */}
        <div className="bg-white border-t border-[#EBE3D5] shadow-xs">
          <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x md:divide-x-reverse divide-[#EBE3D5]">
            {/* 1. توصيل سريع */}
            <div className="p-4 sm:p-5 flex items-center justify-center gap-3.5 text-right">
              <div className="w-10 h-10 rounded-full bg-[#FAF4E8] flex items-center justify-center text-[#C9972B] shrink-0 border border-[#EADBCE]">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#26221C]">توصيل سريع</h4>
                <p className="text-xs text-[#746A5D]">داخل الإمارات وخارجها</p>
              </div>
            </div>

            {/* 2. تغليف فاخر */}
            <div className="p-4 sm:p-5 flex items-center justify-center gap-3.5 text-right">
              <div className="w-10 h-10 rounded-full bg-[#FAF4E8] flex items-center justify-center text-[#C9972B] shrink-0 border border-[#EADBCE]">
                <Gift className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#26221C]">تغليف فاخر</h4>
                <p className="text-xs text-[#746A5D]">جاهز للإهداء والتقديم</p>
              </div>
            </div>

            {/* 3. الأصالة أولاً */}
            <div className="p-4 sm:p-5 flex items-center justify-center gap-3.5 text-right">
              <div className="w-10 h-10 rounded-full bg-[#FAF4E8] flex items-center justify-center text-[#C9972B] shrink-0 border border-[#EADBCE]">
                <Gem className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#26221C]">الأصالة أولاً</h4>
                <p className="text-xs text-[#746A5D]">قطع مختارة بعناية وفحص</p>
              </div>
            </div>

            {/* 4. خدمة مميزة */}
            <div className="p-4 sm:p-5 flex items-center justify-center gap-3.5 text-right">
              <div className="w-10 h-10 rounded-full bg-[#FAF4E8] flex items-center justify-center text-[#C9972B] shrink-0 border border-[#EADBCE]">
                <Headphones className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#26221C]">خدمة مميزة</h4>
                <p className="text-xs text-[#746A5D]">نحن هنا لخدمتكم واستشارتكم</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 1.B Mobile App Experience: Compact Hero & Category Stories Chips (Mobile App Only) */}
      <section className="block md:hidden px-3 pt-3 space-y-3">
        {/* Compact App Hero Card with Dynamic Slider */}
        <HeroBannerSlider banners={banners} compact />

        {/* Mobile Horizontal Category Stories Chips */}
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 -mx-3 px-3">
          {[
            { id: 'all', label: 'الكل', icon: '📿' },
            { id: 'rare', label: 'النوادر', icon: '🏺' },
            { id: 'gemstones', label: 'الأحجار الكريمة', icon: '💎' },
            { id: 'gifts', label: 'الهدايا', icon: '🎁' },
          ].map((cat) => {
            const isActive = activeCategoryFilter === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => {
                  if (onCategoryFilterChange) onCategoryFilterChange(cat.id);
                }}
                className={`shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all active:scale-95 cursor-pointer ${
                  isActive
                    ? 'bg-[#26221C] text-[#E2B84B] shadow-sm border border-[#26221C]'
                    : 'bg-white text-[#554C41] border border-[#E8DEC9] hover:bg-[#FAF4E8]'
                }`}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* 3. Showcase Grid of Luxury Rosaries */}
      <section id="products-section" className="max-w-7xl mx-auto px-2.5 sm:px-6 lg:px-8 py-5 sm:py-10 pb-28 md:pb-12 flex-1 w-full space-y-4 sm:space-y-6">
        {/* Section Heading Bar */}
        <div id="products" className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#EBE3D5]">
          <div>
            <h2 className="text-xl sm:text-2xl font-black text-[#26221C] flex items-center gap-2">
              <Gem className="w-6 h-6 text-[#C9972B]" />
              <span>المعروضات الفاخرة المتاحة للاقتناء</span>
            </h2>
            <p className="text-xs sm:text-sm text-[#746A5D] mt-1">
              كل مسبحة قطعة حصرية وحيدة لا تتكرر، محصنة ضد الازدواج ومعتمدة بفحص مخبري
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-[#9A6817] bg-[#FAF4E8] border border-[#EADBCE] px-3.5 py-1.5 rounded-full shrink-0 shadow-xs">
              {filteredProducts.length} قطعة متوفرة
            </span>
          </div>
        </div>

        {/* Active Category Banner (النوادر / الأحجار الكريمة / الهدايا) */}
        {activeCategoryFilter === 'rare' && (
          <div className="bg-gradient-to-r from-[#1E1912] via-[#2F261B] to-[#1E1912] text-white p-4 sm:p-5 rounded-3xl border border-[#C9972B]/60 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl animate-in fade-in">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#C9972B]/20 border border-[#C9972B]/50 flex items-center justify-center shrink-0 text-xl shadow-inner">
                🏺
              </div>
              <div>
                <h3 className="font-black text-sm sm:text-base text-[#F7E7CE] flex items-center gap-2">
                  <span>جناح النوادر والمقتنيات الملكية الحصرية</span>
                  <span className="text-[10px] bg-[#C9972B] text-black px-2 py-0.5 rounded-full font-bold">VIP Rare</span>
                </h3>
                <p className="text-xs text-[#C8BCAB] mt-0.5">
                  قطع متحفية نادرة وفريدة مخصصة لعشاق الأصالة وأصحاب المجموعات الخاصة
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => onCategoryFilterChange && onCategoryFilterChange('all')}
              className="text-xs px-4 py-2 bg-white/10 hover:bg-white/20 text-[#F7E7CE] rounded-xl font-bold transition cursor-pointer border border-[#C9972B]/40 shrink-0"
            >
              عرض كافة المعروضات ✕
            </button>
          </div>
        )}

        {/* 4. Luxury Search & Price Range Filter Control Panel */}
        <div className="bg-white border border-[#EBE3D5] rounded-3xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <input
                id="store-search-input"
                type="text"
                placeholder="بحث باسم المسبحة، الخامة، أو كود SKU..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full py-2.5 pr-10 pl-4 text-xs rounded-2xl bg-[#FAF7F2] border border-[#DDD3C1] text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B] focus:bg-white transition"
              />
              <Search className="w-4 h-4 text-[#9E9485] absolute right-3.5 top-3" />
            </div>

            {/* Price Range: Min & Max Inputs + Sorting */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs">
              {/* Min Price */}
              <div className="flex items-center gap-1.5 bg-[#FAF7F2] border border-[#DDD3C1] px-3 py-1.5 rounded-2xl focus-within:border-[#C9972B] focus-within:bg-white transition shadow-2xs">
                <span className="text-[#8C8275] font-bold">من:</span>
                <input
                  type="number"
                  min="0"
                  step="100"
                  placeholder="0"
                  value={minPrice}
                  onChange={(e) => handleCustomMinChange(e.target.value)}
                  className="w-20 text-xs font-bold text-[#26221C] bg-transparent focus:outline-none"
                />
                <span className="text-[10px] text-[#9A6817] font-semibold">د.إ</span>
              </div>

              {/* Max Price */}
              <div className="flex items-center gap-1.5 bg-[#FAF7F2] border border-[#DDD3C1] px-3 py-1.5 rounded-2xl focus-within:border-[#C9972B] focus-within:bg-white transition shadow-2xs">
                <span className="text-[#8C8275] font-bold">إلى:</span>
                <input
                  type="number"
                  min="0"
                  step="100"
                  placeholder="أقصى سعر"
                  value={maxPrice}
                  onChange={(e) => handleCustomMaxChange(e.target.value)}
                  className="w-24 text-xs font-bold text-[#26221C] bg-transparent focus:outline-none"
                />
                <span className="text-[10px] text-[#9A6817] font-semibold">د.إ</span>
              </div>

              {/* Sorting Order */}
              <div className="flex items-center gap-1.5 bg-[#FAF7F2] border border-[#DDD3C1] px-3 py-1.5 rounded-2xl shadow-2xs">
                <ArrowUpDown className="w-3.5 h-3.5 text-[#C9972B]" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-transparent text-xs font-bold text-[#26221C] focus:outline-none cursor-pointer"
                >
                  <option value="featured">المميز والأحدث</option>
                  <option value="price_asc">السعر: من الأقل للأعلى</option>
                  <option value="price_desc">السعر: من الأعلى للأقل</option>
                </select>
              </div>

              {/* Reset Button */}
              {hasActiveFilter && (
                <button
                  onClick={handleResetFilters}
                  className="flex items-center gap-1 px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-2xl text-xs font-bold transition cursor-pointer shadow-2xs"
                  title="إلغاء وتفريغ الفلاتر"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>إعادة ضبط</span>
                </button>
              )}
            </div>
          </div>

          {/* Quick Price Range Presets */}
          <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-[#F2ECE1]">
            <span className="text-xs text-[#8C8275] font-bold flex items-center gap-1 shrink-0">
              <Coins className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>نطاقات سريعة:</span>
            </span>

            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={() => onCategoryFilterChange && onCategoryFilterChange(activeCategoryFilter === 'rare' ? 'all' : 'rare')}
                className={`text-xs px-3 py-1 rounded-full font-bold transition cursor-pointer border flex items-center gap-1 ${
                  activeCategoryFilter === 'rare'
                    ? 'bg-gradient-to-r from-[#9A6817] via-[#C9972B] to-[#E2B84B] text-black border-[#C9972B] font-black shadow-xs'
                    : 'bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border-[#E4D5B8]'
                }`}
              >
                <span>🏺</span>
                <span>النوادر الملكية</span>
              </button>

              {pricePresets.map((preset) => {
                const isSelected = selectedPreset === preset.id;
                return (
                  <button
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset)}
                    className={`text-xs px-3 py-1 rounded-full font-bold transition cursor-pointer border ${
                      isSelected
                        ? 'bg-[#26221C] text-[#E2B84B] border-[#26221C] shadow-xs'
                        : 'bg-[#FAF7F2] hover:bg-[#F3E7CE] text-[#4B4338] border-[#E8DEC8]'
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>

            {/* Active Range Indicator Pill */}
            {(minPrice || maxPrice) && (
              <span className="mr-auto text-[11px] font-bold text-[#9A6817] bg-[#FAF4E8] border border-[#EADBCE] px-3 py-1 rounded-full flex items-center gap-1">
                <span>النطاق النشط:</span>
                <span className="font-mono">
                  {minPrice ? `${Number(minPrice).toLocaleString()} د.إ` : '0 د.إ'} - {maxPrice ? `${Number(maxPrice).toLocaleString()} د.إ` : 'بلا حد'}
                </span>
              </span>
            )}
          </div>
        </div>

        {/* Product Cards */}
        {loading ? (
          <div className="py-24 text-center">
            <div className="inline-block w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin mb-3"></div>
            <p className="text-xs text-[#746A5D] font-medium">جارِ تحميل التحف النادرة والمعروضات...</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-[#EBE3D5] p-8 shadow-xs space-y-4">
            <Gem className="w-12 h-12 text-[#C9972B]/60 mx-auto" />
            <h3 className="text-base font-bold text-[#26221C]">لا توجد قطع مطابقة لمعايير البحث ونطاق السعر المحدد</h3>
            <p className="text-xs text-[#746A5D] max-w-md mx-auto">
              {minPrice || maxPrice
                ? `لم نجد أي مسبحة في النطاق السعري (${minPrice ? `من ${Number(minPrice).toLocaleString()} د.إ` : ''} ${maxPrice ? `إلى ${Number(maxPrice).toLocaleString()} د.إ` : ''}) حالياً.`
                : 'كافة المعروضات في هذه الفئة قد تم اقتناؤها أو حجزها. تواصل معنا لمعرفة موعد الطرح القادم.'}
            </p>
            {hasActiveFilter && (
              <button
                onClick={handleResetFilters}
                className="px-5 py-2.5 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] rounded-xl text-xs font-bold transition shadow-xs cursor-pointer inline-flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>عرض كافة الأسعار والمعروضات</span>
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-2.5 sm:gap-6 sm:gap-8">
            {filteredProducts.map((p) => (
              <div
                key={p.id}
                className="bg-white border border-[#EBE3D5] rounded-2xl sm:rounded-3xl overflow-hidden flex flex-col justify-between hover:shadow-[0_10px_30px_rgba(201,151,43,0.15)] hover:border-[#C9972B] transition-all duration-300 group"
              >
                <div>
                  {/* Image Container with Badges */}
                  <div
                    onClick={() => onViewProduct && onViewProduct(p)}
                    className="relative aspect-square overflow-hidden bg-[#FBF8F2] cursor-pointer group/img"
                    title="انقر لعرض تفاصيل وقصة المسبحة ومواصفاتها الفنية وتكبير الصور"
                  >
                    <img
                      src={p.image_url || '/branding/hero-amber.jpg'}
                      alt={p.name_ar}
                      loading="lazy"
                      decoding="async"
                      className="w-full h-full object-cover group-hover/img:scale-108 transition-transform duration-700"
                    />

                    {/* Hover Zoom & Inspection Overlay (desktop only) */}
                    <div className="hidden sm:flex absolute inset-0 bg-black/25 opacity-0 group-hover/img:opacity-100 transition-opacity duration-300 items-center justify-center pointer-events-none">
                      <span className="bg-[#1C1814]/90 text-[#F4E3BA] text-xs font-bold px-3.5 py-1.5 rounded-xl border border-[#C9972B]/60 shadow-xl flex items-center gap-1.5 backdrop-blur-xs scale-95 group-hover/img:scale-100 transition-transform">
                        <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
                        <span>عرض التفاصيل وتكبير الصور</span>
                      </span>
                    </div>

                    {/* SKU Pill */}
                    <div className="absolute top-2 right-2 sm:top-3 sm:right-3 bg-white/95 backdrop-blur px-2 sm:px-3 py-0.5 sm:py-1 rounded-full text-[9px] sm:text-[11px] font-bold text-[#9A6817] border border-[#E8DEC8] shadow-xs">
                      {p.sku}
                    </div>

                    {/* Certification Badge */}
                    {p.verification_status === 'CERTIFIED' ? (
                      <div className="absolute bottom-2 right-2 sm:bottom-3 sm:right-3 bg-emerald-700/95 backdrop-blur px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg text-[8px] sm:text-[10px] font-bold text-white flex items-center gap-1 shadow-xs">
                        <Award className="w-2.5 h-2.5 sm:w-3.5 sm:h-3.5" />
                        <span className="hidden sm:inline">شهادة فحص معتمدة</span>
                        <span className="sm:hidden">معتمدة</span>
                      </div>
                    ) : (
                      <div className="absolute bottom-2 right-2 sm:bottom-3 sm:right-3 bg-black/60 backdrop-blur px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg text-[8px] sm:text-[10px] font-bold text-[#E5DAC8] flex items-center gap-1 shadow-xs border border-white/10">
                        <span className="hidden sm:inline">بدون شهادة فحص</span>
                        <span className="sm:hidden">أصلي</span>
                      </div>
                    )}
                  </div>

                  {/* Card Details */}
                  <div className="p-2.5 sm:p-5 space-y-1.5 sm:space-y-3">
                    <h3
                      onClick={() => onViewProduct && onViewProduct(p)}
                      className="font-extrabold text-xs sm:text-base text-[#26221C] group-hover:text-[#9A6817] transition line-clamp-2 sm:line-clamp-1 cursor-pointer leading-tight sm:leading-normal"
                      title="انقر لعرض تفاصيل وقصة المسبحة"
                    >
                      {p.name_ar}
                    </h3>

                    {/* Mobile Compact Specs Pill (visible only on mobile) */}
                    <div className="flex sm:hidden items-center justify-between text-[10px] text-[#746A5D] bg-[#FAF7F2] px-2 py-1 rounded-lg border border-[#EEE4D4]">
                      <span>{p.bead_count} خرزة</span>
                      <span className="text-[#C9972B]">•</span>
                      <span>
                        {p.bead_size_mm ? (String(p.bead_size_mm).toLowerCase().includes('mm') || String(p.bead_size_mm).includes('ملم') ? p.bead_size_mm : `${p.bead_size_mm}mm`) : '-'}
                      </span>
                      <span className="text-[#C9972B]">•</span>
                      <span>{p.weight_g}g</span>
                    </div>

                    {/* Desktop Rosary Specs Grid (hidden on mobile) */}
                    <div className="hidden sm:grid grid-cols-3 gap-2 text-center text-xs bg-[#FAF7F2] p-2.5 rounded-xl border border-[#EEE4D4] text-[#4B4338]">
                      <div>
                        <span className="block text-[10px] text-[#8C8275]">الخرز</span>
                        <span className="font-bold text-[#26221C]">{p.bead_count}</span>
                      </div>
                      <div className="border-r border-l border-[#E2D8C6]">
                        <span className="block text-[10px] text-[#8C8275]">القياس</span>
                        <span className="font-bold text-[#26221C]">
                          {p.bead_size_mm ? (String(p.bead_size_mm).toLowerCase().includes('mm') || String(p.bead_size_mm).includes('ملم') ? p.bead_size_mm : `${p.bead_size_mm}mm`) : '-'}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-[#8C8275]">الوزن</span>
                        <span className="font-bold text-[#26221C]">{p.weight_g}g</span>
                      </div>
                    </div>

                    {/* Desktop Attributes (hidden on mobile) */}
                    <div className="hidden sm:block text-xs text-[#746A5D] space-y-1 pt-1">
                      <p><span className="text-[#9E9485]">القصة:</span> <span className="font-medium text-[#3D352E]">{p.shape || 'برميلي'}</span></p>
                      <p><span className="text-[#9E9485]">الكركوشة:</span> <span className="font-medium text-[#3D352E]">{p.tassel_type || 'فضة عيار 925'}</span></p>
                      <p><span className="text-[#9E9485]">المنشأ:</span> <span className="font-medium text-[#3D352E]">{p.origin || 'ألمانيا / البلطيق'}</span></p>
                    </div>

                    {/* Desktop View Details Link */}
                    {onViewProduct && (
                      <button
                        onClick={() => onViewProduct(p)}
                        className="hidden sm:flex w-full pt-1 text-xs font-bold text-[#9A6817] hover:text-[#C9972B] items-center justify-center gap-1 transition cursor-pointer"
                      >
                        <span>عرض القصة والمواصفات الكاملة</span>
                        <ChevronLeft className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Card Pricing & Action Buttons */}
                <div className="p-2.5 sm:p-5 pt-0 border-t border-[#F5EFE6] mt-1 sm:mt-3">
                  <div className="flex items-baseline justify-between mb-2 sm:mb-3 pt-2 sm:pt-3">
                    <span className="text-[10px] sm:text-xs text-[#746A5D]">قيمة الاقتناء:</span>
                    <span className="text-sm sm:text-xl font-black text-[#9A6817]">
                      {p.selling_price.toLocaleString()} <span className="text-[10px] sm:text-xs font-bold text-[#746A5D]">AED</span>
                    </span>
                  </div>

                  {/* --- MOBILE ACTION BAR (App Style, 1-tap Thumb Friendly) --- */}
                  <div className="flex sm:hidden items-center gap-1.5 pt-1">
                    {cartItem && cartItem.id === p.id ? (
                      <button
                        onClick={() => onOpenCheckout(p)}
                        className="flex-1 py-2 bg-gradient-to-r from-[#9A6817] to-[#C9972B] text-black text-[11px] font-black rounded-xl flex items-center justify-center gap-1 shadow-xs active:scale-98 transition"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>محجوزة لك</span>
                      </button>
                    ) : p.status === 'RESERVED' ? (
                      <button
                        disabled
                        className="flex-1 py-2 bg-[#FAF4E8] text-[#9E9485] text-[10px] font-bold rounded-xl border border-[#EADBCE] flex items-center justify-center gap-1 cursor-not-allowed"
                      >
                        <Clock className="w-3 h-3 text-[#C9972B]" />
                        <span>محجوزة</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => onOpenCheckout(p)}
                        className="flex-1 py-2 bg-[#C9972B] active:bg-[#B8851E] text-white text-[11px] font-black rounded-xl flex items-center justify-center gap-1 shadow-xs active:scale-98 transition"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>اقتناء</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleWhatsAppOrder(p)}
                      title="طلب عبر واتساب"
                      aria-label="طلب عبر واتساب"
                      className="p-2 bg-[#25D366] active:bg-[#1EBE5D] text-white rounded-xl flex items-center justify-center shadow-xs active:scale-98 transition"
                    >
                      <MessageCircle className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* --- DESKTOP ACTION BUTTONS (hidden on mobile) --- */}
                  <div className="hidden sm:block">
                    {cartItem && cartItem.id === p.id ? (
                      <button
                        onClick={() => onOpenCheckout(p)}
                        className="w-full py-2.5 mb-2 bg-gradient-to-r from-[#9A6817] via-[#C9972B] to-[#E2B84B] hover:brightness-110 text-[#12100D] text-xs font-black rounded-xl transition flex items-center justify-center gap-2 shadow-md cursor-pointer animate-pulse"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>إتمام الاقتناء (محجوزة باسمك)</span>
                      </button>
                    ) : p.status === 'RESERVED' ? (
                      <button
                        disabled
                        className="w-full py-2.5 mb-2 bg-[#FAF4E8] text-[#9E9485] text-xs font-bold rounded-xl border border-[#EADBCE] flex items-center justify-center gap-2 cursor-not-allowed"
                      >
                        <Clock className="w-3.5 h-3.5 text-[#C9972B]" />
                        <span>محجوزة مؤقتاً لعميل آخر</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => onOpenCheckout(p)}
                        className="w-full py-2.5 mb-2 bg-[#C9972B] hover:bg-[#B8851E] text-white text-xs font-black rounded-xl transition flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>اقتناء فوري أونلاين</span>
                      </button>
                    )}

                    <div className="grid grid-cols-2 gap-2">
                      {cartItem && cartItem.id === p.id ? (
                        <div className="py-2 bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-bold rounded-xl flex items-center justify-center gap-1">
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>محجوزة لك ✓</span>
                        </div>
                      ) : p.status === 'RESERVED' ? (
                        <button
                          disabled
                          className="py-2 bg-[#F5EFE6] text-[#A89D8F] border border-[#E0D7C6] text-[11px] font-medium rounded-xl flex items-center justify-center gap-1 cursor-not-allowed"
                          title="المسبحة محجوزة مؤقتاً لعميل آخر. ستصبح متاحة تلقائياً في حال انتهاء المهلة (15 دقيقة)."
                        >
                          <Clock className="w-3 h-3 text-[#B0A493]" />
                          <span>محجوزة مؤقتاً</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleReserve(p)}
                          className="py-2 bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border border-[#E4D5B8] text-[11px] font-bold rounded-xl transition flex items-center justify-center gap-1 cursor-pointer"
                          title="حجز مؤقت يمنع أي شخص آخر من شرائه لمدة 15 دقيقة"
                        >
                          <Clock className="w-3 h-3" />
                          <span>حجز 15 دقيقة</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleWhatsAppOrder(p)}
                        className="py-2 bg-[#25D366] hover:bg-[#1EBE5D] text-white text-[11px] font-bold rounded-xl transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <MessageCircle className="w-3 h-3" />
                        <span>واتساب</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 4. Luxury Footer */}
      <footer className="mt-12 bg-white border-t border-[#EBE3D5] text-center text-xs text-[#746A5D]">
        {/* Royal Trust & Benefits Announcement Bar */}
        <div className="bg-gradient-to-r from-[#F7EFE3] via-[#FBF8F2] to-[#F6EEE2] border-b border-[#EEE4D4] py-3 px-4 text-xs text-[#2B241B]">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 font-medium">
              <Gift className="w-4 h-4 text-[#C9972B]" />
              <span>تغليف فاخر للهدايا ومستندات الفحص الرسمية</span>
            </div>

            <div className="flex items-center gap-1.5 font-bold text-[#9A6817]">
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>✦ هيبة السلطان — أصالة المقتنيات الملكية</span>
            </div>

            <div className="flex items-center gap-2 font-medium">
              <Truck className="w-4 h-4 text-[#C9972B]" />
              <span>شحن مؤمن لجميع دول الخليج والعالم</span>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-3">
          <div className="flex items-center justify-center gap-2 text-[#9A6817] font-black text-sm">
            <span>هيبة السلطان للمسابيح الفاخرة</span>
            <span>•</span>
            <span className="text-[11px] font-mono tracking-wider">HAYBAT ALSULTAN</span>
          </div>
          <p className="text-[#8C8275] flex items-center justify-center gap-2 flex-wrap">
            <span>أبوظبي، الإمارات العربية المتحدة</span>
            <span className="text-[#D0C5B4]">|</span>
            <span>خدمة العملاء:</span>
            <a
              href="https://wa.me/971504084006"
              target="_blank"
              rel="noopener noreferrer"
              dir="ltr"
              className="font-mono font-bold text-[#9A6817] hover:underline inline-block direction-ltr"
            >
              +971 50 408 4006
            </a>
          </p>

          <div className="pt-3 border-t border-[#F2ECE1] text-[11px] text-[#A89E90]">
            <span>جميع الحقوق محفوظة © {new Date().getFullYear()} — نظام حماية الحصرية وإدارة المسابيح الملكية</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
