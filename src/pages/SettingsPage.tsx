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
  AlertCircle,
  Image,
  Sparkles,
  Layers,
  Edit2,
  Upload
} from 'lucide-react';
import { api } from '../lib/api';
import { StoreSettings, Country, Banner } from '../types';
import { toast } from '../utils/toast';
import { compressImageFile } from '../lib/imageCompressor';

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

  // Banners & Announcement Slider State
  const [banners, setBanners] = useState<Banner[]>([]);
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [editingBanner, setEditingBanner] = useState<Banner | null>(null);
  const [bannerForm, setBannerForm] = useState({
    title: '',
    subtitle: '',
    image_url: '',
    button_text: 'تسوق المجموعة',
    link_url: '#products-section',
    is_active: true,
    sort_order: 1
  });
  const [isUploadingBannerImage, setIsUploadingBannerImage] = useState(false);
  const [savingBanner, setSavingBanner] = useState(false);

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
      const [s, lic, c, logs, countryData, bannerData] = await Promise.all([
        api.getSettings(),
        api.getLicenseStatus(),
        fetch('/api/cloud/config').then((r) => r.json()).catch(() => ({})),
        api.getAuditLogs(),
        api.getCountries(true).catch(() => []),
        api.getBanners(true).catch(() => [])
      ]);
      if (s && s.store_name_ar) setSettings(s);
      setLicense(lic);
      setCloud(c);
      setAuditLogs(logs || []);
      setCountries(countryData || []);
      setBanners(bannerData || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadBanners = async () => {
    try {
      const data = await api.getBanners(true);
      setBanners(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenAddBannerModal = () => {
    setEditingBanner(null);
    setBannerForm({
      title: '',
      subtitle: '',
      image_url: '',
      button_text: 'تسوق المجموعة',
      link_url: '#products-section',
      is_active: true,
      sort_order: (banners.length + 1) * 10
    });
    setIsBannerModalOpen(true);
  };

  const handleOpenEditBannerModal = (b: Banner) => {
    setEditingBanner(b);
    setBannerForm({
      title: b.title || '',
      subtitle: b.subtitle || '',
      image_url: b.image_url || '',
      button_text: b.button_text || 'تسوق المجموعة',
      link_url: b.link_url || '#products-section',
      is_active: Boolean(b.is_active),
      sort_order: b.sort_order || 1
    });
    setIsBannerModalOpen(true);
  };

  const handleBannerImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingBannerImage(true);
    try {
      const compressed = await compressImageFile(file, 1600, 0.85);
      const res = await api.uploadImage(compressed.dataUrl, file.name);
      if (res && res.url) {
        setBannerForm((prev) => ({ ...prev, image_url: res.url }));
        toast.success('تم رفع وضغط صورة الإعلان بنجاح');
      }
    } catch (err: any) {
      console.error(err);
      toast.error('فشل رفع صورة الإعلان');
    } finally {
      setIsUploadingBannerImage(false);
    }
  };

  const handleSaveBanner = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bannerForm.image_url.trim()) {
      toast.error('يرجى اختيار أو رفع صورة للإعلان');
      return;
    }

    setSavingBanner(true);
    try {
      if (editingBanner) {
        await api.updateBanner(editingBanner.id, {
          ...bannerForm,
          is_active: bannerForm.is_active ? 1 : 0
        });
        toast.success('تم تحديث الإعلان بنجاح');
      } else {
        await api.createBanner({
          ...bannerForm,
          is_active: bannerForm.is_active ? 1 : 0
        });
        toast.success('تمت إضافة الإعلان الجديد بنجاح');
      }
      setIsBannerModalOpen(false);
      await loadBanners();
    } catch (err: any) {
      console.error(err);
      toast.error('فشل حفظ الإعلان');
    } finally {
      setSavingBanner(false);
    }
  };

  const handleToggleBannerActive = async (banner: Banner) => {
    try {
      const newActive = banner.is_active ? 0 : 1;
      await api.updateBanner(banner.id, {
        ...banner,
        is_active: newActive
      });
      toast.success(newActive ? 'تم تفعيل الإعلان في السلايدر' : 'تم تعطيل الإعلان مؤقتاً');
      await loadBanners();
    } catch (err) {
      toast.error('فشل تعديل حالة الإعلان');
    }
  };

  const handleDeleteBanner = async (id: number) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا الإعلان من السلايدر نهائياً؟')) return;
    try {
      await api.deleteBanner(id);
      toast.success('تم حذف الإعلان من السلايدر');
      await loadBanners();
    } catch (err) {
      toast.error('فشل حذف الإعلان');
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
      toast.success('تم حفظ إعدادات المتجر بنجاح');
    } catch (err: any) {
      toast.error('فشل حفظ الإعدادات');
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
        toast.success(res.message, 'تفعيل الترخيص');
        loadAll();
      } else {
        toast.error(res.message, 'تنبيه الترخيص');
      }
    } catch (err: any) {
      toast.error('فشل تفعيل الترخيص');
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
      toast.info(`تم ${newStatus ? 'تفعيل' : 'تعطيل'} الشحن إلى (${country.name_ar})`);
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر تعديل حالة تفعيل الدولة');
    }
  };

  // Delete Country (Allowed for non-system custom countries)
  const handleDeleteCountry = async (country: Country) => {
    const confirmed = await toast.confirm({
      title: 'حذف دولة شحن',
      message: `هل أنت متأكد من حذف الدولة (${country.name_ar})؟`,
      confirmText: 'حذف الدولة',
      cancelText: 'إلغاء',
      type: 'danger'
    });
    if (!confirmed) return;
    try {
      await api.deleteCountry(country.id);
      setCountries((prev) => prev.filter((c) => c.id !== country.id));
      toast.success('تم حذف الدولة بنجاح');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر حذف الدولة');
    }
  };

  // Create New Country
  const handleCreateCountry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCountry.name_ar.trim()) {
      toast.warning('يرجى كتابة اسم الدولة بالعربية');
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
      toast.success('تم إضافة الدولة بنجاح إلى قائمة وجهات الشحن وتظهر للعملاء الآن');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر إضافة الدولة');
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

        {/* 2. Hero Banners & Announcements Slider Management */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#F2ECE1] pb-3">
            <div>
              <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2">
                <Image className="w-4 h-4 text-[#C9972B]" />
                <span>إدارة إعلانات وبنرات الواجهة الرئيسية (سلايدر العروض)</span>
              </h3>
              <p className="text-xs text-[#746A5D] mt-0.5">
                تتبادل الصور تلقائياً في واجهة المتجر كشريط متحرك فاخر. الصورة الأساسية للمتجر تظل ثابتة كشريحة رئيسية دائماً.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-[#9A6817] bg-[#FAF4E8] px-3 py-1 rounded-xl border border-[#EADBCE]">
                {banners.length + 1} شرائح (1 أساسية + {banners.length} إعلانات)
              </span>
              <button
                type="button"
                onClick={handleOpenAddBannerModal}
                className="px-3.5 py-1.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>إضافة إعلان جديد</span>
              </button>
            </div>
          </div>

          {/* Fixed Base Banner Display (Cannot be deleted or moved) */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-[#FAF6EE] to-[#F5EFE3] border border-[#E8DEC8] flex flex-col sm:flex-row items-center gap-4">
            <div className="relative w-full sm:w-48 h-24 rounded-xl overflow-hidden shrink-0 border border-[#D8CCA8] shadow-xs bg-black">
              <img
                src="/branding/hero-amber.jpg"
                alt="هيبة الأصل... جمال الكهرمان"
                className="w-full h-full object-cover"
              />
              <span className="absolute top-1.5 right-1.5 bg-black/75 backdrop-blur-xs text-[#E2B84B] text-[9px] font-black px-2 py-0.5 rounded-md">
                الشريحة 1 (الرئيسية)
              </span>
            </div>

            <div className="flex-1 space-y-1 text-center sm:text-right">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <span className="font-extrabold text-sm text-[#26221C]">هيبة الأصل... جمال الكهرمان</span>
                <span className="text-[10px] font-bold bg-[#C9972B] text-black px-2 py-0.5 rounded-md flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-black" />
                  <span>الصورة الأساسية الثابتة (دائمة)</span>
                </span>
              </div>
              <p className="text-xs text-[#746A5D]">
                مسابيح وأحجار طبيعية ونوادر مختارة بعناية لعشاق التميز • زر الإجراء: «تسوق المجموعة»
              </p>
              <p className="text-[10px] text-[#9E9485]">
                🔒 هذه هي الصورة الأساسية للمتجر، تظل ثابتة دائماً وتتبادل مع أي صور إعلانات تضيفها أدناه.
              </p>
            </div>
          </div>

          {/* List of Custom Announcement Banners */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-[#4B4338] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>الإعلانات والبنرات الإضافية المضافة:</span>
            </h4>

            {banners.length === 0 ? (
              <div className="p-6 text-center border border-dashed border-[#E0D7C6] rounded-2xl bg-[#FAF8F5] text-xs text-[#8C8275] space-y-2">
                <p>لا توجد إعلانات إضافية حالياً. السلايدر يعرض الصورة الأساسية الثابتة للمتجر.</p>
                <button
                  type="button"
                  onClick={handleOpenAddBannerModal}
                  className="px-4 py-1.5 bg-white hover:bg-[#FAF4E8] text-[#9A6817] border border-[#D8CCA8] rounded-xl text-xs font-bold inline-flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Plus className="w-3 h-3" />
                  <span>إضافة أول إعلان / بنر ترويجي الآن</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {banners.map((b, idx) => (
                  <div
                    key={b.id}
                    className="p-3 bg-white border border-[#EBE3D5] rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 hover:border-[#C9972B] transition shadow-2xs"
                  >
                    <div className="flex items-center gap-3 w-full sm:w-auto">
                      <div className="relative w-28 h-16 rounded-xl overflow-hidden shrink-0 border border-[#EADBCE] bg-[#F7F3EC]">
                        <img
                          src={b.image_url}
                          alt={b.title || 'إعلان'}
                          className="w-full h-full object-cover"
                        />
                        <span className="absolute bottom-1 right-1 bg-black/70 text-white text-[8px] font-bold px-1.5 py-0.5 rounded">
                          #{idx + 2}
                        </span>
                      </div>
                      <div className="space-y-0.5 min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-[#26221C] truncate">{b.title || 'بدون عنوان (صورة إعلانية فقط)'}</span>
                          {b.is_active ? (
                            <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[9px] font-bold px-1.5 py-0.5 rounded">
                              نشط في السلايدر
                            </span>
                          ) : (
                            <span className="bg-neutral-100 text-neutral-500 border border-neutral-200 text-[9px] font-bold px-1.5 py-0.5 rounded">
                              معطل
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#746A5D] truncate">{b.subtitle || 'بدون وصف'}</p>
                        <div className="text-[10px] text-[#9E9485] flex items-center gap-2">
                          <span>الترتيب: {b.sort_order}</span>
                          {b.link_url && <span className="font-mono text-[#9A6817] truncate">{b.link_url}</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <button
                        type="button"
                        onClick={() => handleToggleBannerActive(b)}
                        className={`px-2.5 py-1 text-[11px] font-bold rounded-xl border transition cursor-pointer ${
                          b.is_active
                            ? 'bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-200'
                            : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-200'
                        }`}
                      >
                        {b.is_active ? 'تعطيل مؤقت' : 'تفعيل'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenEditBannerModal(b)}
                        className="p-1.5 text-[#746A5D] hover:text-[#26221C] hover:bg-[#FAF4E8] rounded-xl transition cursor-pointer"
                        title="تعديل الإعلان"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteBanner(b.id)}
                        className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition cursor-pointer"
                        title="حذف الإعلان"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 3. Countries & Shipping Destinations Section */}
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

      {/* 5. Banner / Announcement Modal */}
      {isBannerModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-lg w-full border border-[#EBE3D5] shadow-2xl overflow-hidden my-8">
            <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
              <div className="flex items-center gap-2">
                <Image className="w-5 h-5 text-[#C9972B]" />
                <h3 className="font-extrabold text-sm text-[#26221C]">
                  {editingBanner ? 'تعديل بيانات الإعلان' : 'إضافة إعلان جديد للسلايدر'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsBannerModalOpen(false)}
                className="text-[#8C8275] hover:text-[#26221C] p-1 rounded-lg hover:bg-white transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveBanner} className="p-6 space-y-4">
              {/* Image Upload & Preview */}
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1.5">
                  صورة الإعلان <span className="text-rose-500">*</span>
                </label>

                {bannerForm.image_url ? (
                  <div className="relative rounded-2xl overflow-hidden border border-[#D8CCA8] bg-black/5 aspect-21/9 mb-2.5">
                    <img
                      src={bannerForm.image_url}
                      alt="معاينة الإعلان"
                      className="w-full h-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => setBannerForm({ ...bannerForm, image_url: '' })}
                      className="absolute top-2 left-2 p-1.5 bg-black/70 hover:bg-black text-white rounded-lg backdrop-blur-xs transition cursor-pointer"
                      title="إزالة الصورة"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-[#D8CCA8] hover:border-[#C9972B] rounded-2xl p-5 text-center bg-[#FAF7F2] transition mb-2.5">
                    <input
                      type="file"
                      id="banner-image-input"
                      accept="image/*"
                      onChange={handleBannerImageUpload}
                      className="hidden"
                    />
                    <label
                      htmlFor="banner-image-input"
                      className="cursor-pointer flex flex-col items-center justify-center gap-2"
                    >
                      <div className="w-12 h-12 rounded-full bg-[#FAF4E8] border border-[#EADBCE] text-[#C9972B] flex items-center justify-center">
                        <Upload className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-bold text-[#26221C]">
                        {isUploadingBannerImage ? 'جار رفع وضغط الصورة...' : 'انقر لرفع صورة من جهازك'}
                      </span>
                      <span className="text-[10px] text-[#8C8275]">
                        يفضل استخدام صور أفقية بدقة عالية (PNG, JPG, WebP)
                      </span>
                    </label>
                  </div>
                )}

                {/* Direct URL Input */}
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="أو الصق رابط الصورة مباشرة (URL)..."
                    value={bannerForm.image_url}
                    onChange={(e) => setBannerForm({ ...bannerForm, image_url: e.target.value })}
                    className="flex-1 bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs font-mono text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              {/* Title & Subtitle */}
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                  عنوان الإعلان (يظهر بخط كبير)
                </label>
                <input
                  type="text"
                  placeholder="مثال: عروض شهر رمضان المبارك على نوادر الكهرمان"
                  value={bannerForm.title}
                  onChange={(e) => setBannerForm({ ...bannerForm, title: e.target.value })}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                  الوصف الإعلاني المختصر
                </label>
                <input
                  type="text"
                  placeholder="مثال: خصم استثنائي وقطع حصرية متوفرة لفترة محدودة"
                  value={bannerForm.subtitle}
                  onChange={(e) => setBannerForm({ ...bannerForm, subtitle: e.target.value })}
                  className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                />
              </div>

              {/* CTA Button Text & Link */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">نص زر الشراء/الإجراء</label>
                  <input
                    type="text"
                    placeholder="تسوق العرض الآن"
                    value={bannerForm.button_text}
                    onChange={(e) => setBannerForm({ ...bannerForm, button_text: e.target.value })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">الرابط الموجه للزر</label>
                  <input
                    type="text"
                    placeholder="#products-section أو رابط خارجي"
                    value={bannerForm.link_url}
                    onChange={(e) => setBannerForm({ ...bannerForm, link_url: e.target.value })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs font-mono text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>
              </div>

              {/* Sort Order & Active Toggle */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-[#4B4338] mb-1">ترتيب الظهور في السلايدر</label>
                  <input
                    type="number"
                    value={bannerForm.sort_order}
                    onChange={(e) => setBannerForm({ ...bannerForm, sort_order: Number(e.target.value) })}
                    className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                </div>

                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="banner-is-active"
                    checked={bannerForm.is_active}
                    onChange={(e) => setBannerForm({ ...bannerForm, is_active: e.target.checked })}
                    className="w-4 h-4 text-[#C9972B] rounded border-[#D8CCA8] focus:ring-[#C9972B] cursor-pointer"
                  />
                  <label htmlFor="banner-is-active" className="text-xs font-bold text-[#26221C] cursor-pointer">
                    تفعيل وظهور الإعلان في السلايدر
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-[#F2ECE1] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsBannerModalOpen(false)}
                  className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-semibold rounded-xl cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={savingBanner || isUploadingBannerImage}
                  className="px-6 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {savingBanner ? 'جار الحفظ...' : editingBanner ? 'حفظ التعديلات' : 'إضافة الإعلان'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
