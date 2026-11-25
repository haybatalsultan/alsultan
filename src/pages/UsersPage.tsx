import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Edit3,
  Trash2,
  Lock,
  Sparkles,
  Phone,
  Mail,
  UserCheck,
  Building2,
  Key,
  Clock,
  FileCheck,
  Check,
  Ban
} from 'lucide-react';
import { api } from '../lib/api';
import { User } from '../types';
import { toast } from '../utils/toast';
import { UserModal } from '../components/UserModal';
import { hasPermission } from '../lib/permissions';

interface UsersPageProps {
  currentUser: User;
}

export const UsersPage: React.FC<UsersPageProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'staff' | 'b2b'>('staff');
  const [users, setUsers] = useState<User[]>([]);
  const [b2bMerchants, setB2BMerchants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingB2B, setLoadingB2B] = useState(false);
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [b2bStatusFilter, setB2BStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const canCreate = hasPermission(currentUser, 'users.create');
  const canEdit = hasPermission(currentUser, 'users.edit');
  const canDelete = hasPermission(currentUser, 'users.delete');

  useEffect(() => {
    loadUsers();
    loadB2BMerchants();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await api.getUsers();
      setUsers(data);
    } catch (e) {
      console.error('Failed to load users:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadB2BMerchants = async () => {
    setLoadingB2B(true);
    try {
      const data = await api.getB2BMerchants();
      setB2BMerchants(data || []);
    } catch (e) {
      console.error('Failed to load B2B merchants:', e);
    } finally {
      setLoadingB2B(false);
    }
  };

  const handleApproveMerchant = async (merchantId: number, companyName: string) => {
    const confirmed = await toast.confirm({
      title: 'اعتماد تاجر جملة',
      message: `هل أنت متأكد من اعتماد ترقية حساب تاجر الجملة (${companyName}) وتمكينه من استعراض أسعار الجملة والطلب بالحد الأدنى؟`,
      confirmText: 'اعتماد التاجر',
      cancelText: 'إلغاء',
      type: 'info'
    });
    if (!confirmed) {
      return;
    }
    setActionLoadingId(merchantId);
    try {
      await api.approveB2BMerchant(merchantId);
      toast.success(`تم اعتماد التاجر (${companyName}) بنجاح! يمكنه الآن الوصول لبوابة الجملة.`, 'اعتماد تاجر جملة');
      await loadB2BMerchants();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'فشل اعتماد التاجر');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRejectMerchant = async (merchantId: number, companyName: string) => {
    const confirmed = await toast.confirm({
      title: 'تعليق / رفض تاجر جملة',
      message: `هل أنت متأكد من رفض أو تعليق طلب تاجر الجملة (${companyName})؟ سيتم سحب صلاحيات الشراء بالجملة فوراً.`,
      confirmText: 'تعليق الصلاحيات',
      cancelText: 'إلغاء',
      type: 'warning'
    });
    if (!confirmed) {
      return;
    }
    setActionLoadingId(merchantId);
    try {
      await api.rejectB2BMerchant(merchantId);
      toast.warning(`تم رفض/تعليق حساب التاجر (${companyName}) وتحويله إلى عميل عادي.`);
      await loadB2BMerchants();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'فشل رفض التاجر');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenCreate = () => {
    setSelectedUser(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (user: User) => {
    setSelectedUser(user);
    setIsModalOpen(true);
  };

  const handleSaveUser = async (userData: any) => {
    if (selectedUser) {
      // Update
      await api.updateUser(selectedUser.id, userData);
      toast.success('تم تحديث بيانات وصلاحيات المستخدم بنجاح');
    } else {
      // Create
      await api.createUser(userData);
      toast.success('تم إنشاء حساب المستخدم وتعيين الصلاحيات بنجاح');
    }
    await loadUsers();
  };

  const handleDeleteUser = async (user: User) => {
    if (user.username === 'owner' || user.id === 1) {
      toast.error('حظر أمني: لا يمكن حذف الحساب الرئيسي للمالك (owner)');
      return;
    }

    const confirmed = await toast.confirm({
      title: 'حذف مستخدم',
      message: `هل أنت متأكد من حذف المستخدم (${user.full_name} - @${user.username})؟ سيتم إلغاء وصوله للنظام نهائياً.`,
      confirmText: 'حذف نهائي',
      cancelText: 'إلغاء',
      type: 'danger'
    });
    if (!confirmed) {
      return;
    }

    try {
      await api.deleteUser(user.id, currentUser.full_name);
      toast.success('تم حذف المستخدم بنجاح');
      loadUsers();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'فشل حذف المستخدم');
    }
  };

  const filteredUsers = users.filter(u => {
    if (roleFilter !== 'ALL' && u.role !== roleFilter) return false;
    if (statusFilter === 'ACTIVE' && !u.is_active) return false;
    if (statusFilter === 'INACTIVE' && u.is_active) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        (u.full_name && u.full_name.toLowerCase().includes(q)) ||
        (u.username && u.username.toLowerCase().includes(q)) ||
        (u.phone && u.phone.includes(q)) ||
        (u.email && u.email.toLowerCase().includes(q));
      if (!match) return false;
    }

    return true;
  });

  const filteredB2BMerchants = b2bMerchants.filter(m => {
    if (b2bStatusFilter === 'PENDING' && m.role !== 'b2b_pending') return false;
    if (b2bStatusFilter === 'APPROVED' && m.role !== 'b2b_approved') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        (m.company_name && m.company_name.toLowerCase().includes(q)) ||
        (m.commercial_register && m.commercial_register.toLowerCase().includes(q)) ||
        (m.tax_id && m.tax_id.toLowerCase().includes(q)) ||
        (m.full_name && m.full_name.toLowerCase().includes(q)) ||
        (m.username && m.username.toLowerCase().includes(q)) ||
        (m.phone && m.phone.includes(q)) ||
        (m.email && m.email.toLowerCase().includes(q));
      if (!match) return false;
    }

    return true;
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'OWNER':
        return { label: '👑 مالك المتجر (OWNER)', bg: 'bg-[#26221C] text-[#E2B84B] border-[#C9972B]' };
      case 'SUPERVISOR':
        return { label: '🛡️ مشرف عام (SUPERVISOR)', bg: 'bg-purple-50 text-purple-800 border-purple-200' };
      case 'SALES':
        return { label: '🛍️ كاشير ومبيعات (SALES)', bg: 'bg-blue-50 text-blue-800 border-blue-200' };
      case 'ACCOUNTANT':
        return { label: '📊 محاسب مالي (ACCOUNTANT)', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
      case 'WORKSHOP':
        return { label: '✂️ فني ورشة (WORKSHOP)', bg: 'bg-amber-50 text-amber-800 border-amber-200' };
      case 'b2b_approved':
        return { label: '🏛️ تاجر جملة معتمد', bg: 'bg-emerald-50 text-emerald-800 border-emerald-300' };
      case 'b2b_pending':
        return { label: '⏳ تاجر جملة قيد المراجعة', bg: 'bg-amber-50 text-amber-800 border-amber-300' };
      default:
        return { label: role, bg: 'bg-slate-50 text-slate-800 border-slate-200' };
    }
  };

  const activeCount = users.filter(u => u.is_active).length;
  const supervisorCount = users.filter(u => u.role === 'SUPERVISOR').length;
  const salesCount = users.filter(u => u.role === 'SALES').length;
  const pendingB2BCount = b2bMerchants.filter(m => m.role === 'b2b_pending').length;
  const approvedB2BCount = b2bMerchants.filter(m => m.role === 'b2b_approved').length;

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-7xl mx-auto selection:bg-[#C9972B]/20" dir="rtl">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#EBE3D5]">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-[#26221C] flex items-center gap-2.5">
            <UserCheck className="w-6 h-6 text-[#C9972B]" />
            <span>إدارة المستخدمين، الموظفين، واعتماد تجار الجملة (B2B)</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#746A5D] mt-1">
            التحكم الشامل في حسابات فريق العمل وصلاحياتهم، ومراجعة واعتماد طلبات انضمام كبار تجار الجملة
          </p>
        </div>

        {activeTab === 'staff' && canCreate && (
          <button
            onClick={handleOpenCreate}
            className="px-5 py-2.5 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] rounded-xl text-xs sm:text-sm font-black transition shadow-md flex items-center justify-center gap-2 shrink-0 cursor-pointer"
          >
            <UserPlus className="w-4 h-4" />
            <span>إضافة موظف جديد</span>
          </button>
        )}
      </div>

      {/* 2. Primary Tabs: Staff vs B2B Wholesale */}
      <div className="flex items-center gap-3 border-b border-[#EBE3D5] pb-2">
        <button
          onClick={() => setActiveTab('staff')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-xs sm:text-sm font-black transition ${
            activeTab === 'staff'
              ? 'bg-[#26221C] text-[#E2B84B] shadow-sm'
              : 'bg-white text-[#746A5D] hover:text-[#26221C] border border-[#EBE3D5]'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>طاقم العمل والموظفين</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF4E8] text-[#9A6817]">
            {users.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('b2b')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-xs sm:text-sm font-black transition ${
            activeTab === 'b2b'
              ? 'bg-[#26221C] text-[#E2B84B] shadow-sm'
              : 'bg-white text-[#746A5D] hover:text-[#26221C] border border-[#EBE3D5]'
          }`}
        >
          <Building2 className="w-4 h-4 text-[#C9972B]" />
          <span>تجار وطلبات الجملة (B2B)</span>
          {pendingB2BCount > 0 ? (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-500 text-white animate-pulse">
              {pendingB2BCount} بانتظار الاعتماد
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-[#746A5D]">
              {b2bMerchants.length}
            </span>
          )}
        </button>
      </div>

      {activeTab === 'staff' ? (
        <>
          {/* STAFF KPI CARDS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] shadow-xs">
              <span className="block text-xs font-bold text-[#8C8275]">إجمالي الموظفين</span>
              <span className="text-2xl font-black text-[#26221C] mt-1 block">{users.length}</span>
              <span className="text-[10px] text-[#746A5D]">حسابات مسجلة بالنظام</span>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] shadow-xs">
              <span className="block text-xs font-bold text-emerald-700">الحسابات النشطة</span>
              <span className="text-2xl font-black text-emerald-700 mt-1 block">{activeCount}</span>
              <span className="text-[10px] text-[#746A5D]">مصرح لهم بالدخول الفوري</span>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] shadow-xs">
              <span className="block text-xs font-bold text-purple-700">المشرفون والإدارة</span>
              <span className="text-2xl font-black text-purple-700 mt-1 block">{supervisorCount}</span>
              <span className="text-[10px] text-[#746A5D]">صلاحيات الإشراف والعهد</span>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] shadow-xs">
              <span className="block text-xs font-bold text-blue-700">الكاشير ونقاط البيع</span>
              <span className="text-2xl font-black text-blue-700 mt-1 block">{salesCount}</span>
              <span className="text-[10px] text-[#746A5D]">مسؤولو المبيعات المباشرة</span>
            </div>
          </div>

          {/* STAFF FILTERS & SEARCH */}
          <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] flex flex-wrap items-center justify-between gap-4 shadow-xs">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-[#8C8275] font-bold">الدور:</span>
                <select
                  value={roleFilter}
                  onChange={e => setRoleFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-xl bg-[#FAF7F2] border border-[#DDD3C1] text-[#26221C] text-xs font-bold focus:outline-none focus:border-[#C9972B]"
                >
                  <option value="ALL">كافة الأدوار</option>
                  <option value="OWNER">المالك (OWNER)</option>
                  <option value="SUPERVISOR">مشرف عام (SUPERVISOR)</option>
                  <option value="SALES">كاشير ومبيعات (SALES)</option>
                  <option value="ACCOUNTANT">محاسب (ACCOUNTANT)</option>
                  <option value="WORKSHOP">فني ورشة (WORKSHOP)</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-[#8C8275] font-bold">الحالة:</span>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-xl bg-[#FAF7F2] border border-[#DDD3C1] text-[#26221C] text-xs font-bold focus:outline-none focus:border-[#C9972B]"
                >
                  <option value="ALL">الكل</option>
                  <option value="ACTIVE">النشطة فقط</option>
                  <option value="INACTIVE">المعطلة فقط</option>
                </select>
              </div>
            </div>

            <div className="relative w-full sm:w-72">
              <input
                type="text"
                placeholder="بحث بالاسم، المستخدم، الهاتف..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full py-2 pr-9 pl-4 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
              />
              <Search className="w-4 h-4 text-[#9E9485] absolute right-3 top-2.5" />
            </div>
          </div>

          {/* STAFF USERS GRID */}
          {loading ? (
            <div className="py-24 text-center">
              <div className="inline-block w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs text-[#746A5D] font-medium">جارِ تحميل مستخدمي النظام والصلاحيات...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-[#EBE3D5] p-8 shadow-xs">
              <Users className="w-12 h-12 text-[#C9972B]/60 mx-auto mb-3" />
              <h3 className="text-base font-bold text-[#26221C]">لا يوجد مستخدمون مطابقون لمعايير البحث</h3>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredUsers.map(user => {
                const roleStyle = getRoleBadge(user.role);
                const isOwner = user.role === 'OWNER';
                const customPermCount = user.permissions && typeof user.permissions === 'object'
                  ? Object.values(user.permissions).filter(Boolean).length
                  : 0;

                return (
                  <div
                    key={user.id}
                    className="bg-white border border-[#EBE3D5] rounded-3xl p-5 shadow-xs hover:shadow-md hover:border-[#C9972B] transition-all flex flex-col justify-between space-y-4"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#FAF4E8] to-[#F5ECE0] border border-[#E4D5B8] flex items-center justify-center text-[#9A6817] font-black text-base shadow-xs shrink-0">
                            {user.full_name?.charAt(0) || 'م'}
                          </div>
                          <div>
                            <h3 className="font-extrabold text-sm text-[#26221C] leading-snug">
                              {user.full_name}
                            </h3>
                            <p className="text-xs text-[#8C8275] font-mono dir-ltr text-right">
                              @{user.username}
                            </p>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] px-2.5 py-1 rounded-full font-bold border flex items-center gap-1 ${
                            user.is_active
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                          <span>{user.is_active ? 'نشط' : 'معطل'}</span>
                        </span>
                      </div>

                      <div className="mt-3">
                        <span className={`inline-block text-[11px] font-bold px-3 py-1 rounded-xl border ${roleStyle.bg}`}>
                          {roleStyle.label}
                        </span>
                      </div>

                      <div className="mt-4 pt-3 border-t border-[#F2ECE1] space-y-1.5 text-xs text-[#746A5D]">
                        {user.phone && (
                          <p className="flex items-center gap-2">
                            <Phone className="w-3.5 h-3.5 text-[#C9972B] shrink-0" />
                            <span className="font-mono">{user.phone}</span>
                          </p>
                        )}
                        {user.email && (
                          <p className="flex items-center gap-2 truncate">
                            <Mail className="w-3.5 h-3.5 text-[#C9972B] shrink-0" />
                            <span className="truncate">{user.email}</span>
                          </p>
                        )}
                      </div>

                      <div className="mt-3 p-2.5 rounded-xl bg-[#FAF7F2] border border-[#EEE4D4] flex items-center justify-between text-xs">
                        <span className="text-[#8C8275] flex items-center gap-1.5 font-bold">
                          <ShieldCheck className="w-3.5 h-3.5 text-[#C9972B]" />
                          <span>الصلاحيات الممنوحة:</span>
                        </span>
                        <span className="font-bold text-[#9A6817]">
                          {isOwner ? '👑 مطلقة (كاملة)' : `${customPermCount} صلاحية مفعلة`}
                        </span>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-[#F2ECE1] flex items-center justify-between gap-2">
                      {canEdit && (
                        <button
                          onClick={() => handleOpenEdit(user)}
                          className="flex-1 py-2 bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border border-[#E4D5B8] rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>تعديل والصلاحيات</span>
                        </button>
                      )}

                      {canDelete && !isOwner && user.username !== 'owner' && (
                        <button
                          onClick={() => handleDeleteUser(user)}
                          className="p-2 text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-xl transition cursor-pointer"
                          title="حذف المستخدم نهائياً"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      ) : (
        /* B2B WHOLESALE MERCHANTS TAB */
        <>
          {/* B2B KPI CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-[#EBE3D5] shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#8C8275]">إجمالي طلبات وتجار الجملة</span>
                <Building2 className="w-5 h-5 text-[#C9972B]" />
              </div>
              <span className="text-2xl font-black text-[#26221C] mt-2 block">{b2bMerchants.length}</span>
              <span className="text-[10px] text-[#746A5D]">شركات ومؤسسات مسجلة</span>
            </div>

            <div className="bg-amber-50/60 p-5 rounded-2xl border border-amber-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-800">بانتظار الاعتماد والتدقيق</span>
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <span className="text-2xl font-black text-amber-900 mt-2 block">{pendingB2BCount}</span>
              <span className="text-[10px] text-amber-700">تتطلب مراجعة السجل التجاري والضريبة</span>
            </div>

            <div className="bg-emerald-50/60 p-5 rounded-2xl border border-emerald-200 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800">التجار المعتمدون (نشط)</span>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <span className="text-2xl font-black text-emerald-900 mt-2 block">{approvedB2BCount}</span>
              <span className="text-[10px] text-emerald-700">يملكون صلاحية الشراء بأسعار الجملة</span>
            </div>
          </div>

          {/* B2B FILTERS & SEARCH */}
          <div className="bg-white p-4 rounded-2xl border border-[#EBE3D5] flex flex-wrap items-center justify-between gap-4 shadow-xs">
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#8C8275] font-bold">تصفية حسب الحالة:</span>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setB2BStatusFilter('ALL')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    b2bStatusFilter === 'ALL'
                      ? 'bg-[#26221C] text-white'
                      : 'bg-[#FAF7F2] text-[#746A5D] hover:bg-[#F3E7CE]'
                  }`}
                >
                  الكل ({b2bMerchants.length})
                </button>
                <button
                  onClick={() => setB2BStatusFilter('PENDING')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    b2bStatusFilter === 'PENDING'
                      ? 'bg-amber-600 text-white'
                      : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
                  }`}
                >
                  بانتظار الاعتماد ({pendingB2BCount})
                </button>
                <button
                  onClick={() => setB2BStatusFilter('APPROVED')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    b2bStatusFilter === 'APPROVED'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                  }`}
                >
                  المعتمدون ({approvedB2BCount})
                </button>
              </div>
            </div>

            <div className="relative w-full sm:w-80">
              <input
                type="text"
                placeholder="بحث باسم الشركة، السجل التجاري، الرقم الضريبي..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full py-2 pr-9 pl-4 text-xs bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-[#26221C] placeholder-[#9E9485] focus:outline-none focus:border-[#C9972B]"
              />
              <Search className="w-4 h-4 text-[#9E9485] absolute right-3 top-2.5" />
            </div>
          </div>

          {/* B2B MERCHANTS LIST */}
          {loadingB2B ? (
            <div className="py-24 text-center">
              <div className="inline-block w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs text-[#746A5D] font-medium">جارِ تحميل قائمة كبار التجار وطلبات الجملة...</p>
            </div>
          ) : filteredB2BMerchants.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-[#EBE3D5] p-8 shadow-xs">
              <Building2 className="w-12 h-12 text-[#C9972B]/60 mx-auto mb-3" />
              <h3 className="text-base font-bold text-[#26221C]">لا توجد طلبات أو حسابات تجار مطابقة</h3>
              <p className="text-xs text-[#8C8275] mt-1">يمكن للشركات التقدم بطلب عبر بوابة الجملة (/wholesale)</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredB2BMerchants.map(merchant => {
                const isPending = merchant.role === 'b2b_pending';
                const isApproved = merchant.role === 'b2b_approved';
                const isActionLoading = actionLoadingId === merchant.id;

                return (
                  <div
                    key={merchant.id}
                    className={`bg-white border rounded-3xl p-5 shadow-xs transition-all flex flex-col justify-between space-y-4 ${
                      isPending
                        ? 'border-amber-300 ring-2 ring-amber-400/20 bg-gradient-to-b from-amber-50/20 to-white'
                        : 'border-[#EBE3D5] hover:border-[#C9972B]'
                    }`}
                  >
                    <div>
                      {/* Top Row: Company & Status */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#FAF4E8] to-[#F5ECE0] border border-[#E4D5B8] flex items-center justify-center text-[#9A6817] font-black text-base shadow-xs shrink-0">
                            <Building2 className="w-6 h-6 text-[#9A6817]" />
                          </div>
                          <div>
                            <h3 className="font-extrabold text-sm text-[#26221C] leading-snug">
                              {merchant.company_name || merchant.full_name}
                            </h3>
                            <p className="text-xs text-[#8C8275]">
                              المفوض: {merchant.full_name}
                            </p>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] px-2.5 py-1 rounded-full font-bold border flex items-center gap-1 ${
                            isApproved
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-amber-50 text-amber-700 border-amber-300 animate-pulse'
                          }`}
                        >
                          {isApproved ? (
                            <>
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>معتمد رسمي</span>
                            </>
                          ) : (
                            <>
                              <Clock className="w-3 h-3 text-amber-600" />
                              <span>قيد المراجعة</span>
                            </>
                          )}
                        </span>
                      </div>

                      {/* Corporate Identifiers: CR & TRN */}
                      <div className="mt-4 p-3 rounded-2xl bg-[#FAF7F2] border border-[#EEE4D4] space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-[#8C8275] font-semibold flex items-center gap-1.5">
                            <FileCheck className="w-3.5 h-3.5 text-[#C9972B]" />
                            <span>السجل التجاري (CR):</span>
                          </span>
                          <span className="font-mono font-bold text-[#26221C]">
                            {merchant.commercial_register || 'غير مدخل'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-[#8C8275] font-semibold flex items-center gap-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-[#C9972B]" />
                            <span>الرقم الضريبي (TRN):</span>
                          </span>
                          <span className="font-mono font-bold text-[#26221C]">
                            {merchant.tax_id || 'غير مدخل'}
                          </span>
                        </div>
                      </div>

                      {/* Contact Info */}
                      <div className="mt-3 space-y-1.5 text-xs text-[#746A5D]">
                        {merchant.phone && (
                          <p className="flex items-center gap-2">
                            <Phone className="w-3.5 h-3.5 text-[#C9972B] shrink-0" />
                            <span className="font-mono">{merchant.phone}</span>
                          </p>
                        )}
                        {merchant.email && (
                          <p className="flex items-center gap-2 truncate">
                            <Mail className="w-3.5 h-3.5 text-[#C9972B] shrink-0" />
                            <span className="truncate">{merchant.email}</span>
                          </p>
                        )}
                      </div>

                      {/* Approval Info */}
                      {merchant.approved_at && (
                        <p className="mt-2 text-[10px] text-[#8C8275]">
                          تم الاعتماد بواسطة: {merchant.approved_by || 'الإدارة'} في{' '}
                          {new Date(merchant.approved_at).toLocaleDateString('ar-AE')}
                        </p>
                      )}
                    </div>

                    {/* Merchant Action Buttons */}
                    <div className="pt-3 border-t border-[#F2ECE1] flex items-center gap-2">
                      {isPending ? (
                        <>
                          <button
                            onClick={() => handleApproveMerchant(merchant.id, merchant.company_name || merchant.full_name)}
                            disabled={isActionLoading}
                            className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-black transition flex items-center justify-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50"
                          >
                            <Check className="w-4 h-4" />
                            <span>اعتماد التاجر (Approve)</span>
                          </button>
                          <button
                            onClick={() => handleRejectMerchant(merchant.id, merchant.company_name || merchant.full_name)}
                            disabled={isActionLoading}
                            className="p-2.5 text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-xl transition cursor-pointer disabled:opacity-50"
                            title="رفض الطلب"
                          >
                            <Ban className="w-4 h-4" />
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleRejectMerchant(merchant.id, merchant.company_name || merchant.full_name)}
                          disabled={isActionLoading}
                          className="w-full py-2 text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                        >
                          <Ban className="w-3.5 h-3.5" />
                          <span>تعليق حساب التاجر / سحب الاعتماد</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* User Create/Edit Modal */}
      <UserModal
        user={selectedUser}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveUser}
        currentAdminName={currentUser.full_name}
      />
    </div>
  );
};
