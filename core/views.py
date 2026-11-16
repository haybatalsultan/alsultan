from urllib.parse import quote

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from catalog.models import Category, Product
from core.services.geocoding_service import GeocodingUnavailable, reverse_geocode

COMING_SOON_AR = 'قريبًا… مختارات تستحق الانتظار'
COMING_SOON_EN = 'Coming Soon… A Selection Worth Waiting For'

INFO_PAGES = {
    "shipping": {
        "ar": {
            "title": "سياسة الشحن والتوصيل",
            "sections": [
                (
                    "نطاق التوصيل",
                    [
                        "نوفر التوصيل داخل دولة الإمارات العربية المتحدة وفق مناطق وخيارات الشحن المتاحة عند إتمام الطلب. تظهر رسوم الشحن وأي تكاليف معلنة قبل تأكيد الطلب."
                    ],
                ),
                (
                    "معالجة الطلب ومدة التوصيل",
                    [
                        "تبدأ معالجة الطلب بعد تأكيده وفق طريقة الدفع المعتمدة. أي مدة توصيل معروضة هي مدة تقديرية وقد تتأثر بموقع التسليم أو شركة الشحن أو الظروف التشغيلية. إذا ظهر تأخير جوهري سنسعى لإبلاغ العميل عبر بيانات التواصل المسجلة."
                    ],
                ),
                (
                    "بيانات التسليم",
                    [
                        "يتحمل العميل مسؤولية تقديم اسم ورقم هاتف وعنوان توصيل صحيح وقابل للوصول. قد يؤدي الخطأ أو النقص في البيانات إلى تأخير التسليم أو الحاجة إلى إعادة التنسيق."
                    ],
                ),
                (
                    "فحص الشحنة",
                    [
                        "ننصح بفحص حالة التغليف والقطعة عند الاستلام متى كان ذلك ممكنًا، والتواصل معنا فور ملاحظة تلف ظاهر أو اختلاف جوهري عن الطلب."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Shipping & Delivery Policy",
            "sections": [
                (
                    "Delivery area",
                    [
                        "We deliver within the United Arab Emirates according to the delivery options available at checkout. Applicable shipping charges are displayed before the order is confirmed."
                    ],
                ),
                (
                    "Processing and estimated delivery",
                    [
                        "Order processing starts after confirmation in accordance with the selected payment method. Any delivery time shown is an estimate and may be affected by destination, courier operations or other circumstances. We will seek to notify the customer of any material delay using the contact details provided."
                    ],
                ),
                (
                    "Delivery information",
                    [
                        "The customer is responsible for providing an accurate name, mobile number and deliverable address. Incomplete or incorrect information may delay delivery or require a new delivery arrangement."
                    ],
                ),
                (
                    "Inspecting the shipment",
                    [
                        "Where practical, we recommend inspecting the packaging and item on receipt and contacting us promptly if there is visible damage or a material discrepancy with the order."
                    ],
                ),
            ],
        },
    },
    "returns": {
        "ar": {
            "title": "سياسة الاسترجاع والاستبدال",
            "sections": [
                (
                    "قبل إتمام الشراء",
                    [
                        "نظرًا لطبيعة منتجات HaybatAlsultan، وبخاصة المسابيح والقطع النادرة والكهرمان والخامات الطبيعية، يرجى مراجعة صور القطعة ووصفها ومقاساتها ووزنها وخامتها وحالتها والمعلومات المعروضة بعناية قبل تأكيد الطلب."
                    ],
                ),
                (
                    "تغيير الرأي",
                    [
                        "لا نقبل طلب الاسترجاع أو الاستبدال لمجرد تغيير الرأي أو عدم الرغبة في القطعة بعد إتمام الشراء، وذلك في الحدود التي يسمح بها القانون المعمول به في دولة الإمارات العربية المتحدة."
                    ],
                ),
                (
                    "العيب أو عدم المطابقة",
                    [
                        "لا تمس هذه السياسة أي حق إلزامي مقرر للمستهلك. إذا ثبت أن المنتج معيب بعيب غير معلن، أو غير مطابق للوصف أو المواصفات المتفق عليها، أو وجدت حالة أخرى يقرر فيها القانون حقًا للمستهلك، فسيتم التعامل معها وفق القانون والخيارات النظامية المتاحة."
                    ],
                ),
                (
                    "كيفية التواصل",
                    [
                        "لأي مطالبة متعلقة بعيب أو عدم مطابقة، تواصل معنا مع رقم الطلب وصور واضحة ووصف للمشكلة دون إجراء تعديل أو إصلاح على القطعة قبل مراجعة الطلب."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Returns & Exchanges Policy",
            "sections": [
                (
                    "Before purchasing",
                    [
                        "Because HaybatAlsultan offers Misbah, rare pieces, amber and natural materials, please carefully review the item photographs, description, dimensions, weight, material, condition and other disclosed information before confirming your order."
                    ],
                ),
                (
                    "Change of mind",
                    [
                        "We do not accept returns or exchanges solely because the customer changes their mind or no longer wants the item after purchase, to the extent permitted by applicable law in the United Arab Emirates."
                    ],
                ),
                (
                    "Defect or non-conformity",
                    [
                        "Nothing in this policy limits a mandatory consumer right. Where an item has an undisclosed defect, materially differs from the agreed description or specifications, or another legal entitlement applies, the matter will be handled in accordance with applicable law and the remedies available under it."
                    ],
                ),
                (
                    "How to contact us",
                    [
                        "For a defect or non-conformity claim, contact us with the order reference, clear photographs and a description of the issue. Please do not alter or repair the item before the claim is reviewed."
                    ],
                ),
            ],
        },
    },
    "authenticity": {
        "ar": {
            "title": "سياسة حالة وأصالة المنتجات",
            "sections": [
                (
                    "طبيعة القطع",
                    [
                        "نحرص على وصف كل قطعة وصورها وخصائصها بأكبر قدر عملي من الدقة. المنتجات الطبيعية قد تتضمن فروقًا طبيعية في اللون والشفافية والنقوش والتكوين والوزن والأبعاد، وهذه الفروق المعلنة أو الظاهرة في عرض القطعة لا تعد بحد ذاتها عيبًا."
                    ],
                ),
                (
                    "وصف الأصالة والندرة",
                    [
                        "لا نصف منتجًا بأنه طبيعي أو أصلي أو نادر إلا بناءً على المعلومات المتوفرة لدينا والأساس المناسب لهذا الوصف. إذا كانت القطعة قد خضعت لفحص أو كانت لها شهادة موثقة فسيتم بيان الحالة صراحة في صفحة المنتج، ولا يفترض وجود فحص أو شهادة ما لم يذكر ذلك."
                    ],
                ),
                (
                    "الصور والعرض",
                    [
                        "نسعى إلى أن تمثل الصور القطعة المعروضة بدقة، مع احتمال وجود اختلاف محدود في ظهور الألوان بسبب الشاشة أو الإضاءة. ولا نستخدم هذا الاختلاف لتبرير عيب أو عدم مطابقة جوهرية."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Product Condition & Authenticity Policy",
            "sections": [
                (
                    "Nature of the pieces",
                    [
                        "We aim to describe and photograph each item as accurately as reasonably practical. Natural materials may have inherent variations in colour, transparency, pattern, formation, weight and dimensions. Variations disclosed or visible in the item presentation are not, by themselves, defects."
                    ],
                ),
                (
                    "Authenticity and rarity descriptions",
                    [
                        "We describe an item as natural, authentic or rare only where we have an appropriate basis for doing so. Where an item has been inspected or has a documented certificate, the product page will state that status expressly; neither inspection nor certification should be assumed unless stated."
                    ],
                ),
                (
                    "Images and display",
                    [
                        "We seek to represent the actual item accurately. Screen settings and lighting can cause limited colour differences, but such differences will not be used to excuse a material defect or non-conformity."
                    ],
                ),
            ],
        },
    },
    "reservation-cancellation": {
        "ar": {
            "title": "سياسة الحجز وإلغاء الطلب",
            "sections": [
                (
                    "حجز إتمام الطلب",
                    [
                        "إضافة القطعة إلى السلة لا تحجز المخزون. يبدأ الحجز الفعلي عند إتمام الطلب لمدة محدودة، مع حد افتراضي لعدد القطع لحماية توفر المخزون لجميع العملاء."
                    ],
                ),
                (
                    "مدة الحجز",
                    [
                        "مدة الحجز يحددها المتجر ويحسبها الخادم، ولا يؤدي تحديث الصفحة أو تعديل عدّاد المتصفح إلى تمديدها. عند الانتقال إلى الدفع قد يستمر حجز الطلب وفق مهلة جلسة الدفع الآمنة."
                    ],
                ),
                (
                    "إلغاء الطلب",
                    [
                        "يعتمد التعامل مع طلب الإلغاء على حالة الطلب والدفع والشحن والحقوق النظامية الواجبة. لا تفسر هذه السياسة بما يلغي أي حق إلزامي للمستهلك بموجب القانون الإماراتي."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Reservation & Order Cancellation Policy",
            "sections": [
                (
                    "Checkout reservation",
                    [
                        "Adding an item to the cart does not reserve inventory. A time-limited reservation starts at checkout, with a default item limit to protect availability for all customers."
                    ],
                ),
                (
                    "Reservation duration",
                    [
                        "The reservation duration is enforced by the server. Refreshing the page or changing a browser countdown does not extend it. Once secure payment starts, any provider-specific payment window is tracked separately and does not rewrite the original reservation deadline."
                    ],
                ),
                (
                    "Order cancellation",
                    [
                        "Cancellation handling depends on the order, payment and shipping status and any mandatory legal rights. This policy must not be interpreted as excluding any mandatory consumer right under UAE law."
                    ],
                ),
            ],
        },
    },
    "privacy": {
        "ar": {
            "title": "سياسة الخصوصية",
            "sections": [
                (
                    "البيانات التي نعالجها",
                    [
                        "قد نعالج بيانات الحساب والاسم والهاتف والبريد الإلكتروني وعنوان التوصيل والطلبات والسلة وموافقة تذكير واتساب والبيانات التقنية اللازمة للأمان وتشغيل المتجر. لا نطلب الموقع الجغرافي إلا بعد اختيار المستخدم الصريح لاستخدامه."
                    ],
                ),
                (
                    "أغراض الاستخدام",
                    [
                        "نستخدم البيانات لتشغيل الحساب والمتجر، تنفيذ الطلبات، التوصيل، خدمة العميل، منع الاحتيال وإساءة الاستخدام، حفظ السجلات المطلوبة، وتحسين موثوقية الخدمة. الموافقة التسويقية منفصلة عن إنشاء الحساب أو تنفيذ الطلب."
                    ],
                ),
                (
                    "المشاركة",
                    [
                        "قد تتم مشاركة الحد الأدنى اللازم من البيانات مع مزودي الخدمات الذين نحتاجهم لتنفيذ الطلب، مثل مزود الدفع أو شركة التوصيل أو خدمات البنية التحتية، وفق الغرض المخصص لهم والمتطلبات القانونية ذات الصلة."
                    ],
                ),
                (
                    "الحماية والاحتفاظ",
                    [
                        "نطبق ضوابط تقنية وتنظيمية مناسبة لحماية البيانات ونحتفظ بها للمدة اللازمة للأغراض المشروعة والمتطلبات القانونية والتشغيلية، ثم نتعامل معها وفق سياسة الاحتفاظ المعتمدة."
                    ],
                ),
                (
                    "التواصل بشأن الخصوصية",
                    [
                        "للاستفسارات المتعلقة بالخصوصية تواصل معنا عبر info@haybatalsultan.com."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Privacy Policy",
            "sections": [
                (
                    "Data we process",
                    [
                        "We may process account information, name, mobile number, email address, delivery address, orders, cart data, WhatsApp reminder consent and technical information required for security and store operation. Geolocation is requested only after the user explicitly chooses to use it."
                    ],
                ),
                (
                    "Purposes",
                    [
                        "We use information to operate accounts and the store, fulfil and deliver orders, provide customer service, prevent fraud and abuse, maintain required records and improve service reliability. Marketing consent is separate from account creation or purchasing."
                    ],
                ),
                (
                    "Sharing",
                    [
                        "We may share the minimum information necessary with service providers needed to fulfil an order, such as payment, delivery or infrastructure providers, for their defined purpose and subject to applicable legal requirements."
                    ],
                ),
                (
                    "Security and retention",
                    [
                        "We apply appropriate technical and organisational controls and retain information for as long as needed for legitimate operational and legal purposes, after which it is handled under the applicable retention process."
                    ],
                ),
                (
                    "Privacy contact",
                    ["For privacy enquiries, contact info@haybatalsultan.com."],
                ),
            ],
        },
    },
    "terms": {
        "ar": {
            "title": "الشروط والأحكام",
            "sections": [
                (
                    "استخدام المتجر",
                    [
                        "باستخدام HaybatAlsultan أو إنشاء طلب، يلتزم المستخدم بتقديم معلومات صحيحة وعدم إساءة استخدام الموقع أو محاولة تجاوز ضوابط الأمان أو الوصول إلى وظائف غير مصرح بها."
                    ],
                ),
                (
                    "المنتجات والأسعار والتوفر",
                    [
                        "نعرض معلومات المنتج والسعر والتوفر بأكبر قدر عملي من الدقة. يخضع البيع للتوفر الفعلي والتحقق النهائي من الطلب والدفع وفق الطريقة المعتمدة. لا يعتبر فتح واتساب أو إرسال رسالة بحد ذاته إتمامًا للبيع أو إثباتًا للدفع."
                    ],
                ),
                (
                    "المنتجات الطبيعية",
                    [
                        "يقر العميل بأنه راجع الوصف والصور والمواصفات والحالة المعروضة للقطعة، مع مراعاة الخصائص الطبيعية المبينة في سياسة حالة وأصالة المنتجات."
                    ],
                ),
                (
                    "الحسابات والأمان",
                    [
                        "يتحمل المستخدم مسؤولية المحافظة على سرية بيانات دخوله وإبلاغنا عند الاشتباه في استخدام غير مصرح به. يجوز لنا اتخاذ إجراءات معقولة لحماية المتجر والعملاء من إساءة الاستخدام أو الاحتيال."
                    ],
                ),
                (
                    "الحقوق القانونية",
                    [
                        "لا يجوز تفسير أي حكم من هذه الشروط بما يؤدي إلى إسقاط أو تقييد أي حق إلزامي مقرر للمستهلك بموجب القوانين السارية في دولة الإمارات العربية المتحدة."
                    ],
                ),
                (
                    "التحديثات",
                    [
                        "قد نحدّث هذه الشروط مستقبلًا. الطلبات تحتفظ بإصدار السياسة الذي أقر به العميل وقت إنشاء الطلب، ولا نطبق نسخة أحدث على قبول سابق بأثر رجعي."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Terms & Conditions",
            "sections": [
                (
                    "Use of the store",
                    [
                        "By using HaybatAlsultan or placing an order, the user agrees to provide accurate information and not misuse the website, circumvent security controls or attempt to access unauthorised functions."
                    ],
                ),
                (
                    "Products, prices and availability",
                    [
                        "We seek to present product, price and availability information accurately. A sale remains subject to actual availability and final order and payment validation under the supported method. Opening WhatsApp or sending a message does not by itself complete a sale or prove payment."
                    ],
                ),
                (
                    "Natural products",
                    [
                        "The customer acknowledges reviewing the disclosed description, photographs, specifications and condition of the item, taking into account the natural characteristics described in the Product Condition & Authenticity Policy."
                    ],
                ),
                (
                    "Accounts and security",
                    [
                        "Users are responsible for keeping their login credentials confidential and notifying us of suspected unauthorised use. We may take reasonable measures to protect the store and customers from abuse or fraud."
                    ],
                ),
                (
                    "Mandatory legal rights",
                    [
                        "Nothing in these terms may be interpreted as excluding or restricting a mandatory consumer right under the laws applicable in the United Arab Emirates."
                    ],
                ),
                (
                    "Updates",
                    [
                        "We may update these terms in the future. Orders retain the policy version accepted when the order was placed; a later version is not retroactively substituted for that acceptance."
                    ],
                ),
            ],
        },
    },
    "faq": {
        "ar": {
            "title": "الأسئلة الشائعة",
            "sections": [
                (
                    "هل وضع المنتج في السلة يحجزه؟",
                    [
                        "لا. السلة تحفظ اختيارك فقط، والحجز الفعلي يبدأ عند إتمام الطلب. الحد الافتراضي 3 قطع ويمكن للإدارة منح عميل مسجل استثناءً مؤقتًا عند الحاجة."
                    ],
                ),
                (
                    "كيف أتتبع طلبي؟",
                    [
                        "استخدم صفحة تتبع الطلب وأدخل رقم الطلب ورقم الهاتف المستخدم عند الشراء."
                    ],
                ),
                (
                    "هل الصور تخص القطعة نفسها؟",
                    [
                        "نسعى إلى عرض صور دقيقة للقطعة المعروضة. راجع صفحة المنتج وسياسة حالة وأصالة المنتجات لأي تفاصيل خاصة بالقطعة."
                    ],
                ),
                (
                    "هل كل قطعة لديها شهادة أو فحص؟",
                    [
                        "لا. إذا تم فحص المنتج أو كان موثقًا بشهادة فستظهر الحالة صراحة في صفحة المنتج، ولا يفترض وجود فحص أو شهادة إذا لم تذكر."
                    ],
                ),
                (
                    "هل يمكنني الاسترجاع بسبب تغيير الرأي؟",
                    [
                        "لا نقبل الاسترجاع أو الاستبدال لمجرد تغيير الرأي في الحدود التي يسمح بها القانون، مع بقاء أي حقوق إلزامية للمستهلك في حالات العيب أو عدم المطابقة أو غيرها من الحالات التي يقررها القانون."
                    ],
                ),
                (
                    "كيف أتواصل معكم؟",
                    [
                        "عبر +971 50 408 4006 أو info@haybatalsultan.com أو قنوات HaybatAlsultan الرسمية المبينة في الموقع."
                    ],
                ),
            ],
        },
        "en": {
            "title": "Frequently Asked Questions",
            "sections": [
                (
                    "Does adding an item to my cart reserve it?",
                    [
                        "No. The cart only saves your selection. The real reservation starts at checkout. The default limit is 3 items, and management can grant a temporary exception to a registered customer when needed."
                    ],
                ),
                (
                    "How do I track my order?",
                    [
                        "Use the order tracking page and enter the order reference and the mobile number used for the purchase."
                    ],
                ),
                (
                    "Are the photographs of the actual item?",
                    [
                        "We aim to show accurate photographs of the item offered. Review the product page and Product Condition & Authenticity Policy for item-specific details."
                    ],
                ),
                (
                    "Is every item inspected or certified?",
                    [
                        "No. If an item has been inspected or is certified, that status is expressly shown on the product page and should not be assumed otherwise."
                    ],
                ),
                (
                    "Can I return an item because I changed my mind?",
                    [
                        "We do not accept a return or exchange solely for change of mind to the extent permitted by law, while mandatory consumer rights for defects, non-conformity or other legally protected cases remain unaffected."
                    ],
                ),
                (
                    "How can I contact you?",
                    [
                        "Contact us on +971 50 408 4006, info@haybatalsultan.com, or the official HaybatAlsultan channels shown on the website."
                    ],
                ),
            ],
        },
    },
}


COMING_SOON_PAGES = {
    "gemstones": {
        "ar": (
            "الأحجار الكريمة",
            COMING_SOON_AR,
            "نعمل حاليًا على تجهيز مجموعة استثنائية من الأحجار الكريمة المختارة بعناية لتليق بذائقتكم. ترقبوا الإطلاق قريبًا، حيث تبدأ الحكاية مع تفاصيل لا تشبه سواها.",
        ),
        "en": (
            "Gemstones",
            COMING_SOON_EN,
            "We are curating an exceptional collection of gemstones, selected with care for those who value distinction. Stay tuned for a refined release where every detail is chosen to stand apart.",
        ),
    },
    "rare-collectibles": {
        "ar": (
            "النوادر",
            COMING_SOON_AR,
            "نعمل حاليًا على تجهيز مجموعة استثنائية من النوادر والقطع المختارة بعناية لتليق بذائقتكم. ترقبوا الإطلاق قريبًا، حيث تبدأ الحكاية مع تفاصيل لا تشبه سواها.",
        ),
        "en": (
            "Rare Collectibles",
            COMING_SOON_EN,
            "We are curating an exceptional collection of rare pieces for discerning collectors. Stay tuned for a refined release where rarity, story and character come together.",
        ),
    },
    "gifts": {
        "ar": (
            "الهدايا",
            COMING_SOON_AR,
            "نعمل حاليًا على تجهيز مجموعة هدايا استثنائية بتفاصيل راقية تليق بالمناسبات المميزة. ترقبوا الإطلاق قريبًا، حيث تبدأ الحكاية مع تفاصيل لا تشبه سواها.",
        ),
        "en": (
            "Gifts",
            COMING_SOON_EN,
            "We are preparing a refined gifting collection designed for memorable occasions. Stay tuned for a premium selection where presentation and detail are part of the experience.",
        ),
    },
}

ABOUT_CONTENT = {
    "ar": {
        "title": "هيبة السلطان",
        "paragraphs": [
            "هيبة السلطان متجر إماراتي متخصص في انتقاء وتقديم المسابيح الفاخرة، والنوادر، والكهرمان الطبيعي الحر، بعناية تليق بعشّاق التميّز والاقتناء.",
            "جاء اختيار اسم «هيبة السلطان» ليجسّد معنى الفخامة والأصالة والحضور؛ فالهيبة تعبّر عن القيمة والوقار، والسلطان يرمز إلى التفرّد والمكانة. وهي المعاني التي نحرص أن تنعكس في كل قطعة نختارها ونقدمها.",
            "نفخر بأن هيبة السلطان بإدارة وطنية إماراتية، انطلقت برؤية تهدف إلى بناء اسم موثوق يجمع بين جودة الاختيار، أصالة القطعة، جمال التفاصيل، والاهتمام بتجربة العميل.",
            "نؤمن أن بعض القطع لا تُقتنى لمجرد جمالها، بل لما تحمله من قصة وقيمة وندرة؛ لذلك نبحث بعناية عمّا يستحق أن يكون ضمن مجموعتكم.",
        ],
        "closing": "من أبوظبي 🇦🇪 ✈️ إلى عشّاق النوادر والكهرمان الطبيعي الحر",
    },
    "en": {
        "title": "Haybat Al Sultan",
        "paragraphs": [
            "Haybat Al Sultan is an Emirati store dedicated to curating premium Misbah, rare collectibles and natural free-form amber for collectors who appreciate distinction and character.",
            "The name “Haybat Al Sultan” reflects prestige, authenticity and presence. “Haybat” conveys dignity and value, while “Al Sultan” represents distinction and stature—qualities we seek to reflect in every piece we select and present.",
            "Proudly managed by an Emirati national team, Haybat Al Sultan was founded with a vision to build a trusted name defined by thoughtful selection, authenticity, refined detail and a premium customer experience.",
            "We believe some pieces are collected not only for their beauty, but for the story, value and rarity they carry. That is why we carefully seek what truly deserves a place in your collection.",
        ],
        "closing": "From Abu Dhabi 🇦🇪 ✈️ to collectors of rare pieces and natural amber",
    },
}


@require_GET
def home(request):
    from django.db.models import F

    from orders.services.cart_service import purge_expired_cart_items

    purge_expired_cart_items(limit=100)
    products = (
        Product.objects.filter(
            status=Product.Status.AVAILABLE,
            is_featured=True,
            available_quantity__gt=F("reserved_quantity"),
        )
        .select_related("category", "material")
        .prefetch_related("images")[:12]
    )
    return render(
        request,
        "core/home.html",
        {
            "products": products,
            "categories": Category.objects.filter(is_active=True)[:8],
        },
    )


@require_GET
def about(request):
    lang = "en" if getattr(request, "LANGUAGE_CODE", "ar") == "en" else "ar"
    return render(request, "core/about.html", {"about": ABOUT_CONTENT[lang]})


@require_GET
def digital_services(request):
    lang = "en" if getattr(request, "LANGUAGE_CODE", "ar") == "en" else "ar"
    if lang == "en":
        consultation_message = (
            "Hello Haybat Al Sultan, I would like to request a consultation "
            "regarding e-commerce store design or development. "
            "I contacted you through the Digital Services page. "
            "Source code: HS-DIGITAL-SERVICES."
        )
    else:
        consultation_message = (
            "مرحبًا هيبة السلطان، أرغب في طلب استشارة بخصوص تصميم أو تطوير متجر إلكتروني. "
            "تواصلت معكم من خلال صفحة خدماتنا الأخرى. "
            "رمز المصدر: HS-DIGITAL-SERVICES."
        )

    whatsapp_digits = "".join(ch for ch in settings.WHATSAPP_NUMBER if ch.isdigit())
    consultation_whatsapp_url = (
        f"https://wa.me/{whatsapp_digits}?text={quote(consultation_message)}"
    )

    return render(
        request,
        "core/digital_services.html",
        {
            "consultation_whatsapp_url": consultation_whatsapp_url,
        },
    )


@require_GET
def coming_soon(request, slug):
    page = COMING_SOON_PAGES.get(slug)
    if not page:
        raise Http404
    lang = "en" if getattr(request, "LANGUAGE_CODE", "ar") == "en" else "ar"
    title, headline, body = page[lang]
    return render(
        request,
        "core/coming_soon.html",
        {"page_title": title, "headline": headline, "page_body": body},
    )


@require_GET
def info_page(request, slug):
    page = INFO_PAGES.get(slug)
    if not page:
        raise Http404
    lang = "en" if getattr(request, "LANGUAGE_CODE", "ar") == "en" else "ar"
    content = page[lang]
    return render(
        request,
        "core/info_page.html",
        {
            "page_title": content["title"],
            "sections": content["sections"],
            "policy_slug": slug,
        },
    )


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


def robots(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /management/\nSitemap: /sitemap.xml\n",
        content_type="text/plain",
    )


@require_POST
def reverse_geocode_location(request):
    try:
        result = reverse_geocode(
            request.POST.get("latitude"),
            request.POST.get("longitude"),
            language=getattr(request, "LANGUAGE_CODE", "ar"),
        )
    except ValueError:
        return JsonResponse({"detail": "Invalid location."}, status=400)
    except GeocodingUnavailable:
        return JsonResponse(
            {"detail": "Location lookup is currently unavailable."}, status=503
        )
    except Exception:
        return JsonResponse({"detail": "Location lookup failed."}, status=502)
    return JsonResponse(result)
