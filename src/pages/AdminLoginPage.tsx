import React, { useState } from 'react';
import { ShieldCheck, Lock, User, AlertTriangle, ArrowRight, Sparkles, Building2 } from 'lucide-react';
import { api } from '../lib/api';

interface AdminLoginPageProps {
  onSuccess: (user: any) => void;
  onBackToStore: () => void;
}

export const AdminLoginPage: React.FC<AdminLoginPageProps> = ({ onSuccess, onBackToStore }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isCustomerRejection, setIsCustomerRejection] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setIsCustomerRejection(false);
    setLoading(true);

    try {
      const res = await api.adminLogin(username.trim(), password);
      localStorage.setItem('haybat_staff_token', res.token);
      localStorage.setItem('haybat_staff_user', JSON.stringify(res.user));
      onSuccess(res.user);
    } catch (err: any) {
      const status = err.response?.status;
      const msg = err.response?.data?.error || 'فشل تسجيل الدخول. يرجى التحقق من اسم المستخدم وكلمة المرور.';
      setErrorMessage(msg);
      if (status === 403 || msg.includes('عملاء')) {
        setIsCustomerRejection(true);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF7F2] flex flex-col justify-between items-center p-4 selection:bg-[#C9972B]/20" dir="rtl">
      {/* Top Bar with Back Link */}
      <div className="w-full max-w-5xl flex items-center justify-between py-4">
        <button
          onClick={onBackToStore}
          className="flex items-center gap-2 text-xs sm:text-sm font-bold text-[#746A5D] hover:text-[#9A6817] transition bg-white border border-[#EBE3D5] px-4 py-2 rounded-xl shadow-xs"
        >
          <ArrowRight className="w-4 h-4 text-[#C9972B]" />
          <span>العودة للمتجر والواجهة الرئيسية</span>
        </button>

        <div className="flex items-center gap-1.5 text-xs text-[#8C8275] font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>بوابة الدخول المشفرة (SSL 256-bit)</span>
        </div>
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-md my-auto">
        <div className="bg-white border border-[#EBE3D5] rounded-3xl shadow-xl overflow-hidden">
          {/* Card Top Brand Banner */}
          <div className="bg-gradient-to-b from-[#F9F5EC] to-white p-8 text-center border-b border-[#F0E8DC]">
            <div className="inline-flex p-3 rounded-2xl bg-white shadow-xs border border-[#EEE4D4] mb-4">
              <img
                src="/branding/logo-header.png"
                alt="هيبة السلطان"
                className="h-16 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            <h1 className="text-xl font-black text-[#26221C] flex items-center justify-center gap-2">
              <Sparkles className="w-5 h-5 text-[#C9972B]" />
              <span>بوابة الإدارة ونقاط البيع</span>
            </h1>
            <p className="text-xs text-[#746A5D] mt-1.5 font-medium">
              نظام هيبة السلطان المركزي لإدارة المخزون والعهدة والحسابات
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 sm:p-8 space-y-5">
            {/* Warning or Error Box */}
            {errorMessage && (
              <div
                className={`p-4 rounded-2xl text-xs sm:text-sm flex items-start gap-3 border ${
                  isCustomerRejection
                    ? 'bg-rose-50/90 border-rose-200 text-rose-900'
                    : 'bg-amber-50/90 border-amber-200 text-amber-900'
                }`}
              >
                <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${isCustomerRejection ? 'text-rose-600' : 'text-amber-600'}`} />
                <div className="space-y-1">
                  <p className="font-bold">
                    {isCustomerRejection ? 'تم حظر الدخول - حساب عميل' : 'خطأ في المصادقة'}
                  </p>
                  <p className="leading-relaxed">{errorMessage}</p>
                  {isCustomerRejection && (
                    <button
                      type="button"
                      onClick={onBackToStore}
                      className="mt-2 inline-flex items-center gap-1 font-bold text-rose-700 underline text-xs"
                    >
                      اضغط هنا للانتقال إلى واجهة متجر العملاء
                    </button>
                  )}
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                اسم المستخدم / المعرّف الوظيفي
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="مثال: owner أو اسم المستخدم"
                  className="w-full px-4 py-3 pr-10 text-sm bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] focus:ring-2 focus:ring-[#C9972B]/20 text-[#26221C] font-medium"
                />
                <User className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 pr-10 text-sm bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] focus:ring-2 focus:ring-[#C9972B]/20 text-[#26221C] font-medium font-mono"
                />
                <Lock className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3.5" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] font-black rounded-xl text-sm transition shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#E2B84B] border-t-transparent rounded-full animate-spin" />
                  <span>جارٍ التحقق والمصادقة...</span>
                </>
              ) : (
                <>
                  <Building2 className="w-4 h-4" />
                  <span>دخول لوحة التحكم ونقاط البيع</span>
                </>
              )}
            </button>
          </form>

          {/* Footer Note */}
          <div className="bg-[#FAF7F2] px-6 py-4 border-t border-[#EBE3D5] text-center text-[11px] text-[#746A5D]">
            <span>الدخول مخصص لفريق عمل هيبة السلطان، المحاسبين، ومسؤولي المعارض والورش.</span>
          </div>
        </div>
      </div>

      {/* Bottom Copyright */}
      <footer className="w-full text-center py-4 text-xs text-[#8C8275]">
        جميع الحقوق محفوظة © {new Date().getFullYear()} — هيبة السلطان للمسابيح الفاخرة
      </footer>
    </div>
  );
};
