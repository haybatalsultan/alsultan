import React, { useState, useEffect } from 'react';
import {
  Gem,
  ShoppingBag,
  TrendingUp,
  ShieldCheck,
  Scissors,
  Receipt,
  Clock,
  Sparkles,
  ArrowUpRight,
  Plus
} from 'lucide-react';
import { api } from '../lib/api';
import { AccountantReport, Product, Order, User } from '../types';
import { hasPermission } from '../lib/permissions';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onOpenQuickSale: (product: Product) => void;
  currentUser?: User;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onOpenQuickSale, currentUser }) => {
  const canFinancialKpis = hasPermission(currentUser, 'dashboard.financial_kpis');
  const canPos = hasPermission(currentUser, 'pos.view');
  const canCreateProduct = hasPermission(currentUser, 'inventory.create');
  const [report, setReport] = useState<AccountantReport | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rep, prods, ords] = await Promise.all([
        api.getAccountantReport('month'),
        api.getProducts(),
        api.getOrders({ limit: 5 })
      ]);
      setReport(rep);
      setProducts(prods);
      setRecentOrders(ords.slice(0, 5));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const availableCount = products.filter(p => p.status === 'AVAILABLE').length;
  const soldCount = products.filter(p => p.status === 'SOLD').length;
  const custodyCount = products.filter(p => p.status === 'IN_CUSTODY').length;
  const reservedCount = products.filter(p => p.status === 'RESERVED').length;

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Welcome & KPI Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-[#FAF4E8] via-white to-[#FAF4E8] p-6 rounded-3xl border border-[#EBE3D5] shadow-[0_4px_20px_rgba(70,45,15,0.04)]">
        <div>
          <div className="flex items-center gap-2 text-[#9A6817] font-bold text-xs uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4 text-[#C9972B]" />
            <span>نظام الإدارة الشاملة للمسابيح الفاخرة</span>
          </div>
          <h1 className="text-2xl font-black text-[#26221C]">هيبة السلطان - لوحة التحكم التنفيذية</h1>
          <p className="text-xs text-[#746A5D] mt-1">
            متابعة فورية للمخزون الحصري، العهد الميدانية، المبيعات المباشرة، وحساب الأرباح المحققة.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canPos && (
            <button
              onClick={() => onNavigate('pos')}
              className="px-5 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-black text-xs rounded-xl transition shadow-[0_4px_14px_rgba(201,151,43,0.3)] flex items-center gap-2 cursor-pointer"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>شاشة البيع السريع (POS)</span>
            </button>
          )}
          {canCreateProduct && (
            <button
              onClick={() => onNavigate('inventory')}
              className="px-4 py-2.5 bg-white hover:bg-[#FAF4E8] text-[#4B4338] font-bold text-xs rounded-xl transition border border-[#DCD3C3] shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>إضافة مسبحة</span>
            </button>
          )}
        </div>
      </div>

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-[#EBE3D5] shadow-[0_4px_16px_rgba(70,45,15,0.03)] relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs text-[#746A5D] font-medium">المبيعات المحققة (الشهر)</p>
              <h3 className="text-2xl font-black text-[#9A6817] mt-2">
                {report?.totalSales?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
              </h3>
              {canFinancialKpis && (
                <p className="text-[11px] text-emerald-700 mt-1 flex items-center gap-1 font-semibold">
                  <span>صافي الأرباح: {report?.netProfit?.toLocaleString() || 0} AED</span>
                </p>
              )}
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] flex items-center justify-center border border-[#EADBCE]">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#EBE3D5] shadow-[0_4px_16px_rgba(70,45,15,0.03)]">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs text-[#746A5D] font-medium">المسابيح الحصرية المتاحة</p>
              <h3 className="text-2xl font-black text-[#26221C] mt-2">{availableCount}</h3>
              <p className="text-[11px] text-[#746A5D] mt-1">
                {custodyCount} في العهدة | {reservedCount} محجوز مؤقتاً
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200">
              <Gem className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#EBE3D5] shadow-[0_4px_16px_rgba(70,45,15,0.03)]">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs text-[#746A5D] font-medium">المستحقات الآجلة (ديون المعارض)</p>
              <h3 className="text-2xl font-black text-[#C9972B] mt-2">
                {report?.totalReceivables?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
              </h3>
              <p className="text-[11px] text-[#9A6817] mt-1 font-semibold">
                {report?.countReceivables || 0} طلبات بانتظار استكمال السداد
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-[#C9972B] flex items-center justify-center border border-amber-200">
              <Clock className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[#EBE3D5] shadow-[0_4px_16px_rgba(70,45,15,0.03)]">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs text-[#746A5D] font-medium">قطع تم بيعها واقتناؤها</p>
              <h3 className="text-2xl font-black text-[#26221C] mt-2">{soldCount}</h3>
              <p className="text-[11px] text-[#746A5D] mt-1">
                هامش الربح المحقق: {report?.profitMargin || '0'}%
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#4B4338] flex items-center justify-center border border-[#EADBCE]">
              <Receipt className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launchpad & Exclusivity Showcase */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Available Rare Rosaries for Quick POS Sale */}
        <div className="lg:col-span-2 bg-white border border-[#EBE3D5] rounded-3xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-[#26221C] flex items-center gap-2">
                <Gem className="w-4 h-4 text-[#C9972B]" />
                <span>مسابيح حصرية جاهزة للبيع الفوري</span>
              </h3>
              <p className="text-xs text-[#746A5D] mt-0.5">انقر لإتمام بيع فوري ونقل ملكية القطعة</p>
            </div>
            <button
              onClick={() => onNavigate('inventory')}
              className="text-xs text-[#9A6817] hover:text-[#C9972B] flex items-center gap-1 font-bold"
            >
              <span>عرض كل المخزون</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {products.filter(p => p.status === 'AVAILABLE').slice(0, 4).map((p) => (
              <div
                key={p.id}
                className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] hover:border-[#C9972B] transition flex flex-col justify-between group shadow-sm"
              >
                <div>
                  <div className="flex items-start gap-3">
                    <img
                      src={p.image_url || '/branding/hero-amber.jpg'}
                      alt=""
                      className="w-14 h-14 object-cover rounded-xl border border-[#E0D7C6]"
                    />
                    <div>
                      <span className="text-[10px] font-mono text-[#9A6817] bg-[#FAF4E8] border border-[#EADBCE] px-2 py-0.5 rounded-full font-bold">
                        {p.sku}
                      </span>
                      <h4 className="font-bold text-xs text-[#26221C] mt-1 line-clamp-2 leading-relaxed group-hover:text-[#9A6817] transition">
                        {p.name_ar}
                      </h4>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-[#746A5D] mt-3 pt-2 border-t border-[#EEE6D8]">
                    <span>{p.color}</span>
                    <span>•</span>
                    <span>{p.bead_count} خرزة</span>
                    <span>•</span>
                    <span>
                      {p.bead_size_mm ? (String(p.bead_size_mm).toLowerCase().includes('mm') || String(p.bead_size_mm).includes('ملم') ? p.bead_size_mm : `${p.bead_size_mm}mm`) : '-'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-4 pt-2 border-t border-[#EEE6D8]">
                  <span className="font-black text-[#9A6817] text-sm">{p.selling_price.toLocaleString()} AED</span>
                  <button
                    onClick={() => onOpenQuickSale(p)}
                    className="px-3 py-1.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm"
                  >
                    بيع فوري (POS)
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Operational Status */}
        <div className="space-y-6">
          {/* Quick Shortcuts */}
          <div className="bg-white border border-[#EBE3D5] rounded-3xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#26221C] mb-4">الوصول السريع للعمليات</h3>
            <div className="space-y-2.5">
              <button
                onClick={() => onNavigate('custody')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EBE3D5] hover:border-[#C9972B] text-xs font-bold text-[#26221C] transition"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>تسليم عهدة لمعرض أو مندوب</span>
                </div>
                <span className="text-[10px] text-[#746A5D] font-normal">{custodyCount} قيد العهدة</span>
              </button>

              <button
                onClick={() => onNavigate('workshop')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EBE3D5] hover:border-[#C9972B] text-xs font-bold text-[#26221C] transition"
              >
                <div className="flex items-center gap-2.5">
                  <Scissors className="w-4 h-4 text-[#C9972B]" />
                  <span>أوامر ورشة تعديل الخرز</span>
                </div>
                <span className="text-[10px] text-[#746A5D] font-normal">تجهيز أكياس الحفظ</span>
              </button>

              <button
                onClick={() => onNavigate('accountant')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EBE3D5] hover:border-[#C9972B] text-xs font-bold text-[#26221C] transition"
              >
                <div className="flex items-center gap-2.5">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <span>المحاسب الذكي وإدارة المصاريف</span>
                </div>
                <span className="text-[10px] text-[#746A5D] font-normal">كشف الأرباح</span>
              </button>
            </div>
          </div>

          {/* Recent Orders Overview */}
          <div className="bg-white border border-[#EBE3D5] rounded-3xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#26221C] mb-3">أحدث الفواتير والمبيعات</h3>
            <div className="space-y-2.5">
              {recentOrders.map((ord) => (
                <div key={ord.id} className="p-3 rounded-xl bg-[#FAF7F2] border border-[#EEE6D8] flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-[#26221C] font-mono text-[11px]">{ord.reference}</p>
                    <p className="text-[#746A5D] text-[11px] mt-0.5">{ord.customer_name}</p>
                  </div>
                  <div className="text-left">
                    <p className="font-bold text-[#9A6817]">{ord.grand_total.toLocaleString()} AED</p>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
                      {ord.payment_status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
