import React, { useRef } from 'react';
import { X, Printer, Award, ShieldCheck, Sparkles } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { Product } from '../types';

interface BoxQRLabelModalProps {
  product: Product | null;
  onClose: () => void;
}

export const BoxQRLabelModal: React.FC<BoxQRLabelModalProps> = ({ product, onClose }) => {
  const printAreaRef = useRef<HTMLDivElement>(null);

  if (!product) return null;

  // Dedicated unpredictable URL for this unique piece
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://haybatalsultan.com';
  const qrUrl = `${origin}/p/${product.public_id || product.id}`;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs" dir="rtl">
      {/* Print-specific style sheet */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #box-qr-print-zone, #box-qr-print-zone * {
            visibility: visible;
          }
          #box-qr-print-zone {
            position: fixed;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 80mm;
            max-width: 80mm;
            padding: 4mm;
            margin: 0;
            background: white !important;
            color: black !important;
            border: 2px solid #C9972B !important;
            box-shadow: none !important;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>

      <div className="bg-[#131B2E] border border-[#C9972B]/40 rounded-3xl max-w-md w-full p-6 text-white shadow-2xl relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 no-print">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-[#C9972B]" />
            <h3 className="font-bold text-base text-[#F4E3BA]">ملصق علبة السبحة الملكية (QR)</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-white/70 hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Printable Label Preview Container */}
        <div className="my-6 flex justify-center">
          <div
            id="box-qr-print-zone"
            ref={printAreaRef}
            className="w-[280px] bg-[#FAF7F2] text-[#26221C] p-4 rounded-2xl border-2 border-[#C9972B] shadow-lg flex flex-col items-center text-center relative overflow-hidden"
          >
            {/* Golden Header Crest */}
            <div className="flex items-center gap-1.5 text-[#9A6817] font-bold text-xs uppercase tracking-wider mb-1">
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>هيبة السلطان</span>
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
            </div>
            <p className="text-[10px] text-[#746A5D] font-medium mb-3">HAYBAT AL SULTAN LUXURY ROSARIES</p>

            {/* High-Resolution QR Code */}
            <div className="bg-white p-2.5 rounded-xl border border-[#D5C9B3] shadow-inner mb-3">
              <QRCodeSVG
                value={qrUrl}
                size={140}
                level="H"
                includeMargin={false}
                bgColor="#FFFFFF"
                fgColor="#1C1814"
              />
            </div>

            {/* Product Title & Reference */}
            <h4 className="font-bold text-xs text-[#26221C] line-clamp-2 leading-snug px-1 mb-1">
              {product.name_ar}
            </h4>

            {/* SKU and Certified Serial */}
            <div className="flex items-center justify-center gap-2 text-[10px] text-[#9A6817] font-mono font-bold mt-1 mb-2">
              <span className="bg-[#FAF4E8] px-2 py-0.5 rounded border border-[#E0D4C0]">{product.sku}</span>
              <span>•</span>
              <span className="text-[#645A4C]">{product.product_reference}</span>
            </div>

            {/* Scanning Instruction */}
            <div className="flex items-center gap-1 text-[9px] text-[#746A5D] bg-[#F2ECE1] px-2.5 py-1 rounded-full border border-[#DDD3C1]">
              <ShieldCheck className="w-3 h-3 text-emerald-700 shrink-0" />
              <span>امسح الكود لقراءة قصة ومواصفات القطعة</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2 no-print">
          <button
            onClick={handlePrint}
            className="flex-1 py-3 bg-gradient-to-r from-[#C9972B] to-[#9A6817] hover:from-[#DFB048] hover:to-[#B47B1F] text-white font-bold text-sm rounded-xl flex items-center justify-center gap-2 shadow-lg transition cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>طباعة ملصق العلبة الآن</span>
          </button>
          <button
            onClick={onClose}
            className="px-4 py-3 bg-white/10 hover:bg-white/15 text-white/80 hover:text-white rounded-xl text-xs font-semibold transition cursor-pointer"
          >
            إغلاق
          </button>
        </div>

        <p className="text-[11px] text-center text-white/50 mt-3 no-print">
          يمكنك طباعة هذا الملصق ولصقه مباشرة على علبة المسبحة الفاخرة للتحقق السريع.
        </p>
      </div>
    </div>
  );
};
