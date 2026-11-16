import React, { useState, useEffect } from 'react';
import {
  X,
  User as UserIcon,
  ShieldCheck,
  Lock,
  Phone,
  Mail,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';
import { User } from '../types';
import { PERMISSION_MODULES, ROLE_PRESETS, ALL_PERMISSION_KEYS } from '../lib/permissions';

interface UserModalProps {
  user: User | null; // null if adding new user
  isOpen: boolean;
  onClose: () => void;
  onSave: (userData: any) => Promise<void>;
  currentAdminName: string;
}

export const UserModal: React.FC<UserModalProps> = ({
  user,
  isOpen,
  onClose,
  onSave,
  currentAdminName
}) => {
  const isEdit = Boolean(user);

  const [activeTab, setActiveTab] = useState<'INFO' | 'PERMISSIONS'>('INFO');
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'OWNER' | 'SUPERVISOR' | 'SALES' | 'ACCOUNTANT' | 'WORKSHOP'>('SALES');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [permissions, setPermissions] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setUsername(user.username || '');
      setPassword(''); // Keep empty if not changing
      setRole((user.role as any) || 'SALES');
      setPhone(user.phone || '');
      setEmail(user.email || '');
      setIsActive(user.is_active !== undefined ? Boolean(user.is_active) : true);

      // Initialize permissions from user or fallback to preset
      const existingPerms = user.permissions && typeof user.permissions === 'object' ? user.permissions : {};
      const preset = ROLE_PRESETS[user.role] || {};
      const merged: Record<string, boolean> = {};
      ALL_PERMISSION_KEYS.forEach(key => {
        merged[key] = existingPerms[key] !== undefined ? Boolean(existingPerms[key]) : Boolean(preset[key]);
      });
      setPermissions(merged);
    } else {
      // New User Default
      setFullName('');
      setUsername('');
      setPassword('');
      setRole('SALES');
      setPhone('');
      setEmail('');
      setIsActive(true);
      setPermissions({ ...(ROLE_PRESETS.SALES || {}) });
    }
    setActiveTab('INFO');
    setErrorMsg('');
  }, [user, isOpen]);

  if (!isOpen) return null;

  const handleRoleChange = (newRole: any) => {
    setRole(newRole);
    // Apply preset for this role
    const preset = ROLE_PRESETS[newRole] || {};
    const updated: Record<string, boolean> = {};
    ALL_PERMISSION_KEYS.forEach(key => {
      updated[key] = Boolean(preset[key]);
    });
    setPermissions(updated);
  };

  const handleTogglePermission = (key: string) => {
    if (role === 'OWNER') return; // Owner has all permissions
    setPermissions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleToggleModule = (moduleId: string, enableAll: boolean) => {
    if (role === 'OWNER') return;
    const mod = PERMISSION_MODULES.find(m => m.id === moduleId);
    if (!mod) return;
    setPermissions(prev => {
      const next = { ...prev };
      mod.permissions.forEach(p => {
        next[p.key] = enableAll;
      });
      return next;
    });
  };

  const handleToggleAll = (enableAll: boolean) => {
    if (role === 'OWNER') return;
    const next: Record<string, boolean> = {};
    ALL_PERMISSION_KEYS.forEach(k => {
      next[k] = enableAll;
    });
    setPermissions(next);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!fullName.trim() || !username.trim()) {
      setErrorMsg('الاسم واسم المستخدم مطلوبان');
      return;
    }

    if (!isEdit && !password.trim()) {
      setErrorMsg('كلمة المرور مطلوبة لإنشاء مستخدم جديد');
      return;
    }

    setLoading(true);
    try {
      await onSave({
        full_name: fullName.trim(),
        username: username.trim(),
        password: password.trim() || undefined,
        role,
        phone: phone.trim(),
        email: email.trim(),
        is_active: isActive ? 1 : 0,
        permissions,
        actor_name: currentAdminName
      });
      onClose();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error || err.message || 'حدث خطأ أثناء حفظ المستخدم');
    } finally {
      setLoading(false);
    }
  };

  const activePermissionsCount = ALL_PERMISSION_KEYS.filter(k => permissions[k]).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-sm p-4" dir="rtl">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Top Header */}
        <div className="bg-gradient-to-r from-[#FAF4E8] via-[#FFFDF8] to-[#F5ECE0] p-5 border-b border-[#EBE3D5] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#C9972B] text-white flex items-center justify-center shadow-md">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-[#26221C]">
                {isEdit ? `تعديل المستخدم وصلاحياته: ${user?.full_name}` : 'إضافة موظف ومستخدم جديد للنظام'}
              </h2>
              <p className="text-xs text-[#746A5D]">
                تخصيص الأدوار والصلاحيات الفردية والتحكم في كافة شاشات وعمليات التطبيق
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white hover:bg-rose-50 text-[#8C8275] hover:text-rose-600 flex items-center justify-center transition border border-[#EADBCE]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-6 pt-4 border-b border-[#F0E8DC] bg-[#FCFBF8]">
          <button
            type="button"
            onClick={() => setActiveTab('INFO')}
            className={`px-4 py-2.5 text-xs font-bold rounded-t-xl transition border-b-2 flex items-center gap-1.5 ${
              activeTab === 'INFO'
                ? 'border-[#C9972B] text-[#9A6817] bg-white'
                : 'border-transparent text-[#746A5D] hover:text-[#26221C]'
            }`}
          >
            <UserIcon className="w-4 h-4" />
            <span>بيانات الموظف الأساسية</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('PERMISSIONS')}
            className={`px-4 py-2.5 text-xs font-bold rounded-t-xl transition border-b-2 flex items-center gap-1.5 ${
              activeTab === 'PERMISSIONS'
                ? 'border-[#C9972B] text-[#9A6817] bg-white'
                : 'border-transparent text-[#746A5D] hover:text-[#26221C]'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>مصفوفة الصلاحيات الفردية</span>
            <span className="text-[10px] bg-[#FAF4E8] text-[#9A6817] border border-[#E4D5B8] px-2 py-0.5 rounded-full font-mono">
              {activePermissionsCount} / {ALL_PERMISSION_KEYS.length}
            </span>
          </button>
        </div>

        {/* Modal Body Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {activeTab === 'INFO' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    الاسم الكامل للموظف <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="مثال: محمد سعيد العبدالله"
                    className="w-full px-4 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    اسم المستخدم (معرف الدخول) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    disabled={isEdit && user?.username === 'owner'}
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    placeholder="مثال: mohamed_sales"
                    className="w-full px-4 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    الدور الوظيفي الأساسي <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={role}
                    disabled={isEdit && user?.username === 'owner'}
                    onChange={e => handleRoleChange(e.target.value)}
                    className="w-full px-4 py-2.5 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-bold text-[#26221C]"
                  >
                    <option value="OWNER">👑 مالك المتجر (OWNER - كافة الصلاحيات بدون قيود)</option>
                    <option value="SUPERVISOR">🛡️ مشرف عام (SUPERVISOR - إدارة العمليات والعهد)</option>
                    <option value="SALES">🛍️ مسؤول مبيعات وكاشير (SALES - نقاط البيع فقط)</option>
                    <option value="ACCOUNTANT">📊 محاسب مالي (ACCOUNTANT - المالية والمصروفات)</option>
                    <option value="WORKSHOP">✂️ فني ورشة (WORKSHOP - تعديل وقص الخرز)</option>
                  </select>
                  <p className="text-[10px] text-[#8C8275] mt-1">
                    اختيار الدور يعين الصلاحيات الافتراضية المناسبة، ويمكنك تخصيص أي صلاحية بعد ذلك.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    {isEdit ? 'كلمة المرور (اتركها فارغة إذا لم ترغب بتغييرها)' : 'كلمة المرور *'}
                  </label>
                  <div className="relative">
                    <input
                      type="password"
                      value={password}
                      required={!isEdit}
                      onChange={e => setPassword(e.target.value)}
                      placeholder={isEdit ? '••••••••' : 'أدخل كلمة مرور قوية'}
                      className="w-full px-4 py-2.5 pr-10 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
                    />
                    <Lock className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    رقم الهاتف / الواتساب
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="+971 50 000 0000"
                      className="w-full px-4 py-2.5 pr-10 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                    />
                    <Phone className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4B4338] mb-1.5">
                    البريد الإلكتروني
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="employee@haybatalsultan.com"
                      className="w-full px-4 py-2.5 pr-10 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B]"
                    />
                    <Mail className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-3" />
                  </div>
                </div>
              </div>

              {/* Status Switch */}
              <div className="pt-2 border-t border-[#F0E8DC] flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-[#26221C]">حالة تنشيط الحساب</p>
                  <p className="text-[11px] text-[#746A5D]">المستخدمون المعطلون لا يمكنهم تسجيل الدخول للنظام</p>
                </div>

                <button
                  type="button"
                  disabled={isEdit && user?.username === 'owner'}
                  onClick={() => setIsActive(!isActive)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition border ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border-rose-200'
                  }`}
                >
                  {isActive ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>الحساب نشط</span>
                    </>
                  ) : (
                    <>
                      <X className="w-4 h-4 text-rose-600" />
                      <span>الحساب معطل</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'PERMISSIONS' && (
            <div className="space-y-6">
              {/* Quick Actions Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-[#FAF4E8] rounded-2xl border border-[#E4D5B8]">
                <div className="flex items-center gap-2 text-xs font-bold text-[#9A6817]">
                  <Sparkles className="w-4 h-4 text-[#C9972B]" />
                  <span>تخصيص الصلاحيات الفردية للموظف</span>
                </div>

                {role !== 'OWNER' && (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleToggleAll(true)}
                      className="px-2.5 py-1 text-[11px] font-bold bg-white text-[#9A6817] hover:bg-[#F3E7CE] border border-[#EADBCE] rounded-lg transition"
                    >
                      تحديد الكل
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleAll(false)}
                      className="px-2.5 py-1 text-[11px] font-bold bg-white text-rose-700 hover:bg-rose-50 border border-rose-200 rounded-lg transition"
                    >
                      إلغاء الكل
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRoleChange(role)}
                      className="px-2.5 py-1 text-[11px] font-bold bg-white text-[#4B4338] hover:bg-slate-100 border border-[#EADBCE] rounded-lg transition flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>استعادة افتراضي الدور</span>
                    </button>
                  </div>
                )}
              </div>

              {role === 'OWNER' && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 font-bold flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0" />
                  <span>حساب مالك المتجر (OWNER) يمتلك صلاحيات مطلقة وغير مقيدة لكافة أجزاء النظام ولا يمكن حجب أي صلاحية عنه.</span>
                </div>
              )}

              {/* Modules Matrix */}
              <div className="space-y-4">
                {PERMISSION_MODULES.map(module => {
                  const moduleActiveCount = module.permissions.filter(p => permissions[p.key]).length;
                  const allActive = moduleActiveCount === module.permissions.length;

                  return (
                    <div
                      key={module.id}
                      className="bg-white border border-[#EBE3D5] rounded-2xl overflow-hidden shadow-xs"
                    >
                      {/* Module Header */}
                      <div className="bg-[#FAF7F2] p-3 border-b border-[#EEE4D4] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-[#26221C]">{module.label_ar}</span>
                          <span className="text-[10px] text-[#8C8275] bg-white px-2 py-0.5 rounded-full border border-[#DDD3C1]">
                            {moduleActiveCount} / {module.permissions.length}
                          </span>
                        </div>

                        {role !== 'OWNER' && (
                          <div className="flex items-center gap-1.5 text-[11px]">
                            <button
                              type="button"
                              onClick={() => handleToggleModule(module.id, !allActive)}
                              className="text-[#9A6817] hover:underline font-bold"
                            >
                              {allActive ? 'إلغاء القسم' : 'تفعيل القسم'}
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Permissions Checklist */}
                      <div className="p-3.5 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {module.permissions.map(perm => {
                          const isChecked = role === 'OWNER' ? true : Boolean(permissions[perm.key]);

                          return (
                            <label
                              key={perm.key}
                              className={`flex items-start gap-2.5 p-2.5 rounded-xl border transition cursor-pointer select-none ${
                                isChecked
                                  ? 'bg-[#FAF4E8]/60 border-[#E4D5B8] text-[#26221C]'
                                  : 'bg-white border-[#F0E8DC] text-[#746A5D] hover:bg-[#FAF7F2]'
                              }`}
                            >
                              <input
                                type="checkbox"
                                disabled={role === 'OWNER'}
                                checked={isChecked}
                                onChange={() => handleTogglePermission(perm.key)}
                                className="mt-1 w-4 h-4 text-[#C9972B] rounded border-[#DDD3C1] focus:ring-[#C9972B]"
                              />
                              <div className="space-y-0.5">
                                <p className="text-xs font-bold">{perm.label_ar}</p>
                                <p className="text-[10px] text-[#8C8275]">{perm.description_ar}</p>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Modal Footer Actions */}
          <div className="pt-4 border-t border-[#EBE3D5] flex items-center justify-between">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-[#746A5D] hover:bg-[#F2ECE1] transition border border-[#EADBCE]"
            >
              إلغاء
            </button>

            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl text-xs font-black bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] shadow-md transition disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-[#E2B84B] border-t-transparent rounded-full animate-spin" />
                  <span>جارٍ الحفظ...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{isEdit ? 'حفظ التعديلات والصلاحيات' : 'إنشاء المستخدم وتعيين الصلاحيات'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
