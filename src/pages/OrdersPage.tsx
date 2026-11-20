import React, { useState, useEffect } from 'react';
import { Receipt, Search, Eye, Printer, Clock, CheckCircle2, ArrowRight, MapPin } from 'lucide-react';
import { api } from '../lib/api';
import { Order } from '../types';

interface OrdersPageProps {
  onViewInvoice: (order: Order) => void;
}

export const OrdersPage: React.FC<OrdersPageProps> = ({ onViewInvoice }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await api.getOrders();
      setOrders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filtered = orders.filter(o => {
    const matchesSearch =
      o.reference.toLowerCase().includes(search.toLowerCase()) ||
      o.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      o.customer_phone.toLowerCase().includes(search.toLowerCase());

    const matchesPayment = paymentFilter === 'ALL' || o.payment_status === paymentFilter;
    return matchesSearch && matchesPayment;
  });

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
            <Receipt className="w-5 h-5 text-[#C9972B]" />
            <span>سجلات المبيعات والفواتير الموثقة</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            أرشيف العمليات المباشرة والإلكترونية، تتبع الحجوزات، وطباعة الفواتير بباركود QR.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white border border-[#EBE3D5] flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-2.5" />
          <input
            type="text"
            placeholder="ابحث برقم الفاتورة، اسم المشتري، أو الهاتف..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#FAF7F2] border border-[#E0D7C6] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
          />
        </div>

        <select
          value={paymentFilter}
          onChange={(e) => setPaymentFilter(e.target.value)}
          className="bg-[#FAF7F2] border border-[#E0D7C6] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
        >
          <option value="ALL">كافة حالات الدفع</option>
          <option value="PAID">مدفوع بالكامل</option>
          <option value="PARTIALLY_PAID">مدفوع جزئياً</option>
          <option value="UNPAID">آجل غير مسدد</option>
        </select>
      </div>

      {/* Orders Table */}
      <div className="bg-white border border-[#EBE3D5] rounded-3xl overflow-hidden shadow-sm">
        {loading ? (
          <p className="text-center py-12 text-xs text-[#746A5D]">جار تحميل سجلات الفواتير...</p>
        ) : filtered.length === 0 ? (
          <p className="text-center py-12 text-xs text-[#746A5D]">لا توجد طلبات مسجلة مطابقة للبحث.</p>
        ) : (
          <table className="w-full text-right text-xs">
            <thead className="bg-[#FAF7F2] text-[#746A5D] border-b border-[#EBE3D5]">
              <tr>
                <th className="p-4">رقم المرجع (Invoice Ref)</th>
                <th className="p-4">العميل</th>
                <th className="p-4">القناة والتسليم</th>
                <th className="p-4">طريقة الدفع</th>
                <th className="p-4">المبلغ الإجمالي</th>
                <th className="p-4">حالة السداد</th>
                <th className="p-4 text-center">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F2ECE1] text-[#26221C]">
              {filtered.map((ord) => (
                <tr key={ord.id} className="hover:bg-[#FAF7F2]/60 transition">
                  <td className="p-4 font-mono font-bold text-[#9A6817]">
                    {ord.reference}
                    <span className="block text-[10px] text-[#8C8275] font-normal">{ord.created_at}</span>
                  </td>
                  <td className="p-4">
                    <p className="font-bold text-[#26221C]">{ord.customer_name}</p>
                    <p className="text-[#746A5D] text-[11px]">{ord.customer_phone}</p>
                    {(ord.country || ord.city || ord.area) && (
                      <p className="text-[#9A6817] text-[10px] flex items-center gap-1 mt-0.5 font-medium">
                        <MapPin className="w-3 h-3 text-[#C9972B] shrink-0" />
                        <span>
                          {ord.country || 'الإمارات'}
                          {ord.city ? ` • ${ord.city}` : ''}
                          {ord.area ? ` (${ord.area})` : ''}
                        </span>
                      </p>
                    )}
                  </td>
                  <td className="p-4">
                    <span className="text-[#3D352E] font-medium">
                      {ord.sale_channel === 'DIRECT' ? 'معرض مباشر' : 'متجر إلكتروني'}
                    </span>
                    <span className="block text-[10px] text-[#8C8275]">تسليم يدوي</span>
                  </td>
                  <td className="p-4 font-medium">
                    <span className="px-2 py-0.5 rounded bg-[#FAF7F2] border border-[#E0D7C6] text-[11px] text-[#4B4338]">
                      {ord.payment_method}
                    </span>
                  </td>
                  <td className="p-4 font-black text-[#9A6817] text-sm">
                    {ord.grand_total.toLocaleString()} AED
                    {ord.discount_total > 0 && (
                      <span className="block text-[10px] text-rose-600 font-normal">خصم: -{ord.discount_total}</span>
                    )}
                  </td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      ord.payment_status === 'PAID'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : ord.payment_status === 'PARTIALLY_PAID'
                        ? 'bg-amber-100 text-amber-800 border border-amber-300'
                        : 'bg-rose-100 text-rose-800 border border-rose-300'
                    }`}>
                      {ord.payment_status}
                    </span>
                  </td>
                  <td className="p-4 text-center">
                    <button
                      onClick={() => onViewInvoice(ord)}
                      className="px-3 py-1.5 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#9A6817] font-bold text-xs rounded-xl border border-[#E0D7C6] transition flex items-center gap-1.5 mx-auto cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5 text-[#C9972B]" />
                      <span>عرض الفاتورة</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
