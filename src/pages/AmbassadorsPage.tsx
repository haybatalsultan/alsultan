import React, { useState, useEffect } from 'react';
import { Users, Award, Plus, Search, ShieldCheck, Share2, Copy } from 'lucide-react';
import { api } from '../lib/api';
import { Ambassador } from '../types';

export const AmbassadorsPage: React.FC = () => {
  const [ambassadors, setAmbassadors] = useState<Ambassador[]>([]);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadAmbassadors();
  }, []);

  const loadAmbassadors = async () => {
    setLoading(true);
    try {
      const data = await api.getAmbassadors();
      setAmbassadors(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !phone.trim()) return;

    try {
      const res = await api.createAmbassador({
        name: name.trim(),
        phone: phone.trim(),
        email: email.trim()
      });
      alert(`✅ تم تسجيل السفير بنجاح وتوليد كود الإحالة: ${res.code}`);
      setShowAddModal(false);
      setName('');
      setPhone('');
      setEmail('');
      await loadAmbassadors();
    } catch (err: any) {
      alert(err.response?.data?.error || 'حدث خطأ أثناء تسجيل السفير');
    }
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    alert(`تم نسخ كود السفير (${code}) إلى الحافظة.`);
  };

  const filtered = ambassadors.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.code.toLowerCase().includes(search.toLowerCase()) ||
    a.phone.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
            <Users className="w-5 h-5 text-[#C9972B]" />
            <span>برنامج سفراء هيبة السلطان (Affiliate & Points)</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            إدارة مسوقي النخبة، احتساب نقاط المبيعات التلقائي (25 نقطة لكل 1000 درهم)، وسجل حماية الإحالات.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition flex items-center gap-2 shadow-[0_4px_14px_rgba(201,151,43,0.3)] cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>إضافة سفير جديد</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="p-4 rounded-2xl bg-white border border-[#EBE3D5] shadow-sm">
        <div className="relative">
          <Search className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-2.5" />
          <input
            type="text"
            placeholder="ابحث باسم السفير، الكود (HSA-XXXX)، أو الهاتف..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#FAF7F2] border border-[#E0D7C6] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
          />
        </div>
      </div>

      {/* Ambassadors Grid */}
      {loading ? (
        <p className="text-center py-16 text-xs text-[#746A5D]">جار تحميل قائمة السفراء...</p>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-[#D8CCA8] rounded-3xl shadow-sm">
          <Users className="w-12 h-12 text-[#C9972B]/50 mx-auto mb-2" />
          <p className="text-sm font-bold text-[#26221C]">لا يوجد سفراء مسجلين بعد</p>
          <p className="text-xs text-[#746A5D] mt-1">أضف سفيراً لمنحه كود تسويق خاص وحساب نقاطه</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((amb) => (
            <div
              key={amb.id}
              className="p-5 rounded-3xl bg-white border border-[#EBE3D5] flex flex-col justify-between hover:border-[#C9972B] hover:shadow-[0_8px_24px_rgba(201,151,43,0.12)] transition shadow-sm space-y-4"
            >
              <div>
                <div className="flex items-center justify-between border-b border-[#F2ECE1] pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-black text-[#9A6817] bg-[#FAF4E8] px-2.5 py-0.5 rounded-full border border-[#EADBCE]">
                      {amb.code}
                    </span>
                    <button
                      onClick={() => copyCode(amb.code)}
                      title="نسخ الكود"
                      className="p-1 text-[#8C8275] hover:text-[#C9972B] transition cursor-pointer"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <span className="text-[10px] text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full font-bold border border-emerald-300">
                    نشط
                  </span>
                </div>

                <div className="mt-3">
                  <h4 className="font-bold text-sm text-[#26221C]">{amb.name}</h4>
                  <p className="text-xs text-[#746A5D]">{amb.phone}</p>
                  {amb.email && <p className="text-[11px] text-[#746A5D]">{amb.email}</p>}
                </div>

                {/* Points ledger snapshot */}
                <div className="grid grid-cols-2 gap-2 mt-4 p-3 bg-[#FAF7F2] rounded-2xl border border-[#EEE6D8] text-center text-xs">
                  <div>
                    <span className="text-[10px] text-[#8C8275] block">الرصيد المتاح</span>
                    <span className="font-black text-[#9A6817] text-base">{amb.points_balance}</span>
                    <span className="text-[10px] text-[#8C8275] block">نقطة</span>
                  </div>
                  <div className="border-r border-[#E2D8C6]">
                    <span className="text-[10px] text-[#8C8275] block">إجمالي المكتسب</span>
                    <span className="font-black text-[#26221C] text-base">{amb.total_earned}</span>
                    <span className="text-[10px] text-[#8C8275] block">نقطة</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#F2ECE1] flex items-center justify-between text-[10px] text-[#746A5D]">
                <span>تاريخ التسجيل: {amb.created_at.slice(0, 10)}</span>
                <span className="text-[#9A6817] font-bold">1000 درهم = 25 نقطة</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-[#26221C] text-sm">تسجيل سفير جديد وتوليد كود الإحالة</h3>

            <form onSubmit={handleAdd} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم السفير *</label>
                <input
                  type="text"
                  required
                  placeholder="مثال: راشد المنصوري"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف *</label>
                <input
                  type="text"
                  required
                  placeholder="+97150..."
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">البريد الإلكتروني</label>
                <input
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#F2ECE1]">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-bold rounded-xl cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
                >
                  توليد الكود والحفظ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
