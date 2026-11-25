import React, { useState, useEffect } from 'react';
import { ShoppingBag, X, Check, Truck, CreditCard, Banknote, ShieldCheck, Globe, MapPin } from 'lucide-react';
import { api } from '../lib/api';
import { Product, Country } from '../types';
import { toast } from '../utils/toast';

interface CheckoutModalProps {
  product: Product | null;
  customerUser: any;
  onClose: () => void;
  onSuccess: (order: any) => void;
}

const DEFAULT_ARAB_COUNTRIES = [
  'الإمارات العربية المتحدة',
  'المملكة العربية السعودية',
  'دولة الكويت',
  'دولة قطر',
  'سلطنة عمان',
  'مملكة البحرين',
  'جمهورية مصر العربية',
  'المملكة الأردنية الهاشمية',
  'جمهورية العراق',
  'الجمهورية اللبنانية',
  'دولة فلسطين',
  'الجمهورية العربية السورية',
  'الجمهورية اليمنية',
  'دولة ليبيا',
  'الجمهورية التونسية',
  'الجمهورية الجزائرية',
  'المملكة المغربية',
  'جمهورية السودان',
  'جمهورية الصومال',
  'الجمهورية الإسلامية الموريتانية',
  'جمهورية جيبوتي',
  'جزر القمر'
];

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  product,
  customerUser,
  onClose,
  onSuccess
}) => {
  const [customerName, setCustomerName] = useState(customerUser?.full_name || '');
  const [customerPhone, setCustomerPhone] = useState(customerUser?.phone || '');
  const [customerEmail, setCustomerEmail] = useState(customerUser?.email || '');
  const [country, setCountry] = useState(customerUser?.country || 'الإمارات العربية المتحدة');
  const [city, setCity] = useState(customerUser?.city || 'أبوظبي');
  const [address, setAddress] = useState(customerUser?.address || '');
  const [notes, setNotes] = useState('');
  const [countriesList, setCountriesList] = useState<string[]>(DEFAULT_ARAB_COUNTRIES);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Fetch countries from server (Arab + Custom countries from Settings)
    api.getCountries().then((data: Country[]) => {
      if (Array.isArray(data) && data.length > 0) {
        const countryNames = data.map((c) => c.name_ar);
        setCountriesList(countryNames);
        if (!countryNames.includes(country)) {
          setCountry(countryNames[0]);
        }
      }
    }).catch(() => {
      // Fallback already pre-set to DEFAULT_ARAB_COUNTRIES
    });
  }, []);

  if (!product) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerName.trim() || !customerPhone.trim()) {
      toast.warning('يرجى كتابة الاسم ورقم الهاتف للتوصيل');
      return;
    }

    if (!country.trim()) {
      toast.warning('يرجى تحديد دولة الشحن والتوصيل');
      return;
    }

    if (!address.trim()) {
      toast.warning('يرجى كتابة العنوان بالتفصيل لضمان دقة التوصيل');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.checkoutOnline({
        product_id: product.id,
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim(),
        customer_email: customerEmail.trim(),
        country: country.trim(),
        city: city.trim() || 'الرئيسية',
        address: address.trim(),
        notes: notes.trim(),
        payment_method: 'عند الاستلام / التنسيق المباشر'
      });

      toast.success(`${res.message}\nرقم الطلب المرجعي: ${res.order.reference}`, 'تم إتمام الطلب بنجاح');
      onSuccess(res.order);
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'تعذر إتمام الطلب، يرجى المحاولة لاحقاً');
    } finally {
      setSubmitting(false);
    }
  };

  const isUAE = country.includes('الإمارات');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white border border-[#EBE3D5] rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden my-6 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#F2ECE1] flex items-center justify-between bg-[#FAF7F2]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FAF4E8] text-[#C9972B] border border-[#EADBCE] flex items-center justify-center">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#26221C]">إتمام طلب الاقتناء الفاخر</h3>
              <p className="text-xs text-[#746A5D]">توصيل مؤمن وسريع لكافة دول الخليج والعالم العربي</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8C8275] hover:text-[#26221C] hover:bg-white border border-transparent hover:border-[#E0D7C6] transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Product preview */}
        <div className="p-4 mx-6 mt-4 rounded-2xl bg-[#FAF7F2] border border-[#EBE3D5] flex items-center gap-3.5">
          <img
            src={product.image_url || '/branding/hero-amber.jpg'}
            alt=""
            className="w-14 h-14 object-cover rounded-xl border border-[#E0D7C6]"
          />
          <div className="flex-1 min-w-0">
            <span className="text-[10px] font-mono font-bold text-[#9A6817] bg-[#FAF4E8] px-2 py-0.5 rounded border border-[#EADBCE]">
              {product.sku}
            </span>
            <h4 className="font-bold text-xs text-[#26221C] truncate mt-1">{product.name_ar}</h4>
            <p className="text-sm font-black text-[#9A6817] mt-0.5">
              {product.selling_price.toLocaleString()} AED
            </p>
          </div>
        </div>

        {/* Checkout Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">الاسم الكريم *</label>
              <input
                type="text"
                required
                placeholder="اسم المستلم"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1">رقم الهاتف للتوصيل *</label>
              <input
                type="text"
                required
                placeholder="+97150..."
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          {/* Country & Shipping Destination Section */}
          <div className="p-3.5 rounded-2xl bg-[#FCFAF7] border border-[#EBE3D5] space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Country Selection Dropdown */}
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1 flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-[#C9972B]" />
                  <span>دولة الشحن والتوصيل *</span>
                </label>
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full bg-white border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] font-semibold focus:outline-none focus:border-[#C9972B]"
                >
                  {countriesList.map((cName) => (
                    <option key={cName} value={cName}>
                      {cName}
                    </option>
                  ))}
                </select>
              </div>

              {/* City / Province */}
              <div>
                <label className="block text-xs font-semibold text-[#4B4338] mb-1">
                  {isUAE ? 'الإمارة / المدينة *' : 'المدينة / المحافظة *'}
                </label>
                {isUAE ? (
                  <select
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full bg-white border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  >
                    <option value="أبوظبي">أبوظبي</option>
                    <option value="دبي">دبي</option>
                    <option value="الشارقة">الشارقة</option>
                    <option value="عجمان">عجمان</option>
                    <option value="رأس الخيمة">رأس الخيمة</option>
                    <option value="الفجيرة">الفجيرة</option>
                    <option value="أم القيوين">أم القيوين</option>
                    <option value="العين">العين</option>
                  </select>
                ) : (
                  <input
                    type="text"
                    required
                    placeholder="مثال: الرياض، الدوحة، القاهرة..."
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full bg-white border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
                  />
                )}
              </div>
            </div>

            {/* Detailed Street & Address */}
            <div>
              <label className="block text-xs font-semibold text-[#4B4338] mb-1 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-[#C9972B]" />
                <span>العنوان بالتفصيل (الحي، اسم الشارع، رقم المبنى/الفيلا) *</span>
              </label>
              <input
                type="text"
                required
                placeholder="مثال: حي الروضة، شارع الفلاح، فيلا 14"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full bg-white border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#4B4338] mb-1">ملاحظات التوصيل أو الإهداء</label>
            <input
              type="text"
              placeholder="مثال: يرجى إرفاق كيس الهدايا الفاخر"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-[#FAF7F2] border border-[#D8CCA8] rounded-xl px-3 py-2 text-xs text-[#26221C] focus:outline-none focus:border-[#C9972B]"
            />
          </div>

          <div className="pt-2 border-t border-[#F2ECE1] flex items-center justify-between">
            <div>
              <span className="text-[11px] text-[#746A5D] block">الإجمالي النهائي:</span>
              <span className="text-lg font-black text-[#9A6817]">
                {product.selling_price.toLocaleString()} AED
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-white hover:bg-[#FAF7F2] border border-[#E0D7C6] text-[#4B4338] text-xs font-semibold rounded-xl cursor-pointer"
              >
                إلغاء
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2.5 bg-[#C9972B] hover:bg-[#B8851E] text-white font-bold text-xs rounded-xl transition shadow-[0_4px_14px_rgba(201,151,43,0.3)] disabled:opacity-50 cursor-pointer"
              >
                {submitting ? 'جار المعالجة...' : 'تأكيد طلب الاقتناء'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
