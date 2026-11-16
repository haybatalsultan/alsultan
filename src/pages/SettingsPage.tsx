import React, { useState, useEffect } from 'react';
import { Settings, Shield, Cloud, Key, Save, CheckCircle, Database, FileText } from 'lucide-react';
import { api } from '../lib/api';
import { StoreSettings } from '../types';

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

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [s, lic, c, logs] = await Promise.all([
        api.getSettings(),
        api.getLicenseStatus(),
        fetch('/api/cloud/config').then(r => r.json()).catch(() => ({})),
        api.getAuditLogs()
      ]);
      if (s && s.store_name_ar) setSettings(s);
      setLicense(lic);
      setCloud(c);
      setAuditLogs(logs || []);
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

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-black text-[#26221C] flex items-center gap-2">
          <Settings className="w-5 h-5 text-[#C9972B]" />
          <span>إعدادات النظام، التراخيص والمزامنة السحابية</span>
        </h2>
        <p className="text-xs text-[#746A5D] mt-1">
          تخصيص بيانات المتجر والفواتير، ترخيص الجهاز المادي (HWID)، وإعدادات سحابة Turso.
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
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف الرسمي</label>
              <input
                type="text"
                value={settings.phone}
                onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم واتساب الطلبات</label>
              <input
                type="text"
                value={settings.whatsapp_number}
                onChange={(e) => setSettings({ ...settings, whatsapp_number: e.target.value })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">مهلة حجز السلة التنازلية (دقائق)</label>
              <input
                type="number"
                value={settings.reservation_minutes}
                onChange={(e) => setSettings({ ...settings, reservation_minutes: Number(e.target.value) })}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#9A6817] font-bold focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">عنوان المتجر والمقر الرئيسي</label>
            <input
              type="text"
              value={settings.address}
              onChange={(e) => setSettings({ ...settings, address: e.target.value })}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">عبارة الشكر وتذييل الفاتورة</label>
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
              className="px-5 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition flex items-center gap-2 shadow-[0_4px_14px_rgba(201,151,43,0.3)] cursor-pointer"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'جار الحفظ...' : 'حفظ الإعدادات'}</span>
            </button>
          </div>
        </form>

        {/* 2. Hardware ID Machine Licensing */}
        <div className="p-6 rounded-3xl bg-white border border-[#EBE3D5] space-y-4 shadow-sm">
          <h3 className="font-bold text-sm text-[#26221C] flex items-center gap-2 border-b border-[#F2ECE1] pb-3">
            <Key className="w-4 h-4 text-[#C9972B]" />
            <span>ترخيص الجهاز المادي (HWID Machine Licensing)</span>
          </h3>

          <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#E0D7C6] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div>
              <p className="text-[#746A5D]">معرف الجهاز المادي الفريد (Hardware ID):</p>
              <p className="font-mono font-bold text-[#9A6817] text-sm mt-1">{license?.hwid || 'جار الفحص...'}</p>
            </div>
            <div className="text-left">
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">
                {license?.message || 'ترخيص صالح ومفعل'}
              </span>
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

        {/* 3. Turso Cloud Sync Configuration */}
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

        {/* 4. Immutable Audit Logs */}
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
    </div>
  );
};
