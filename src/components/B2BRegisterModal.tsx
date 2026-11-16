import React, { useState } from 'react';
import {
  Building2,
  X,
  ShieldCheck,
  FileText,
  Phone,
  Mail,
  Lock,
  User,
  AlertCircle,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { api } from '../lib/api';

interface B2BRegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (data: any) => void;
  onSwitchToLogin: () => void;
}

export const B2BRegisterModal: React.FC<B2BRegisterModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  onSwitchToLogin
}) => {
  const [companyName, setCompanyName] = useState('');
  const [commercialRegister, setCommercialRegister] = useState('');
  const [taxId, setTaxId] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  // Honeypot field (hidden from real users, automated bots fill it)
  const [websiteHp, setWebsiteHp] = useState('');

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      const res = await api.b2bRegister({
        company_name: companyName.trim(),
        commercial_register: commercialRegister.trim(),
        tax_id: taxId.trim(),
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        password,
        website_hp: websiteHp
      });

      setSubmitted(true);
      onSuccess(res);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error || 'تعذر تقديم طلب اعتماد الجملة، يرجى التحقق من البيانات.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" dir="rtl">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#FAF4E8] via-[#FFFDF8] to-[#F5ECE0] p-6 border-b border-[#EBE3D5] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center shadow-md">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-black text-[#26221C]">
                طلب انضمام لشبكة تجار الجملة (B2B)
              </h2>
              <p className="text-xs text-[#746A5D]">
                أسعار مخفضة حصرية وحزم كميات للتجار والمعارض المعتمدة
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

        {/* Content Body */}
        {submitted ? (
          <div className="p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center mx-auto shadow-xs">
              <Clock className="w-8 h-8 animate-pulse" />
            </div>
            <h3 className="text-lg font-black text-[#26221C]">
              تم استلام طلب الاعتماد بنجاح!
            </h3>
            <p className="text-xs text-[#746A5D] leading-relaxed max-w-sm mx-auto">
              شكراً لكم ممثل <strong>{companyName}</strong>. طلبكم الآن في مرحلة التحقق من السجل التجاري ومطابقة البيانات لفتح بوابة الجملة الخاصة بكم.
            </p>
            <div className="pt-4 border-t border-[#F2ECE1]">
              <button
                type="button"
                onClick={onClose}
                className="w-full py-3 bg-[#26221C] text-[#E2B84B] rounded-xl text-xs font-black shadow-md cursor-pointer hover:bg-[#3D352E] transition"
              >
                حسناً، فهمت
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
            {errorMsg && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Honeypot field (hidden from humans, traps bots) */}
            <div
              style={{
                opacity: 0,
                position: 'absolute',
                top: 0,
                left: 0,
                height: 0,
                width: 0,
                zIndex: -1,
                overflow: 'hidden'
              }}
              aria-hidden="true"
            >
              <label htmlFor="website_hp">Leave this field blank</label>
              <input
                id="website_hp"
                type="text"
                name="website_hp"
                tabIndex={-1}
                autoComplete="off"
                value={websiteHp}
                onChange={e => setWebsiteHp(e.target.value)}
              />
            </div>

            {/* Corporate Details */}
            <div className="space-y-3">
              <h4 className="text-xs font-black text-[#9A6817] flex items-center gap-1.5 pb-1 border-b border-[#F2ECE1]">
                <ShieldCheck className="w-4 h-4 text-[#C9972B]" />
                <span>البيانات القانونية للمنشأة</span>
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    اسم الشركة / المعرض <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      value={companyName}
                      onChange={e => setCompanyName(e.target.value)}
                      placeholder="شركة هيبة الفخامة للتجارة"
                      className="w-full px-3.5 py-2.5 pr-9 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                    />
                    <Building2 className="w-4 h-4 text-[#8C8275] absolute right-3 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    رقم السجل التجاري (CR) <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      value={commercialRegister}
                      onChange={e => setCommercialRegister(e.target.value)}
                      placeholder="CN-1234567"
                      className="w-full px-3.5 py-2.5 pr-9 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
                    />
                    <FileText className="w-4 h-4 text-[#8C8275] absolute right-3 top-3" />
                  </div>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    الرقم الضريبي (TRN - اختياري)
                  </label>
                  <input
                    type="text"
                    value={taxId}
                    onChange={e => setTaxId(e.target.value)}
                    placeholder="100XXXXXXXXX003"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Contact Person Details */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-black text-[#9A6817] flex items-center gap-1.5 pb-1 border-b border-[#F2ECE1]">
                <User className="w-4 h-4 text-[#C9972B]" />
                <span>بيانات المفوض وحساب الدخول</span>
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    اسم المسؤول / المفوض <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="سعيد المنصوري"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    رقم الهاتف / الواتساب <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="+971 50 000 0000"
                      className="w-full px-3.5 py-2.5 pr-9 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                    />
                    <Phone className="w-4 h-4 text-[#8C8275] absolute right-3 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    البريد الإلكتروني للعمل <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="procurement@company.ae"
                      className="w-full px-3.5 py-2.5 pr-9 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                    />
                    <Mail className="w-4 h-4 text-[#8C8275] absolute right-3 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1">
                    كلمة المرور <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2.5 pr-9 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
                    />
                    <Lock className="w-4 h-4 text-[#8C8275] absolute right-3 top-3" />
                  </div>
                </div>
              </div>
            </div>

            {/* Submit */}
            <div className="pt-3 border-t border-[#F0E8DC]">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] font-black rounded-xl text-xs transition shadow-md disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#E2B84B] border-t-transparent rounded-full animate-spin" />
                    <span>جارٍ معالجة وتوثيق الطلب...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>تقديم طلب الاعتماد التجاري</span>
                  </>
                )}
              </button>
            </div>

            {/* Switch to login */}
            <div className="text-center pt-2 text-xs text-[#746A5D]">
              <span>لديك حساب جملة معتمد مسبقاً؟ </span>
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-[#9A6817] font-bold hover:underline cursor-pointer"
              >
                تسجيل الدخول هنا
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
