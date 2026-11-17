import React, { useEffect, useState } from 'react';
import {
  Gem,
  Award,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Share2,
  FileText,
  BadgeCheck,
  Copy,
  Check,
  Printer,
  ChevronLeft,
  ExternalLink,
  MessageCircle
} from 'lucide-react';
import { Product } from '../types';
import { BoxQRLabelModal } from '../components/BoxQRLabelModal';

interface ProductDetailPageProps {
  product: Product;
  allProducts?: Product[];
  onBackToStore: () => void;
  currentUser?: any;
}

export const ProductDetailPage: React.FC<ProductDetailPageProps> = ({
  product,
  allProducts = [],
  onBackToStore,
  currentUser
}) => {
  const [copiedLink, setCopiedLink] = useState(false);
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [product.id, product.public_id]);

  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://haybatalsultan.com';
  const pieceUrl = `${origin}/p/${product.public_id || product.id}`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(pieceUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleWhatsAppContact = () => {
    const text = encodeURIComponent(
      `السلام عليكم ورحمة الله وبركاته،\nأنا أستعرض وثيقة هذه المسبحة من هيبة السلطان:\n\n• الاسم: ${product.name_ar}\n• الرمز: ${product.sku} (${product.product_reference})\n• الرابط: ${pieceUrl}\n\nأود الاستفسار عنها أو طلب قطعة مماثلة.`
    );
    window.open(`https://wa.me/971504084006?text=${text}`, '_blank');
  };

  const fallbackStory = `تحفة ملكية نادرة صيغت بحرفية يدوية رفيعة المستوى على يد أمهر خراطي المسابيح التقليديين. تم استخراج خاماتها الطبيعية وعنايتها بدقة للحفاظ على نقائها التاريخي وملمسها الفريد، وتأتي مصحوبة بفحص مخبري رسمي يثبت أصالتها المطلقة وخلوها من أي معالجات صناعية. قطعة فريدة تليق بالمجموعات الخاصة وأصحاب الذوق الرفيع.`;

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#26221C] py-6 sm:py-10 selection:bg-[#C9972B]/20" dir="rtl">
      
      {/* Box QR Print Modal */}
      {isPrintModalOpen && (
        <BoxQRLabelModal
          product={product}
          onClose={() => setIsPrintModalOpen(false)}
        />
      )}

      <div className="max-w-4xl mx-auto px-4 sm:px-6 space-y-8">

        {/* 1. Royal Top Bar & Verification Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-5 border-b border-[#EBE3D5]">
          <div className="flex items-center gap-2">
            <button
              onClick={onBackToStore}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FAF4E8] text-[#26221C] hover:text-[#9A6817] border border-[#DDD3C1] hover:border-[#C9972B] rounded-xl text-xs font-bold transition cursor-pointer"
            >
              <ArrowRight className="w-3.5 h-3.5" />
              <span>المتجر الرئيسي</span>
            </button>
            <span className="text-[#C8BCAB]">/</span>
            <span className="text-xs text-[#8C8275] font-mono">وثيقة التحقق #{product.sku}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPrintModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#FAF4E8] hover:bg-[#F2ECE1] text-[#9A6817] border border-[#C9972B]/30 rounded-xl text-xs font-bold transition shadow-2xs cursor-pointer"
              title="طباعة ملصق العلبة الملكي (QR)"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>طباعة ملصق العلبة</span>
            </button>

            <button
              onClick={handleCopyLink}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FAF4E8] text-[#26221C] border border-[#DDD3C1] rounded-xl text-xs font-semibold transition cursor-pointer"
              title="نسخ رابط التحقق غير القابل للتخمين"
            >
              {copiedLink ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700 font-bold">تم النسخ</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-[#746A5D]" />
                  <span>مشاركة الوثيقة</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 2. Official Certificate Badge */}
        <div className="bg-gradient-to-r from-[#1C1814] via-[#2A241E] to-[#1C1814] text-white p-4 sm:p-5 rounded-3xl border border-[#C9972B]/40 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-right">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-[#C9972B]/20 border border-[#C9972B]/50 flex items-center justify-center shrink-0">
              <Award className="w-6 h-6 text-[#E5B84B]" />
            </div>
            <div>
              <div className="flex items-center justify-center sm:justify-start gap-1.5 text-[#F4E3BA] font-bold text-sm">
                <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
                <span>هيبة السلطان - وثيقة أصالة ومواصفات رسمية</span>
              </div>
              <p className="text-xs text-[#C8BCAB] mt-0.5">
                قطعة مقتناة أصلية موثقة برمز تعريفي فريد غير قابل للتكرار أو التخمين
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-white/10 px-3.5 py-1.5 rounded-full border border-[#C9972B]/30 text-xs font-mono text-[#F4E3BA]">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>AUTHENTIC GUARANTEED</span>
          </div>
        </div>

        {/* 3. Product Presentation Card */}
        <div className="bg-white rounded-3xl border border-[#EBE3D5] p-5 sm:p-8 shadow-xs space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            
            {/* Image Showcase */}
            <div className="relative aspect-square rounded-2xl overflow-hidden bg-[#F5EFE6] border-2 border-[#E5DAC8] group shadow-inner flex items-center justify-center">
              {product.primary_image ? (
                <img
                  src={product.primary_image}
                  alt={product.name_ar}
                  className="w-full h-full object-cover transition duration-700 group-hover:scale-105"
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-[#9E9485] gap-2 p-6 text-center">
                  <Gem className="w-16 h-16 text-[#C9972B]/40" />
                  <span className="text-xs font-serif font-bold text-[#746A5D]">صورة التحفة التوثيقية</span>
                </div>
              )}

              {/* Status Pill */}
              <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-xs px-3 py-1 rounded-full text-xs font-bold text-[#9A6817] border border-[#E0D7C6] shadow-xs flex items-center gap-1.5">
                <BadgeCheck className="w-4 h-4 text-[#C9972B]" />
                <span>قطعة معتمدة</span>
              </div>

              {/* Serial Watermark */}
              <div className="absolute bottom-3 left-3 bg-[#1C1814]/80 backdrop-blur-xs text-white/90 px-3 py-1 rounded-lg text-[11px] font-mono border border-white/10">
                {product.sku}
              </div>
            </div>

            {/* Product Identity & Valuation */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#FAF4E8] rounded-full border border-[#E8DCBE] text-xs font-mono font-bold text-[#9A6817]">
                <span>رقم الصنف: {product.sku}</span>
                <span>•</span>
                <span className="text-[#645A4C]">{product.product_reference}</span>
              </div>

              <h1 className="text-xl sm:text-2xl font-black text-[#26221C] leading-snug">
                {product.name_ar}
              </h1>

              {product.name_en && (
                <p className="text-xs text-[#8C8275] font-serif tracking-wide">
                  {product.name_en}
                </p>
              )}

              {/* Official Valuation */}
              <div className="bg-[#FAF7F2] p-4 rounded-2xl border border-[#EEE4D4] flex items-baseline justify-between">
                <div>
                  <span className="text-xs text-[#746A5D] block">القيمة التقديرية المعتمدة:</span>
                  <span className="text-2xl sm:text-3xl font-black text-[#9A6817]">
                    {product.selling_price.toLocaleString()}
                  </span>
                  <span className="text-xs text-[#746A5D] font-bold mr-1.5">درهم إماراتي (AED)</span>
                </div>
                <div className="text-left text-[11px] text-[#8C8275] font-mono">
                  <span className="block">حالة الصنف:</span>
                  <span className="font-bold text-emerald-700">مقتنى أصلي</span>
                </div>
              </div>

              {/* Quick Specs Highlights */}
              <div className="grid grid-cols-3 gap-2.5 text-center text-xs">
                <div className="p-3 bg-white rounded-xl border border-[#EADBCE]">
                  <span className="block text-[11px] text-[#8C8275] mb-0.5">عدد الخرز</span>
                  <span className="font-black text-[#26221C] text-sm">{product.bead_count} حبة</span>
                </div>
                <div className="p-3 bg-white rounded-xl border border-[#EADBCE]">
                  <span className="block text-[11px] text-[#8C8275] mb-0.5">مقاس الخرزة</span>
                  <span className="font-black text-[#26221C] text-sm">{product.bead_size_mm} mm</span>
                </div>
                <div className="p-3 bg-white rounded-xl border border-[#EADBCE]">
                  <span className="block text-[11px] text-[#8C8275] mb-0.5">الوزن الصافي</span>
                  <span className="font-black text-[#26221C] text-sm">{product.weight_g} g</span>
                </div>
              </div>

              <p className="text-xs text-[#746A5D] leading-relaxed pt-1">
                تأتي هذه التحفة محفوظة في علبة فاخرة ومبطنة بمخمل ملكي، مع ملصق التحقق المشفر وبطاقة الضمان الذهبي من هيبة السلطان.
              </p>
            </div>
          </div>
        </div>

        {/* 4. Heritage Story Section (قصة الصنف) */}
        <div className="bg-white rounded-3xl border border-[#EBE3D5] p-6 sm:p-8 shadow-xs space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[#F2ECE1]">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] border border-[#EADBCE] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-[#C9972B]" />
            </div>
            <div>
              <h2 className="text-lg font-black text-[#26221C]">عراقة وقصة الصنف</h2>
              <p className="text-xs text-[#8C8275]">التاريخ الحرفي والمصدر الطبيعي للخامة</p>
            </div>
          </div>

          <div className="text-sm sm:text-base leading-relaxed text-[#4B4338] bg-[#FAF7F2] p-5 sm:p-6 rounded-2xl border border-[#EEE4D4] font-serif space-y-3">
            <p className="first-letter:text-2xl first-letter:font-black first-letter:text-[#9A6817]">
              {product.description_ar || fallbackStory}
            </p>
          </div>
        </div>

        {/* 5. Technical Specifications Table (جدول مواصفات الصنف الفنية) */}
        <div className="bg-white rounded-3xl border border-[#EBE3D5] p-6 sm:p-8 shadow-xs space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[#F2ECE1]">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] border border-[#EADBCE] flex items-center justify-center">
              <FileText className="w-5 h-5 text-[#9A6817]" />
            </div>
            <div>
              <h2 className="text-lg font-black text-[#26221C]">جدول المواصفات الفنية المعتمدة</h2>
              <p className="text-xs text-[#8C8275]">المعايير المادية الدقيقة المفحوصة مخبرياً</p>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-[#E8DEC9]">
            <table className="w-full text-right text-xs sm:text-sm">
              <tbody className="divide-y divide-[#EFE7D8]">
                <tr className="bg-[#FAF7F2]">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D] w-1/3">الخامة / المادة</td>
                  <td className="py-3 px-4 sm:px-6 font-black text-[#26221C]">{product.material_name_ar || 'خامة طبيعية نادرة'}</td>
                </tr>
                <tr className="bg-white">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">عدد الخرز (Bead Count)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C] font-mono">{product.bead_count} حبة</td>
                </tr>
                <tr className="bg-[#FAF7F2]">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">قياس قطر الخرزة (Size mm)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C] font-mono">{product.bead_size_mm} مليمتر</td>
                </tr>
                <tr className="bg-white">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">الوزن الصافي الإجمالي (Weight)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C] font-mono">{product.weight_g} جرام</td>
                </tr>
                <tr className="bg-[#FAF7F2]">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">قصة وشكل الخراطة (Shape)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C]">{product.shape || 'برميلي ملكي'}</td>
                </tr>
                <tr className="bg-white">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">الكركوشة والشاهد (Tassel)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C]">{product.tassel_type || 'فضة كازازية عيار 1000'}</td>
                </tr>
                <tr className="bg-[#FAF7F2]">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">بلد المنشأ (Origin)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C]">{product.origin || 'أوروبا / البلطيق'}</td>
                </tr>
                <tr className="bg-white">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">اللون ودرجة التعريق (Patina)</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#26221C]">{product.color || 'أصفر ملكي معرق طبيعي'}</td>
                </tr>
                <tr className="bg-[#FAF7F2]">
                  <td className="py-3 px-4 sm:px-6 font-bold text-[#746A5D]">شهادة الفحص المخبري</td>
                  <td className="py-3 px-4 sm:px-6 font-bold text-emerald-800 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>مفحوصة ومطابقة لأعلى معايير الأصالة الدولية</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 6. Sole Primary Action: Explore Storefront / Other Products */}
        <div className="bg-gradient-to-b from-[#FAF4E8] to-[#F2ECE1] p-6 sm:p-8 rounded-3xl border-2 border-[#C9972B]/40 text-center space-y-4 shadow-sm">
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-black text-[#26221C]">
              هل تود اكتشاف المزيد من نوادر هيبة السلطان؟
            </h3>
            <p className="text-xs text-[#746A5D] leading-relaxed">
              استكشف مجموعتنا الحصرية من مسابيح الكهرمان البلطيقي الملكي، الفاتوران النادر، والبكلايت الفاخر.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            {/* The main requested button */}
            <button
              onClick={onBackToStore}
              className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-[#C9972B] via-[#B8851E] to-[#9A6817] hover:from-[#DFB048] hover:to-[#B47B1F] text-white font-black text-sm rounded-2xl shadow-lg hover:shadow-xl transition flex items-center justify-center gap-2.5 cursor-pointer transform hover:-translate-y-0.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>شاهد منتجات أخرى وتصفح المتجر</span>
              <ChevronLeft className="w-4 h-4" />
            </button>

            {/* Subtle WhatsApp consultation */}
            <button
              onClick={handleWhatsAppContact}
              className="w-full sm:w-auto px-6 py-4 bg-white hover:bg-[#FAF7F2] text-[#26221C] border border-[#DDD3C1] hover:border-[#C9972B] font-bold text-xs rounded-2xl transition flex items-center justify-center gap-2 cursor-pointer"
            >
              <MessageCircle className="w-4 h-4 text-emerald-600" />
              <span>استفسار حول هذه القطعة عبر واتساب</span>
            </button>
          </div>
        </div>

        {/* 7. Footer Seal */}
        <div className="text-center text-[11px] text-[#9E9485] space-y-1 pb-4">
          <p>© جميع الحقوق محفوظة لدار هيبة السلطان للمقتنيات والمسابيح الفاخرة</p>
          <p className="font-mono text-[10px] text-[#B0A696]">
            Secure Verification Identifier: {product.public_id || product.id}
          </p>
        </div>

      </div>
    </div>
  );
};
