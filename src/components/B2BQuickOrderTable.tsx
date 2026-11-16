import React, { useState, useMemo } from 'react';
import {
  Building2,
  ShoppingCart,
  AlertCircle,
  Check,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Search,
  Gem
} from 'lucide-react';
import { Product } from '../types';

export interface B2BQuickOrderItem {
  product: Product;
  quantity: number;
}

interface B2BQuickOrderTableProps {
  products: Product[];
  onAddToCartBulk: (items: B2BQuickOrderItem[]) => void;
  onProceedToB2BCheckout: (items: B2BQuickOrderItem[]) => void;
}

export const B2BQuickOrderTable: React.FC<B2BQuickOrderTableProps> = ({
  products,
  onAddToCartBulk,
  onProceedToB2BCheckout,
}) => {
  const [quantities, setQuantities] = useState<Record<string | number, number>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [addedAnimation, setAddedAnimation] = useState(false);

  const handleQuantityChange = (product: Product, val: number) => {
    const cleanVal = isNaN(val) ? 0 : Math.max(0, val);
    setQuantities(prev => ({
      ...prev,
      [product.id]: cleanVal
    }));
  };

  const handleSetMOQ = (product: Product) => {
    const moq = product.b2b_moq || 5;
    setQuantities(prev => ({
      ...prev,
      [product.id]: moq
    }));
  };

  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const match =
          p.name_ar.toLowerCase().includes(term) ||
          p.sku.toLowerCase().includes(term) ||
          p.product_reference.toLowerCase().includes(term) ||
          (p.origin && p.origin.toLowerCase().includes(term));
        if (!match) return false;
      }
      const b2bPrice = Number(p.price_b2b || (p.selling_price * 0.70));
      if (minPrice !== '' && !isNaN(Number(minPrice)) && b2bPrice < Number(minPrice)) return false;
      if (maxPrice !== '' && !isNaN(Number(maxPrice)) && b2bPrice > Number(maxPrice)) return false;
      return true;
    });
  }, [products, searchTerm, minPrice, maxPrice]);

  // Valid items that meet minimum order quantity
  const validOrderItems = useMemo(() => {
    return products
      .filter(p => {
        const qty = quantities[p.id] || 0;
        const moq = p.b2b_moq || 5;
        const stock = p.stock_quantity ?? 50;
        return qty > 0 && qty >= moq && qty <= stock;
      })
      .map(p => ({
        product: p,
        quantity: quantities[p.id]
      }));
  }, [products, quantities]);

  const totalWholesalePrice = useMemo(() => {
    return validOrderItems.reduce((acc, curr) => {
      const price = curr.product.price_b2b || (curr.product.selling_price * 0.70);
      return acc + price * curr.quantity;
    }, 0);
  }, [validOrderItems]);

  const totalUnits = useMemo(() => {
    return validOrderItems.reduce((acc, curr) => acc + curr.quantity, 0);
  }, [validOrderItems]);

  const handleBulkSubmit = () => {
    if (validOrderItems.length === 0) return;
    onAddToCartBulk(validOrderItems);
    setAddedAnimation(true);
    setTimeout(() => setAddedAnimation(false), 2000);
  };

  return (
    <div className="w-full font-sans text-[#26221C] select-none" dir="rtl">
      {/* 1. Header & Live Filter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white p-5 rounded-3xl border border-[#EBE3D5] shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center shadow-md">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base md:text-lg font-black text-[#26221C]">
              جدول طلبات الجملة السريعة (B2B Quick Order Table)
            </h2>
            <p className="text-xs text-[#746A5D]">
              الأسعار حصرية لكبار التجار المعتمدين وتخضع للحد الأدنى للطلب (MOQ)
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 bg-[#FAF7F2] border border-[#DDD3C1] px-3 py-1.5 rounded-xl text-xs">
            <span className="text-[#8C8275] font-bold">من:</span>
            <input
              type="number"
              min="0"
              placeholder="0"
              value={minPrice}
              onChange={e => setMinPrice(e.target.value)}
              className="w-16 text-xs font-bold text-[#26221C] bg-transparent focus:outline-none"
            />
            <span className="text-[10px] text-[#9A6817]">د.إ</span>
          </div>

          <div className="flex items-center gap-1.5 bg-[#FAF7F2] border border-[#DDD3C1] px-3 py-1.5 rounded-xl text-xs">
            <span className="text-[#8C8275] font-bold">إلى:</span>
            <input
              type="number"
              min="0"
              placeholder="أقصى سعر"
              value={maxPrice}
              onChange={e => setMaxPrice(e.target.value)}
              className="w-20 text-xs font-bold text-[#26221C] bg-transparent focus:outline-none"
            />
            <span className="text-[10px] text-[#9A6817]">د.إ</span>
          </div>

          <div className="relative w-full sm:w-64">
            <input
              type="text"
              placeholder="بحث بالـ SKU أو اسم المسبحة..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full py-2 pr-9 pl-4 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-[#26221C] placeholder-[#8C8275] focus:outline-none focus:border-[#C9972B]"
            />
            <Search className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
          </div>

          {(minPrice || maxPrice || searchTerm) && (
            <button
              onClick={() => { setMinPrice(''); setMaxPrice(''); setSearchTerm(''); }}
              className="text-xs px-2.5 py-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-xl font-bold transition cursor-pointer"
            >
              مسح
            </button>
          )}
        </div>
      </div>

      {/* 2. Quick Order Data Grid */}
      <div className="bg-white rounded-3xl border border-[#EBE3D5] shadow-xs overflow-hidden mb-28">
        <div className="overflow-x-auto">
          <table className="w-full text-right border-collapse text-xs">
            <thead>
              <tr className="bg-[#FAF7F2] border-b border-[#EBE3D5] text-[#746A5D] font-bold">
                <th className="py-3.5 px-4 text-center w-16">القطعة</th>
                <th className="py-3.5 px-4">رمز الصنف (SKU)</th>
                <th className="py-3.5 px-4">المسبحة والمواصفات</th>
                <th className="py-3.5 px-4 text-center">الحد الأدنى (MOQ)</th>
                <th className="py-3.5 px-4 text-center">المخزون المتوفر</th>
                <th className="py-3.5 px-4">سعر التجزئة (B2C)</th>
                <th className="py-3.5 px-4">سعر الجملة (B2B)</th>
                <th className="py-3.5 px-4 text-center w-48">الكمية المطلوبة</th>
                <th className="py-3.5 px-4 text-left">الإجمالي الصافي</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F2ECE1]">
              {filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-xs text-[#8C8275]">
                    <Gem className="w-8 h-8 text-[#C9972B]/50 mx-auto mb-2" />
                    <span>لا توجد أصناف تطابق معايير البحث الحالية</span>
                  </td>
                </tr>
              ) : (
                filteredProducts.map(p => {
                  const qty = quantities[p.id] || 0;
                  const moq = p.b2b_moq || 5;
                  const stock = p.stock_quantity ?? 50;
                  const wholesalePrice = p.price_b2b || Math.round(p.selling_price * 0.70);
                  const retailPrice = p.price_b2c || p.selling_price;
                  const isUnderMOQ = qty > 0 && qty < moq;
                  const isOverStock = qty > stock;
                  const isValid = qty >= moq && !isOverStock;
                  const lineTotal = isValid ? wholesalePrice * qty : 0;

                  return (
                    <tr
                      key={p.id}
                      className={`hover:bg-[#FCFBF8] transition-colors ${
                        qty > 0 && !isValid ? 'bg-amber-50/40' : ''
                      }`}
                    >
                      {/* Thumbnail */}
                      <td className="py-3 px-4 text-center">
                        <img
                          src={p.image_url || '/branding/hero-amber.jpg'}
                          alt={p.name_ar}
                          className="w-12 h-12 rounded-xl object-cover border border-[#E8DEC8] mx-auto shadow-2xs"
                        />
                      </td>

                      {/* SKU */}
                      <td className="py-3 px-4 font-mono font-bold text-[#9A6817]">
                        {p.sku}
                      </td>

                      {/* Name & Specs */}
                      <td className="py-3 px-4">
                        <p className="font-extrabold text-[#26221C] text-xs">{p.name_ar}</p>
                        <p className="text-[10px] text-[#8C8275] mt-0.5">
                          {p.bead_count ? `${p.bead_count} خرزة` : ''}
                          {p.bead_size_mm ? ` • ${p.bead_size_mm}mm` : ''}
                          {p.origin ? ` • ${p.origin}` : ''}
                        </p>
                      </td>

                      {/* MOQ */}
                      <td className="py-3 px-4 text-center">
                        <span className="inline-block px-2.5 py-1 bg-[#FAF4E8] text-[#9A6817] font-bold text-[11px] rounded-lg border border-[#EADBCE]">
                          {moq} قطع
                        </span>
                      </td>

                      {/* Stock Quantity */}
                      <td className="py-3 px-4 text-center">
                        {stock > 0 ? (
                          <span className="text-emerald-700 font-bold font-mono">
                            {stock.toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-rose-600 font-bold text-[10px]">نفد المخزون</span>
                        )}
                      </td>

                      {/* Retail Reference Price */}
                      <td className="py-3 px-4 text-[#8C8275] line-through text-[11px]">
                        {retailPrice.toLocaleString()} AED
                      </td>

                      {/* B2B Wholesale Price */}
                      <td className="py-3 px-4">
                        <div className="font-black text-[#9A6817] text-sm">
                          {wholesalePrice.toLocaleString()} <span className="text-[10px] text-[#746A5D]">AED</span>
                        </div>
                      </td>

                      {/* Quantity Input + Validation */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min={0}
                              max={stock}
                              value={quantities[p.id] ?? ''}
                              placeholder="0"
                              disabled={stock === 0}
                              onChange={e => handleQuantityChange(p, parseInt(e.target.value, 10))}
                              className={`w-20 px-2 py-1.5 text-center font-bold text-xs bg-[#FAF7F2] border rounded-xl focus:outline-none transition ${
                                isUnderMOQ || isOverStock
                                  ? 'border-rose-400 text-rose-700 bg-rose-50/50'
                                  : isValid
                                  ? 'border-emerald-500 text-emerald-800 bg-emerald-50/30'
                                  : 'border-[#DDD3C1] text-[#26221C]'
                              }`}
                            />

                            <button
                              type="button"
                              onClick={() => handleSetMOQ(p)}
                              title={`تعيين الحد الأدنى (${moq} قطع)`}
                              className="text-[10px] px-2 py-1.5 bg-[#FAF4E8] text-[#9A6817] hover:bg-[#F3E7CE] border border-[#E4D5B8] rounded-xl font-bold transition cursor-pointer"
                            >
                              MOQ
                            </button>
                          </div>

                          {isUnderMOQ && (
                            <span className="text-[9px] text-rose-600 font-bold flex items-center gap-0.5">
                              <AlertCircle className="w-2.5 h-2.5 shrink-0" />
                              <span>أقل من الحد الأدنى ({moq})</span>
                            </span>
                          )}
                          {isOverStock && (
                            <span className="text-[9px] text-rose-600 font-bold flex items-center gap-0.5">
                              <AlertCircle className="w-2.5 h-2.5 shrink-0" />
                              <span>يتجاوز المخزون ({stock})</span>
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Line Total */}
                      <td className="py-3 px-4 text-left font-black text-xs font-mono text-[#9A6817]">
                        {lineTotal > 0 ? `${lineTotal.toLocaleString()} AED` : '—'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Sticky Bottom Bulk Action Summary Bar */}
      <div className="fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur-md border-t border-[#EBE3D5] p-4 shadow-[0_-8px_25px_rgba(70,45,15,0.08)] z-40">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-5 text-xs text-[#4B4338]">
            <div className="flex items-center gap-2">
              <PackageCheck className="w-4 h-4 text-[#C9972B]" />
              <span>الأصناف المختارة: <strong>{validOrderItems.length}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span>إجمالي القطع: <strong>{totalUnits.toLocaleString()}</strong> حبة</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>قيمة طلبيّة الجملة:</span>
              <span className="text-xl font-black text-[#9A6817]">
                {totalWholesalePrice.toLocaleString()} <span className="text-xs font-bold text-[#746A5D]">AED</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              disabled={validOrderItems.length === 0}
              onClick={handleBulkSubmit}
              className={`flex-1 sm:flex-none px-5 py-2.5 rounded-xl text-xs font-black transition flex items-center justify-center gap-2 shadow-xs cursor-pointer ${
                addedAnimation
                  ? 'bg-emerald-600 text-white'
                  : 'bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border border-[#E4D5B8]'
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {addedAnimation ? <Check className="w-4 h-4" /> : <ShoppingCart className="w-4 h-4" />}
              <span>{addedAnimation ? 'تم الحفظ' : 'تأكيد الكميات'}</span>
            </button>

            <button
              type="button"
              disabled={validOrderItems.length === 0}
              onClick={() => onProceedToB2BCheckout(validOrderItems)}
              className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl text-xs font-black bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] shadow-md transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span>إصدار أمر الشراء (PO) والفاتورة</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
