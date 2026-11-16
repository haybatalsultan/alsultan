import React, { useState, useEffect } from 'react';
import {
  Building2,
  ShieldCheck,
  Clock,
  ArrowRight,
  MessageSquare,
  Lock,
  UserCheck,
  Gem,
  CheckCircle2,
  FileCheck,
  Truck,
  Sparkles,
  PhoneCall
} from 'lucide-react';
import { api } from '../lib/api';
import { Product, User, Order } from '../types';
import { B2BQuickOrderTable, B2BQuickOrderItem } from '../components/B2BQuickOrderTable';
import { B2BRegisterModal } from '../components/B2BRegisterModal';
import { B2BCheckoutModal } from '../components/B2BCheckoutModal';
import { CustomerAuthModal } from '../components/CustomerAuthModal';
import { InvoiceModal } from '../components/InvoiceModal';

interface B2BWholesalePageProps {
  currentUser: User | null;
  onUserLoginSuccess: (user: User) => void;
  onNavigateHome: () => void;
}

export const B2BWholesalePage: React.FC<B2BWholesalePageProps> = ({
  currentUser,
  onUserLoginSuccess,
  onNavigateHome
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [checkoutItems, setCheckoutItems] = useState<B2BQuickOrderItem[]>([]);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [completedOrder, setCompletedOrder] = useState<Order | null>(null);

  const isB2BApproved =
    currentUser &&
    (currentUser.role === 'b2b_approved' ||
      currentUser.role === 'admin' ||
      currentUser.role === 'OWNER' ||
      currentUser.role === 'SUPERVISOR');

  const isB2BPending = currentUser?.role === 'b2b_pending';
  const isRetailCustomer =
    currentUser && (currentUser.role === 'CUSTOMER' || currentUser.role === 'b2c_user');

  useEffect(() => {
    if (isB2BApproved) {
      loadWholesaleProducts();
    } else {
      setLoading(false);
    }
  }, [isB2BApproved]);

  const loadWholesaleProducts = async () => {
    setLoading(true);
    try {
      const data = await api.getB2BProducts();
      setProducts(data);
    } catch (e) {
      console.error('Failed to load B2B wholesale catalog:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleProceedToCheckout = (items: B2BQuickOrderItem[]) => {
    setCheckoutItems(items);
    setIsCheckoutOpen(true);
  };

  const handleOrderSuccess = (order: any) => {
    setCompletedOrder(order);
    loadWholesaleProducts();
  };

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#26221C] font-sans selection:bg-[#C9972B]/20" dir="rtl">
      {/* 1. Wholesale Portal Header Banner */}
      <div className="bg-[#26221C] text-white border-b border-[#C9972B]/40 py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#E2B84B] font-bold text-xs">
              <Sparkles className="w-4 h-4" />
              <span>هيبة السلطان — شبكة التوزيع وتجارة الجملة</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white">
              بوابة التوريد وأوامر الشراء المباشرة (B2B Portal)
            </h1>
            <p className="text-xs text-[#D8CCA8]">
              أسعار توريد حصرية، حزم كميات للمعارض، وإصدار أوامر الشراء القانونية (PO)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onNavigateHome}
              className="text-xs text-[#E2B84B] hover:text-white transition flex items-center gap-1.5 font-bold px-3 py-1.5 rounded-xl border border-[#C9972B]/40 hover:border-[#C9972B] cursor-pointer"
            >
              <ArrowRight className="w-3.5 h-3.5" />
              <span>العودة لمتجر التجزئة العام</span>
            </button>

            {currentUser && (
              <div className="bg-white/10 backdrop-blur px-3 py-1.5 rounded-xl text-xs flex items-center gap-2 border border-white/10">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="font-bold">{currentUser.company_name || currentUser.full_name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2. Main Body Content Based on Authentication State */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Case A: User is Approved B2B Merchant -> Show Quick Order Table */}
        {isB2BApproved ? (
          <div>
            {loading ? (
              <div className="py-24 text-center">
                <div className="inline-block w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin mb-3" />
                <p className="text-xs text-[#746A5D] font-medium">جارِ تحميل كتالوج الجملة وقوائم الأسعار الحصرية...</p>
              </div>
            ) : (
              <B2BQuickOrderTable
                products={products}
                onAddToCartBulk={(items) => {
                  alert(`✅ تم تأكيد واختيار ${items.length} أصناف في قائمة الشراء.`);
                }}
                onProceedToB2BCheckout={handleProceedToCheckout}
              />
            )}
          </div>
        ) : isB2BPending ? (
          /* Case B: Pending Approval Screen */
          <div className="max-w-xl mx-auto my-12 bg-white border border-[#EBE3D5] rounded-3xl p-8 text-center shadow-xl space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center mx-auto shadow-xs">
              <Clock className="w-8 h-8 animate-pulse" />
            </div>
            <h2 className="text-xl font-black text-[#26221C]">
              طلب الاعتماد قيد التدقيق القانوني
            </h2>
            <p className="text-xs text-[#746A5D] leading-relaxed max-w-md mx-auto">
              أهلاً بكم ممثل منشأة <strong>{currentUser?.company_name || 'الشركة الموقرة'}</strong>. تم تسجيل طلبكم بنجاح ونتحقق حالياً من السجل التجاري والبيانات الضريبية لضمان حصرية أسعار وتخفيضات الجملة للتجار الفعليين.
            </p>

            <div className="p-4 bg-[#FAF7F2] rounded-2xl border border-[#EEE4D4] text-xs text-right space-y-2">
              <p className="font-bold text-[#26221C]">ملخص الطلب المسجل:</p>
              <div className="grid grid-cols-2 gap-2 text-[#746A5D]">
                <div>• السجل التجاري: <span className="font-mono font-bold text-[#26221C]">{currentUser?.commercial_register || 'مرفوع'}</span></div>
                <div>• الرقم الضريبي: <span className="font-mono font-bold text-[#26221C]">{currentUser?.tax_id || '—'}</span></div>
                <div>• جهة الاتصال: <span className="font-bold text-[#26221C]">{currentUser?.full_name}</span></div>
                <div>• هاتف العمل: <span className="font-mono font-bold text-[#26221C]">{currentUser?.phone}</span></div>
              </div>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="https://wa.me/971504084006?text=%D8%A7%D9%84%D8%B3%D9%84%D8%A7%D9%85%20%D8%B9%D9%84%D9%8A%D9%83%D9%85%D8%8C%20%D9%86%D9%88%D8%AF%20%D8%AA%D8%B3%D8%B1%D9%8A%D8%B9%20%D8%A7%D8%B9%D8%AA%D9%85%D8%A7%D8%AF%20%D8%AD%D8%B3%D8%A7%D8%A8%20%D8%A7%D9%84%D8%AC%D9%85%D9%84%D8%A9"
                target="_blank"
                rel="noreferrer"
                className="py-3 px-6 bg-[#25D366] hover:bg-[#1EBE5D] text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-xs"
              >
                <MessageSquare className="w-4 h-4" />
                <span>تسريع الاعتماد عبر واتساب الجملة</span>
              </a>

              <button
                type="button"
                onClick={onNavigateHome}
                className="py-3 px-6 bg-[#FAF7F2] hover:bg-[#F2ECE1] text-[#4B4338] rounded-xl text-xs font-bold transition border border-[#EADBCE] cursor-pointer"
              >
                تصفح متجر التجزئة مؤقتاً
              </button>
            </div>
          </div>
        ) : isRetailCustomer ? (
          /* Case C: Logged in as Retail B2C -> Needs Wholesale Application */
          <div className="max-w-lg mx-auto my-12 bg-white border border-[#EBE3D5] rounded-3xl p-8 text-center shadow-xl space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center mx-auto shadow-xs">
              <Building2 className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-black text-[#26221C]">
              الترقية إلى حساب تاجر جملة (B2B)
            </h2>
            <p className="text-xs text-[#746A5D] leading-relaxed">
              أهلاً بك <strong>{currentUser.full_name}</strong>. حسابك الحالي مسجل كـ "عميل تجزئة". للاطلاع على أسعار الجملة المخفضة وإصدار أوامر الشراء القانونية، يرجى تقديم بيانات السجل التجاري لاعتماد حسابك.
            </p>
            <div className="pt-4 flex flex-col gap-2.5">
              <button
                type="button"
                onClick={() => setIsRegisterModalOpen(true)}
                className="py-3 px-6 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] rounded-xl text-xs font-black transition shadow-md cursor-pointer flex items-center justify-center gap-2"
              >
                <FileCheck className="w-4 h-4" />
                <span>تقديم بيانات السجل التجاري الآن</span>
              </button>
            </div>
          </div>
        ) : (
          /* Case D: Guest / Not Logged In -> Wholesale Landing Gateway */
          <div className="my-8 space-y-10">
            {/* Value Proposition Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-3xl border border-[#EBE3D5] shadow-xs space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#FAF4E8] text-[#9A6817] flex items-center justify-center border border-[#EADBCE]">
                  <Gem className="w-6 h-6" />
                </div>
                <h3 className="font-black text-sm text-[#26221C]">أسعار توريد مباشرة من الورش</h3>
                <p className="text-xs text-[#746A5D] leading-relaxed">
                  هوامش ربحية مجزية للتجار والمعارض على كافة خامات الكهرمان، الفاتوران الأنتيك، والبكلايت والفضة.
                </p>
              </div>

              <div className="bg-white p-6 rounded-3xl border border-[#EBE3D5] shadow-xs space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#FAF4E8] text-[#9A6817] flex items-center justify-center border border-[#EADBCE]">
                  <FileCheck className="w-6 h-6" />
                </div>
                <h3 className="font-black text-sm text-[#26221C]">أوامر شراء معتمدة (PO)</h3>
                <p className="text-xs text-[#746A5D] leading-relaxed">
                  إصدار فواتير ضريبية رسمية، تتبع الشحن اللوجستي، ودفع عبر التحويلات البنكية والشيكات المعتمدة.
                </p>
              </div>

              <div className="bg-white p-6 rounded-3xl border border-[#EBE3D5] shadow-xs space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#FAF4E8] text-[#9A6817] flex items-center justify-center border border-[#EADBCE]">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h3 className="font-black text-sm text-[#26221C]">حماية حصرية للشركاء</h3>
                <p className="text-xs text-[#746A5D] leading-relaxed">
                  أسعار الجملة محجوبة تماماً عن عملاء التجزئة والجمهور لضمان أقصى حماية لهوامشكم التجارية.
                </p>
              </div>
            </div>

            {/* Action Card */}
            <div className="bg-gradient-to-r from-[#FAF4E8] via-[#FFFDF8] to-[#F5ECE0] p-8 rounded-3xl border border-[#E4D5B8] text-center max-w-xl mx-auto shadow-md space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center mx-auto shadow-md">
                <Building2 className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-black text-[#26221C]">
                انضم الآن لشبكة تجار هيبة السلطان
              </h2>
              <p className="text-xs text-[#746A5D] leading-relaxed">
                إذا كنت تملك متجراً أو معرضاً أو منشأة تجارية مرخصة، سجل معنا لفتح جدول طلبات الجملة السريعة الفوري.
              </p>

              <div className="pt-2 flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(true)}
                  className="py-3 px-6 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] rounded-xl text-xs font-black transition shadow-md cursor-pointer flex items-center justify-center gap-2"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>تقديم طلب اعتماد تاجر جملة</span>
                </button>

                <button
                  type="button"
                  onClick={() => setIsLoginModalOpen(true)}
                  className="py-3 px-6 bg-white hover:bg-[#FAF4E8] text-[#4B4338] rounded-xl text-xs font-bold transition border border-[#EADBCE] cursor-pointer flex items-center justify-center gap-2"
                >
                  <Lock className="w-4 h-4 text-[#C9972B]" />
                  <span>دخول تاجر معتمد</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 3. Wholesale Registration Modal */}
      <B2BRegisterModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSuccess={(data) => {
          if (data.user) {
            onUserLoginSuccess(data.user);
          }
        }}
        onSwitchToLogin={() => {
          setIsRegisterModalOpen(false);
          setIsLoginModalOpen(true);
        }}
      />

      {/* 4. Login Modal */}
      <CustomerAuthModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onSuccess={(user) => {
          onUserLoginSuccess(user);
        }}
      />

      {/* 5. Wholesale Checkout Modal */}
      <B2BCheckoutModal
        items={checkoutItems}
        customerUser={currentUser}
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
        onSuccess={handleOrderSuccess}
      />

      {/* 6. Invoice Print Modal for Completed PO */}
      {completedOrder && (
        <InvoiceModal
          order={completedOrder}
          onClose={() => setCompletedOrder(null)}
        />
      )}
    </div>
  );
};
