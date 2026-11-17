import React, { useState, useEffect } from 'react';
import {
  Gem,
  Plus,
  Search,
  Filter,
  ShieldCheck,
  Scissors,
  ShoppingBag,
  Award,
  Edit,
  Clock,
  Sparkles,
  CheckCircle2,
  Trash2,
  DollarSign,
  QrCode
} from 'lucide-react';
import { api } from '../lib/api';
import { Product, Category, Material, ProductStatus, User } from '../types';
import { hasPermission } from '../lib/permissions';
import { BoxQRLabelModal } from '../components/BoxQRLabelModal';

interface InventoryPageProps {
  onOpenProductModal: (product: Product | null) => void;
  onOpenCustodyModal: (product: Product) => void;
  onOpenBeadModal: (product: Product) => void;
  onOpenQuickSaleModal: (product: Product) => void;
  currentUser?: User;
}

export const InventoryPage: React.FC<InventoryPageProps> = ({
  onOpenProductModal,
  onOpenCustodyModal,
  onOpenBeadModal,
  onOpenQuickSaleModal,
  currentUser
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [selectedQRProduct, setSelectedQRProduct] = useState<Product | null>(null);

  // Permission Checks
  const canCreate = hasPermission(currentUser, 'inventory.create');
  const canEdit = hasPermission(currentUser, 'inventory.edit');
  const canDelete = hasPermission(currentUser, 'inventory.delete');
  const canViewCost = hasPermission(currentUser, 'inventory.view_cost');
  const canCustody = hasPermission(currentUser, 'custody.assign');
  const canWorkshop = hasPermission(currentUser, 'workshop.adjust');
  const canSale = hasPermission(currentUser, 'pos.checkout');

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    setLoading(true);
    try {
      const [prods, cats, mats] = await Promise.all([
        api.getProducts(),
        api.getCategories(),
        api.getMaterials()
      ]);
      setProducts(prods);
      setCategories(cats);
      setMaterials(mats);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (product: Product) => {
    if (!canDelete) return;
    if (!confirm(`هل أنت متأكد من حذف المسبحة (${product.name_ar} - ${product.sku})؟`)) {
      return;
    }

    try {
      const res = await api.deleteProduct(product.id, currentUser?.full_name);
      alert(res.message || '✅ تم حذف المسبحة بنجاح');
      loadCatalog();
    } catch (err: any) {
      alert(err.response?.data?.error || 'تعذر حذف المسبحة');
    }
  };

  const filteredProducts = products.filter(p => {
    const matchesSearch =
      p.name_ar.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      p.product_reference.toLowerCase().includes(search.toLowerCase()) ||
      p.origin.toLowerCase().includes(search.toLowerCase()) ||
      p.color.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || p.status === statusFilter;
    const matchesCategory = !categoryFilter || String(p.category_id) === categoryFilter;

    return matchesSearch && matchesStatus && matchesCategory;
  });

  const getStatusBadge = (status: ProductStatus) => {
    switch (status) {
      case 'AVAILABLE':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">متاحة للاقتناء</span>;
      case 'RESERVED':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 animate-pulse">محجوزة (15 د)</span>;
      case 'SOLD':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">تم البيع</span>;
      case 'IN_CUSTODY':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-300">في العهدة / المعرض</span>;
      case 'IN_WORKSHOP':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-300">في ورشة التعديل</span>;
      case 'ARCHIVED':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">مؤرشفة</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto selection:bg-[#C9972B]/20" dir="rtl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-[#26221C] flex items-center gap-2">
            <Gem className="w-6 h-6 text-[#C9972B]" />
            <span>كتالوج المسابيح الفاخرة والمخزون</span>
          </h2>
          <p className="text-xs text-[#746A5D] mt-1">
            إدارة القطع النادرة الفريدة، ضبط الأوزان والتكاليف، وإصدار شهادات الأصالة
          </p>
        </div>

        {canCreate && (
          <button
            onClick={() => onOpenProductModal(null)}
            className="px-5 py-2.5 bg-[#26221C] hover:bg-[#3D352E] text-[#E2B84B] rounded-xl text-xs sm:text-sm font-black transition shadow-md flex items-center justify-center gap-2 shrink-0 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>إضافة مسبحة جديدة</span>
          </button>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 bg-white border border-[#EBE3D5] rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
        <div className="relative flex-1 min-w-[240px]">
          <input
            type="text"
            placeholder="بحث بالاسم، الـ SKU، المنشأ، أو الرمز المرجعي..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-4 pr-10 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-xs text-[#26221C] placeholder-[#8C8275] focus:outline-none focus:border-[#C9972B]"
          />
          <Search className="w-4 h-4 text-[#8C8275] absolute right-3.5 top-2.5" />
        </div>

        <div className="flex items-center gap-2 flex-wrap text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-xs font-semibold text-[#26221C] focus:outline-none focus:border-[#C9972B]"
          >
            <option value="ALL">كافة الحالات</option>
            <option value="AVAILABLE">متاحة للاقتناء</option>
            <option value="RESERVED">محجوزة</option>
            <option value="SOLD">تم البيع</option>
            <option value="IN_CUSTODY">في العهدة</option>
            <option value="IN_WORKSHOP">في الورشة</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-[#FAF7F2] border border-[#DDD3C1] rounded-xl text-xs font-semibold text-[#26221C] focus:outline-none focus:border-[#C9972B]"
          >
            <option value="">كافة التصنيفات</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name_ar}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="py-24 text-center">
          <div className="inline-block w-8 h-8 border-3 border-[#C9972B] border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-xs text-[#746A5D] font-medium">جارِ تحميل كتالوج المسابيح الفاخرة...</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-[#D8CCA8] rounded-2xl shadow-xs">
          <Gem className="w-12 h-12 text-[#C9972B]/50 mx-auto mb-2" />
          <h4 className="font-bold text-[#26221C] text-sm">لا توجد مسابيح مطابقة للبحث</h4>
          <p className="text-xs text-[#746A5D] mt-1">جرّب تغيير معايير البحث أو أضف مسبحة جديدة</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filteredProducts.map((p) => {
            const profit = p.selling_price - (p.cost_price || 0);
            const profitPercent = p.cost_price > 0 ? Math.round((profit / p.cost_price) * 100) : 0;

            return (
              <div
                key={p.id}
                className="bg-white border border-[#EBE3D5] rounded-3xl p-5 flex flex-col justify-between hover:border-[#C9972B] hover:shadow-[0_8px_24px_rgba(201,151,43,0.12)] transition duration-300 shadow-xs group"
              >
                <div>
                  {/* Image and Badges */}
                  <div className="relative aspect-video rounded-2xl overflow-hidden bg-[#FAF7F2] border border-[#E0D7C6] mb-4">
                    <img
                      src={p.image_url || '/branding/hero-amber.jpg'}
                      alt=""
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                    />
                    <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5">
                      {getStatusBadge(p.status)}
                    </div>
                    {p.verification_status === 'CERTIFIED' && (
                      <div className="absolute bottom-2.5 right-2.5 bg-white/90 backdrop-blur px-2.5 py-1 rounded-md text-[10px] text-[#9A6817] font-bold flex items-center gap-1 border border-[#E0D7C6] shadow-xs">
                        <Award className="w-3.5 h-3.5 text-[#C9972B]" />
                        <span>شهادة أصالة</span>
                      </div>
                    )}
                  </div>

                  {/* Reference & Name */}
                  <div className="flex items-center gap-2 text-[10px] text-[#746A5D] font-mono">
                    <span className="font-bold text-[#9A6817] bg-[#FAF4E8] px-1.5 py-0.5 rounded border border-[#EADBCE]">{p.sku}</span>
                    <span>•</span>
                    <span>{p.product_reference}</span>
                  </div>

                  <h3 className="font-bold text-sm text-[#26221C] mt-1.5 leading-snug line-clamp-2">
                    {p.name_ar}
                  </h3>

                  {/* Specs Pill List */}
                  <div className="grid grid-cols-3 gap-2 text-center text-[11px] bg-[#FAF7F2] p-2.5 rounded-xl border border-[#EEE4D4] mt-3.5 text-[#4B4338]">
                    <div>
                      <span className="block text-[10px] text-[#8C8275]">عدد الخرز</span>
                      <span className="font-bold text-[#26221C]">{p.bead_count}</span>
                    </div>
                    <div className="border-r border-l border-[#E2D8C6]">
                      <span className="block text-[10px] text-[#8C8275]">القياس</span>
                      <span className="font-bold text-[#26221C]">{p.bead_size_mm} mm</span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-[#8C8275]">الوزن</span>
                      <span className="font-bold text-[#26221C]">{p.weight_g} g</span>
                    </div>
                  </div>

                  <div className="text-xs text-[#746A5D] mt-2.5 space-y-0.5">
                    <p><span className="text-[#9E9485]">القصة:</span> {p.shape} | <span className="text-[#9E9485]">الكركوشة:</span> {p.tassel_type}</p>
                    <p><span className="text-[#9E9485]">المنشأ:</span> {p.origin} ({p.color})</p>
                  </div>

                  {/* Cost & Profit Row (Visible only for authorized roles: OWNER, ACCOUNTANT, SUPERVISOR) */}
                  {canViewCost && (
                    <div className="mt-3 p-2 bg-[#F6F1E6] rounded-xl border border-[#EADBCE] text-[11px] flex items-center justify-between">
                      <div>
                        <span className="text-[#8C8275]">سعر التكلفة: </span>
                        <span className="font-mono font-bold text-[#26221C]">{(p.cost_price || 0).toLocaleString()} AED</span>
                      </div>
                      <div>
                        <span className="text-[#8C8275]">الربح: </span>
                        <span className="font-mono font-bold text-emerald-700">+{profit.toLocaleString()} AED ({profitPercent}%)</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Price & Action Buttons */}
                <div className="mt-4 pt-3 border-t border-[#F2ECE1]">
                  <div className="flex items-baseline justify-between mb-3">
                    <span className="text-xs text-[#746A5D] font-medium">سعر الاقتناء:</span>
                    <div className="text-right">
                      <span className="text-lg font-black text-[#9A6817]">{p.selling_price.toLocaleString()}</span>
                      <span className="text-xs text-[#746A5D] font-normal mr-1">AED</span>
                    </div>
                  </div>

                  {/* Action Buttons with Permission Guards */}
                  <div className="flex items-center gap-1.5 pt-1">
                    {canSale && p.status === 'AVAILABLE' && (
                      <button
                        onClick={() => onOpenQuickSaleModal(p)}
                        title="بيع سريع للمسبحة"
                        className="flex-1 py-2 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1 transition shadow-xs cursor-pointer"
                      >
                        <ShoppingBag className="w-3.5 h-3.5" />
                        <span>بيع فوري</span>
                      </button>
                    )}

                    {canCustody && (
                      <button
                        onClick={() => onOpenCustodyModal(p)}
                        title="قيد أو فحص العهدة والمعارض"
                        className="p-2 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#4B4338] text-xs rounded-xl border border-[#E0D7C6] flex items-center justify-center transition cursor-pointer"
                      >
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      </button>
                    )}

                    {canWorkshop && (
                      <button
                        onClick={() => onOpenBeadModal(p)}
                        title="ورشة تعديل عدد الخرز والشواهد"
                        className="p-2 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#4B4338] text-xs rounded-xl border border-[#E0D7C6] flex items-center justify-center transition cursor-pointer"
                      >
                        <Scissors className="w-4 h-4 text-[#C9972B]" />
                      </button>
                    )}

                    <button
                      onClick={() => setSelectedQRProduct(p)}
                      title="طباعة ملصق العلبة الملكي (QR Code)"
                      className="p-2 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#9A6817] text-xs rounded-xl border border-[#E0D7C6] hover:border-[#C9972B] flex items-center justify-center transition cursor-pointer"
                    >
                      <QrCode className="w-4 h-4" />
                    </button>

                    {canEdit && (
                      <button
                        onClick={() => onOpenProductModal(p)}
                        title="تعديل المواصفات والأسعار"
                        className="p-2 bg-[#FAF7F2] hover:bg-[#FAF4E8] text-[#4B4338] text-xs rounded-xl border border-[#E0D7C6] flex items-center justify-center transition cursor-pointer"
                      >
                        <Edit className="w-4 h-4 text-[#746A5D]" />
                      </button>
                    )}

                    {canDelete && (
                      <button
                        onClick={() => handleDeleteProduct(p)}
                        title="حذف أو أرشفة المسبحة"
                        className="p-2 bg-[#FAF7F2] hover:bg-rose-50 text-rose-600 text-xs rounded-xl border border-[#E0D7C6] hover:border-rose-200 flex items-center justify-center transition cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Luxury Box QR Label Modal */}
      {selectedQRProduct && (
        <BoxQRLabelModal
          product={selectedQRProduct}
          onClose={() => setSelectedQRProduct(null)}
        />
      )}
    </div>
  );
};
