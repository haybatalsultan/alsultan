import React, { useState } from 'react';
import { ShoppingBag, X, Check, CreditCard, Banknote, Clock, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import { Product, PaymentMethod } from '../types';

interface QuickSaleModalProps {
  product: Product | null;
  onClose: () => void;
  onSuccess: (order: any) => void;
  userName?: string;
}

export const QuickSaleModal: React.FC<QuickSaleModalProps> = ({ product, onClose, onSuccess, userName }) => {
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('CASH');
  const [specialDiscount, setSpecialDiscount] = useState(0);
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!product) return null;

  const basePrice = Number(product.selling_price);
  const discount = Number(specialDiscount || 0);
  const grandTotal = Math.max(0, basePrice - discount);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (discount >= basePrice) {
      alert('قيمة الخصم يجب أن تكون أقل من سعر البيع');
      return;
    }
    if (paymentMethod === 'DEFERRED' && !dueDate) {
      alert('يرجى تحديد تاريخ استحقاق الدفع الآجل');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.quickSale({
        product_id: product.id,
        customer_name: customerName.trim() || 'عميل المعرض',
        customer_phone: customerPhone.trim(),
        payment_method: paymentMethod,
        special_discount: discount,
        payment_due_date: paymentMethod === 'DEFERRED' ? dueDate : null,
        notes: notes.trim(),
        actor_name: userName || 'الكاشير'
      });

      alert(`✅ تم إتمام البيع بنجاح وتوثيق الفاتورة رقم: ${res.order.reference}`);
      onSuccess(res.order);
      onClose();
    } catch (err: any) {
      alert(err.response?.data?.error || 'فشلت عملية البيع - تأكد من توفر القطعة');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#26221C]">البيع السريع ونقطة البيع (Exhibition POS)</h3>
              <p className="text-xs text-[#746A5D] font-mono">{product.sku} | {product.product_reference}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Item details banner */}
          <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img
                src={product.image_url || '/branding/hero-amber.jpg'}
                alt=""
                className="w-12 h-12 object-cover rounded-xl border border-[#E0D7C6]"
              />
              <div>
                <h4 className="font-bold text-sm text-[#26221C]">{product.name_ar}</h4>
                <p className="text-xs text-[#746A5D]">{product.color} | {product.bead_count} خرزة | {product.weight_g}g</p>
              </div>
            </div>
            <div className="text-left">
              <span className="text-xs text-[#746A5D]">سعر البيع</span>
              <p className="text-lg font-black text-[#9A6817]">{basePrice.toLocaleString()} AED</p>
            </div>
          </div>

          {/* Payment Method Selector */}
          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-2">طريقة الدفع *</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { id: 'CASH', label: 'نقداً / كاش', icon: Banknote },
                { id: 'POS', label: 'شبكة / بطاقة', icon: CreditCard },
                { id: 'BANK_TRANSFER', label: 'تحويل بنكي', icon: Check },
                { id: 'DEFERRED', label: 'آجل (على الحساب)', icon: Clock }
              ].map((m) => {
                const Icon = m.icon;
                const isSelected = paymentMethod === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setPaymentMethod(m.id as PaymentMethod)}
                    className={`flex flex-col items-center justify-center p-3 rounded-2xl border text-xs font-bold transition cursor-pointer ${
                      isSelected
                        ? 'bg-[#FAF4E8] text-[#9A6817] border-[#C9972B] shadow-sm'
                        : 'bg-[#FAF7F2] text-[#4B4338] border-[#E0D7C6] hover:bg-[#F2ECE1]'
                    }`}
                  >
                    <Icon className="w-5 h-5 mb-1 text-[#C9972B]" />
                    <span>{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Deferred Payment date notice */}
          {paymentMethod === 'DEFERRED' && (
            <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-300 text-xs text-amber-900 space-y-2">
              <p className="font-bold flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-[#C9972B]" />
                تنبيه: سيتم تسجيل هذا الطلب كـ "مستحق آجل" في المحاسب الذكي
              </p>
              <div>
                <label className="block text-[11px] font-bold text-amber-900 mb-1">تاريخ استحقاق السداد *</label>
                <input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="bg-white border border-amber-300 rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
            </div>
          )}

          {/* Pricing & Discounts */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">خصم خاص (درهم)</label>
              <input
                type="number"
                min="0"
                max={basePrice - 1}
                value={specialDiscount}
                onChange={(e) => setSpecialDiscount(Number(e.target.value))}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">صافي الإجمالي المستحق</label>
              <div className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-base font-black text-[#9A6817]">
                {grandTotal.toLocaleString()} AED
              </div>
            </div>
          </div>

          {/* Customer details */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم العميل</label>
              <input
                type="text"
                placeholder="عميل مباشر"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف</label>
              <input
                type="text"
                placeholder="+97150..."
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[#F2ECE1]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-semibold rounded-xl transition cursor-pointer"
            >
              إلغاء
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-sm rounded-xl transition shadow-[0_4px_14px_rgba(201,151,43,0.3)] disabled:opacity-50 flex items-center gap-2 cursor-pointer"
            >
              <span>{submitting ? 'جار المعالجة الذرية...' : 'إتمام البيع الفوري'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
