import React, { useState, useEffect } from 'react';
import { ShieldCheck, MapPin, User, Calendar, Plus, Search, Gem, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import { Product } from '../types';

interface CustodyPageProps {
  onOpenCustodyModal: (product: Product) => void;
}

export const CustodyPage: React.FC<CustodyPageProps> = ({ onOpenCustodyModal }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustodyItems();
  }, []);

  const loadCustodyItems = async () => {
    setLoading(true);
    try {
      const data = await api.getProducts();
      setProducts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const custodyProducts = products.filter(p => p.status === 'IN_CUSTODY');
  const availableProducts = products.filter(p => p.status === 'AVAILABLE');

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <span>سجل العهدة وتتبع حيازة المسابيح النادرة</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            سجل رقابي غير قابل للتعديل (Append-Only) لحفظ أماكن المسابيح، الخزائن، والمعارض والمندوبين.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#4B4338] bg-white border border-[#EBE3D5] px-4 py-2 rounded-xl shadow-sm">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-bold">{custodyProducts.length} مسابيح قيد الحيازة الميدانية</span>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Custody Items (Left 2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-bold text-sm text-[#26221C]">المسابيح المسلمة بعهدة نشطة حالياً ({custodyProducts.length})</h3>

          {loading ? (
            <p className="text-xs text-[#746A5D] text-center py-12">جار تحميل سجلات العهدة...</p>
          ) : custodyProducts.length === 0 ? (
            <div className="p-8 rounded-3xl bg-white border border-dashed border-[#D8CCA8] text-center text-xs text-[#746A5D] space-y-2 shadow-sm">
              <ShieldCheck className="w-8 h-8 text-[#C9972B]/50 mx-auto" />
              <p className="font-medium text-[#4B4338]">لا توجد مسابيح مودعة بالعهدة حالياً. كافة المسابيح متاحة بالمعرض المركزي.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {custodyProducts.map((p) => (
                <div
                  key={p.id}
                  className="p-4 rounded-2xl bg-white border border-[#EBE3D5] flex items-center justify-between hover:border-[#C9972B] transition shadow-sm"
                >
                  <div className="flex items-center gap-4">
                    <img
                      src={p.image_url || '/branding/hero-amber.jpg'}
                      alt=""
                      className="w-14 h-14 object-cover rounded-xl border border-[#E0D7C6]"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] text-[#9A6817] bg-[#FAF4E8] border border-[#EADBCE] px-1.5 py-0.5 rounded font-bold">
                          {p.sku}
                        </span>
                        <span className="text-xs font-bold text-[#26221C]">{p.name_ar}</span>
                      </div>
                      <p className="text-[11px] text-[#746A5D] mt-1">
                        الخامة: {p.origin} | السعر: {p.selling_price.toLocaleString()} AED | {p.bead_count} خرزة
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => onOpenCustodyModal(p)}
                    className="px-3.5 py-1.5 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#4B4338] text-xs font-bold rounded-xl border border-[#E0D7C6] transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>عرض السجل وتحديث العهدة</span>
                    <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Rosaries to Handover (Right 1 col) */}
        <div className="bg-white border border-[#EBE3D5] rounded-3xl p-5 space-y-4 shadow-sm">
          <div>
            <h3 className="font-bold text-sm text-[#26221C]">تسليم مسبحة جديدة للعهدة</h3>
            <p className="text-xs text-[#746A5D] mt-0.5">اختر قطعة متاحة لتسليمها لمندوب أو خزانة</p>
          </div>

          <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
            {availableProducts.slice(0, 10).map((p) => (
              <div
                key={p.id}
                className="p-3 rounded-xl bg-[#FAF7F2] border border-[#EEE6D8] flex items-center justify-between text-xs hover:border-[#C9972B] transition"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <span className="font-mono text-[10px] font-bold text-[#9A6817]">{p.sku}</span>
                  <span className="font-medium text-[#26221C] truncate">{p.name_ar}</span>
                </div>
                <button
                  onClick={() => onOpenCustodyModal(p)}
                  className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-600 text-emerald-700 hover:text-white font-bold text-[11px] rounded-lg transition border border-emerald-300 shrink-0 cursor-pointer"
                >
                  تسليم عهدة
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
