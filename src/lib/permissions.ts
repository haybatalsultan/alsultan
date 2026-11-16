export interface PermissionDefinition {
  key: string;
  label_ar: string;
  description_ar: string;
  module: string;
}

export interface PermissionModule {
  id: string;
  label_ar: string;
  icon: string;
  permissions: PermissionDefinition[];
}

export const PERMISSION_MODULES: PermissionModule[] = [
  {
    id: 'dashboard',
    label_ar: 'لوحة التحكم والمؤشرات',
    icon: 'LayoutDashboard',
    permissions: [
      { key: 'dashboard.view', label_ar: 'عرض شاشة المؤشرات', description_ar: 'مشاهدة الإحصائيات والمخططات البيانية للمبيعات', module: 'dashboard' },
      { key: 'dashboard.financial_kpis', label_ar: 'عرض الأرباح والتكاليف', description_ar: 'مشاهدة صافي الأرباح وهوامش الربح الحقيقية في اللوحة', module: 'dashboard' },
    ]
  },
  {
    id: 'pos',
    label_ar: 'البيع السريع ونقاط البيع (POS)',
    icon: 'ShoppingBag',
    permissions: [
      { key: 'pos.view', label_ar: 'فتح نقطة البيع', description_ar: 'دخول شاشة الكاشير والبيع السريع الفوري', module: 'pos' },
      { key: 'pos.checkout', label_ar: 'إتمام عمليات البيع', description_ar: 'إصدار الفواتير وتحصيل المبالغ', module: 'pos' },
      { key: 'pos.discount', label_ar: 'منح خصومات إضافية', description_ar: 'تطبيق خصم مخصص على الفواتير', module: 'pos' },
    ]
  },
  {
    id: 'inventory',
    label_ar: 'المسابيح والمخزون الفاخر',
    icon: 'Gem',
    permissions: [
      { key: 'inventory.view', label_ar: 'استعراض المخزون', description_ar: 'مشاهدة قائمة المسابيح والبحث والتصفية', module: 'inventory' },
      { key: 'inventory.create', label_ar: 'إضافة مسبحة جديدة', description_ar: 'تسجيل قطع نادرة ومسابيح جديدة في النظام', module: 'inventory' },
      { key: 'inventory.edit', label_ar: 'تعديل بيانات المسبحة', description_ar: 'تعديل المواصفات والأسعار والصور والشهادات', module: 'inventory' },
      { key: 'inventory.delete', label_ar: 'حذف أو أرشفة مسبحة', description_ar: 'حذف المسبحة من المخزون أو أرشفتها', module: 'inventory' },
      { key: 'inventory.view_cost', label_ar: 'الاطلاع على سعر التكلفة', description_ar: 'رؤية رأس المال وتكلفة الشراء للقطعة', module: 'inventory' },
      { key: 'inventory.reserve', label_ar: 'حجز المسبحة', description_ar: 'حجز القطعة باسم عميل أو فك الحجز', module: 'inventory' },
    ]
  },
  {
    id: 'custody',
    label_ar: 'سجل العهدة والمعارض الخارجية',
    icon: 'ShieldCheck',
    permissions: [
      { key: 'custody.view', label_ar: 'عرض سجل العهدة', description_ar: 'الاطلاع على المسابيح المسلمة للمعارض والموظفين', module: 'custody' },
      { key: 'custody.assign', label_ar: 'تسليم ونقل العهدة', description_ar: 'نقل مسبحة لعهدة موظف أو معرض خارجي', module: 'custody' },
      { key: 'custody.return', label_ar: 'استرداد العهدة', description_ar: 'إعادة المسبحة من العهدة للمخزون العام', module: 'custody' },
    ]
  },
  {
    id: 'workshop',
    label_ar: 'ورشة تعديل الخرز والشواهد',
    icon: 'Scissors',
    permissions: [
      { key: 'workshop.view', label_ar: 'فتح شاشة الورشة', description_ar: 'استعراض طلبات ورشة التعديل والقص', module: 'workshop' },
      { key: 'workshop.adjust', label_ar: 'إجراء تعديلات الخرز', description_ar: 'فك أو إضافة خرز وتعديل الوزن وإعادة احتساب التكلفة', module: 'workshop' },
    ]
  },
  {
    id: 'orders',
    label_ar: 'سجلات المبيعات والطلبات',
    icon: 'Receipt',
    permissions: [
      { key: 'orders.view', label_ar: 'استعراض فواتير المبيعات', description_ar: 'مشاهدة تفاصيل الطلبات وفواتير البيع', module: 'orders' },
      { key: 'orders.change_status', label_ar: 'تحديث حالة التوصيل', description_ar: 'تغيير حالة الطلب (قيد التجهيز، تم الشحن، تم التسليم)', module: 'orders' },
      { key: 'orders.cancel', label_ar: 'إلغاء الطلب واسترجاع القطعة', description_ar: 'إلغاء المبيعة وإعادة القطعة للمخزون كمتوفرة', module: 'orders' },
    ]
  },
  {
    id: 'accountant',
    label_ar: 'المحاسب الذكي والمالية',
    icon: 'Calculator',
    permissions: [
      { key: 'accountant.view', label_ar: 'عرض التقارير المحاسبية', description_ar: 'مشاهدة قائمة الدخل والأرباح الصافية', module: 'accountant' },
      { key: 'accountant.expenses_create', label_ar: 'تسجيل مصروف تشغيلي', description_ar: 'إضافة سند صرف لمصاريف المعرض أو العلب', module: 'accountant' },
      { key: 'accountant.expenses_void', label_ar: 'إلغاء سندات الصرف', description_ar: 'إلغاء مصروف مسجل مسبقاً محاسبياً', module: 'accountant' },
      { key: 'accountant.receivables', label_ar: 'إدارة الدفعات الآجلة', description_ar: 'متابعة وتحصيل المبالغ المتبقية على العملاء', module: 'accountant' },
    ]
  },
  {
    id: 'ambassadors',
    label_ar: 'برنامج السفراء والعملاء',
    icon: 'Users',
    permissions: [
      { key: 'ambassadors.view', label_ar: 'عرض قائمة السفراء', description_ar: 'مشاهدة السفراء وأرصدة نقاطهم ومبيعاتهم', module: 'ambassadors' },
      { key: 'ambassadors.manage', label_ar: 'إدارة وتوليد أكواد السفراء', description_ar: 'تسجيل سفير جديد أو تعديل بياناته', module: 'ambassadors' },
    ]
  },
  {
    id: 'users',
    label_ar: 'إدارة مستخدمي النظام والصلاحيات',
    icon: 'UserCheck',
    permissions: [
      { key: 'users.view', label_ar: 'عرض قائمة الموظفين', description_ar: 'الاطلاع على مستخدمي النظام وحالاتهم', module: 'users' },
      { key: 'users.create', label_ar: 'إضافة موظف جديد', description_ar: 'إنشاء حساب موظف وتعيين كلمة المرور', module: 'users' },
      { key: 'users.edit', label_ar: 'تعديل بيانات الموظف', description_ar: 'تعديل الاسم والهاتف والبريد وكلمة المرور', module: 'users' },
      { key: 'users.delete', label_ar: 'حذف أو تعطيل مستخدم', description_ar: 'إيقاف حساب موظف أو حذفه من النظام', module: 'users' },
      { key: 'users.permissions', label_ar: 'تخصيص الصلاحيات الفردية', description_ar: 'تفعيل أو إلغاء أي صلاحية بشكل منفصل للموظف', module: 'users' },
    ]
  },
  {
    id: 'settings',
    label_ar: 'الإعدادات والترخيص والتدقيق',
    icon: 'Settings',
    permissions: [
      { key: 'settings.view', label_ar: 'عرض الإعدادات', description_ar: 'مشاهدة بيانات المتجر والترخيص', module: 'settings' },
      { key: 'settings.edit', label_ar: 'تعديل إعدادات المتجر', description_ar: 'تعديل بيانات الضريبة واسم المتجر ونصوص الفواتير', module: 'settings' },
      { key: 'settings.audit_logs', label_ar: 'سجل التدقيق الأمني (Audit)', description_ar: 'الاطلاع على سجلات العمليات والأمان لجميع الموظفين', module: 'settings' },
      { key: 'settings.cloud_sync', label_ar: 'المزامنة السحابية', description_ar: 'إدارة إعدادات السحابة والمزامنة مع Turso', module: 'settings' },
    ]
  }
];

// Flat list of all permission keys
export const ALL_PERMISSION_KEYS = PERMISSION_MODULES.flatMap(m => m.permissions.map(p => p.key));

// Default role presets
export const ROLE_PRESETS: Record<string, Record<string, boolean>> = {
  OWNER: ALL_PERMISSION_KEYS.reduce((acc, key) => ({ ...acc, [key]: true }), {}),
  SUPERVISOR: {
    'dashboard.view': true,
    'dashboard.financial_kpis': true,
    'pos.view': true,
    'pos.checkout': true,
    'pos.discount': true,
    'inventory.view': true,
    'inventory.create': true,
    'inventory.edit': true,
    'inventory.view_cost': true,
    'inventory.reserve': true,
    'custody.view': true,
    'custody.assign': true,
    'custody.return': true,
    'workshop.view': true,
    'workshop.adjust': true,
    'orders.view': true,
    'orders.change_status': true,
    'orders.cancel': true,
    'accountant.view': true,
    'accountant.expenses_create': true,
    'accountant.receivables': true,
    'ambassadors.view': true,
    'ambassadors.manage': true,
    'users.view': true,
    'settings.view': true,
  },
  SALES: {
    'pos.view': true,
    'pos.checkout': true,
    'pos.discount': false,
    'inventory.view': true,
    'inventory.reserve': true,
    'inventory.view_cost': false,
    'orders.view': true,
    'orders.change_status': true,
    'custody.view': true,
  },
  ACCOUNTANT: {
    'dashboard.view': true,
    'dashboard.financial_kpis': true,
    'inventory.view': true,
    'inventory.view_cost': true,
    'orders.view': true,
    'accountant.view': true,
    'accountant.expenses_create': true,
    'accountant.expenses_void': true,
    'accountant.receivables': true,
    'settings.view': true,
    'settings.audit_logs': true,
  },
  WORKSHOP: {
    'workshop.view': true,
    'workshop.adjust': true,
    'inventory.view': true,
    'custody.view': true,
    'custody.return': true,
  }
};

/**
 * Checks whether a user has a specific permission.
 * - OWNER always has unrestricted access.
 * - If user.permissions explicitly defines the key (true/false), that value takes precedence.
 * - Otherwise falls back to ROLE_PRESETS[user.role][key] || false.
 */
export function hasPermission(user: any | null | undefined, permissionKey: string): boolean {
  if (!user) return false;
  if (user.role === 'OWNER') return true;

  // Check custom individual permission override
  if (user.permissions && typeof user.permissions === 'object') {
    if (user.permissions[permissionKey] !== undefined) {
      return Boolean(user.permissions[permissionKey]);
    }
  }

  // Fallback to role preset
  const preset = ROLE_PRESETS[user.role];
  if (preset && preset[permissionKey] !== undefined) {
    return preset[permissionKey];
  }

  return false;
}
