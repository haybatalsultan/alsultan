import React, { useState, useRef } from 'react';
import {
  Gem,
  X,
  Upload,
  Sparkles,
  Trash2,
  Link2,
  Loader2,
  Image as ImageIcon,
  CheckCircle2,
  Zap
} from 'lucide-react';
import { api } from '../lib/api';
import { Product, Category, Material, VerificationStatus } from '../types';
import { compressImageFile, formatBytes, CompressionResult } from '../lib/imageCompressor';
import { toast } from '../utils/toast';

interface ProductModalProps {
  product: Product | null;
  categories: Category[];
  materials: Material[];
  onClose: () => void;
  onSuccess: () => void;
  userName?: string;
}

interface ImageSlotState {
  url: string;
  isUploading: boolean;
  compressionInfo?: {
    originalSize: number;
    compressedSize: number;
    reductionPercent: number;
  };
}

export const ProductModal: React.FC<ProductModalProps> = ({
  product,
  categories,
  materials,
  onClose,
  onSuccess,
  userName
}) => {
  const [nameAr, setNameAr] = useState(product?.name_ar || '');
  const [nameEn, setNameEn] = useState(product?.name_en || '');
  const [categoryId, setCategoryId] = useState(product?.category_id || categories[0]?.id || 1);
  const [materialId, setMaterialId] = useState(product?.material_id || materials[0]?.id || 1);
  const [origin, setOrigin] = useState(product?.origin || 'بولندا / بحر البلطيق');
  const [color, setColor] = useState(product?.color || 'أصفر معرق');
  const [beadCount, setBeadCount] = useState(product?.bead_count || 33);
  const [beadSizeMm, setBeadSizeMm] = useState<string>(product?.bead_size_mm !== undefined && product?.bead_size_mm !== null ? String(product.bead_size_mm) : '11×13');
  const [weightG, setWeightG] = useState(product?.weight_g || 45.0);
  const [shape, setShape] = useState(product?.shape || 'برميلي');
  const [tasselType, setTasselType] = useState(product?.tassel_type || 'فضة كازازية عيار 1000');
  const [costPrice, setCostPrice] = useState(product?.cost_price || 1200);
  const [sellingPrice, setSellingPrice] = useState(product?.selling_price || 2400);
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>(product?.verification_status || 'NONE');
  const [certificateNumber, setCertificateNumber] = useState(product?.certificate_number || '');

  // 3 Images Slots State (Primary + 2 Secondary)
  const [imageSlots, setImageSlots] = useState<ImageSlotState[]>(() => {
    let sec: string[] = [];
    try {
      if (product?.secondary_images) {
        sec = typeof product.secondary_images === 'string'
          ? JSON.parse(product.secondary_images)
          : product.secondary_images;
      }
    } catch {
      sec = [];
    }

    return [
      { url: product?.image_url || '/branding/hero-amber.jpg', isUploading: false },
      { url: sec[0] || '', isUploading: false },
      { url: sec[1] || '', isUploading: false }
    ];
  });

  const fileInputRefs = [
    useRef<HTMLInputElement | null>(null),
    useRef<HTMLInputElement | null>(null),
    useRef<HTMLInputElement | null>(null)
  ];

  const [submitting, setSubmitting] = useState(false);

  // Handle uploading and client-side compressing image file for slot (0, 1, or 2)
  const handleFileSelect = async (slotIndex: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Set uploading indicator for this slot
    setImageSlots((prev) =>
      prev.map((slot, i) => (i === slotIndex ? { ...slot, isUploading: true } : slot))
    );

    try {
      // 1. Client-side canvas compression (scales down 4K/10MB to crisp ~100KB WebP)
      const compressed: CompressionResult = await compressImageFile(file, 1400, 0.82);

      // 2. Upload compressed payload to server
      const uploadRes = await api.uploadImage(compressed.dataUrl, file.name);

      // 3. Update slot state with uploaded URL and compression statistics
      setImageSlots((prev) =>
        prev.map((slot, i) =>
          i === slotIndex
            ? {
                url: uploadRes.url,
                isUploading: false,
                compressionInfo: {
                  originalSize: compressed.originalSize,
                  compressedSize: compressed.compressedSize,
                  reductionPercent: compressed.reductionPercent
                }
              }
            : slot
        )
      );
    } catch (err: any) {
      toast.error(err?.message || 'تعذر معالجة ورفع الصورة، يرجى المحاولة مرة أخرى');
      setImageSlots((prev) =>
        prev.map((slot, i) => (i === slotIndex ? { ...slot, isUploading: false } : slot))
      );
    } finally {
      // Reset input value so same file can be selected again if desired
      if (e.target) e.target.value = '';
    }
  };

  const handleUrlChange = (slotIndex: number, newUrl: string) => {
    setImageSlots((prev) =>
      prev.map((slot, i) =>
        i === slotIndex
          ? {
              ...slot,
              url: newUrl,
              compressionInfo: undefined // clear upload compression pill if edited manually
            }
          : slot
      )
    );
  };

  const handleClearSlot = (slotIndex: number) => {
    setImageSlots((prev) =>
      prev.map((slot, i) =>
        i === slotIndex ? { url: '', isUploading: false, compressionInfo: undefined } : slot
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nameAr.trim() || !sellingPrice) {
      toast.warning('يرجى كتابة اسم المسبحة وسعر البيع');
      return;
    }

    // Filter valid non-empty URLs
    const validUrls = imageSlots.map((s) => s.url.trim()).filter(Boolean);
    const primaryImage = validUrls[0] || '/branding/hero-amber.jpg';
    const secondaryImages = validUrls.slice(1, 3); // Max 2 secondary images

    setSubmitting(true);
    try {
      const payload = {
        name_ar: nameAr.trim(),
        name_en: nameEn.trim(),
        category_id: categoryId,
        material_id: materialId,
        origin: origin.trim(),
        color: color.trim(),
        bead_count: Number(beadCount),
        bead_size_mm: String(beadSizeMm).trim() || '11×13',
        weight_g: Number(weightG),
        shape: shape.trim(),
        tassel_type: tasselType.trim(),
        cost_price: Number(costPrice),
        selling_price: Number(sellingPrice),
        verification_status: verificationStatus,
        certificate_number: certificateNumber.trim(),
        image_url: primaryImage,
        secondary_images: secondaryImages,
        actor_name: userName || 'المالك'
      };

      if (product) {
        await api.updateProduct(product.id, payload);
      } else {
        await api.createProduct(payload);
      }

      toast.success(product ? 'تم تحديث بيانات المسبحة بنجاح' : 'تم إضافة المسبحة الجديدة بنجاح للمخزون');
      onSuccess();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'حدث خطأ أثناء حفظ المسبحة');
    } finally {
      setSubmitting(false);
    }
  };

  const slotLabels = [
    { title: 'الصورة الرئيسية (الغلاف)', badge: 'أساسية ⭐', desc: 'تظهر في واجهة المتجر والبطاقات وقائمة المخزون' },
    { title: 'الصورة الثانية (التفاصيل)', badge: 'إضافية 🔍', desc: 'صورة توثيقية مقربة للخرز أو لمعان الخامة' },
    { title: 'الصورة الثالثة (الكركوشة)', badge: 'إضافية 📿', desc: 'صورة للشاهد، الكركوشة الفضية أو شهادة الفحص' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden my-8 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <Gem className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#26221C]">
                {product ? 'تعديل بيانات المسبحة الفاخرة' : 'إضافة مسبحة حصرية فريدة جديدة'}
              </h3>
              <p className="text-xs text-[#746A5D]">توثيق مواصفات الخرز، صور المعرض، الشهادة وسعر التكلفة والبيع</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body (Scrollable) */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto flex-1">
          {/* 1. Basic Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">اسم المسبحة بالعربية *</label>
              <input
                type="text"
                required
                placeholder="مثال: مسبحة كهرمان بلطيقي معرق أصفر ملكي"
                value={nameAr}
                onChange={(e) => setNameAr(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">الاسم بالإنجليزية</label>
              <input
                type="text"
                placeholder="Royal Baltic Amber Rosary"
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">التصنيف *</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(Number(e.target.value))}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name_ar}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">الخامة الأصلية *</label>
              <select
                value={materialId}
                onChange={(e) => setMaterialId(Number(e.target.value))}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              >
                {materials.map((m) => (
                  <option key={m.id} value={m.id}>{m.name_ar}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 2. Rosary Specific Bead Specs */}
          <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] space-y-3">
            <h4 className="text-xs font-bold text-[#9A6817] uppercase tracking-wide flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
              المواصفات الفنية للخرز والكركوشة
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">عدد الخرز</label>
                <input
                  type="number"
                  value={beadCount}
                  onChange={(e) => setBeadCount(Number(e.target.value))}
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">قياس الخرز (ملم أو أبعاد)</label>
                <input
                  type="text"
                  placeholder="مثال: 11×13 أو 10.5"
                  value={beadSizeMm}
                  onChange={(e) => setBeadSizeMm(e.target.value)}
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C] focus:border-[#C9972B] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">الوزن الصافي (جرام)</label>
                <input
                  type="number"
                  step="0.1"
                  value={weightG}
                  onChange={(e) => setWeightG(Number(e.target.value))}
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">قصة وشكل الخرزة</label>
                <input
                  type="text"
                  value={shape}
                  onChange={(e) => setShape(e.target.value)}
                  placeholder="برميلي، كروي، ذروي"
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">نوع الكركوشة والشاهد</label>
                <input
                  type="text"
                  value={tasselType}
                  onChange={(e) => setTasselType(e.target.value)}
                  placeholder="فضة 1000، كازازية، حرير"
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">المنشأ / المصدر</label>
                <input
                  type="text"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  placeholder="بولندا، ألمانيا، تركيا"
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">اللون / العروق</label>
                <input
                  type="text"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  placeholder="أصفر زبدي، كبدي شفاف"
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
                />
              </div>
            </div>
          </div>

          {/* 3. Pricing & Verification */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">سعر التكلفة (درهم)</label>
              <input
                type="number"
                value={costPrice}
                onChange={(e) => setCostPrice(Number(e.target.value))}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">سعر البيع المعروض *</label>
              <input
                type="number"
                required
                value={sellingPrice}
                onChange={(e) => setSellingPrice(Number(e.target.value))}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm font-bold text-[#9A6817] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">شهادة الفحص والأصالة</label>
              <select
                value={verificationStatus}
                onChange={(e) => {
                  const val = e.target.value as VerificationStatus;
                  setVerificationStatus(val);
                  if (val === 'NONE') {
                    setCertificateNumber('');
                  }
                }}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              >
                <option value="NONE">بدون شهادة فحص (الافتراضي)</option>
                <option value="CERTIFIED">معتمد بشهادة فحص (Certified)</option>
                <option value="INSPECTED">مفحوص خبير (Inspected)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                رقم شهادة الفحص {verificationStatus === 'NONE' ? '(اختياري)' : '*'}
              </label>
              <input
                type="text"
                placeholder={verificationStatus === 'NONE' ? 'بدون شهادة فحص' : 'AMB-2026-901'}
                value={certificateNumber}
                onChange={(e) => {
                  const val = e.target.value;
                  setCertificateNumber(val);
                  if (val.trim().length > 0 && verificationStatus === 'NONE') {
                    setVerificationStatus('CERTIFIED');
                  }
                }}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          {/* 4. Luxury 3-Image Gallery (Upload + Direct URL + Auto-Compression) */}
          <div className="p-4 rounded-2xl bg-[#FCFAF7] border border-[#EBE3D5] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h4 className="text-xs font-bold text-[#9A6817] uppercase tracking-wide flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-[#C9972B]" />
                  معرض صور المسبحة (3 صور كحد أقصى)
                </h4>
                <p className="text-[11px] text-[#746A5D] mt-0.5">
                  ارفع من جهازك (يتم ضغط الصورة تلقائياً لتقليل الحجم وتسريع المتجر) أو الصق رابط صورة خارجي مباشر.
                </p>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF4E8] text-[#9A6817] border border-[#EADBCE]">
                حد أقصى 3 صور
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {imageSlots.map((slot, idx) => (
                <div
                  key={idx}
                  className="flex flex-col bg-white rounded-2xl border border-[#E8DFC8] p-3 shadow-xs space-y-2.5 relative group hover:border-[#C9972B]/60 transition"
                >
                  {/* Slot Title & Badge */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#26221C] flex items-center gap-1">
                      {slotLabels[idx].title}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md font-bold ${
                        idx === 0
                          ? 'bg-[#C9972B]/15 text-[#9A6817] border border-[#C9972B]/30'
                          : 'bg-gray-100 text-gray-600 border border-gray-200'
                      }`}
                    >
                      {slotLabels[idx].badge}
                    </span>
                  </div>

                  {/* Image Preview & Upload Box */}
                  <div className="relative aspect-4/3 rounded-xl overflow-hidden bg-[#FAF7F2] border border-dashed border-[#D8CCA8] flex items-center justify-center">
                    {slot.isUploading ? (
                      <div className="flex flex-col items-center justify-center gap-2 p-3 text-center text-[#9A6817]">
                        <Loader2 className="w-6 h-6 animate-spin text-[#C9972B]" />
                        <span className="text-xs font-bold">جارِ الضغط والرفع...</span>
                        <span className="text-[10px] text-[#746A5D]">توفير المساحة على السيرفر</span>
                      </div>
                    ) : slot.url ? (
                      <>
                        <img
                          src={slot.url}
                          alt={`مسبحة صورة ${idx + 1}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/branding/hero-amber.jpg';
                          }}
                        />
                        {/* Remove Image Button */}
                        <button
                          type="button"
                          onClick={() => handleClearSlot(idx)}
                          title="حذف هذه الصورة"
                          className="absolute top-2 left-2 p-1.5 rounded-lg bg-black/60 hover:bg-red-600 text-white backdrop-blur-xs transition cursor-pointer shadow-md"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>

                        {/* Local vs External Badge */}
                        <div className="absolute bottom-2 right-2">
                          {slot.url.startsWith('/uploads') ? (
                            <span className="inline-flex items-center gap-1 bg-[#1C1814]/80 backdrop-blur-xs text-white text-[9px] px-2 py-0.5 rounded-md font-mono border border-white/10">
                              <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" /> مرفوعة على السيرفر
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 bg-white/90 backdrop-blur-xs text-[#4B4338] text-[9px] px-2 py-0.5 rounded-md border border-[#E0D7C6]">
                              <Link2 className="w-2.5 h-2.5 text-[#C9972B]" /> رابط خارجي
                            </span>
                          )}
                        </div>
                      </>
                    ) : (
                      <div
                        onClick={() => fileInputRefs[idx].current?.click()}
                        className="flex flex-col items-center justify-center gap-1.5 p-4 text-center cursor-pointer hover:bg-[#FAF4E8]/60 transition w-full h-full"
                      >
                        <div className="w-8 h-8 rounded-full bg-white border border-[#E0D7C6] flex items-center justify-center text-[#9A6817]">
                          <Upload className="w-4 h-4 text-[#C9972B]" />
                        </div>
                        <span className="text-xs font-semibold text-[#4B4338]">اختر صورة من جهازك</span>
                        <span className="text-[10px] text-[#8C8275]">{slotLabels[idx].desc}</span>
                      </div>
                    )}
                  </div>

                  {/* Compression Success Pill */}
                  {slot.compressionInfo && (
                    <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] flex items-center gap-1">
                      <Zap className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span>
                        تم الضغط من <b>{formatBytes(slot.compressionInfo.originalSize)}</b> إلى{' '}
                        <b>{formatBytes(slot.compressionInfo.compressedSize)}</b> (توفير{' '}
                        <b>{slot.compressionInfo.reductionPercent}%</b>)
                      </span>
                    </div>
                  )}

                  {/* Upload from Device Button & Direct URL Bar */}
                  <div className="space-y-1.5 pt-1">
                    {/* Hidden Native File Input */}
                    <input
                      ref={fileInputRefs[idx]}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => handleFileSelect(idx, e)}
                    />

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => fileInputRefs[idx].current?.click()}
                        disabled={slot.isUploading}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-[#FAF4E8] hover:bg-[#F2E8D5] text-[#9A6817] border border-[#E0D7C6] rounded-lg text-[11px] font-bold transition cursor-pointer disabled:opacity-50"
                      >
                        <Upload className="w-3.5 h-3.5 text-[#C9972B]" />
                        <span>{slot.url ? 'تغيير الصورة من الجهاز' : 'رفع صورة من الجهاز'}</span>
                      </button>
                    </div>

                    {/* Direct URL Input Bar */}
                    <div className="relative">
                      <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none text-[#8C8275]">
                        <Link2 className="w-3.5 h-3.5" />
                      </div>
                      <input
                        type="text"
                        value={slot.url}
                        onChange={(e) => handleUrlChange(idx, e.target.value)}
                        placeholder="أو الصق رابط صورة مباشر..."
                        className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-lg pr-8 pl-2 py-1.5 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B] placeholder:text-[#A89E90]"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-3 border-t border-[#F2ECE1]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-semibold rounded-xl transition cursor-pointer"
            >
              إلغاء
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>جار الحفظ...</span>
                </>
              ) : (
                <span>{product ? 'تحديث بيانات المسبحة والصور' : 'حفظ ونشر المسبحة'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
