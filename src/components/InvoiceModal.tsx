import React from 'react';
import { X, Printer, CheckCircle, Shield, Award } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { Order } from '../types';

interface InvoiceModalProps {
  order: Order | null;
  onClose: () => void;
}

export const InvoiceModal: React.FC<InvoiceModalProps> = ({ order, onClose }) => {
  if (!order) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden my-8">
        {/* Action Header (No-print) */}
        <div className="p-4 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2] no-print">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-[#26221C] text-sm">فاتورة المبيعات الرسمية</h3>
            <span className="text-xs text-[#9A6817] font-mono font-bold">#{order.reference}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span>طباعة الفاتورة</span>
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Invoice Container */}
        <div id="printable-invoice" className="p-8 bg-white text-[#26221C] space-y-6">
          {/* Brand & Invoice Header */}
          <div className="flex justify-between items-start border-b border-[#EBE3D5] pb-6">
            <div className="flex items-start gap-4">
              <img
                src="/branding/logo-header.png"
                alt="هيبة السلطان"
                className="h-14 object-contain"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
              <div>
                <h1 className="text-2xl font-black text-[#9A6817] tracking-wide">هيبة السلطان</h1>
                <p className="text-xs text-[#746A5D] mt-1 font-medium">دار المسابيح الفاخرة والقطع الحصرية النادرة</p>
                <p className="text-[11px] text-[#8C8275] mt-0.5">
                  أبوظبي، الإمارات العربية المتحدة | <span dir="ltr" className="font-mono inline-block font-semibold">+971 50 408 4006</span>
                </p>
              </div>
            </div>
            <div className="text-left flex flex-col items-end">
              <div className="bg-[#FAF7F2] p-2 rounded-xl border border-[#E0D7C6]">
                <QRCodeSVG
                  value={`https://haybatalsultan.com/orders/track?ref=${order.reference}`}
                  size={64}
                  bgColor="#FAF7F2"
                  fgColor="#9A6817"
                />
              </div>
              <span className="text-[10px] text-[#746A5D] mt-1 font-mono font-bold">{order.reference}</span>
            </div>
          </div>

          {/* Customer & Order Metadata */}
          <div className="grid grid-cols-2 gap-4 text-xs bg-[#FAF7F2] p-4 rounded-2xl border border-[#EEE6D8]">
            <div>
              <span className="text-[#8C8275] block mb-0.5">بيانات العميل:</span>
              <p className="font-bold text-[#26221C] text-sm">{order.customer_name}</p>
              <p className="text-[#746A5D]">{order.customer_phone}</p>
            </div>
            <div className="text-left">
              <span className="text-[#8C8275] block mb-0.5">تفاصيل الفاتورة:</span>
              <p className="font-bold text-[#26221C]">التاريخ: {order.delivered_at || order.created_at}</p>
              <p className="text-[#746A5D]">
                طريقة الدفع: <span className="text-[#9A6817] font-bold">{order.payment_method}</span> | 
                الحالة: <span className="text-emerald-700 font-bold">{order.payment_status}</span>
              </p>
            </div>
          </div>

          {/* Items Table */}
          <div className="border border-[#EBE3D5] rounded-2xl overflow-hidden">
            <table className="w-full text-right text-xs">
              <thead className="bg-[#FAF7F2] text-[#746A5D] border-b border-[#EBE3D5]">
                <tr>
                  <th className="p-3">المسبحة / القطعة</th>
                  <th className="p-3">الرمز المرجعي (SKU)</th>
                  <th className="p-3 text-center">الكمية</th>
                  <th className="p-3 text-left">السعر الإجمالي</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F2ECE1] text-[#26221C]">
                {order.items?.map((item) => (
                  <tr key={item.id} className="hover:bg-[#FAF7F2]/40">
                    <td className="p-3 font-medium">
                      <div className="flex items-center gap-2">
                        <span>{item.name_ar}</span>
                        {item.requested_bead_count && (
                          <span className="text-[10px] px-2 py-0.5 bg-[#FAF4E8] text-[#9A6817] border border-[#EADBCE] rounded-full font-bold">
                            تم تعديل الخرز إلى {item.requested_bead_count}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-3 font-mono text-[#8C8275]">{item.sku}</td>
                    <td className="p-3 text-center">1 (قطعة فريدة)</td>
                    <td className="p-3 text-left font-black text-[#9A6817]">{item.line_total.toLocaleString()} AED</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Financial Totals */}
          <div className="flex justify-between items-start pt-2">
            <div className="space-y-1 text-xs text-[#746A5D] max-w-xs">
              <div className="flex items-center gap-1.5 text-[#9A6817] font-bold">
                <Award className="w-4 h-4 text-[#C9972B]" />
                <span>شهادة الأصالة والضمان الملكي</span>
              </div>
              <p className="text-[11px] leading-relaxed text-[#8C8275]">
                نضمن في "هيبة السلطان" أصالة الخامات الطبيعية 100%، وخلوها من أي غش أو تصنيع مقلد. كل قطعة مفرزة ومرقمة بسجل حيازة فريد.
              </p>
            </div>

            <div className="w-64 space-y-1.5 text-xs">
              <div className="flex justify-between text-[#746A5D]">
                <span>المجموع الفرعي:</span>
                <span className="font-semibold text-[#26221C]">{order.subtotal.toLocaleString()} AED</span>
              </div>
              {order.discount_total > 0 && (
                <div className="flex justify-between text-rose-600">
                  <span>الخصم الخاص:</span>
                  <span>- {order.discount_total.toLocaleString()} AED</span>
                </div>
              )}
              <div className="flex justify-between text-[#746A5D]">
                <span>الضريبة (0%):</span>
                <span>0.00 AED</span>
              </div>
              <div className="flex justify-between text-base font-black text-[#9A6817] pt-2 border-t border-[#EBE3D5]">
                <span>صافي الفاتورة:</span>
                <span>{order.grand_total.toLocaleString()} AED</span>
              </div>
              {order.payment_method === 'DEFERRED' && (
                <div className="flex justify-between text-xs text-amber-900 font-bold bg-amber-50 p-2 rounded-xl border border-amber-300 mt-1">
                  <span>المستحق الآجل:</span>
                  <span>{order.outstanding_amount?.toLocaleString() || 0} AED</span>
                </div>
              )}
            </div>
          </div>

          {/* Digital Stamp / Footer */}
          <div className="border-t border-[#EBE3D5] pt-4 flex items-center justify-between text-[11px] text-[#8C8275]">
            <p>شكرًا لاختياركم هيبة السلطان - عنوان الفخامة والقطع النادرة</p>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-[#4B4338] font-medium">فاتورة رقمية موثقة إلكترونياً</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
