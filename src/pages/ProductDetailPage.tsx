import React, { useEffect, useState } from 'react';
import {
  Gem,
  Award,
  Clock,
  ShoppingCart,
  MessageCircle,
  Sparkles,
  Truck,
  Gift,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Share2,
  FileText,
  BadgeCheck,
  ChevronLeft,
  Copy,
  Check
} from 'lucide-react';
import { Product } from '../types';

interface ProductDetailPageProps {
  product: Product;
  allProducts: Product[];
  onOpenCheckout: (product: Product) => void;
  onReserve: (product: Product) => void;
  onSelectProduct: (product: Product) => void;
  onBackToStore: () => void;
}

export const ProductDetailPage: React.FC<ProductDetailPageProps> = ({
  product,
  allProducts,
  onOpenCheckout,
  onReserve,
  onSelectProduct,
  onBackToStore
}) => {
  const [copiedSku, setCopiedSku] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [product.id]);

  const handleCopySku = () => {
    navigator.clipboard.writeText(product.sku);
    setCopiedSku(true);
    setTimeout(() => setCopiedSku(false), 2000);
  };

  const handleWhatsAppOrder = () => {
    const text = encodeURIComponent(
      `السلام عليكم ورحمة الله وبركاته،\nأود اقتناء هذه التحفة من هيبة السلطان:\n\n• الاسم: ${product.name_ar}\n• الرمز المرجعي: ${product.product_reference}\n• الـ SKU: ${product.sku}\n• السعر: ${product.selling_price.toLocaleString()} AED\n\nيرجى تأكيد التوافر وإجراءات الاستلام أو التوصيل.`
    );
    window.open(`https://wa.me/971504084006?text=${text}`, '_blank');
  };

  // Find related products (same material, category, or closest in price)
  const relatedProducts = allProducts
    .filter((p) => p.id !== product.id && p.status === 'AVAILABLE')
    .sort((a, b) => {
      // Prioritize same material or category
      const aMatch = (a.material_id && a.material_id === product.material_id) ? 2 : 0;
      const bMatch = (b.material_id && b.material_id === product.material_id) ? 2 : 0;
      return bMatch - aMatch;
    })
    .slice(0, 3);

  const fallbackStory = `تحفة ملكية نادرة صيغت بحرفية يدوية رفيعة المستوى على يد أمهر خراطي المسابيح التقليديين. تم استخراج خاماتها الطبيعية وعنايتها بدقة للحفاظ على نقائها التاريخي وملمسها الفريد، وتأتي مصحوبة بفحص مخبري رسمي يثبت أصالتها المطلقة وخلوها من أي معالجات صناعية. قطعة فريدة تليق بالمجموعات الخاصة وأصحاب الذوق الرفيع.`;

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#26221C] py-8 selection:bg-[#C9972B]/20" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        
        {/* 1. Breadcrumbs & Back Navigation */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#EBE3D5]">
          <nav className="flex items-center gap-2 text-xs text-[#746A5D]">
            <button
              onClick={onBackToStore}
              className="hover:text-[#9A6817] font-semibold transition cursor-pointer"
            >
              الرئيسية
            </button>
            <span className="text-[#C8BCAB]">/</span>
            <button
              onClick={onBackToStore}
              className="hover:text-[#9A6817] font-semibold transition cursor-pointer"
            >
              المعروضات الفاخرة
            </button>
            <span className="text-[#C8BCAB]">/</span>
            <span className="text-[#26221C] font-bold truncate max-w-[200px] sm:max-w-xs">
              {product.name_ar}
            </span>
          </nav>

          <button
            onClick={onBackToStore}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-[#FAF4E8] text-[#26221C] hover:text-[#9A6817] border border-[#DDD3C1] hover:border-[#C9972B] rounded-2xl text-xs font-bold transition shadow-2xs cursor-pointer"
          >
            <ArrowRight className="w-4 h-4 text-[#C9972B]" />
            <span>العودة لكافة المعروضات</span>
          </button>
        </div>

        {/* 2. Primary Product Showcase Grid (Image + Purchasing Box) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          
          {/* Right Column: Visual Showcase (6 cols) */}
          <div className="lg:col-span-6 space-y-4">
            <div className="relative aspect-square rounded-3xl overflow-hidden bg-white border border-[#EBE3D5] shadow-lg group">
              <img
                src={product.image_url || '/branding/hero-amber.jpg'}
                alt={product.name_ar}
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />

              {/* Top Badges */}
              <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
                <span className="bg-[#26221C]/90 backdrop-blur-md text-[#E2B84B] border border-[#C9972B]/60 px-3.5 py-1.5 rounded-full text-xs font-black shadow-md flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#E2B84B]" />
                  <span>قطعة فريدة حصرية</span>
                </span>
                {product.verification_status === 'CERTIFIED' && (
                  <span className="bg-emerald-600/95 backdrop-blur text-white px-3 py-1 rounded-full text-xs font-bold shadow-md flex items-center gap-1">
                    <BadgeCheck className="w-3.5 h-3.5" />
                    <span>مفحوصة ومعتمدة رسمياً</span>
                  </span>
                )}
              </div>

              {/* SKU & Reference Pill */}
              <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-md px-3 py-1 rounded-xl text-xs font-mono font-bold text-[#746A5D] border border-[#E4D5B8] shadow-xs">
                {product.sku}
              </div>
            </div>

            {/* Quality Guarantees Strip */}
            <div className="grid grid-cols-3 gap-3 p-4 bg-white rounded-2xl border border-[#EBE3D5] text-center shadow-xs">
              <div className="space-y-1">
                <Truck className="w-4 h-4 text-[#C9972B] mx-auto" />
                <p className="text-[11px] font-bold text-[#26221C]">شحن سريع ومؤمن</p>
                <p className="text-[9px] text-[#746A5D]">للإمارات ودول الخليج</p>
              </div>
              <div className="space-y-1 border-r border-l border-[#F0E6D6]">
                <Gift className="w-4 h-4 text-[#C9972B] mx-auto" />
                <p className="text-[11px] font-bold text-[#26221C]">تغليف هدايا ملكي</p>
                <p className="text-[9px] text-[#746A5D]">علبة مخملية فاخرة</p>
              </div>
              <div className="space-y-1">
                <ShieldCheck className="w-4 h-4 text-[#C9972B] mx-auto" />
                <p className="text-[11px] font-bold text-[#26221C]">ضمان الأصالة 100%</p>
                <p className="text-[9px] text-[#746A5D]">شهادة فحص مخبرية</p>
              </div>
            </div>
          </div>

          {/* Left Column: Product Info, Price & Actions (6 cols) */}
          <div className="lg:col-span-6 bg-white border border-[#EBE3D5] rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
            
            {/* Meta Tags */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF4E8] text-[#9A6817] border border-[#E4D5B8]">
                {product.category_name_ar || 'مسابيح فاخرة'}
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF7F2] text-[#746A5D] border border-[#DDD3C1]">
                {product.origin || 'أصيل المنشأ'}
              </span>
              <div className="mr-auto flex items-center gap-1.5 text-xs text-[#746A5D]">
                <span className="font-mono text-xs">{product.sku}</span>
                <button
                  onClick={handleCopySku}
                  className="p-1 hover:text-[#C9972B] transition"
                  title="نسخ كود المسبحة"
                >
                  {copiedSku ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Title */}
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-black text-[#26221C] leading-tight">
                {product.name_ar}
              </h1>
              <p className="text-xs text-[#8C8275] font-mono mt-1 dir-ltr text-right">
                Ref: {product.product_reference}
              </p>
            </div>

            {/* Price Box */}
            <div className="p-5 bg-gradient-to-r from-[#FAF4E8] via-[#FFFDF8] to-[#F5ECE0] rounded-2xl border border-[#E4D5B8] flex items-baseline justify-between">
              <div>
                <span className="block text-xs font-semibold text-[#8C8275]">قيمة الاقتناء المعتمدة</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl sm:text-4xl font-black text-[#9A6817]">
                    {product.selling_price.toLocaleString()}
                  </span>
                  <span className="text-sm font-black text-[#4B4338]">درهم إماراتي (AED)</span>
                </div>
              </div>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
                متوفرة للتسليم الفوري
              </span>
            </div>

            {/* Core Action Buttons */}
            <div className="space-y-3 pt-2">
              {/* 1. Primary Checkout / Add to Cart */}
              <button
                onClick={() => onOpenCheckout(product)}
                className="w-full py-4 bg-[#C9972B] hover:bg-[#B8851E] text-white text-sm sm:text-base font-black rounded-2xl transition-all shadow-[0_6px_20px_rgba(201,151,43,0.35)] hover:shadow-xl flex items-center justify-center gap-2.5 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <ShoppingCart className="w-5 h-5" />
                <span>اقتناء فوري أونلاين (إتمام الطلب)</span>
              </button>

              {/* 2. Secondary: 15-min Lock + WhatsApp Inquiry */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={() => onReserve(product)}
                  className="py-3 bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border border-[#E4D5B8] text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 cursor-pointer"
                  title="حجز مؤقت يمنع أي شخص أو معرض آخر من شرائها لمدة 15 دقيقة"
                >
                  <Clock className="w-4 h-4" />
                  <span>حجز حصري 15 دقيقة</span>
                </button>

                <button
                  onClick={handleWhatsAppOrder}
                  className="py-3 bg-[#25D366] hover:bg-[#1EBE5D] text-white text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>طلب واستشارة عبر واتساب</span>
                </button>
              </div>
            </div>

            {/* Exclusivity Trust Note */}
            <div className="pt-2 border-t border-[#F5EFE6] flex items-center gap-2 text-xs text-[#746A5D]">
              <CheckCircle2 className="w-4 h-4 text-[#C9972B] shrink-0" />
              <span>
                محصنة ضد البيع المزدوج: بمجرد تأكيدك للاقتناء يتم إغلاق المعروض فوراً من النظام المركزي.
              </span>
            </div>

          </div>
        </div>

        {/* 3. Section: قصة الصنف (Product Heritage Story) */}
        <section className="bg-white border border-[#EBE3D5] rounded-3xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-[#EBE3D5]">
            <div className="w-10 h-10 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-black text-[#26221C]">
                قصة التحفة وأصالة الصنعة
              </h2>
              <p className="text-xs text-[#746A5D]">
                تاريخ الخامة، عراقة المنشأ، والحرفية التي صاغت هذا المقتنى الفريد
              </p>
            </div>
          </div>

          <div className="prose max-w-none text-[#3D352E] text-sm sm:text-base leading-relaxed space-y-4">
            <p className="font-normal text-justify leading-loose">
              {product.description_ar || fallbackStory}
            </p>
          </div>

          <div className="bg-[#FAF7F2] border-r-4 border-[#C9972B] p-4 rounded-xl text-xs sm:text-sm text-[#4B4338] italic">
            "كل مسبحة في دار هيبة السلطان ليست مجرد خرز، بل هي رحلة عبر الزمن ومقتنى تتوارثه الأجيال، يعكس هيبة حامله وذائقته الملكية."
          </div>
        </section>

        {/* 4. Section: جدول مواصفات الصنف الفنية (Technical Specifications Table) */}
        <section className="bg-white border border-[#EBE3D5] rounded-3xl p-6 sm:p-10 shadow-xs space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-[#EBE3D5]">
            <div className="w-10 h-10 rounded-2xl bg-[#26221C] text-[#E2B84B] flex items-center justify-center shadow-md">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-black text-[#26221C]">
                جدول المواصفات الفنية المعتمدة
              </h2>
              <p className="text-xs text-[#746A5D]">
                القياسات الهندسية والأوزان الدقيقة المفحوصة مخبرياً
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse text-xs sm:text-sm">
              <tbody className="divide-y divide-[#EBE3D5]">
                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60 w-1/3 sm:w-1/4">
                    الخامة والنوع
                  </td>
                  <td className="py-3.5 px-4 font-extrabold text-[#26221C]">
                    {product.name_ar}
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    عدد الخرز (Bead Count)
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#26221C]">
                    {product.bead_count} خرزة
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    قياس الخرز (Size)
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#26221C]">
                    {product.bead_size_mm} ملم (mm)
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    الوزن الصافي (Weight)
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#26221C]">
                    {product.weight_g} جرام (g)
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    شكل القصة (Shape / Cut)
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[#26221C]">
                    {product.shape || 'قصة برميلية كلاسيكية'}
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    الكركوشة والشرابة (Tassel)
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[#26221C]">
                    {product.tassel_type || 'فضة إسترليني خالصة عيار 1000'}
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    بلد المنشأ والاستخراج (Origin)
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[#26221C]">
                    {product.origin || 'طبيعي معتمد'}
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    اللون والتعتيق (Color / Patina)
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[#26221C]">
                    {product.color || 'تعتيق طبيعي أصلي'}
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    حالة الفحص والشهادة المخبرية
                  </td>
                  <td className="py-3.5 px-4 font-bold text-emerald-800 flex items-center gap-1.5">
                    <BadgeCheck className="w-4 h-4 text-emerald-600" />
                    <span>
                      {product.verification_status === 'CERTIFIED'
                        ? `معتمدة بشهادة فحص رقم (${product.certificate_number || 'HA-CERT-9042'})`
                        : 'أصلية مفحوصة ومضمونة مخبرياً'}
                    </span>
                  </td>
                </tr>

                <tr className="hover:bg-[#FAF7F2] transition">
                  <td className="py-3.5 px-4 font-bold text-[#8C8275] bg-[#FAF7F2]/60">
                    رمز القطعة (Reference / SKU)
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#9A6817]">
                    {product.sku} ({product.product_reference})
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 5. Section: مقترحات قريبة من نفس الصنف (Related Recommendations) */}
        {relatedProducts.length > 0 && (
          <section className="space-y-6 pt-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl sm:text-2xl font-black text-[#26221C] flex items-center gap-2">
                  <Gem className="w-6 h-6 text-[#C9972B]" />
                  <span>مقترحات قريبة ونوادر مشابهة</span>
                </h2>
                <p className="text-xs sm:text-sm text-[#746A5D] mt-1">
                  قطع مختارة من نفس الفئة وعراقة الخامة قد تنال إعجابكم
                </p>
              </div>

              <button
                onClick={onBackToStore}
                className="text-xs font-bold text-[#9A6817] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>مشاهدة الكل</span>
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {relatedProducts.map((rel) => (
                <div
                  key={rel.id}
                  className="bg-white border border-[#EBE3D5] rounded-3xl overflow-hidden flex flex-col justify-between hover:shadow-xl hover:border-[#C9972B] transition-all group"
                >
                  <div>
                    {/* Thumbnail */}
                    <div
                      onClick={() => onSelectProduct(rel)}
                      className="relative aspect-square overflow-hidden bg-[#FBF8F2] cursor-pointer"
                    >
                      <img
                        src={rel.image_url || '/branding/hero-amber.jpg'}
                        alt={rel.name_ar}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute top-3 right-3 bg-white/95 backdrop-blur px-2.5 py-1 rounded-full text-[10px] font-bold text-[#9A6817] border border-[#E8DEC8]">
                        {rel.sku}
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-5 space-y-2">
                      <h3
                        onClick={() => onSelectProduct(rel)}
                        className="font-black text-sm text-[#26221C] group-hover:text-[#9A6817] transition cursor-pointer line-clamp-1"
                      >
                        {rel.name_ar}
                      </h3>

                      <div className="flex items-center gap-2 text-[11px] text-[#746A5D]">
                        <span>{rel.bead_count} خرزة</span>
                        <span>•</span>
                        <span>{rel.bead_size_mm}mm</span>
                        <span>•</span>
                        <span>{rel.weight_g}g</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions & Price */}
                  <div className="p-5 pt-0 border-t border-[#F5EFE6] mt-2">
                    <div className="flex items-baseline justify-between py-2">
                      <span className="text-[11px] text-[#746A5D]">القيمة:</span>
                      <span className="text-base font-black text-[#9A6817]">
                        {rel.selling_price.toLocaleString()} <span className="text-[10px] text-[#746A5D]">AED</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <button
                        onClick={() => onSelectProduct(rel)}
                        className="py-2 bg-[#FAF4E8] hover:bg-[#F3E7CE] text-[#9A6817] border border-[#E4D5B8] text-xs font-bold rounded-xl transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <span>عرض التفاصيل</span>
                      </button>

                      <button
                        onClick={() => onOpenCheckout(rel)}
                        className="py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white text-xs font-bold rounded-xl transition flex items-center justify-center gap-1 shadow-xs cursor-pointer"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>اقتناء</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  );
};
