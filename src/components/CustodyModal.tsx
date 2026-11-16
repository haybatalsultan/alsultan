import React, { useState, useEffect } from 'react';
import { ShieldCheck, X, Plus, Calendar, MapPin, User, FileText } from 'lucide-react';
import { api } from '../lib/api';
import { Product, CustodyRecord } from '../types';

interface CustodyModalProps {
  product: Product | null;
  onClose: () => void;
  onSuccess: () => void;
  userName?: string;
}

export const CustodyModal: React.FC<CustodyModalProps> = ({ product, onClose, onSuccess, userName }) => {
  const [history, setHistory] = useState<CustodyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [holderName, setHolderName] = useState('');
  const [locationName, setLocationName] = useState('معرض الصيد والفروسية');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (product) {
      loadHistory();
    }
  }, [product]);

  const loadHistory = async () => {
    if (!product) return;
    setLoading(true);
    try {
      const data = await api.getCustody(product.id);
      setHistory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product || !holderName.trim()) return;

    setSubmitting(true);
    try {
      await api.assignCustody(product.id, {
        holder_name: holderName.trim(),
        location_name: locationName.trim(),
        note: note.trim(),
        actor_name: userName || 'المشرف'
      });
      setHolderName('');
      setNote('');
      await loadHistory();
      onSuccess();
    } catch (err: any) {
      alert(err.response?.data?.error || 'حدث خطأ أثناء قيد العهدة');
    } finally {
      setSubmitting(false);
    }
  };

  if (!product) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#26221C]">سجل عهدة وحيازة المسبحة</h3>
              <p className="text-xs text-[#746A5D] font-mono">{product.sku} | {product.product_reference}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Product Summary */}
          <div className="p-3.5 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] flex items-center gap-4">
            <img
              src={product.image_url || '/branding/hero-amber.jpg'}
              alt=""
              className="w-14 h-14 object-cover rounded-xl border border-[#E0D7C6]"
            />
            <div>
              <h4 className="font-bold text-sm text-[#9A6817]">{product.name_ar}</h4>
              <p className="text-xs text-[#746A5D] mt-0.5">
                الخامة: {product.origin || 'أصلية'} | عدد الخرز: {product.bead_count} | السعر: {product.selling_price.toLocaleString()} AED
              </p>
            </div>
          </div>

          {/* New Handover Form */}
          <form onSubmit={handleAssign} className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] space-y-4">
            <h4 className="text-xs font-bold text-[#26221C] uppercase tracking-wider flex items-center gap-2">
              <Plus className="w-4 h-4 text-[#C9972B]" />
              تسليم عهدة جديد (إيداع أو نقل للمعاينة)
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم الحائز / المستلم *</label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="مثال: سعيد الهاجري / مندوب المعرض"
                    value={holderName}
                    onChange={(e) => setHolderName(e.target.value)}
                    className="w-full bg-white border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-sm text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">مكان الحيازة / الموقع *</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="مثال: المعرض، الخزنة الرئيسية، جناح VIP"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    className="w-full bg-white border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-sm text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">ملاحظات العهدة والتسليم</label>
              <input
                type="text"
                placeholder="مثال: تسليم باليد لعميل مميز للمعاينة مع الالتزام بالإرجاع"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="w-full bg-white border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
              />
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {submitting ? 'جار الحفظ...' : 'تثبيت حركة العهدة في السجل'}
              </button>
            </div>
          </form>

          {/* Historical Audit Trail */}
          <div>
            <h4 className="text-xs font-bold text-[#746A5D] uppercase tracking-wider mb-3">
              السجل التاريخي غير القابل للتعديل ({history.length})
            </h4>

            {loading ? (
              <p className="text-xs text-[#746A5D] text-center py-4">جار تحميل السجل...</p>
            ) : history.length === 0 ? (
              <p className="text-xs text-[#746A5D] text-center py-4 bg-[#FAF7F2] rounded-xl border border-dashed border-[#D8CCA8]">
                لا توجد حركات عهدة سابقة لهذه المسبحة.
              </p>
            ) : (
              <div className="space-y-2.5">
                {history.map((item) => (
                  <div key={item.id} className="p-3 rounded-xl bg-[#FAF7F2] border border-[#EEE6D8] flex items-start justify-between text-xs">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#26221C]">{item.holder_name}</span>
                        <span className="px-2 py-0.5 rounded-full bg-[#FAF4E8] text-[#9A6817] text-[10px] font-bold border border-[#EADBCE]">
                          {item.location_name}
                        </span>
                      </div>
                      {item.note && <p className="text-[#746A5D] mt-1">{item.note}</p>}
                      <p className="text-[10px] text-[#8C8275] mt-1 flex items-center gap-2">
                        <span>المسجل: {item.recorded_by_name}</span>
                        <span>•</span>
                        <span>{item.created_at}</span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
