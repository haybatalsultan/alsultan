import React, { useState, useEffect } from 'react';
import {
  Settings,
  Shield,
  Cloud,
  Key,
  Save,
  CheckCircle,
  Database,
  FileText,
  Globe,
  Plus,
  Trash2,
  Search,
  Check,
  X,
  AlertCircle
} from 'lucide-react';
import { api } from '../lib/api';
import { StoreSettings, Country } from '../types';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<StoreSettings>({
    store_name_ar: 'هيبة السلطان للمسابيح الفاخرة',
    store_name_en: 'Haybat Al Sultan Luxury Rosaries',
    phone: '+971 50 408 4006',
    email: 'info@haybatalsultan.com',
    address: 'أبوظبي، الإمارات العربية المتحدة',
    currency: 'AED',
    tax_rate: 0,
    shipping_fee: 0,
    reservation_minutes: 15,
    invoice_thank_you: 'شكرًا لاختياركم هيبة السلطان - عنوان الفخامة والقطع النادرة',
    whatsapp_number: '+971504084006'
  });

  const [license, setLicense] = useState<any>(null);
  const [licenseKeyInput, setLicenseKeyInput] = useState('');
  const [cloud, setCloud] = useState<any>({ turso_url: '', turso_auth_token: '', is_active: false });
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  // Countries & Destinations State
  const [countries, setCountries] = useState<Country[]>([]);
  const [countriesSearch, setCountriesSearch] = useState('');
  const [isAddCountryModalOpen, setIsAddCountryModalOpen] = useState(false);
  const [newCountry, setNewCountry] = useState({
    name_ar: '',
    name_en: '',
    code: '',
    phone_code: '',
    currency: 'AED',
    sort_order: 50
  });
  const [addingCountry, setAddingCountry] = useState(false);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [s, lic, c, logs, countryData] = await Promise.all([
        api.getSettings(),
        api.getLicenseStatus(),
        fetch('/api/cloud/config').then((r) => r.json()).catch(() => ({})),
        api.getAuditLogs(),
        api.getCountries(true).catch(() => [])
      ]);
      if (s && s.store_name_ar) setSettings(s);
      setLicense(lic);
      setCloud(c);
      setAuditLogs(logs || []);
      setCountries(countryData || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCountries = async () => {
    try {
      const data = await api.getCountries(true);
      setCountries(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateSettings(settings);
      alert('✅ تم حفظ إعدادات المتجر بنجاح');
    } catch (err: any) {
      alert('فشل حفظ الإعدادات');
    } finally {
      setSaving(false);
    }
  };

  const handleActivateLicense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!licenseKeyInput.trim()) return;
    try {
      const res = await api.activateLicense(licenseKeyInput.trim());
      if (res.success) {
        alert('🎉 ' + res.message);
        loadAll();
      } else {
        alert('❌ ' + res.message);
      }
    } catch (err: any) {
      alert('فشل تفعيل الترخيص');
    }
  };

  // Toggle Country Active Status
  const handleToggleCountry = async (country: Country) => {
    try {
      const newStatus = country.is_active ? 0 : 1;
      await api.updateCountry(country.id, { is_active: newStatus });
      setCountries((prev) =>
        prev.map((c) => (c.id === country.id ? { ...c, is_active: newStatus } : c))
      );
    } catch (err: any) {
      alert(err.response?.data?.error || 'تعذر تعديل حالة تفعيل الدولة');
    }
  };

  // Delete Country (Allowed for non-system custom countries)
  const handleDeleteCountry = async (country: Country) => {
    if (!confirm(`هل أنت متأكد من حذف الدولة (${country.name_ar})؟`)) return;
    try {
      await api.deleteCountry(country.id);
      setCountries((prev) => prev.filter((c) => c.id !== country.id));
      alert('✅ تم حذف الدولة بنجاح');
    } catch (err: any) {
      alert(err.response?.data?.error || 'تعذر حذف الدولة');
    }
  };

  // Create New Country
  const handleCreateCountry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCountry.name_ar.trim()) {
      alert('يرجى كتابة اسم الدولة بالعربية');
      return;
    }

    setAddingCountry(true);
    try {
      await api.createCountry(newCountry);
      await loadCountries();
      setIsAddCountryModalOpen(false);
      setNewCountry({
        name_ar: '',
        name_en: '',
        code: '',
        phone_code: '',
        currency: 'AED',
        sort_order: 50
      });
      alert('🎉 تم إضافة الدولة بنجاح إلى قائمة وجهات الشحن وتظهر للعملاء الآن');
    } catch (err: any) {
      alert(err.response?.data?.error || 'تعذر إضافة الدولة');
    } finally {
      setAddingCountry(false);
    }
  };

  const filteredCountries = countries.filter((c) => {
    const q = countriesSearch.trim().toLowerCase();
    if (!q) return true;
    return (
      c.name_ar.toLowerCase().includes(q) ||
      (c.name_en && c.name_en.toLowerCase().includes(q)) ||
      (c.code && c.code.toLowerCase().includes(q)) ||
      (c.phone_code && c.phone_code.includes(q))
    );
  });

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
          <Settings className="w-5 h-5 text-[#C9972B]" />
          <span>إعدادات النظام، وجهات الشحن والمزامنة</span>
        </h2>
        <p className="text-xs text-[#746A5D] mt-1">
          تخصيص بيانات المتجر والفواتير، إدارة الدول ووجهات الشحن، ترخيص الجهاز المادي (HWID)، وإعدادات سحابة Turso.
        </p>
      </div>

      {/* Grid of Sections */}
      <div className="space-y-6">
        {/* 1. Store & Invoice Settings */}
        <form onSubmit={handleSaveSettings} className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2 border-b border-[#F2ECE1] pb-3">
            <Settings className="w-4 h-4 text-[#C9972B]" />
            <span>بيانات المتجر والفواتير والضريبة</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم المتجر بالعربية</label>
              <input
                type="text"
                value={settings.store_name_ar}
                onChange={(e) => setSettings({ ...settings, store_name_ar: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم المتجر بالإنجليزية</label>
              <input
                type="text"
                value={settings.store_name_en}
                onChange={(e) => setSettings({ ...settings, store_name_en: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم هاتف المتجر</label>
              <input
                type="text"
                value={settings.phone}
                onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الواتساب الرسمي (بدون + أو مسافات)</label>
              <input
                type="text"
                value={settings.whatsapp_number}
                onChange={(e) => setSettings({ ...settings, whatsapp_number: e.target.value })}
                placeholder="971504084006"
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] font-mono focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">البريد الإلكتروني</label>
              <input
                type="email"
                value={settings.email}
                onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">مقر المتجر / صالة العرض</label>
              <input
                type="text"
                value={settings.address}
                onChange={(e) => setSettings({ ...settings, address: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">عبارة الشكر أسفل الفاتورة</label>
            <input
              type="text"
              value={settings.invoice_thank_you}
              onChange={(e) => setSettings({ ...settings, invoice_thank_you: e.target.value })}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'جار الحفظ...' : 'حفظ الإعدادات'}</span>
            </button>
          </div>
        </form>

        {/* 2. Countries & Shipping Destinations Section (NEW) */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#F2ECE1] pb-3">
            <div>
              <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#C9972B]" />
                <span>إدارة الدول ووجهات الشحن (قائمة منسدلة تلقائية عند طلب العميل)</span>
              </h3>
              <p className="text-xs text-[#746A5D] mt-0.5">
                تضم جميع الدول العربية الـ 22 مفعلة تلقائياً مع إمكانية إضافة وتفعيل دول عالمية أخرى للشحن الدولي.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-[#9A6817] bg-[#FAF4E8] px-3 py-1 rounded-xl border border-[#EADBCE]">
                الإجمالي: {countries.length} دولة
              </span>
              <button
                type="button"
                onClick={() => setIsAddCountryModalOpen(true)}
                className="px-3.5 py-1.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>إضافة دولة أخرى</span>
              </button>
            </div>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-[#8C8275] absolute right-3 top-2.5" />
            <input
              type="text"
              placeholder="ابحث عن دولة بالاسم، الرمز (SA, AE, EG...) أو المفتاح الدولي..."
              value={countriesSearch}
              onChange={(e) => setCountriesSearch(e.target.value)}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl pr-9 pl-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
          </div>

          {/* Countries Table / List */}
          <div className="max-h-[320px] overflow-y-auto border border-[#EBE3D5] rounded-2xl divide-y divide-[#F2ECE1]">
            {filteredCountries.length === 0 ? (
              <div className="p-6 text-center text-[#8C8275] text-xs">لا توجد دول مطابقة لبحثك.</div>
            ) : (
              filteredCountries.map((c) => (
                <div
                  key={c.id}
                  className="p-3 bg-white hover:bg-[#FAF7F2]/60 flex items-center justify-between gap-3 text-xs transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#FAF4E8] border border-[#EADBCE] text-[#9A6817] flex items-center justify-center font-bold text-xs font-mono">
                      {c.code || '🌐'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#26221C]">{c.name_ar}</span>
                        {c.name_en && (
                          <span className="text-[11px] text-[#746A5D] font-mono">({c.name_en})</span>
                        )}
                        {c.is_system ? (
                          <span className="text-[9px] px-2 py-0.5 rounded-full bg-[#FAF4E8] text-[#9A6817] font-semibold border border-[#EADBCE]">
                            دولة عربية أساسية
                          </span>
                        ) : (
                          <span className="text-[9px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                            مخصصة
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-[#8C8275] mt-0.5">
                        {c.phone_code && <span>مفتاح الاتصال: <b className="font-mono">{c.phone_code}</b></span>}
                        {c.currency && <span>• العملة: <b className="font-mono">{c.currency}</b></span>}
                        <span>• الترتيب: {c.sort_order}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Active Toggle Button */}
                    <button
                      type="button"
                      onClick={() => handleToggleCountry(c)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition cursor-pointer flex items-center gap-1 ${
                        c.is_active
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                          : 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200'
                      }`}
                      title={c.is_active ? 'انقر للتعطيل من القائمة' : 'انقر للتفعيل بالقائمة'}
                    >
                      <Check className={`w-3 h-3 ${c.is_active ? 'text-emerald-600' : 'text-gray-400'}`} />
                      <span>{c.is_active ? 'مفعلة' : 'معطلة'}</span>
                    </button>

                    {/* Delete Custom Country Button */}
                    {!c.is_system && (
                      <button
                        type="button"
                        onClick={() => handleDeleteCountry(c)}
                        className="p-1.5 rounded-lg text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition cursor-pointer"
                        title="حذف هذه الدولة"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 3. Hardware License Verification */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#F2ECE1] pb-3">
            <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#C9972B]" />
              <span>ترخيص النظام وبصمة العتاد المادي (HWID)</span>
            </h3>
            {license?.licensed ? (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>النسخة مرخصة ورسمية</span>
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                وضع التجربة (Trial Mode)
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-2xl bg-[#FAF7F2] border border-[#EEE6D8]">
              <span className="text-[#746A5D] block mb-1">بصمة العتاد المادي (Hardware ID):</span>
              <span className="font-mono font-bold text-[#26221C] select-all">{license?.hwid || 'جاري الفحص...'}</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#FAF7F2] border border-[#EEE6D8]">
              <span className="text-[#746A5D] block mb-1">حالة التفعيل:</span>
              <span className="font-bold text-[#9A6817]">{license?.message || 'غير مفعل'}</span>
            </div>
          </div>

          <form onSubmit={handleActivateLicense} className="flex gap-2">
            <input
              type="text"
              placeholder="أدخل مفتاح ترخيص النسخة (License Key)..."
              value={licenseKeyInput}
              onChange={(e) => setLicenseKeyInput(e.target.value)}
              className="flex-1 bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-[#FAF4E8] hover:bg-[#FAF7F2] text-[#9A6817] font-bold text-xs rounded-xl border border-[#E0D7C6] transition cursor-pointer"
            >
              تفعيل الترخيص
            </button>
          </form>
        </div>

        {/* 4. Turso Cloud Sync Configuration */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2 border-b border-[#F2ECE1] pb-3">
            <Cloud className="w-4 h-4 text-[#C9972B]" />
            <span>سحابة Turso ومزامنة الفروع الموزعة (Distributed libSQL)</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">Turso Database URL</label>
              <input
                type="text"
                placeholder="libsql://haybatalsultan-...turso.io"
                value={cloud.turso_url || ''}
                onChange={(e) => setCloud({ ...cloud, turso_url: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] font-mono focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">Turso Auth Token</label>
              <input
                type="password"
                placeholder="eyJhbGciOi..."
                value={cloud.turso_auth_token || ''}
                onChange={(e) => setCloud({ ...cloud, turso_auth_token: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] font-mono focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <p className="text-[11px] text-[#746A5D] leading-relaxed">
            * يدعم النظام العمل المحلي الكامل في وضع عدم الاتصال (Offline-First) بواسطة محرك SQLite المدمج في data/haybatalsultan.db مع المزامنة التلقائية عند توفر الإنترنت.
          </p>
        </div>

        {/* 5. Immutable Audit Logs */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2 border-b border-[#F2ECE1] pb-3">
            <FileText className="w-4 h-4 text-[#C9972B]" />
            <span>سجل التدقيق الرقابي غير القابل للمسح (Audit Logs)</span>
          </h3>

          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 text-xs">
            {auditLogs.length === 0 ? (
              <p className="text-[#746A5D] text-center py-4">لا توجد سجلات تدقيق بعد.</p>
            ) : (
              auditLogs.slice(0, 50).map((log) => (
                <div key={log.id} className="p-2.5 rounded-xl bg-[#FAF7F2] border border-[#EEE6D8] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#9A6817] font-mono text-[11px]">{log.action}</span>
                    <span className="text-[#26221C]">{log.actor_name} ({log.actor_role})</span>
                  </div>
                  <span className="text-[#8C8275] text-[10px]">{log.created_at}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Modal: Add New Country */}
      {isAddCountryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-md shadow-2xl overflow-hidden my-6">
            <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-[#26221C]">إضافة دولة أو وجهة شحن جديدة</h4>
                  <p className="text-[11px] text-[#746A5D]">تظهر فوراً في القائمة المنسدلة للعميل عند الطلب</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAddCountryModalOpen(false)}
                className="p-1 rounded-lg text-[#8C8275] hover:text-[#26221C]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCountry} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم الدولة بالعربية *</label>
                <input
                  type="text"
                  required
                  placeholder="مثال: المملكة المتحدة، ألمانيا، تركيا..."
                  value={newCountry.name_ar}
                  onChange={(e) => setNewCountry({ ...newCountry, name_ar: e.target.value })}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">الاسم بالإنجليزية</label>
                  <input
                    type="text"
                    placeholder="United Kingdom"
                    value={newCountry.name_en}
                    onChange={(e) => setNewCountry({ ...newCountry, name_en: e.target.value })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">رمز الدولة (ISO)</label>
                  <input
                    type="text"
                    placeholder="GB, DE, TR..."
                    value={newCountry.code}
                    onChange={(e) => setNewCountry({ ...newCountry, code: e.target.value.toUpperCase() })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs font-mono text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">مفتاح الاتصال الدولي</label>
                  <input
                    type="text"
                    placeholder="+44, +49, +90..."
                    value={newCountry.phone_code}
                    onChange={(e) => setNewCountry({ ...newCountry, phone_code: e.target.value })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs font-mono text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">العملة المفضلة</label>
                  <input
                    type="text"
                    placeholder="AED, USD, EUR..."
                    value={newCountry.currency}
                    onChange={(e) => setNewCountry({ ...newCountry, currency: e.target.value.toUpperCase() })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs font-mono text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">ترتيب الظهور في القائمة</label>
                <input
                  type="number"
                  value={newCountry.sort_order}
                  onChange={(e) => setNewCountry({ ...newCountry, sort_order: Number(e.target.value) })}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div className="pt-3 border-t border-[#F2ECE1] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsAddCountryModalOpen(false)}
                  className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-semibold rounded-xl cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={addingCountry}
                  className="px-5 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {addingCountry ? 'جار الحفظ...' : 'حفظ الدولة وتفعيلها'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
