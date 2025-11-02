import httpx
import re


class AIClient:
    def __init__(self, provider: str, api_key: str | None):
        self.provider = provider
        self.api_key = api_key
        # no external knowledge module (reverted per request)

    # --- Public API ---
    def chat(self, messages: list[dict]) -> str:
        # Cloud provider
        if self.provider == "openai" and self.api_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": messages}
            r = httpx.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

        # Local smart fallback (no API key needed)
        return self._respond_local(messages)

    # --- Local rule-based assistant about the site ---
    def _respond_local(self, messages: list[dict]) -> str:
        text = (messages[-1].get("content", "") if messages else "").strip()
        q = self._norm(text)

        # Knowledge: update as the site grows
        site = {
            "name": "DARK Shop",
            "links": {
                "home": "/",
                "shop": "/shop",
                "tools": "/tools",
                "contact": "/contact",
                "cart": "/shop/cart",
            },
            "payments": [
                "عبر ديسكورد: https://discord.gg/FtprtXweuZ",
                "واتساب/اتصال: +971 56 625 2595",
                "تليجرام: @DARK_PB",
            ],
            "buy_steps": [
                "اذهب إلى صفحة المتجر: /shop",
                "اختر المنتج ثم اضغط إضافة للسلة",
                "انتقل إلى السلة: /shop/cart لمراجعة الكمية والإجمالي",
                "اضغط متابعة الدفع لتظهر لك طرق الدفع (ديسكورد/واتساب/تليجرام)",
                "أرسل إثبات الدفع وسيتم تسليم المنتج"
            ],
        }

        def bullets(lines):
            return "\n".join([f"• {ln}" for ln in lines])

        # Small‑talk and natural replies
        if any(k in q for k in ["السلام عليكم", "السلام", "سلام عليكم", "salam", "salam alaikum"]):
            return "وعليكم السلام ورحمة الله، أهلًا بك! كيف أقدر أساعدك؟"

        if any(k in q for k in ["مرحبا", "اهلا", "هلا", "هاي", "hi", "hello", "hey", "hey there", "yo", "sup", "what's up", "whats up", "good morning", "good afternoon", "good evening"]):
            return "مرحبًا! أنا مساعد DARK — كيف أقدر أساعدك اليوم؟"

        if any(k in q for k in ["كيفك", "كيف الحال", "اخبارك", "how are you"]):
            return "أنا بخير ولله الحمد. كيف أقدر أساعدك؟"

        if any(k in q for k in ["شكرا", "مشكو", "thanks", "thank you", "thanks a lot", "thank you so much"]):
            return "العفو! أي خدمة أخرى؟"

        if any(k in q for k in ["باي", "مع السلامة", "الى اللقاء", "goodbye", "bye", "see you", "see ya", "take care"]):
            return "مع السلامة! إذا احتجت أي شيء أنا موجود هنا."

        if any(k in q for k in ["ok", "okay", "cool", "great", "تمام", "تمام تمام", "تمام يا بطل"]):
            return "تمام! هل تحتاج مساعدة إضافية؟"

        # Q/A by intent
        if any(k in q for k in ["طرق الدفع", "الدفع", "وسائل الدفع", "pay", "payment", "whatsapp", "ديسكورد", "تلجرام", "telegram"]):
            return (
                "طرق الدفع المتوفرة حالًا:\n" + bullets(site["payments"]) +
                "\n\nتواصل عبر أي وسيلة وسيتم إرشادك لإتمام العملية بسرعة."
            )

        if any(k in q for k in ["كيف", "طريقة", "شراء", "buy", "add to cart", "السلة", "cart"]):
            return "طريقة الشراء خطوة بخطوة:\n" + bullets(site["buy_steps"]) + f"\n\nروابط مفيدة: المتجر {site['links']['shop']} | السلة {site['links']['cart']}"

        if any(k in q for k in ["عن", "معلومات", "الموقع", "المتجر", "what is", "info", "support", "help"]):
            return (
                f"{site['name']} متجر وأدوات رقمية بتصميم فاخر.\n"
                "يوفر منتجات وخدمات تُدار من خلال لوحة بسيطة.\n\n"
                "أهم الصفحات:\n" + bullets([
                    f"الرئيسية: {site['links']['home']}",
                    f"المتجر: {site['links']['shop']}",
                    f"الأدوات: {site['links']['tools']}",
                    f"التواصل: {site['links']['contact']}",
                ]) +
                "\nللشراء أو الاستفسار استخدم وسائل الدفع/التواصل أعلاه."
            )

        # Products / prices intent (English keywords as robust fallback)
        if any(k in q for k in ["product", "products", "price", "prices", "item", "items", "منتج", "منتجات", "المنتجات", "سعر", "الاسعار", "اسعار"]):
            listing = self._list_products()
            if listing:
                return "المنتجات المتاحة وأسعارها:\n" + listing + "\n\nللتفاصيل والشراء زر المتجر: /shop"
            else:
                return "لا أستطيع جلب قائمة المنتجات الآن. تفضل بزيارة المتجر: /shop"

        # No site-knowledge answers (reverted)

        # Security tips intent
        if any(k in q for k in ['tips','security','safe','safety','نصائح','امان','الأمان']):
            tips = [
                'تحقق من الحساب/الرابط قبل الدفع وتجنب الروابط المجهولة',
                'احتفظ بإثبات الدفع حتى استلام المنتج',
                'تواصل عبر القنوات الرسمية (Discord/WhatsApp/Telegram)',
                'لا تشارك مفاتيح التفعيل أو بياناتك الحساسة'
            ]
            return "نصائح أمان للشراء:\n" + bullets(tips)

        if any(k in q for k in ["تواصل", "اتصال", "contact", "email", "support"]):
            return "قنوات التواصل:\n" + bullets(site["payments"]) + "\n\nيمكنك كذلك استخدام صفحة التواصل: /contact"

        # Safety / generic helpful response
        last = text or "سأساعدك في أي استفسار يخص المتجر."
        return (
            "أنا مساعد DARK. يمكنني شرح طريقة الشراء، وسائل الدفع، وروابط الصفحات.\n"
            "اسألني مثلًا: ما هي طرق الدفع؟ أو كيف أشتري منتج؟\n\n"
            f"طلبك: {last}"
        )

    def _norm(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[\u0617-\u061A\u064B-\u0652]", "", s)  # remove Arabic diacritics
        s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
        return s

    def _list_products(self) -> str:
        """Read products from Supabase if configured and format nicely."""
        try:
            from .supabase_client import get_supabase
            sb = get_supabase()
            res = sb.table('products').select('id,name,price').order('id').execute()
            data = getattr(res, 'data', None) or []
            lines = []
            for p in data:
                name = str(p.get('name') or 'منتج')
                try:
                    price = float(p.get('price') or 0)
                except Exception:
                    price = p.get('price') or 0
                lines.append(f"{name} — ${price:.2f}")
            return "\n".join([f"• {ln}" for ln in lines]) if lines else ""
        except Exception:
            return ""
