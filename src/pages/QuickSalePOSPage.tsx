import React, { useState, useEffect } from 'react';
import { ShoppingBag, Search, Barcode, CheckCircle, Clock, Banknote, CreditCard, ArrowRight, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';
import { Product, PaymentMethod, User } from '../types';
import { hasPermission } from '../lib/permissions';

interface QuickSalePOSPageProps {
  onSaleComplete: (order: any) => void;
  userName?: string;
  currentUser?: User;
}

export const QuickSalePOSPage: React.FC<QuickSalePOSPageProps> = ({ onSaleComplete, userName, currentUser }) => {
  const canDiscount = hasPermission(currentUser, 'pos.discount');
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('CASH');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [specialDiscount, setSpecialDiscount] = useState(0);
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAvailableProducts();
  }, []);

  const loadAvailableProducts = async () => {
    setLoading(true);
    try {
      const data = await api.getProducts({ status: 'AVAILABLE' });
      setProducts(data);
      if (data.length > 0 && !selectedProduct) {
        setSelectedProduct(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(p =>
    p.name_ar.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase()) ||
    p.product_reference.toLowerCase().includes(search.toLowerCase()) ||
    (p.origin && p.origin.toLowerCase().includes(search.toLowerCase()))
  );

  const basePrice = Number(selectedProduct?.selling_price || 0);
  const discount = Number(specialDiscount || 0);
  const grandTotal = Math.max(0, basePrice - discount);

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProduct) {
      alert('يرجى اختيار مسبحة للبيع');
      return;
    }
    if (discount >= basePrice) {
      alert('قيمة الخصم يجب أن تكون أقل من سعر البيع');
      return;
    }
    if (paymentMethod === 'DEFERRED' && !dueDate) {
      alert('يرجى تحديد تاريخ استحقاق السداد الآجل');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.quickSale({
        product_id: selectedProduct.id,
        customer_name: customerName.trim() || 'عميل المعرض',
        customer_phone: customerPhone.trim(),
        payment_method: paymentMethod,
        special_discount: discount,
        payment_due_date: paymentMethod === 'DEFERRED' ? dueDate : null,
        notes: notes.trim(),
        actor_name: userName || 'الكاشير'
      });

      alert(`✅ تم إتمام البيع بنجاح وتوثيق الفاتورة رقم: ${res.order.reference}`);
      const orderToEmit = {
        ...res.order,
        items: (res.order?.items && res.order.items.length > 0) ? res.order.items : [{
          id: selectedProduct.id,
          product_id: selectedProduct.id,
          name_ar: selectedProduct.name_ar,
          sku: selectedProduct.sku,
          unit_price: Number(selectedProduct.selling_price),
          line_total: grandTotal,
          quantity: 1,
          requested_bead_count: isCustomBeads ? customBeadCount : undefined
        }]
      };
      onSaleComplete(orderToEmit);

      // Reload products list to exclude sold item
      setSelectedProduct(null);
      setCustomerName('');
      setCustomerPhone('');
      setSpecialDiscount(0);
      setNotes('');
      await loadAvailableProducts();
    } catch (err: any) {
      alert(err.response?.data?.error || 'فشلت عملية البيع - تأكد من حصرية القطعة وتوفرها');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col lg:flex-row overflow-hidden bg-[#FAF7F2] text-[#26221C]">
      {/* Left side: Available Products Grid & Barcode Search */}
      <div className="flex-1 flex flex-col border-l border-[#EBE3D5] p-6 overflow-hidden">
        {/* Search & Barcode Bar */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3" />
            <input
              type="text"
              placeholder="ابحث باسم المسبحة، الـ SKU، الباركود، الخامة، أو المنشأ..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white border border-[#E0D7C6] rounded-xl pr-10 pl-4 py-2.5 text-xs sm:text-sm text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B] shadow-sm"
            />
          </div>
          <button
            onClick={() => loadAvailableProducts()}
            className="px-4 py-2.5 bg-white hover:bg-[#FAF4E8] border border-[#E0D7C6] text-[#4B4338] text-xs font-bold rounded-xl flex items-center gap-2 transition shadow-sm"
          >
            <Barcode className="w-4 h-4 text-[#C9972B]" />
            <span>تحديث ({filteredProducts.length})</span>
          </button>
        </div>

        {/* Products Grid */}
        <div className="flex-1 overflow-y-auto pr-1">
          {loading ? (
            <p className="text-center text-xs text-[#746A5D] py-12">جار تحميل المسابيح المتاحة...</p>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-16 text-[#746A5D]">
              <ShoppingBag className="w-10 h-10 mx-auto mb-2 text-[#C9972B]/50" />
              <p className="text-sm font-bold text-[#4B4338]">لا توجد مسابيح متاحة مطابقة للبحث</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3.5">
              {filteredProducts.map((p) => {
                const isSelected = selectedProduct?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProduct(p)}
                    className={`p-3.5 rounded-2xl border transition cursor-pointer select-none flex flex-col justify-between ${
                      isSelected
                        ? 'bg-[#FAF4E8] border-[#C9972B] shadow-md ring-1 ring-[#C9972B]'
                        : 'bg-white border-[#EBE3D5] hover:border-[#D5C7B0] shadow-sm'
                    }`}
                  >
                    <div>
                      <div className="flex items-start gap-3">
                        <img
                          src={p.image_url || '/branding/hero-amber.jpg'}
                          alt=""
                          className="w-14 h-14 object-cover rounded-xl border border-[#E0D7C6]"
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-[10px] font-mono font-bold text-[#9A6817] bg-[#FAF4E8] border border-[#EADBCE] px-1.5 py-0.5 rounded">
                            {p.sku}
                          </span>
                          <h4 className="font-bold text-xs text-[#26221C] mt-1 line-clamp-2 leading-tight">
                            {p.name_ar}
                          </h4>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-[10px] text-[#746A5D] mt-2.5 pt-2 border-t border-[#F2ECE1]">
                        <span>{p.bead_count} خرزة</span>
                        <span>•</span>
                        <span>{p.bead_size_mm}mm</span>
                        <span>•</span>
                        <span>{p.weight_g}g</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#F2ECE1]">
                      <span className="font-black text-[#9A6817] text-sm">{p.selling_price.toLocaleString()} AED</span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        قطعة فريدة
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right side: POS Checkout Terminal */}
      <div className="w-full lg:w-96 bg-white border-t lg:border-t-0 border-[#EBE3D5] p-6 flex flex-col justify-between overflow-y-auto shadow-sm">
        <form onSubmit={handleCheckout} className="space-y-4">
          <div className="flex items-center justify-between border-b border-[#EBE3D5] pb-3">
            <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-[#C9972B]" />
              <span>إتمام البيع الفوري (POS)</span>
            </h3>
            <span className="text-[10px] text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              حماية الحصرية نشطة
            </span>
          </div>

          {/* Selected Item Summary */}
          {selectedProduct ? (
            <div className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EBE3D5]">
              <div className="flex items-center gap-3">
                <img
                  src={selectedProduct.image_url || '/branding/hero-amber.jpg'}
                  alt=""
                  className="w-12 h-12 object-cover rounded-lg border border-[#E0D7C6]"
                />
                <div className="flex-1 min-w-0">
                  <span className="text-[10px] font-mono text-[#9A6817] font-bold">{selectedProduct.sku}</span>
                  <h4 className="font-bold text-xs text-[#26221C] truncate">{selectedProduct.name_ar}</h4>
                  <p className="text-[11px] text-[#9A6817] font-bold mt-0.5">{selectedProduct.selling_price.toLocaleString()} AED</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-[#FAF7F2] border border-dashed border-[#D8CCA8] text-center text-xs text-[#746A5D]">
              اختر مسبحة من القائمة للبدء بعملية البيع
            </div>
          )}

          {/* Payment Methods */}
          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1.5">طريقة الدفع *</label>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                { id: 'CASH', label: 'نقداً / كاش', icon: Banknote },
                { id: 'POS', label: 'بطاقة / شبكة', icon: CreditCard },
                { id: 'BANK_TRANSFER', label: 'تحويل بنكي', icon: CheckCircle },
                { id: 'DEFERRED', label: 'آجل (على الحساب)', icon: Clock }
              ].map((m) => {
                const Icon = m.icon;
                const isSelected = paymentMethod === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setPaymentMethod(m.id as PaymentMethod)}
                    className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-bold transition ${
                      isSelected
                        ? 'bg-[#FAF4E8] text-[#9A6817] border-[#C9972B] shadow-sm'
                        : 'bg-[#FAF7F2] text-[#4B4338] border-[#E0D7C6] hover:bg-[#F2ECE1]'
                    }`}
                  >
                    <Icon className="w-4 h-4 text-[#C9972B]" />
                    <span>{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Deferred Date Picker */}
          {paymentMethod === 'DEFERRED' && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-xs text-amber-900 space-y-1.5">
              <label className="block text-[11px] font-bold text-amber-900">تاريخ استحقاق السداد الآجل *</label>
              <input
                type="date"
                required
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full bg-white border border-amber-300 rounded px-2.5 py-1.5 text-xs text-[#26221C]"
              />
            </div>
          )}

          {/* Customer fields */}
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم المشتري / العميل</label>
              <input
                type="text"
                placeholder="عميل المعرض المباشر"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-lg px-3 py-1.5 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف</label>
              <input
                type="text"
                placeholder="+97150..."
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-lg px-3 py-1.5 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          {/* Discount & Totals */}
          <div className="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EBE3D5] space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[#746A5D]">سعر المسبحة:</span>
              <span className="text-[#26221C] font-bold">{basePrice.toLocaleString()} AED</span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center gap-1">
                <span className="text-[#746A5D]">خصم خاص (AED):</span>
                {!canDiscount && <span className="text-[10px] text-[#A89E90]">(مقتصر على المشرف)</span>}
              </div>
              <input
                type="number"
                disabled={!canDiscount}
                min="0"
                max={basePrice}
                value={specialDiscount}
                onChange={(e) => setSpecialDiscount(Number(e.target.value))}
                className="w-24 bg-white border border-[#D8CCA8] rounded px-2 py-1 text-left text-xs font-bold text-rose-600 disabled:bg-[#F0E8DC]/50 disabled:cursor-not-allowed"
                title={!canDiscount ? 'ليس لديك صلاحية منح خصومات إضافية' : 'تطبيق خصم مخصص'}
              />
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-[#EBE3D5] text-sm">
              <span className="font-bold text-[#26221C]">الإجمالي الصافي:</span>
              <span className="font-black text-[#9A6817] text-lg">{grandTotal.toLocaleString()} AED</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={!selectedProduct || submitting}
            className="w-full py-3 bg-[#C9972B] hover:bg-[#B8851E] text-white font-black text-sm rounded-xl transition shadow-[0_4px_14px_rgba(201,151,43,0.3)] disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>{submitting ? 'جار التنفيذ الذري...' : 'تأكيد وإتمام البيع الآن'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
