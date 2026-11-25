import React, { useEffect, useState, useRef, useCallback } from 'react';
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
  ChevronRight,
  ExternalLink,
  MessageCircle,
  Gift,
  Truck,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  X,
  Maximize2,
  Move
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

  // Zoom Lightbox State
  const [isZoomOpen, setIsZoomOpen] = useState(false);
  const [zoomScale, setZoomScale] = useState(1);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Parse all available product images (primary + secondary up to 3)
  const rawImages: string[] = [
    product.image_url || (product as any).primary_image,
    ...(() => {
      try {
        if (typeof product.secondary_images === 'string') {
          return JSON.parse(product.secondary_images);
        }
        if (Array.isArray(product.secondary_images)) {
          return product.secondary_images;
        }
      } catch {}
      return [];
    })()
  ].filter((img): img is string => typeof img === 'string' && img.trim().length > 0);

  const productImages: string[] = Array.from(new Set(rawImages)).length > 0
    ? Array.from(new Set(rawImages))
    : ['/branding/hero-amber.jpg'];

  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const activeImage = productImages[activeImageIndex] || productImages[0];

  const handleNextImage = useCallback(() => {
    setActiveImageIndex((prev) => (prev + 1) % productImages.length);
    setZoomScale(1);
    setPanPosition({ x: 0, y: 0 });
  }, [productImages.length]);

  const handlePrevImage = useCallback(() => {
    setActiveImageIndex((prev) => (prev - 1 + productImages.length) % productImages.length);
    setZoomScale(1);
    setPanPosition({ x: 0, y: 0 });
  }, [productImages.length]);

  const handleResetZoom = () => {
    setZoomScale(1);
    setPanPosition({ x: 0, y: 0 });
  };

  const handleZoomIn = () => {
    setZoomScale((s) => Math.min(3.5, Math.round((s + 0.5) * 10) / 10));
  };

  const handleZoomOut = () => {
    setZoomScale((s) => {
      const next = Math.max(1, Math.round((s - 0.5) * 10) / 10);
      if (next === 1) setPanPosition({ x: 0, y: 0 });
      return next;
    });
  };

  const handleToggleZoom = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (zoomScale === 1) {
      setZoomScale(2);
    } else if (zoomScale === 2) {
      setZoomScale(3);
    } else {
      handleResetZoom();
    }
  };

  // Keyboard navigation when zoom lightbox is open
  useEffect(() => {
    if (!isZoomOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsZoomOpen(false);
        handleResetZoom();
      } else if (e.key === 'ArrowRight') {
        handlePrevImage(); // RTL layout
      } else if (e.key === 'ArrowLeft') {
        handleNextImage();
      } else if (e.key === '+' || e.key === '=') {
        handleZoomIn();
      } else if (e.key === '-') {
        handleZoomOut();
      } else if (e.key === '0') {
        handleResetZoom();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isZoomOpen, handleNextImage, handlePrevImage]);

  // Drag to Pan when zoomed
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoomScale <= 1) return;
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPosition.x, y: e.clientY - panPosition.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || zoomScale <= 1) return;
    setPanPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

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
            
            {/* Image Showcase & Multi-Angle Gallery */}
            <div className="space-y-3">
              <div 
                onClick={() => setIsZoomOpen(true)}
                className="relative aspect-square rounded-2xl overflow-hidden bg-[#F5EFE6] border-2 border-[#E5DAC8] group shadow-inner flex items-center justify-center cursor-zoom-in"
                title="انقر لتكبير الصورة وفحص تفاصيل الخامة والخرز"
              >
                {activeImage ? (
                  <img
                    src={activeImage}
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
                <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-xs px-3 py-1 rounded-full text-xs font-bold text-[#9A6817] border border-[#E0D7C6] shadow-xs flex items-center gap-1.5 pointer-events-none">
                  <BadgeCheck className="w-4 h-4 text-[#C9972B]" />
                  <span>قطعة معتمدة</span>
                </div>

                {/* Zoom Badge on hover / top left */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsZoomOpen(true);
                  }}
                  className="absolute top-3 left-3 bg-[#1C1814]/85 hover:bg-[#1C1814] text-[#F4E3BA] px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 border border-[#C9972B]/50 shadow-md transition cursor-pointer backdrop-blur-xs"
                >
                  <ZoomIn className="w-3.5 h-3.5 text-[#E2B84B]" />
                  <span>تكبير الصورة</span>
                </button>

                {/* Navigation Arrows on image when multiple images */}
                {productImages.length > 1 && (
                  <>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePrevImage();
                      }}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/60 hover:bg-[#C9972B] text-white flex items-center justify-center border border-white/20 transition shadow-lg cursor-pointer opacity-85 hover:opacity-100"
                      title="الصورة السابقة"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNextImage();
                      }}
                      className="absolute left-2.5 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/60 hover:bg-[#C9972B] text-white flex items-center justify-center border border-white/20 transition shadow-lg cursor-pointer opacity-85 hover:opacity-100"
                      title="الصورة التالية"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                  </>
                )}

                {/* Image Counter & Serial Watermark */}
                <div className="absolute bottom-3 inset-x-3 flex items-center justify-between pointer-events-none">
                  <div className="bg-[#1C1814]/85 backdrop-blur-xs text-white/90 px-2.5 py-1 rounded-lg text-[11px] font-mono border border-white/10">
                    {product.sku}
                  </div>
                  {productImages.length > 1 && (
                    <div className="bg-black/75 backdrop-blur-xs text-[#E2B84B] px-2.5 py-1 rounded-lg text-[11px] font-bold border border-[#C9972B]/40">
                      صورة {activeImageIndex + 1} من {productImages.length}
                    </div>
                  )}
                </div>
              </div>

              {/* Multi-Image Thumbnails (Up to 3 images or more) */}
              {productImages.length > 1 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2.5 pt-1">
                    {productImages.map((img, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setActiveImageIndex(idx);
                          setZoomScale(1);
                        }}
                        className={`relative w-20 h-20 rounded-xl overflow-hidden border-2 transition cursor-pointer group/thumb ${
                          activeImageIndex === idx
                            ? 'border-[#C9972B] shadow-md ring-2 ring-[#C9972B]/50 scale-105'
                            : 'border-[#E0D7C6] opacity-75 hover:opacity-100 hover:border-[#C9972B]'
                        }`}
                      >
                        <img src={img} alt={`صورة ${idx + 1}`} className="w-full h-full object-cover" />
                        <span className="absolute bottom-0 inset-x-0 bg-black/70 text-white text-[9px] font-bold py-0.5 text-center leading-none">
                          {idx === 0 ? 'الغلاف ⭐' : idx === 1 ? 'تفاصيل 🔍' : 'كركوشة 📿'}
                        </span>
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-center text-[#8C8275]">
                    انقر على أي صورة لمعاينتها أو انقر على الصورة الرئيسية لتكبيرها وفحص الخامة
                  </p>
                </div>
              )}

              {/* Dedicated Zoom Inspection Button */}
              <button
                type="button"
                onClick={() => setIsZoomOpen(true)}
                className="w-full py-2.5 px-4 bg-[#FAF4E8] hover:bg-[#F2ECE1] text-[#9A6817] border border-[#C9972B]/40 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-2xs cursor-pointer"
              >
                <ZoomIn className="w-4 h-4 text-[#C9972B]" />
                <span>فتح معرض الصور التفاعلي وتكبير التفاصيل (HD Zoom)</span>
              </button>
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

        {/* Royal Trust & Benefits Announcement Bar in Footer */}
        <div className="bg-gradient-to-r from-[#F7EFE3] via-[#FBF8F2] to-[#F6EEE2] border border-[#EEE4D4] rounded-2xl py-3 px-4 text-xs text-[#2B241B]">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-right">
            <div className="flex items-center gap-2 font-medium">
              <Gift className="w-4 h-4 text-[#C9972B]" />
              <span>تغليف فاخر للهدايا ومستندات الفحص الرسمية</span>
            </div>

            <div className="flex items-center gap-1.5 font-bold text-[#9A6817]">
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
              <span>✦ هيبة السلطان — أصالة المقتنيات الملكية</span>
            </div>

            <div className="flex items-center gap-2 font-medium">
              <Truck className="w-4 h-4 text-[#C9972B]" />
              <span>شحن مؤمن لجميع دول الخليج والعالم</span>
            </div>
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

      {/* 8. Luxury Fullscreen Zoom & Image Gallery Lightbox Modal */}
      {isZoomOpen && (
        <div 
          className="fixed inset-0 z-[999999] bg-black/95 backdrop-blur-md flex flex-col justify-between animate-in fade-in duration-200 select-none"
          dir="rtl"
        >
          {/* Top Control Bar */}
          <div className="p-4 sm:p-5 flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent border-b border-white/10 z-20">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#26221C] text-[#E2B84B] border border-[#C9972B]/40 flex items-center justify-center shadow-md">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                  <span>{product.name_ar}</span>
                  <span className="text-xs font-mono font-bold text-[#E2B84B] bg-white/10 px-2 py-0.5 rounded">
                    {product.sku}
                  </span>
                </h3>
                <p className="text-xs text-white/60">
                  معاينة مجهرية مكبرة للأصالة وتفاصيل الخرز • صورة {activeImageIndex + 1} من {productImages.length}
                </p>
              </div>
            </div>

            {/* Zoom & Action Controls */}
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-1 bg-white/10 p-1 rounded-xl border border-white/15">
                <button
                  type="button"
                  onClick={handleZoomOut}
                  disabled={zoomScale <= 1}
                  className="p-1.5 text-white/80 hover:text-white disabled:opacity-30 rounded-lg hover:bg-white/10 transition cursor-pointer"
                  title="تصغير (-)"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>

                <span className="text-xs font-mono font-bold text-[#E2B84B] px-2 min-w-[50px] text-center">
                  {Math.round(zoomScale * 100)}%
                </span>

                <button
                  type="button"
                  onClick={handleZoomIn}
                  disabled={zoomScale >= 3.5}
                  className="p-1.5 text-white/80 hover:text-white disabled:opacity-30 rounded-lg hover:bg-white/10 transition cursor-pointer"
                  title="تكبير (+)"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>

                {zoomScale > 1 && (
                  <button
                    type="button"
                    onClick={handleResetZoom}
                    className="p-1.5 text-amber-300 hover:text-white rounded-lg hover:bg-white/10 transition cursor-pointer"
                    title="إعادة ضبط الحجم (0)"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => {
                  setIsZoomOpen(false);
                  handleResetZoom();
                }}
                className="p-2 rounded-xl bg-white/10 hover:bg-rose-600/80 text-white transition border border-white/20 cursor-pointer shadow-md"
                title="إغلاق (Esc)"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Central Interactive Image Stage */}
          <div 
            className="flex-1 relative overflow-hidden flex items-center justify-center p-4"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onClick={handleToggleZoom}
            style={{
              cursor: zoomScale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'zoom-in'
            }}
          >
            {/* Previous Image Side Button */}
            {productImages.length > 1 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handlePrevImage();
                }}
                className="absolute right-4 sm:right-8 z-30 w-12 h-12 rounded-2xl bg-black/70 hover:bg-[#C9972B] text-white flex items-center justify-center border border-white/20 transition shadow-2xl cursor-pointer"
                title="الصورة السابقة (سهم يمين)"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
            )}

            {/* Next Image Side Button */}
            {productImages.length > 1 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleNextImage();
                }}
                className="absolute left-4 sm:left-8 z-30 w-12 h-12 rounded-2xl bg-black/70 hover:bg-[#C9972B] text-white flex items-center justify-center border border-white/20 transition shadow-2xl cursor-pointer"
                title="الصورة التالية (سهم يسار)"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
            )}

            {/* Zoomed Image */}
            <div 
              className="transition-transform duration-100 ease-out flex items-center justify-center max-w-full max-h-full"
              style={{
                transform: `scale(${zoomScale}) translate(${panPosition.x / zoomScale}px, ${panPosition.y / zoomScale}px)`
              }}
            >
              <img
                src={activeImage}
                alt={product.name_ar}
                draggable={false}
                className="max-h-[75vh] max-w-[90vw] object-contain rounded-xl shadow-2xl pointer-events-auto"
              />
            </div>
          </div>

          {/* Bottom Thumbnails Strip & Help Instructions */}
          <div className="p-4 bg-gradient-to-t from-black via-black/80 to-transparent border-t border-white/10 z-20 space-y-3">
            {/* Thumbnails */}
            {productImages.length > 1 && (
              <div className="flex items-center justify-center gap-3 overflow-x-auto py-1">
                {productImages.map((img, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveImageIndex(idx);
                      handleResetZoom();
                    }}
                    className={`relative w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden border-2 transition cursor-pointer shrink-0 ${
                      activeImageIndex === idx
                        ? 'border-[#C9972B] ring-2 ring-[#C9972B] scale-105 opacity-100'
                        : 'border-white/20 opacity-50 hover:opacity-90'
                    }`}
                  >
                    <img src={img} alt="" className="w-full h-full object-cover" />
                    <span className="absolute bottom-0 inset-x-0 bg-black/80 text-white text-[9px] font-bold py-0.5 text-center leading-none">
                      {idx === 0 ? 'الغلاف ⭐' : idx === 1 ? 'تفاصيل 🔍' : 'كركوشة 📿'}
                    </span>
                  </button>
                ))}
              </div>
            )}

            <div className="text-center text-xs text-white/60 flex items-center justify-center gap-4">
              <span>💡 انقر على الصورة للتبديل بين درجات التكبير (1x / 2x / 3x)</span>
              {zoomScale > 1 && (
                <span className="text-[#E2B84B] font-bold flex items-center gap-1">
                  <Move className="w-3.5 h-3.5" />
                  اسحب بالماوس لتحريك الصورة وفحص أدق التفاصيل
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
