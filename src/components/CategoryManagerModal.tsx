import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, FolderTree, Check, AlertCircle, Save, Sparkles } from 'lucide-react';
import { api } from '../lib/api';
import { Category, Product } from '../types';

interface CategoryManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  products: Product[];
  onCategoryChanged: () => void;
}

export const CategoryManagerModal: React.FC<CategoryManagerModalProps> = ({
  isOpen,
  onClose,
  categories,
  products,
  onCategoryChanged
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [nameAr, setNameAr] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [slug, setSlug] = useState('');
  const [sortOrder, setSortOrder] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const resetForm = () => {
    setEditingId(null);
    setNameAr('');
    setNameEn('');
    setSlug('');
    setSortOrder(categories.length + 1);
    setError(null);
  };

  const handleStartEdit = (cat: Category) => {
    setEditingId(cat.id);
    setNameAr(cat.name_ar);
    setNameEn(cat.name_en || '');
    setSlug(cat.slug || '');
    setSortOrder(cat.sort_order || 0);
    setError(null);
    setSuccess(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nameAr.trim()) {
      setError('يرجى كتابة اسم التصنيف بالعربية');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (editingId) {
        // Update existing category
        await api.updateCategory(editingId, {
          name_ar: nameAr.trim(),
          name_en: nameEn.trim(),
          slug: slug.trim(),
          sort_order: Number(sortOrder)
        });
        setSuccess('✅ تم تحديث التصنيف بنجاح');
      } else {
        // Create new category
        await api.createCategory({
          name_ar: nameAr.trim(),
          name_en: nameEn.trim(),
          slug: slug.trim(),
          sort_order: Number(sortOrder)
        });
        setSuccess('✅ تم إضافة التصنيف الجديد بنجاح');
      }
      resetForm();
      onCategoryChanged();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'حدث خطأ أثناء حفظ التصنيف');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (cat: Category) => {
    const linkedCount = products.filter(p => p.category_id === cat.id).length;
    if (linkedCount > 0) {
      alert(`⚠️ لا يمكن حذف التصنيف (${cat.name_ar}) لوجود ${linkedCount} مسبحة مرتبطة به حالياً. يرجى نقل أو تغيير تصنيف هذه المسابيح أولاً.`);
      return;
    }

    if (!confirm(`هل أنت متأكد من حذف التصنيف (${cat.name_ar})؟`)) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await api.deleteCategory(cat.id);
      setSuccess('✅ تم حذف التصنيف بنجاح');
      if (editingId === cat.id) resetForm();
      onCategoryChanged();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'تعذر حذف التصنيف');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs" dir="rtl">
      <div className="bg-[#FAF7F2] border border-[#E0D7C6] rounded-3xl max-w-3xl w-full p-6 text-[#26221C] shadow-2xl relative max-h-[90vh] flex flex-col">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E8DEC8]">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#FAF4E8] border border-[#E5DAC8] flex items-center justify-center">
              <FolderTree className="w-5 h-5 text-[#C9972B]" />
            </div>
            <div>
              <h3 className="font-black text-lg text-[#26221C]">إدارة تصنيفات المسابيح الفاخرة</h3>
              <p className="text-xs text-[#746A5D]">إضافة، تعديل وحذف تصنيفات الكتالوج والمخزن</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-[#F0E6D2] text-[#746A5D] transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
            <Check className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{success}</span>
          </div>
        )}

        {/* Form Container: Add / Edit Category */}
        <form onSubmit={handleSave} className="mt-5 p-4 bg-white rounded-2xl border border-[#EBE3D5] shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#9A6817] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#C9972B]" />
              {editingId ? 'تعديل بيانات التصنيف' : 'إضافة تصنيف جديد للكتالوج'}
            </span>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="text-[11px] text-[#746A5D] hover:text-[#9A6817] font-semibold underline cursor-pointer"
              >
                إلغاء التعديل
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
            <div className="sm:col-span-2 space-y-1">
              <label className="block text-[11px] font-bold text-[#4B4338]">اسم التصنيف (بالعربية) *</label>
              <input
                type="text"
                required
                placeholder="مثال: مسابيح عاج طبيعي وكهرمان"
                value={nameAr}
                onChange={(e) => setNameAr(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-medium"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[11px] font-bold text-[#4B4338]">الاسم (بالإنجليزية)</label>
              <input
                type="text"
                placeholder="Amber & Ivory"
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-medium"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[11px] font-bold text-[#4B4338]">ترتيب العرض</label>
              <input
                type="number"
                min="0"
                value={sortOrder}
                onChange={(e) => setSortOrder(parseInt(e.target.value, 10) || 0)}
                className="w-full px-3 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl focus:outline-none focus:border-[#C9972B] font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-gradient-to-r from-[#C9972B] to-[#9A6817] hover:from-[#DFB048] hover:to-[#B47B1F] text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {editingId ? <Save className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
              <span>{editingId ? 'حفظ التعديلات' : 'إضافة التصنيف'}</span>
            </button>
          </div>
        </form>

        {/* Existing Categories Table */}
        <div className="mt-5 flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-[#746A5D]">
              التصنيفات الحالية ({categories.length})
            </span>
          </div>

          <div className="overflow-hidden rounded-2xl border border-[#E8DEC8] bg-white shadow-2xs">
            <table className="w-full text-right text-xs">
              <thead className="bg-[#FAF4E8] text-[#746A5D] font-bold border-b border-[#E8DEC8]">
                <tr>
                  <th className="py-2.5 px-3">الترتيب</th>
                  <th className="py-2.5 px-3">اسم التصنيف</th>
                  <th className="py-2.5 px-3">الاسم بالإنجليزية</th>
                  <th className="py-2.5 px-3 text-center">المسابيح المرتبطة</th>
                  <th className="py-2.5 px-3 text-center">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F2ECE1]">
                {categories.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-xs text-[#8C8275]">
                      لا توجد تصنيفات معرفة حتى الآن.
                    </td>
                  </tr>
                ) : (
                  categories.map((cat) => {
                    const linkedCount = products.filter(p => p.category_id === cat.id).length;
                    const isEditing = editingId === cat.id;

                    return (
                      <tr key={cat.id} className={isEditing ? 'bg-[#FAF4E8]/60' : 'hover:bg-[#FAF7F2]'}>
                        <td className="py-2.5 px-3 font-mono font-bold text-[#9A6817]">
                          #{cat.sort_order || cat.id}
                        </td>
                        <td className="py-2.5 px-3 font-bold text-[#26221C]">
                          {cat.name_ar}
                        </td>
                        <td className="py-2.5 px-3 text-[#746A5D] font-serif">
                          {cat.name_en || '—'}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            linkedCount > 0
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {linkedCount} قطعة
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <div className="flex items-center justify-center gap-1.5">
                            <button
                              onClick={() => handleStartEdit(cat)}
                              title="تعديل التصنيف"
                              className="p-1.5 hover:bg-[#FAF4E8] text-[#9A6817] rounded-lg transition cursor-pointer"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(cat)}
                              title={linkedCount > 0 ? "لا يمكن حذف تصنيف به مسابيح" : "حذف التصنيف"}
                              disabled={linkedCount > 0}
                              className={`p-1.5 rounded-lg transition ${
                                linkedCount > 0
                                  ? 'text-gray-300 cursor-not-allowed'
                                  : 'hover:bg-rose-50 text-rose-600 cursor-pointer'
                              }`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="mt-4 pt-3 border-t border-[#E8DEC8] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-white hover:bg-[#FAF4E8] text-[#26221C] border border-[#DDD3C1] font-bold text-xs rounded-xl transition cursor-pointer"
          >
            إغلاق النافذة
          </button>
        </div>

      </div>
    </div>
  );
};
