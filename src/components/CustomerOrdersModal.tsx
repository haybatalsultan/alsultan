import React, { useState, useEffect } from 'react';
import { Package, X, Clock, CheckCircle2, Eye, Receipt, Phone, User, ShoppingBag } from 'lucide-react';
import { api } from '../lib/api';
import { Order } from '../types';
import { toast } from '../utils/toast';

interface CustomerOrdersModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerUser: any;
  onViewInvoice: (order: Order) => void;
  onLogoutCustomer: () => void;
}

export const CustomerOrdersModal: React.FC<CustomerOrdersModalProps> = ({
  isOpen,
  onClose,
  customerUser,
  onViewInvoice,
  onLogoutCustomer
}) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && customerUser) {
      loadOrders();
    }
  }, [isOpen, customerUser]);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await api.getCustomerOrders({
        phone: customerUser.phone,
        email: customerUser.email
      });
      setOrders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !customerUser) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 backdrop-blur-sm p-4">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#26221C]">مرحباً، {customerUser.full_name}</h3>
              <p className="text-xs text-[#746A5D]">سجل مشترياتك وطلباتك من هيبة السلطان ({customerUser.phone})</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                const confirmed = await toast.confirm({
                  title: 'تسجيل الخروج',
                  message: 'هل ترغب بتسجيل الخروج من حسابك في هيبة السلطان؟',
                  confirmText: 'تسجيل الخروج',
                  cancelText: 'إلغاء',
                  type: 'warning'
                });
                if (confirmed) {
                  onLogoutCustomer();
                  onClose();
                  toast.info('تم تسجيل الخروج بنجاح');
                }
              }}
              className="text-[11px] font-bold text-rose-600 hover:text-rose-700 bg-rose-50 px-2.5 py-1 rounded-lg border border-rose-200 transition cursor-pointer"
            >
              تسجيل الخروج
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Orders List */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <p className="text-center py-12 text-xs text-[#746A5D]">جارِ جلب سجل طلباتك...</p>
          ) : orders.length === 0 ? (
            <div className="text-center py-12 bg-[#FAF7F2] rounded-2xl border border-dashed border-[#D8CCA8] p-6 space-y-2">
              <ShoppingBag className="w-10 h-10 mx-auto text-[#C9972B]/60" />
              <h4 className="font-bold text-sm text-[#26221C]">لا توجد طلبات سابقة مسجلة</h4>
              <p className="text-xs text-[#746A5D]">
                تصفح تشكيلة المسابيح الفاخرة واختر قطعتك الفريدة لتظهر هنا.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {orders.map((ord) => (
                <div
                  key={ord.id}
                  className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm hover:border-[#C9972B] transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs text-[#9A6817] bg-[#FAF4E8] px-2 py-0.5 rounded border border-[#EADBCE]">
                        {ord.reference}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        ord.status === 'DELIVERED'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : 'bg-amber-100 text-amber-800 border border-amber-300'
                      }`}>
                        {ord.status === 'DELIVERED' ? 'تم التسليم' : 'قيد التجهيز والشحن'}
                      </span>
                    </div>

                    <div className="text-xs text-[#4B4338] font-medium pt-1">
                      {ord.items && ord.items.length > 0 ? (
                        <span>{ord.items.map(it => it.name_ar).join(' • ')}</span>
                      ) : (
                        <span>طلب اقتناء مسبحة فاخرة</span>
                      )}
                    </div>
                    <p className="text-[11px] text-[#8C8275]">
                      التاريخ: {ord.created_at} | طريقة الدفع: {ord.payment_method}
                    </p>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 border-t sm:border-t-0 pt-2 sm:pt-0 border-[#E8DEC8]">
                    <span className="font-black text-sm text-[#9A6817]">
                      {ord.grand_total.toLocaleString()} AED
                    </span>
                    <button
                      onClick={() => {
                        onViewInvoice(ord);
                      }}
                      className="px-3 py-1 bg-white hover:bg-[#FAF4E8] text-[#9A6817] font-bold text-xs rounded-xl border border-[#E0D7C6] transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                    >
                      <Receipt className="w-3.5 h-3.5" />
                      <span>عرض الفاتورة</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
