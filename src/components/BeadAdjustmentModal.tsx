import React, { useState } from 'react';
import { Scissors, X, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';
import { Product } from '../types';
import { toast } from '../utils/toast';

interface BeadAdjustmentModalProps {
  product: Product | null;
  onClose: () => void;
  onSuccess: () => void;
  userName?: string;
}

export const BeadAdjustmentModal: React.FC<BeadAdjustmentModalProps> = ({ product, onClose, onSuccess, userName }) => {
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [requestedCount, setRequestedCount] = useState(33);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!product) return null;

  const originalCount = Number(product.bead_count || 33);
  const removedCount = Math.max(0, originalCount - requestedCount);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (requestedCount >= originalCount) {
      toast.warning('عدد الخرز المطلوب يجب أن يكون أقل من العدد الأصلي لتصغير المسبحة');
      return;
    }

    setSubmitting(true);
    try {
      await api.createBeadAdjustment({
        product_id: product.id,
        customer_name: customerName.trim() || 'عميل المحل',
        customer_phone: customerPhone.trim(),
        requested_bead_count: requestedCount,
        notes: notes.trim(),
        actor_name: userName || 'الفني'
      });
      toast.success(`تم إرسال أمر الورشة بنجاح وتجهيز كيس حفظ لعدد (${removedCount}) خرزات مفكوكة.`);
      onSuccess();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'حدث خطأ أثناء قيد أمر الورشة');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <Scissors className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#26221C]">ورشة تعديل قياس المسبحة (فك خرز)</h3>
              <p className="text-xs text-[#746A5D]">{product.name_ar}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Sizing Indicator */}
          <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] flex items-center justify-between text-center">
            <div>
              <p className="text-xs text-[#746A5D]">العدد الأصلي</p>
              <p className="text-2xl font-black text-[#26221C] mt-1">{originalCount}</p>
              <span className="text-[10px] text-[#8C8275]">خرزة</span>
            </div>

            <div className="text-[#C9972B] font-bold text-xl">←</div>

            <div>
              <p className="text-xs text-[#746A5D]">العدد المطلوب</p>
              <p className="text-2xl font-black text-[#9A6817] mt-1">{requestedCount}</p>
              <span className="text-[10px] text-[#9A6817]">خرزة</span>
            </div>

            <div className="text-[#C9972B] font-bold text-xl">=</div>

            <div>
              <p className="text-xs text-[#746A5D]">الخرز المفكوك المرفق</p>
              <p className="text-2xl font-black text-emerald-700 mt-1">{removedCount}</p>
              <span className="text-[10px] text-emerald-700">في كيس حفظ خاص</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1.5">
              حدد عدد الخرز الجديد بعد التعديل (خرزة) *
            </label>
            <input
              type="number"
              min="11"
              max={originalCount - 1}
              value={requestedCount}
              onChange={(e) => setRequestedCount(Number(e.target.value))}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#9A6817] font-bold focus:outline-none focus:border-[#C9972B]"
            />
            <p className="text-[11px] text-[#746A5D] mt-1">
              * سيتم تسليم الخرزات المفكوكة ({removedCount} خرزة) داخل كيس مخملي مخصص للعميل.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم العميل</label>
              <input
                type="text"
                placeholder="اسم العميل"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">هاتف العميل</label>
              <input
                type="text"
                placeholder="+97150..."
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">تعليمات إضافية للورشة والشاهد والكركوشة</label>
            <textarea
              rows={2}
              placeholder="مثال: ضبط الشاهد وإعادة ربط الخيط الحريري بإحكام"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
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
              disabled={submitting || requestedCount >= originalCount}
              className="px-4 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm disabled:opacity-50 cursor-pointer"
            >
              {submitting ? 'جار الإرسال...' : 'إصدار أمر الورشة'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
