import React, { useState, useEffect } from 'react';
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Clock,
  Plus,
  AlertTriangle,
  FileText,
  Calendar,
  CheckCircle,
  XCircle,
  Banknote
} from 'lucide-react';
import { api } from '../lib/api';
import { AccountantReport, Expense, Order } from '../types';

export const AccountantPage: React.FC = () => {
  const [period, setPeriod] = useState('month');
  const [report, setReport] = useState<AccountantReport | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [receivables, setReceivables] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  // New Expense form state
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expCategory, setExpCategory] = useState('BOXES');
  const [expDesc, setExpDesc] = useState('');
  const [expAmount, setExpAmount] = useState('');
  const [expSupplier, setExpSupplier] = useState('');

  // Settle Receivable state
  const [selectedReceivable, setSelectedReceivable] = useState<Order | null>(null);
  const [payAmount, setPayAmount] = useState('');

  useEffect(() => {
    loadAccountantData();
  }, [period]);

  const loadAccountantData = async () => {
    setLoading(true);
    try {
      const [rep, exps, recs] = await Promise.all([
        api.getAccountantReport(period),
        api.getExpenses(),
        api.getReceivables()
      ]);
      setReport(rep);
      setExpenses(exps);
      setReceivables(recs);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expDesc.trim() || !expAmount) return;

    try {
      await api.createExpense({
        category: expCategory,
        description: expDesc.trim(),
        amount: Number(expAmount),
        supplier: expSupplier.trim()
      });
      setShowExpenseModal(false);
      setExpDesc('');
      setExpAmount('');
      setExpSupplier('');
      await loadAccountantData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'حدث خطأ أثناء إضافة المصروف');
    }
  };

  const handleVoidExpense = async (id: number) => {
    const reason = prompt('يرجى كتابة سبب إلغاء هذا المصروف محاسبياً:');
    if (!reason || !reason.trim()) return;

    try {
      await api.voidExpense(id, reason.trim());
      await loadAccountantData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'فشل إلغاء المصروف');
    }
  };

  const handleSettleReceivable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReceivable || !payAmount) return;

    try {
      await api.payReceivable(selectedReceivable.id, {
        amount: Number(payAmount),
        payment_method: 'CASH',
        note: 'سداد دفعة للمستحق الآجل'
      });
      alert('✅ تم قيد سداد الدفعة وتحديث الرصيد المتبقي بنجاح');
      setSelectedReceivable(null);
      setPayAmount('');
      await loadAccountantData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'فشلت عملية السداد');
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header and Period Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
            <Calculator className="w-5 h-5 text-[#C9972B]" />
            <span>المحاسب الذكي والأرباح المحققة الصافية</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            احتساب أرباح الطلبات المسلمة فعلياً استناداً لتكلفة الخامات (COGS)، المصاريف التشغيلية، والديون الآجلة.
          </p>
        </div>

        {/* Time period switcher */}
        <div className="flex items-center gap-1.5 bg-white border border-[#EBE3D5] p-1 rounded-2xl text-xs shadow-sm">
          {[
            { id: 'today', label: 'اليوم' },
            { id: 'week', label: 'الأسبوع' },
            { id: 'month', label: 'الشهر الحالي' },
            { id: 'year', label: 'السنة' }
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setPeriod(t.id)}
              className={`px-3 py-1.5 rounded-xl font-bold transition cursor-pointer ${
                period === t.id
                  ? 'bg-[#C9972B] text-white shadow-sm'
                  : 'text-[#746A5D] hover:text-[#26221C]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Financial Matrix Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-3xl bg-white border border-[#EBE3D5] shadow-sm">
          <p className="text-xs text-[#746A5D] font-medium">إجمالي المبيعات المحققة</p>
          <h3 className="text-2xl font-black text-[#9A6817] mt-2">
            {report?.totalSales?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
          </h3>
          <p className="text-[11px] text-[#746A5D] mt-1">{report?.orderCount || 0} طلبات مسلمة ومدفوعة</p>
        </div>

        <div className="p-5 rounded-3xl bg-white border border-[#EBE3D5] shadow-sm">
          <p className="text-xs text-[#746A5D] font-medium">تكلفة البضاعة المباعة (COGS)</p>
          <h3 className="text-2xl font-black text-[#26221C] mt-2">
            {report?.totalCostOfGoodsSold?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
          </h3>
          <p className="text-[11px] text-[#746A5D] mt-1">لقطات التكلفة التاريخية المجمدة</p>
        </div>

        <div className="p-5 rounded-3xl bg-white border border-[#EBE3D5] shadow-sm">
          <p className="text-xs text-[#746A5D] font-medium">المصاريف التشغيلية (النشطة)</p>
          <h3 className="text-2xl font-black text-rose-600 mt-2">
            {report?.totalExpenses?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
          </h3>
          <p className="text-[11px] text-[#746A5D] mt-1">باستثناء المصاريف الملغاة (Voided)</p>
        </div>

        <div className="p-5 rounded-3xl bg-gradient-to-br from-[#FAF4E8] to-[#FFFDF8] border border-[#E4D5B8] shadow-sm">
          <p className="text-xs text-[#9A6817] font-bold">صافي الأرباح الحقيقية</p>
          <h3 className="text-2xl font-black text-emerald-700 mt-2">
            {report?.netProfit?.toLocaleString() || 0} <span className="text-xs text-[#746A5D] font-normal">AED</span>
          </h3>
          <p className="text-[11px] text-[#9A6817] font-bold mt-1">
            هامش الربح الإجمالي: {report?.profitMargin || '0'}%
          </p>
        </div>
      </div>

      {/* Two sections: Receivables & Operational Expenses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Receivables (Deferred Payments on Exhibition sales) */}
        <div className="bg-white border border-[#EBE3D5] rounded-3xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#F2ECE1] pb-3">
            <div>
              <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#C9972B]" />
                <span>المستحقات والديون الآجلة ({receivables.length})</span>
              </h3>
              <p className="text-xs text-[#746A5D] mt-0.5">
                متابعة مبيعات المعارض بالآجل وتحصيل الدفعات
              </p>
            </div>
            <span className="text-xs font-black text-[#9A6817] bg-[#FAF4E8] px-2.5 py-1 rounded-full border border-[#EADBCE]">
              إجمالي: {report?.totalReceivables?.toLocaleString() || 0} AED
            </span>
          </div>

          <div className="space-y-3 max-h-[450px] overflow-y-auto pr-1">
            {receivables.length === 0 ? (
              <p className="text-center py-8 text-xs text-[#746A5D]">لا توجد ديون أو مستحقات آجلة معلقة. جميع الحسابات مسددة.</p>
            ) : (
              receivables.map((rec) => (
                <div key={rec.id} className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EEE6D8] flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#26221C]">{rec.customer_name}</span>
                      <span className="font-mono text-[10px] text-[#8C8275]">({rec.reference})</span>
                    </div>
                    <p className="text-[#746A5D] mt-0.5">هاتف: {rec.customer_phone}</p>
                    <p className="text-[#9A6817] text-[11px] font-semibold mt-1">
                      استحقاق السداد: {rec.payment_due_date || 'غير محدد'}
                    </p>
                  </div>

                  <div className="text-left space-y-1">
                    <p className="text-rose-600 font-black text-sm">متبقي: {rec.outstanding_amount.toLocaleString()} AED</p>
                    <p className="text-[#746A5D] text-[10px]">المدفوع: {rec.paid_amount.toLocaleString()} AED</p>
                    <button
                      onClick={() => {
                        setSelectedReceivable(rec);
                        setPayAmount(String(rec.outstanding_amount));
                      }}
                      className="px-3 py-1 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-[11px] rounded-lg transition shadow-sm cursor-pointer"
                    >
                      تسجيل دفعة سداد
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Operational Expenses */}
        <div className="bg-white border border-[#EBE3D5] rounded-3xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#F2ECE1] pb-3">
            <div>
              <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
                <Banknote className="w-4 h-4 text-rose-600" />
                <span>المصاريف التشغيلية (علب، تغليف، شحن)</span>
              </h3>
              <p className="text-xs text-[#746A5D] mt-0.5">المصاريف غير قابلة للحذف ويتم إلغاؤها بسبب موثق</p>
            </div>
            <button
              onClick={() => setShowExpenseModal(true)}
              className="px-3 py-1.5 bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] text-xs font-bold rounded-xl border border-[#E4D5B8] flex items-center gap-1.5 transition shadow-sm cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>إضافة مصروف</span>
            </button>
          </div>

          <div className="space-y-2.5 max-h-[450px] overflow-y-auto pr-1">
            {expenses.length === 0 ? (
              <p className="text-center py-8 text-xs text-[#746A5D]">لا توجد مصاريف تشغيلية مقيدة.</p>
            ) : (
              expenses.map((exp) => {
                const isVoided = exp.status === 'VOIDED';
                return (
                  <div
                    key={exp.id}
                    className={`p-3.5 rounded-2xl border flex items-center justify-between text-xs transition ${
                      isVoided
                        ? 'bg-[#F5F2EB]/50 border-[#E5DECF] opacity-60 line-through'
                        : 'bg-[#FAF7F2] border-[#EEE6D8]'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#26221C]">{exp.description}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-[#E0D7C6] text-[#746A5D]">
                          {exp.category}
                        </span>
                        {isVoided && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                            ملغي: {exp.void_reason}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#746A5D] mt-1">
                        المورد: {exp.supplier || 'محلي'} | التاريخ: {exp.incurred_on}
                      </p>
                    </div>

                    <div className="text-left flex items-center gap-3">
                      <span className={`font-black text-sm ${isVoided ? 'text-[#8C8275]' : 'text-rose-600'}`}>
                        {exp.amount.toLocaleString()} AED
                      </span>
                      {!isVoided && (
                        <button
                          onClick={() => handleVoidExpense(exp.id)}
                          title="إلغاء المصروف وتوثيقه محاسبياً"
                          className="p-1 text-[#8C8275] hover:text-rose-600 transition cursor-pointer"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Settle Receivable Modal */}
      {selectedReceivable && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-[#26221C] text-sm">سداد دفعة للمستحق الآجل</h3>
            <p className="text-xs text-[#746A5D]">
              العميل: {selectedReceivable.customer_name} | الفاتورة: {selectedReceivable.reference}
            </p>

            <form onSubmit={handleSettleReceivable} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                  المبلغ المراد سداده الآن (درهم) - المتبقي: {selectedReceivable.outstanding_amount} AED
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max={selectedReceivable.outstanding_amount}
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm font-bold text-[#9A6817] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#F2ECE1]">
                <button
                  type="button"
                  onClick={() => setSelectedReceivable(null)}
                  className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-bold rounded-xl cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
                >
                  تأكيد وقيد السداد
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Expense Modal */}
      {showExpenseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-[#26221C] text-sm">إضافة مصروف تشغيلي جديد</h3>

            <form onSubmit={handleAddExpense} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">التصنيف *</label>
                <select
                  value={expCategory}
                  onChange={(e) => setExpCategory(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                >
                  <option value="BOXES">علب وصناديق فاخرة</option>
                  <option value="BAGS">أكياس قماش ومخمل للخرز</option>
                  <option value="PACKAGING">مواد تغليف وحماية</option>
                  <option value="SHIPPING">شحن وتوصيل</option>
                  <option value="MARKETING">تسويق وإعلانات</option>
                  <option value="OPERATIONS">تشغيل المعرض والمحل</option>
                  <option value="OTHER">مصاريف أخرى</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">بيان ووصف المصروف *</label>
                <input
                  type="text"
                  required
                  placeholder="مثال: شراء علب خشبية مطعمة بالصدف"
                  value={expDesc}
                  onChange={(e) => setExpDesc(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">المبلغ (درهم) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={expAmount}
                  onChange={(e) => setExpAmount(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm font-bold text-rose-600 focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">المورد / الجهة</label>
                <input
                  type="text"
                  placeholder="اسم المورد أو الشركة"
                  value={expSupplier}
                  onChange={(e) => setExpSupplier(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#F2ECE1]">
                <button
                  type="button"
                  onClick={() => setShowExpenseModal(false)}
                  className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-bold rounded-xl cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
                >
                  حفظ المصروف
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
