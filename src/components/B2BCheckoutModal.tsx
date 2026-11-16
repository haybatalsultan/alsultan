import React, { useState } from 'react';
import {
  Building2,
  X,
  Check,
  Truck,
  CreditCard,
  Banknote,
  ShieldCheck,
  FileCheck2,
  AlertCircle
} from 'lucide-react';
import { api } from '../lib/api';
import { B2BQuickOrderItem } from './B2BQuickOrderTable';

interface B2BCheckoutModalProps {
  items: B2BQuickOrderItem[];
  customerUser: any;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (order: any) => void;
}

export const B2BCheckoutModal: React.FC<B2BCheckoutModalProps> = ({
  items,
  customerUser,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [companyName, setCompanyName] = useState(customerUser?.company_name || '');
  const [commercialRegister, setCommercialRegister] = useState(customerUser?.commercial_register || '');
  const [taxId, setTaxId] = useState(customerUser?.tax_id || '');
  const [contactName, setContactName] = useState(customerUser?.full_name || '');
  const [phone, setPhone] = useState(customerUser?.phone || '');
  const [email, setEmail] = useState(customerUser?.email || '');
  const [city, setCity] = useState('أبوظبي');
  const [shippingAddress, setShippingAddress] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<'BANK_TRANSFER' | 'CHEQUE' | 'CREDIT_TERMS'>('BANK_TRANSFER');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen || items.length === 0) return null;

  const totalUnits = items.reduce((acc, curr) => acc + curr.quantity, 0);
  const totalAmount = items.reduce((acc, curr) => {
    const price = curr.product.price_b2b || (curr.product.selling_price * 0.70);
    return acc + price * curr.quantity;
  }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!companyName.trim() || !contactName.trim() || !phone.trim()) {
      setErrorMsg('يرجى استيفاء بيانات المنشأة واسم المفوض ورقم الهاتف.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        items: items.map(i => ({
          product_id: i.product.id,
          quantity: i.quantity
        })),
        company_name: companyName.trim(),
        commercial_register: commercialRegister.trim(),
        tax_id: taxId.trim(),
        contact_name: contactName.trim(),
        phone: phone.trim(),
        email: email.trim(),
        shipping_address: shippingAddress.trim() || 'المقر التجاري للمنشأة',
        city,
        payment_method: paymentMethod,
        notes: notes.trim()
      };

      const res = await api.b2bCheckout(payload);
      onSuccess(res.order);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error || 'تعذر إصدار أمر الشراء. يرجى المحاولة لاحقاً.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" dir="rtl">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 font-sans">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#FAF4E8] via-[#FFFDF8] to-[#F5ECE0] p-6 border-b border-[#EBE3D5] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center shadow-md">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-black text-[#26221C]">
                إصدار أمر شراء الجملة (Purchase Order)
              </h2>
              <p className="text-xs text-[#746A5D]">
                فواتير تجارية رسمية، تتبع الشحن اللوجستي، وطرق دفع مخصصة للشركات
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white hover:bg-rose-50 text-[#8C8275] hover:text-rose-600 flex items-center justify-center transition border border-[#EADBCE] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto flex-1">
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Order Summary Box */}
          <div className="p-4 bg-[#FAF7F2] rounded-2xl border border-[#EEE4D4] space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#746A5D]">عدد الأصناف المختارة:</span>
              <span className="font-bold text-[#26221C]">{items.length} أصناف</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#746A5D]">إجمالي عدد القطع:</span>
              <span className="font-bold text-[#26221C]">{totalUnits.toLocaleString()} حبة</span>
            </div>
            <div className="flex items-center justify-between text-sm pt-2 border-t border-[#E8DEC8]">
              <span className="font-black text-[#26221C]">إجمالي قيمة أمر الشراء (B2B):</span>
              <span className="font-black text-lg text-[#9A6817]">
                {totalAmount.toLocaleString()} <span className="text-xs text-[#746A5D]">AED</span>
              </span>
            </div>
          </div>

          {/* Company & Legal Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-black text-[#9A6817] flex items-center gap-1.5 pb-1 border-b border-[#F2ECE1]">
              <Building2 className="w-4 h-4 text-[#C9972B]" />
              <span>بيانات المنشأة التجارية</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-[#4B4338] mb-1">
                  اسم الشركة / المنشأة <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={e => setCompanyName(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#4B4338] mb-1">
                  السجل التجاري (CR)
                </label>
                <input
                  type="text"
                  value={commercialRegister}
                  onChange={e => setCommercialRegister(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#4B4338] mb-1">
                  اسم المفوض بالاستلام <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={contactName}
                  onChange={e => setContactName(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#4B4338] mb-1">
                  رقم الهاتف / الواتساب <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-[#4B4338] mb-1">
                  عنوان التسليم / المستودع
                </label>
                <input
                  type="text"
                  value={shippingAddress}
                  onChange={e => setShippingAddress(e.target.value)}
                  placeholder="مثال: دبي - منطقة القوز الصناعية - مستودع رقم 4"
                  className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                />
              </div>
            </div>
          </div>

          {/* B2B Payment Methods */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-black text-[#9A6817] flex items-center gap-1.5 pb-1 border-b border-[#F2ECE1]">
              <Banknote className="w-4 h-4 text-[#C9972B]" />
              <span>طريقة الدفع التجاري المعتمدة</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <label
                className={`p-3 rounded-2xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-1.5 ${
                  paymentMethod === 'BANK_TRANSFER'
                    ? 'border-[#C9972B] bg-[#FAF4E8] text-[#9A6817] font-bold shadow-xs'
                    : 'border-[#EBE3D5] bg-white text-[#746A5D] hover:bg-[#FAF7F2]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Banknote className="w-4 h-4 text-[#C9972B]" />
                  <input
                    type="radio"
                    name="b2b_payment"
                    checked={paymentMethod === 'BANK_TRANSFER'}
                    onChange={() => setPaymentMethod('BANK_TRANSFER')}
                    className="text-[#C9972B] focus:ring-[#C9972B]"
                  />
                </div>
                <span className="font-extrabold">تحويل بنكي رسمي</span>
                <span className="text-[10px] text-[#8C8275] leading-tight">إيداع مباشر في حساب الشركة</span>
              </label>

              <label
                className={`p-3 rounded-2xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-1.5 ${
                  paymentMethod === 'CHEQUE'
                    ? 'border-[#C9972B] bg-[#FAF4E8] text-[#9A6817] font-bold shadow-xs'
                    : 'border-[#EBE3D5] bg-white text-[#746A5D] hover:bg-[#FAF7F2]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <CreditCard className="w-4 h-4 text-[#C9972B]" />
                  <input
                    type="radio"
                    name="b2b_payment"
                    checked={paymentMethod === 'CHEQUE'}
                    onChange={() => setPaymentMethod('CHEQUE')}
                    className="text-[#C9972B] focus:ring-[#C9972B]"
                  />
                </div>
                <span className="font-extrabold">شيك مصرفي</span>
                <span className="text-[10px] text-[#8C8275] leading-tight">شيك بنكي معتمد عند التسليم</span>
              </label>

              <label
                className={`p-3 rounded-2xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-1.5 ${
                  paymentMethod === 'CREDIT_TERMS'
                    ? 'border-[#C9972B] bg-[#FAF4E8] text-[#9A6817] font-bold shadow-xs'
                    : 'border-[#EBE3D5] bg-white text-[#746A5D] hover:bg-[#FAF7F2]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <ShieldCheck className="w-4 h-4 text-[#C9972B]" />
                  <input
                    type="radio"
                    name="b2b_payment"
                    checked={paymentMethod === 'CREDIT_TERMS'}
                    onChange={() => setPaymentMethod('CREDIT_TERMS')}
                    className="text-[#C9972B] focus:ring-[#C9972B]"
                  />
                </div>
                <span className="font-extrabold">آجل Net 30</span>
                <span className="text-[10px] text-[#8C8275] leading-tight">تسهيلات ائتمانية للتجار المعتمدين</span>
              </label>
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs font-bold text-[#4B4338] mb-1">
              ملاحظات أو تعليمات الشحن
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="تعليمات إضافية بخصوص فحص البضاعة، مواعيد الاستلام..."
              className="w-full px-3.5 py-2 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
            />
          </div>

          {/* Submit */}
          <div className="pt-3 border-t border-[#F0E8DC]">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] font-black rounded-xl text-xs transition shadow-md disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#E2B84B] border-t-transparent rounded-full animate-spin" />
                  <span>جارٍ تسجيل أمر الشراء اللوجستي...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>تأكيد وإصدار أمر الشراء الرسمي</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
