import React, { useState } from 'react';
import { Gem, X, Upload, Sparkles } from 'lucide-react';
import { api } from '../lib/api';
import { Product, Category, Material, VerificationStatus } from '../types';

interface ProductModalProps {
  product: Product | null;
  categories: Category[];
  materials: Material[];
  onClose: () => void;
  onSuccess: () => void;
  userName?: string;
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
  const [beadSizeMm, setBeadSizeMm] = useState(product?.bead_size_mm || 11.0);
  const [weightG, setWeightG] = useState(product?.weight_g || 45.0);
  const [shape, setShape] = useState(product?.shape || 'برميلي');
  const [tasselType, setTasselType] = useState(product?.tassel_type || 'فضة كازازية عيار 1000');
  const [costPrice, setCostPrice] = useState(product?.cost_price || 1200);
  const [sellingPrice, setSellingPrice] = useState(product?.selling_price || 2400);
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>(product?.verification_status || 'CERTIFIED');
  const [certificateNumber, setCertificateNumber] = useState(product?.certificate_number || '');
  const [imageUrl, setImageUrl] = useState(product?.image_url || '/branding/hero-amber.jpg');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nameAr.trim() || !sellingPrice) {
      alert('يرجى كتابة اسم المسبحة وسعر البيع');
      return;
    }

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
        bead_size_mm: Number(beadSizeMm),
        weight_g: Number(weightG),
        shape: shape.trim(),
        tassel_type: tasselType.trim(),
        cost_price: Number(costPrice),
        selling_price: Number(sellingPrice),
        verification_status: verificationStatus,
        certificate_number: certificateNumber.trim(),
        image_url: imageUrl.trim(),
        actor_name: userName || 'المالك'
      };

      if (product) {
        await api.updateProduct(product.id, payload);
      } else {
        await api.createProduct(payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      alert(err.response?.data?.error || 'حدث خطأ أثناء حفظ المسبحة');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-3xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <Gem className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#26221C]">
                {product ? 'تعديل بيانات المسبحة الفاخرة' : 'إضافة مسبحة حصرية فريدة جديدة'}
              </h3>
              <p className="text-xs text-[#746A5D]">توثيق مواصفات الخرز، الوزن، الشهادة وسعر التكلفة والبيع</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
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

          {/* Rosary Specific Bead Specs */}
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
                <label className="block text-[11px] font-semibold text-[#4B4338] mb-1">قياس الخرز (ملم)</label>
                <input
                  type="number"
                  step="0.1"
                  value={beadSizeMm}
                  onChange={(e) => setBeadSizeMm(Number(e.target.value))}
                  className="w-full bg-white border border-[#D8CCA8] rounded-lg px-2.5 py-1.5 text-xs text-[#26221C]"
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

          {/* Pricing & Verification */}
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
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">حالة الفحص والأصالة</label>
              <select
                value={verificationStatus}
                onChange={(e) => setVerificationStatus(e.target.value as VerificationStatus)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              >
                <option value="CERTIFIED">معتمد بشهادة فحص (Certified)</option>
                <option value="INSPECTED">مفحوص خبير (Inspected)</option>
                <option value="NONE">بدون شهادة فحص</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم شهادة الفحص</label>
              <input
                type="text"
                placeholder="AMB-2026-901"
                value={certificateNumber}
                onChange={(e) => setCertificateNumber(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">رابط الصورة الرئيسية للمسبحة</label>
            <input
              type="text"
              placeholder="/branding/hero-amber.jpg أو رابط خارجي"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-sm text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
          </div>

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
              className="px-6 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-sm disabled:opacity-50 cursor-pointer"
            >
              {submitting ? 'جار الحفظ...' : (product ? 'تحديث المسبحة' : 'حفظ ونشر المسبحة')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
