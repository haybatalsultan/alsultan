import React, { useState, useEffect } from 'react';
import { Scissors, CheckCircle, Clock, PackageCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { BeadAdjustment } from '../types';
import { toast } from '../utils/toast';

export const WorkshopPage: React.FC = () => {
  const [adjustments, setAdjustments] = useState<BeadAdjustment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdjustments();
  }, []);

  const loadAdjustments = async () => {
    setLoading(true);
    try {
      const data = await api.getBeadAdjustments();
      setAdjustments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id: number, status: string) => {
    try {
      await api.updateBeadStatus(id, status, 'فني الورشة');
      toast.success('تم تحديث حالة الورشة بنجاح');
      await loadAdjustments();
    } catch (e: any) {
      toast.error(e.response?.data?.error || 'حدث خطأ أثناء تحديث حالة الورشة');
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
            <Scissors className="w-5 h-5 text-[#C9972B]" />
            <span>ورشة تعديل قياسات وخرز المسابيح</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            متابعة طلبات تفصيل وإنقاص خرز المسابيح، ضبط الشاهد، وتجهيز أكياس الحفظ للخرز المرفق.
          </p>
        </div>

        <button
          onClick={loadAdjustments}
          className="px-3.5 py-2 bg-white hover:bg-[#FAF4E8] text-[#4B4338] border border-[#E0D7C6] text-xs font-bold rounded-xl flex items-center gap-2 transition shadow-sm cursor-pointer"
        >
          <RefreshCw className="w-4 h-4 text-[#C9972B]" />
          <span>تحديث الطلبات ({adjustments.length})</span>
        </button>
      </div>

      {/* Adjustments Cards Grid */}
      {loading ? (
        <p className="text-xs text-[#746A5D] text-center py-16">جار تحميل أوامر الورشة...</p>
      ) : adjustments.length === 0 ? (
        <div className="p-12 rounded-3xl bg-white border border-dashed border-[#D8CCA8] text-center text-xs text-[#746A5D] space-y-2 shadow-sm">
          <Scissors className="w-10 h-10 text-[#C9972B]/50 mx-auto" />
          <p className="font-medium text-[#4B4338]">لا توجد طلبات تعديل خرز حالياً. يمكنك فتح طلب تعديل من صفحة المخزون.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {adjustments.map((adj) => {
            const isCompleted = adj.status === 'COMPLETED' || adj.status === 'DELIVERED';
            return (
              <div
                key={adj.id}
                className="p-5 rounded-3xl bg-white border border-[#EBE3D5] flex flex-col justify-between space-y-4 hover:border-[#C9972B] hover:shadow-[0_8px_24px_rgba(201,151,43,0.12)] transition shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between border-b border-[#F2ECE1] pb-3">
                    <span className="font-mono text-[10px] text-[#9A6817] bg-[#FAF4E8] px-2 py-0.5 rounded-full font-bold border border-[#EADBCE]">
                      {adj.product_reference}
                    </span>
                    <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${
                      isCompleted
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-amber-100 text-amber-800 border border-amber-300'
                    }`}>
                      {adj.status}
                    </span>
                  </div>

                  {/* Customer and rosary info */}
                  <div className="mt-3">
                    <h4 className="font-bold text-sm text-[#26221C]">{adj.customer_name}</h4>
                    <p className="text-xs text-[#746A5D]">{adj.customer_phone}</p>
                  </div>

                  {/* Bead count transformation badge */}
                  <div className="mt-3 p-3 rounded-xl bg-[#FAF7F2] border border-[#EEE4D4] flex items-center justify-between text-center">
                    <div>
                      <span className="text-[10px] text-[#8C8275] block">العدد الأصلي</span>
                      <span className="font-black text-[#26221C] text-sm">{adj.original_bead_count}</span>
                    </div>
                    <div className="text-[#C9972B] text-xs font-bold">←</div>
                    <div>
                      <span className="text-[10px] text-[#8C8275] block">العدد المطلوب</span>
                      <span className="font-black text-[#9A6817] text-sm">{adj.requested_bead_count}</span>
                    </div>
                    <div className="text-[#C9972B] text-xs font-bold">=</div>
                    <div>
                      <span className="text-[10px] text-[#8C8275] block">الخرز المفكوك</span>
                      <span className="font-black text-emerald-700 text-sm">{adj.removed_beads_count} خرزة</span>
                    </div>
                  </div>

                  {/* Velvet bag verification pill */}
                  <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-800 bg-emerald-50 p-2.5 rounded-xl border border-emerald-200">
                    <PackageCheck className="w-4 h-4 shrink-0 text-emerald-600" />
                    <span>تم توثيق كيس مخملي لحفظ الخرز المفكوك ({adj.removed_beads_count})</span>
                  </div>

                  {adj.notes && (
                    <p className="mt-2 text-xs text-[#746A5D] bg-[#FAF7F2] p-2 rounded-lg border border-[#EEE4D4]">
                      ملاحظات: {adj.notes}
                    </p>
                  )}
                </div>

                {/* Status action buttons */}
                <div className="pt-3 border-t border-[#F2ECE1] flex items-center justify-between">
                  <span className="text-[10px] text-[#8C8275]">{adj.created_at}</span>
                  <div className="flex items-center gap-1.5">
                    {adj.status === 'PENDING' && (
                      <button
                        onClick={() => updateStatus(adj.id, 'IN_WORKSHOP')}
                        className="px-3 py-1 bg-[#FAF4E8] hover:bg-[#C9972B] text-[#9A6817] hover:text-white font-bold text-xs rounded-xl transition border border-[#EADBCE] cursor-pointer"
                      >
                        بدء العمل في الورشة
                      </button>
                    )}
                    {adj.status === 'IN_WORKSHOP' && (
                      <button
                        onClick={() => updateStatus(adj.id, 'COMPLETED')}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
                      >
                        اكتمال التعديل والتجهيز
                      </button>
                    )}
                    {adj.status === 'COMPLETED' && (
                      <button
                        onClick={() => updateStatus(adj.id, 'DELIVERED')}
                        className="px-3 py-1 bg-white hover:bg-[#FAF4E8] text-[#4B4338] font-bold text-xs rounded-xl border border-[#E0D7C6] transition cursor-pointer"
                      >
                        تم التسليم للعميل
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
