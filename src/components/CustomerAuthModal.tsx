import React, { useState, useEffect } from 'react';
import { User, Lock, Phone, Mail, X, ArrowLeft, CheckCircle2, AlertCircle, Globe, MapPin } from 'lucide-react';
import { api } from '../lib/api';
import { toast } from '../utils/toast';

const DEFAULT_ARAB_COUNTRIES = [
  'الإمارات العربية المتحدة',
  'المملكة العربية السعودية',
  'دولة الكويت',
  'دولة قطر',
  'سلطنة عمان',
  'مملكة البحرين',
  'جمهورية مصر العربية',
  'المملكة الأردنية الهاشمية',
  'جمهورية العراق',
  'الجمهورية اللبنانية',
  'دولة فلسطين',
  'الجمهورية العربية السورية',
  'الجمهورية اليمنية',
  'دولة ليبيا',
  'الجمهورية التونسية',
  'الجمهورية الجزائرية',
  'المملكة المغربية',
  'جمهورية السودان',
  'جمهورية الصومال',
  'الجمهورية الإسلامية الموريتانية',
  'جمهورية جيبوتي',
  'جزر القمر'
];

interface CustomerAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (customer: any) => void;
}

export const CustomerAuthModal: React.FC<CustomerAuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<'LOGIN' | 'REGISTER'>('LOGIN');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [country, setCountry] = useState('الإمارات العربية المتحدة');
  const [address, setAddress] = useState('');
  const [countriesList, setCountriesList] = useState<string[]>(DEFAULT_ARAB_COUNTRIES);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      api.getCountries().then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setCountriesList(data.map((c: any) => c.name_ar));
        }
      }).catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      if (mode === 'LOGIN') {
        const res = await api.customerLogin(identifier, password);
        localStorage.setItem('haybat_customer_token', res.token);
        localStorage.setItem('haybat_customer_user', JSON.stringify(res.user));
        onSuccess(res.user);
        onClose();
      } else {
        const res = await api.customerRegister({
          username: username.trim(),
          password,
          full_name: fullName.trim(),
          phone: phone.trim(),
          email: email.trim(),
          country: country.trim(),
          address: address.trim()
        });
        localStorage.setItem('haybat_customer_token', res.token);
        localStorage.setItem('haybat_customer_user', JSON.stringify(res.user));
        toast.success('مرحباً بك في هيبة السلطان! تم إنشاء حسابك بنجاح.', 'أهلاً وسهلاً');
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error || 'تعذر تسجيل الدخول، يرجى التحقق من البيانات.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#26221C]">
                {mode === 'LOGIN' ? 'تسجيل دخول العملاء' : 'إنشاء حساب عميل جديد'}
              </h3>
              <p className="text-[11px] text-[#746A5D]">
                {mode === 'LOGIN' ? 'أهلاً بعودتك إلى متجر هيبة السلطان' : 'انضم لنخبة مقتني المسابيح الفاخرة'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 p-2 bg-[#F6F1E8] border-b border-[#EBE3D5] text-xs font-bold text-center">
          <button
            type="button"
            onClick={() => { setMode('LOGIN'); setErrorMsg(''); }}
            className={`py-2 rounded-xl transition cursor-pointer ${
              mode === 'LOGIN' ? 'bg-white text-[#9A6817] shadow-sm' : 'text-[#746A5D] hover:text-[#26221C]'
            }`}
          >
            تسجيل الدخول
          </button>
          <button
            type="button"
            onClick={() => { setMode('REGISTER'); setErrorMsg(''); }}
            className={`py-2 rounded-xl transition cursor-pointer ${
              mode === 'REGISTER' ? 'bg-white text-[#9A6817] shadow-sm' : 'text-[#746A5D] hover:text-[#26221C]'
            }`}
          >
            حساب جديد
          </button>
        </div>

        {/* Error message banner */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {mode === 'REGISTER' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">الاسم الكامل *</label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="مثال: محمد سعيد المنصوري"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم المستخدم *</label>
                <input
                  type="text"
                  required
                  placeholder="اسم المستخدم بالإنجليزية (مثال: mohammed22)"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف *</label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="+97150..."
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">البريد الإلكتروني (اختياري)</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                  <input
                    type="email"
                    placeholder="example@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1 flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-[#C9972B]" />
                  <span>دولة الإقامة *</span>
                </label>
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] font-semibold focus:outline-none focus:border-[#C9972B]"
                >
                  {countriesList.map((cName) => (
                    <option key={cName} value={cName}>{cName}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-[#C9972B]" />
                  <span>العنوان بالتفصيل</span>
                </label>
                <input
                  type="text"
                  placeholder="المدينة، الحي، الشارع، المبنى"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>
            </>
          )}

          {mode === 'LOGIN' && (
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                اسم المستخدم / رقم الهاتف / البريد *
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
                <input
                  type="text"
                  required
                  placeholder="أدخل اسم المستخدم أو الهاتف أو البريد"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">كلمة المرور *</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-[0_4px_14px_rgba(201,151,43,0.3)] disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer mt-2"
          >
            <span>{loading ? 'جار المعالجة...' : (mode === 'LOGIN' ? 'تسجيل الدخول' : 'تأكيد التسجيل')}</span>
            <ArrowLeft className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
