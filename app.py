import streamlit as st
import services
import sqlite3
import random
import os
import hashlib
import urllib.parse
import shutil
from datetime import datetime

# ==========================================
# 🛑 رفع حد رفع الملفات والصوت (يجب أن يكون في البداية)
# ==========================================
st.config.set_option("server.maxUploadSize", 200)

# ==========================================
# 🎨 واجهة وتصميم التطبيق والخلفية الاحترافية الجديدة
# ==========================================
st.set_page_config(
    page_title="مؤسسة جايا لك للتوصيل الذكي",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 📂 المجلدات المخصصة لحفظ الصور والأصوات والنسخ الاحتياطي
VOICE_DIR = "saved_voices"
IMAGE_DIR = "saved_images"
BACKUP_DIR = "system_backups"

for folder in [VOICE_DIR, IMAGE_DIR, BACKUP_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==========================================
# 🛠️ دالات الأمان والتشفير وقاعدة البيانات
# ==========================================

def hash_password(password):
    SECRET_SALT = "JayaLak_Secure_2026_@Key"
    salted_pass = password + SECRET_SALT
    return hashlib.sha256(salted_pass.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('jaya_lak.db', timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def make_backup():
    try:
        today_str = datetime.now().strftime("%Y_%m_%d")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{today_str}.db")
        if not os.path.exists(backup_file) and os.path.exists('jaya_lak.db'):
            shutil.copyfile('jaya_lak.db', backup_file)
    except Exception:
        pass

def init_db():
    with sqlite3.connect('jaya_lak.db', timeout=30) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                from_loc TEXT,
                to_loc TEXT,
                type TEXT,
                status TEXT,
                cost INTEGER,
                driver TEXT,
                payment_method TEXT,
                notes TEXT,
                voice_path TEXT,
                image_path TEXT,
                order_time TEXT DEFAULT '',
                delivery_time TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'voice_path' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN voice_path TEXT DEFAULT ''")
        if 'image_path' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN image_path TEXT DEFAULT ''")
        if 'order_time' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN order_time TEXT DEFAULT ''")
        if 'delivery_time' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN delivery_time TEXT DEFAULT ''")
            
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                assigned_village TEXT,
                password TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute("PRAGMA table_info(drivers)")
        d_columns = [column[1] for column in cursor.fetchall()]
        if 'password' not in d_columns:
            default_d_pass = hash_password("1234")
            cursor.execute(f"ALTER TABLE drivers ADD COLUMN password TEXT DEFAULT '{default_d_pass}'")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        default_hashed = hash_password("admin123")
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings VALUES ('admin_password', ?)", (default_hashed,))
            
        cursor.execute("SELECT value FROM settings WHERE key='admin_whatsapp'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings VALUES ('admin_whatsapp', '770000000')")
            
        conn.commit()
    make_backup()

init_db()

def check_admin_password(input_pwd):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        res = cursor.fetchone()
        saved_hash = res['value'] if res else ""
    return saved_hash == hash_password(input_pwd)

def get_admin_whatsapp():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='admin_whatsapp'")
        res = cursor.fetchone()
        return res['value'] if res else "770000000"

def update_admin_whatsapp(new_phone):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value=? WHERE key='admin_whatsapp'", (new_phone,))
        conn.commit()

def send_whatsapp_notification(phone, message):
    if phone.startswith("0"):
        phone = phone[1:]
    if not phone.startswith("967"):
        phone = "967" + phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone}?text={encoded_msg}"

def send_sms_notification(phone, message):
    if phone.startswith("0"):
        phone = phone[1:]
    if not phone.startswith("967") and not phone.startswith("+967"):
        phone = "+967" + phone
    encoded_msg = urllib.parse.quote(message)
    return f"sms:{phone}?&body={encoded_msg}"

# نظام التحذير من انقطاع الإنترنت
st.components.v1.html("""
<script>
window.addEventListener('offline', function(e) {
    alert('⚠️ تنبيه ميداني: انقطع الاتصال بالإنترنت لديك حالياً! يرجى عدم إغلاق هذه الصفحة لضمان حفظ بيانات الشحنة المفتوحة فور عودة الشبكة.');
});
</script>
""", height=0)

# تضخيم الأزرار وإجبار الواجهة على التحديث الفوري لتخطي الـ Cache
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;600;700&display=swap');
    
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    [data-testid="stViewerToolbar"] {display: none !important;}
    iframe[title="Manage app"] {display: none !important;}
    button[title="Manage app"] {display: none !important;}
    
    /* خلفية تحتوى على مواد غذائية، توابل، وخضروات متنوعة مجتمعة */
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.65), rgba(255, 255, 255, 0.65)), 
                          url('https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1974&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    * { 
        font-family: 'Cairo', sans-serif; 
        text-align: right; 
        direction: rtl; 
        color: #000000 !important; 
    }
    
    .card { 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 22px; 
        border-radius: 16px; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
        margin-bottom: 18px; 
        border: 1px solid rgba(255, 255, 255, 0.8); 
    }
    
    .voice-box { border: 2px dashed #16a34a; padding: 20px; background-color: rgba(240, 253, 244, 0.95); border-radius: 16px; margin-bottom: 15px; text-align: center; }
    .jeeb-panel { background-color: rgba(240, 253, 244, 0.95); border-right: 6px solid #0d9488; padding: 15px; border-radius: 8px; font-weight: bold; }
    .price-tag { background-color: rgba(239, 246, 255, 0.95); color: #1d4ed8 !important; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 24px; border: 2px dashed #3b82f6; }
    
    /* 🚨 تضخيم وإجبار أزرار البوابة الرئيسية الثلاثة لتصبح عملاقة جداً */
    div[data-testid="stMain"] div.stButton > button {
        width: 100% !important;
        height: 120px !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        border: 2px solid #000000 !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
        margin-bottom: 15px !important;
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    /* تمييز واستهداف زر العميل الأخضر وتكبيره بشكل هائل */
    div.client-main-btn div.stButton > button {
        background-color: #16a34a !important;
        color: #ffffff !important;
        height: 95px !important;
        font-size: 24px !important;
    }
    
    /* 🚨 تضخيم وإجبار زر تأكيد الطلب للزبون باللون الأخضر الفاقع والكبير */
    div.big-confirm-btn div.stButton > button {
        background-color: #16a34a !important;
        color: #ffffff !important;
        height: 130px !important;
        font-size: 34px !important;
        font-weight: 900 !important;
        border: 3px solid #0f766e !important;
        box-shadow: 0 10px 20px rgba(22, 163, 74, 0.4) !important;
    }
    
    .whatsapp-btn a, .sms-btn a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 60px !important;
        background-color: #25D366 !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        color: white !important;
        text-decoration: none !important;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15) !important;
        margin-bottom: 8px !important;
    }
    .sms-btn a { background-color: #0284c7 !important; }
    
    .back-btn button { 
        background-color: #64748b !important; 
        color: white !important;
        height: 50px !important; 
        font-size: 18px !important; 
    }
    
    h1, h2, h3, h4, h5, h6, label, p, span, li, td, th { color: #000000 !important; font-weight: 700 !important; }
    input, select, textarea { color: #000000 !important; font-weight: bold !important; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>📦 مؤسسة جَايَا لَك للتوصيل الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; font-weight: bold;'>الخدمة الأسرع لتوصيل المواد الغذائية والطلبات - كِتَاب والقرى المجاورة</p>", unsafe_allow_html=True)
st.write("---")

# ==========================================
# 🧭 إدارة الجلسة (Session State)
# ==========================================
if 'current_role' not in st.session_state:
    st.session_state.current_role = "main_gate"

if st.session_state.current_role != "main_gate":
    st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
    if st.button("🔙 العودة لصفحة الاختيار الرئيسية"):
        st.session_state.current_role = "main_gate"
        st.rerun()
    st.markdown("</div><br>", unsafe_allow_html=True)

# قاعدة البيانات الجغرافية
to_locations_db = {
    "مدينة كتاب": {"light": 200, "heavy": 400},
    "قرية الحزة": {"light": 300, "heavy": 500},
    "قرية رباط القلعة": {"light": 400, "heavy": 600},
    "قرية المنزل": {"light": 500, "heavy": 700},
    "قرية دخلة المسالمة": {"light": 500, "heavy": 700},
    "قرية شهصان": {"light": 500, "heavy": 700},
    "قرية الدريعاء": {"light": 500, "heavy": 700},
    "قرية الخربة": {"light": 500, "heavy": 700},
    "قرية رباط مصرع": {"light": 700, "heavy": 1200},
    "قرية بيح": {"light": 700, "heavy": 1000},
    "قرية سنب": {"light": 700, "heavy": 1000},
    "قرية الضربة": {"light": 700, "heavy": 1000},
    "قرية الجرين": {"light": 700, "heavy": 1000},
    "قرية بعلان": {"light": 700, "heavy": 1000},
    "قرية الشماري": {"light": 800, "heavy": 1200},
    "قرية رباط الأحكل": {"light": 800, "heavy": 1200},
    "قرية العزازي": {"light": 1000, "heavy": 1500},
    "قرى الصفي": {"light": 1500, "heavy": 2500}
}

# -------------------------------------------------------------------------
# 🚪 أ: البوابة الرئيسية المشتركة لاختيار الهوية (Main Gate)
# -------------------------------------------------------------------------
if st.session_state.current_role == "main_gate":
    st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color:#16a34a;'>مرحباً بك في منظومة جايا لك الذكية 🤝</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>يرجى اختيار هويتك للدخول إلى الواجهة المخصصة لك:</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='client-main-btn'>", unsafe_allow_html=True)
    if st.button("👤 أنا عميل (أريد إرسال طلب أو تتبع شحنة)"):
        st.session_state.current_role = "client_portal"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🛵 أنا مندوب كابتن حركة (توصيل ميداني)"):
        st.session_state.current_role = "driver_portal"
        st.rerun()
    
    if st.button("💼 لوحة تحكم الإدارة والمدير المركزي"):
        st.session_state.current_role = "manager_portal"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 👤 ب: واجهة العميل الكاملة المستقلة (إرسال طلب + تتبع)
# -------------------------------------------------------------------------
elif st.session_state.current_role == "client_portal":
    st.markdown("<h2 style='color:#16a34a;'>👤 بوابة العميل الذكية</h2>", unsafe_allow_html=True)
    
    client_sub_tab1, client_sub_tab2 = st.tabs(["🚀 إرسال طلب جديد", "🔍 تتبع حالة شحنتك الميدانية"])
    
    with client_sub_tab1:
        if 'client_order_success' not in st.session_state:
            st.session_state.client_order_success = False
            st.session_state.last_order_id = ""

        if st.session_state.client_order_success:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.success(f"🎉 تم استلام طلبك بنجاح! كود تتبع شحنتك الميداني هو: {st.session_state.last_order_id}")
            
            admin_tel = get_admin_whatsapp()
            client_msg = f"🚨 طلب جديد في جايا لك برقم ({st.session_state.last_order_id}). يرجى المراجعة والتعميد الفوري من لوحة المدير."
            
            wa_url = send_whatsapp_notification(admin_tel, client_msg)
            sms_url = send_sms_notification(admin_tel, client_msg)
            
            col_notif1, col_notif2 = st.columns(2)
            with col_notif1:
                st.markdown(f"<div class='whatsapp-btn'><a href='{wa_url}' target='_blank'>💬 إشعار واتساب للإدارة</a></div>", unsafe_allow_html=True)
            with col_notif2:
                st.markdown(f"<div class='sms-btn'><a href='{sms_url}'>✉️ إرسال رسالة نصية SMS</a></div>", unsafe_allow_html=True)
            
            if st.button("🔄 إرسال طلب شحنة جديدة أخرى"):
                st.session_state.client_order_success = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#16a34a;'>👤 بياناتك الشخصية</h3>", unsafe_allow_html=True)
            cl_col1, cl_col2 = st.columns(2)
            with cl_col1:
                c_name = st.text_input("اكتب اسمك الكامل هنا *", placeholder="أحمد...", key="c_name")
            with cl_col2:
                c_phone = st.text_input("رقم هاتفك للتواصل (9 أرقام) *", max_chars=9, placeholder="77XXXXXXX", key="c_phone")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#16a34a;'>📍 مسار التوصيل المعتمد</h3>", unsafe_allow_html=True)
            loc_col1, loc_col2 = st.columns(2)
            with loc_col1:
                # تم إلغاء القرى تماماً والإبقاء على المركز الرئيسي كتاب فقط بناء على طلبك
                from_loc = st.selectbox("مكان استلاف وتجهيز البضاعة (من أين؟) *", ["المركز الرئيسي كتاب"])
            with loc_col2:
                to_loc = st.selectbox("مكان تسليم البضاعة لبيتك (إلى أين؟) *", list(to_locations_db.keys()))
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='voice-box'>", unsafe_allow_html=True)
            st.markdown("<h3>🎙️ سجل تفاصيل طلبك بصوتك مباشرة</h3>", unsafe_allow_html=True)
            voice_file = st.audio_input("اضغط لبدء تسجيل صوتك المباشر:")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3>✏️ حجم وتفاصيل الشحنة</h3>", unsafe_allow_html=True)
            user_notes = st.text_area("إذا تريد كتابة ملاحظة إضافية للمندوب اكتبها هنا:", placeholder="مثال: كرتون صلصة، بهارات، كيس دقيق...")
            weight_opt = st.selectbox("اختر ثقل وحجم شحنتك الميدانية لتحديد السعر الاقتصادية لها:", ["📦 خفيفة", "📦 متوسطة", "📦 ثقيلة"])
            image_file = st.file_uploader("صورة الفاتورة أو الطلب (اختياري):", type=["jpg", "png", "jpeg"])
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            pay_opt = st.radio("💳 كيف تريد سداد قيمة التوصيل？", ["دفع نقدي كاش (عند الاستلام)", "خصم من نقاط البيع المعتمدة", "📱 عبر محفظة جيب الإلكترونية"])
            is_emergency = st.checkbox("🚨 هذا الطلب طارئ ومستعجل جداً وتريده الآن")
            if pay_opt == "📱 عبر محفظة جيب الإلكترونية":
                st.markdown("<div class='jeeb-panel'>📲 يرجى تحويل الرصيد لحساب جيب (541419) التابع لجايا لك، وأدخل رقم العملية بالأسفل.</div><br>", unsafe_allow_html=True)
                jeeb_tx = st.text_input("أدخل رقم إشعار عملية التحويل المالي للتأكيد:")
            st.markdown("</div>", unsafe_allow_html=True)

            # حساب التسعيرة بناء على نقطة كتاب الثابتة
            light_price = to_locations_db[to_loc]["light"]
            heavy_price = to_locations_db[to_loc]["heavy"]
            medium_price = int((light_price + heavy_price) / 2)
            final_cost = heavy_price if is_emergency else (light_price if "خفيفة" in weight_opt else (medium_price if "متوسطة" in weight_opt else heavy_price))
            display_type = "🚨 طوارئ مستعجلة" if is_emergency else f"عادي - {weight_opt}"

            st.markdown(f"<div class='price-tag'>💰 تكلفة التوصيل الإجمالية: {final_cost} ريال يمني</div><br>", unsafe_allow_html=True)

            # 🚨 تضخيم وتكبير زر الإرسال للعميل ليصبح ضخماً جداً ومميزاً باللون الأخضر
            st.markdown("<div class='big-confirm-btn'>", unsafe_allow_html=True)
            if st.button("🚀 إرسال وتأكيد الطلب نهائياً الآن"):
                if not c_name.strip() or not c_phone.isdigit() or len(c_phone) < 9:
                    st.error("❌ خطأ: يرجى كتابة الاسم ورقم الهاتف الصحيح المكون من 9 أرقام لتواصل المندوب.")
                else:
                    order_id = str(random.randint(100000, 999999))
                    saved_voice_path = ""
                    saved_img_path = ""
                    
                    current_time_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                    
                    if voice_file is not None:
                        saved_voice_path = os.path.join(VOICE_DIR, f"{order_id}.wav")
                        with open(saved_voice_path, "wb") as f:
                            f.write(voice_file.read())
                            
                    if image_file is not None:
                        i_ext = image_file.name.split(".")[-1].lower()
                        saved_img_path = os.path.join(IMAGE_DIR, f"{order_id}.{i_ext}")
                        with open(saved_img_path, "wb") as f:
                            f.write(image_file.getbuffer())

                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (order_id, c_name.strip(), c_phone.strip(), from_loc, to_loc, display_type, "بانتظار الموافقة", final_cost, "لم يحدد", pay_opt, user_notes, saved_voice_path, saved_img_path, current_time_str, "")
                        )
                        conn.commit()
                    
                    st.session_state.client_order_success = True
                    st.session_state.last_order_id = order_id
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    with client_sub_tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔍 استعلم عن شحنتك وحركتها فوراً")
        track_id = st.text_input("أدخل كود تتبع الشحنة الرقمي (مثال: 583921):", key="track_input_id").strip()
        
        if track_id:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM orders WHERE id=?", (track_id,))
                res = cursor.fetchone()
                
                if res:
                    status_text = res['status']
                    driver_code = res['driver']
                    driver_name = "لم يحدد بعد"
                    if driver_code != "لم يحدد":
                        cursor.execute("SELECT name FROM drivers WHERE id=?", (driver_code,))
                        d_res = cursor.fetchone()
                        if d_res:
                            driver_name = d_res['name']
                    
                    st.write("---")
                    st.info(f"👤 **صاحب الطلب:** {res['name']}")
                    st.warning(f"📍 **المسار:** من **{res['from_loc']}** إلى **{res['to_loc']}**")
                    st.info(f"📅 **وقت إرسال الطلب:** {res['order_time']}")
                    if res['delivery_time']:
                        st.success(f"⏱️ **وقت التسليم الفعلي:** {res['delivery_time']}")
                    st.success(f"📊 **حالة الشحنة الحالية:** {status_text}")
                    st.info(f"🛵 **المندوب المسؤول ميدانياً:** {driver_name}")
                    st.metric("المبلغ المطلوب تصفيتة", f"{res['cost']:,} ريال")
                else:
                    st.error("❌ عذراً، لم نجد أي شحنة مسجلة بهذا الكود الرقمي.")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 🛵 ج: واجهة المندوب المستقلة 
# -------------------------------------------------------------------------
elif st.session_state.current_role == "driver_portal":
    st.markdown("<h2 style='color:#1e293b;'>🛵 واجهة المندوب وكباتن الحركة الميدانية</h2>", unsafe_allow_html=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers")
        drvs = cursor.fetchall()
    
    if drvs:
        drvs_choices = {r['id']: f"{r['name']} - التغطية: {r['assigned_village']}" for r in drvs}
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        drv_col1, drv_col2 = st.columns(2)
        with drv_col1:
            active_driver_id = st.selectbox("اختر اسمك لتسجيل الدخول الفوري:", list(drvs_choices.keys()), format_func=lambda x: drvs_choices[x])
        with drv_col2:
            driver_password_input = st.text_input(f"🔐 أدخل كلمة السر التابعة لك:", type="password", key=f"pwd_drv_{active_driver_id}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if driver_password_input:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password, name FROM drivers WHERE id=?", (active_driver_id,))
                drv_auth = cursor.fetchone()
                
            if drv_auth and drv_auth['password'] == hash_password(driver_password_input):
                drv_actual_name = drv_auth['name']
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM orders WHERE driver=? AND status='جاري التوصيل' ORDER BY order_time DESC LIMIT 1", (active_driver_id,))
                    latest_mission = cursor.fetchone()
                
                if latest_mission:
                    st.markdown(f"""
                    <div class='card' style='border-right: 8px solid #0284c7; background-color: #f0fdfa;'>
                        <h4 style='color:#0284c7 !important; margin:0;'>🔔 تنبيه تكليف جديد صادر من الإدارة الآن:</h4>
                        <p style='margin:5px 0 0 0;'>تم إسناد الشحنة رقم <b>({latest_mission['id']})</b> لك المتوجهة إلى <b>{latest_mission['to_loc']}</b>. يرجى مراجعة التفاصيل أدناه وتأكيد التحرك الميداني.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM orders WHERE driver=? AND status='جاري التوصيل' ORDER BY order_time DESC", (active_driver_id,))
                    driver_missions = cursor.fetchall()
                
                if driver_missions:
                    st.warning(f"⚠️ كابتن {drv_actual_name}: لديك ({len(driver_missions)}) شحنات جارية قيد التوصيل والتصفية:")
                    for m in driver_missions:
                        st.markdown(f"""
                        <div class='card'>
                        <h4 style='color:#0284c7 !important;'>🔢 شحنة رقم: {m['id']}</h4>
                        <b>📅 وقت الطلب المعتمد:</b> {m['order_time']}<br>
                        <b>📍 المسار الجغرافي:</b> من [ {m['from_loc']} ] 👈 إلى [ {m['to_loc']} ]<br>
                        <b>👤 اسم الزبون:</b> {m['name']}<br>
                        <b>📞 هاتف العميل: <span style='color:green; font-weight:bold;'>{m['phone']}</span></b><br>
                        <b>💳 آلية السداد:</b> {m['payment_method']}<br>
                        <b>📝 ملاحظات الطلب:</b> {m['notes'] if m['notes'] else 'لا يوجد'}<br>
                        <h5 style='color:red !important;'>💰 الحساب المطلوب استلامه: {m['cost']:,} ريال</h5>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if m['voice_path'] and os.path.exists(m['voice_path']):
                            st.audio(m['voice_path'])
                        
                        if st.button(f"✅ تأكيد تسليم شحنة {m['id']} وتصفية المالي", key=f"drv_btn_{m['id']}"):
                            current_delivery_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE orders SET status='تم التسليم ✅', delivery_time=? WHERE id=?", (current_delivery_str, m['id']))
                                conn.commit()
                            
                            cust_msg = f"تم تسليم طلبك رقم ({m['id']}) وتصفية الحساب في ({current_delivery_str}). شكراً لتعاملك مع جايا لك!"
                            cust_wa_url = send_whatsapp_notification(m['phone'], cust_msg)
                            cust_sms_url = send_sms_notification(m['phone'], cust_msg)
                            
                            st.success("🎉 تم الإنهاء والتصفية وتسجيل وقت التسليم بنجاح!")
                            
                            col_d_notif1, col_d_notif2 = st.columns(2)
                            with col_d_notif1:
                                st.markdown(f"<div class='whatsapp-btn'><a href='{cust_wa_url}' target='_blank'>💬 إشعار واتساب للزبون</a></div>", unsafe_allow_html=True)
                            with col_d_notif2:
                                st.markdown(f"<div class='sms-btn'><a href='{cust_sms_url}'>✉️ رسالة نصية SMS للزبون</a></div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.info("🟢 لا توجد شحنات معلقة لك في الميدان حالياً. عمل ممتاز!")
            else:
                st.error("❌ خطأ: كلمة السر غير صحيحة أو غير متطابقة.")
    else:
        st.info("ℹ️ لا يوجد مناديب مسجلين في النظام حالياً.")

# -------------------------------------------------------------------------
# 💼 د: لوحة التحكم والمدير المركزي (جدول التفاصيل الكاملة)
# -------------------------------------------------------------------------
elif st.session_state.current_role == "manager_portal":
    st.markdown("<h2 style='color:#1e293b;'>💼 لوحة إدارة العمليات المركزية</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    password_input = st.text_input("🔑 أدخل كلمة مرور الإدارة المركزية للدخول لغرفة العمليات:", type="password", key="admin_pwd_main")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if password_input and check_admin_password(password_input):
        st.success("🔓 تم فتح البوابة والتحقق من صلاحيات المدير بنجاح.")

import menu_manager
menu_manager.show_menu_manager()
   
            if 'show_assignment_notif' not in st.session_state:
            st.session_state.show_assignment_notif = False
            st.session_state.saved_wa_url = ""
            st.session_state.saved_sms_url = ""
            st.session_state.saved_drv_name = ""
            st.session_state.saved_order_id = ""

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            st.markdown("### ⚙️ إعدادات النظام الحيوية")
            curr_adm_wa = get_admin_whatsapp()
            new_adm_wa = st.text_input("رقم هاتف المدير لاستقبال إشعارات طلبات الزبائن (9 أرقام):", value=curr_adm_wa)
            if st.button("💾 حفظ رقم المدير الجديد"):
                update_admin_whatsapp(new_adm_wa.strip())
                st.success("✅ تم تحديث وحفظ رقم الواتساب الخاص بالمدير بنجاح.")
            
            st.write("---")
            
            cursor.execute("SELECT * FROM orders")
            all_orders_for_stats = cursor.fetchall()
            delivered_revenue = sum(row['cost'] for row in all_orders_for_stats if row['status'] == "تم التسليم ✅")
            pending_count = sum(1 for row in all_orders_for_stats if row['status'] == "بانتظار الموافقة")
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("إجمالي الطلبات تاريخياً", f"{len(all_orders_for_stats)} طلب")
            m_col2.metric("طلبات معلقة جديدة", f"{pending_count} طلب")
            m_col3.metric("صافي الخزنة الميدانية", f"{delivered_revenue:,} ريال")
            st.markdown("</div>", unsafe_allow_html=True)

            st.write("---")
            
            st.markdown("### 📊 كشوفات وتقارير حركة الطلبات اليومية المتقدمة")
            manager_view_tab1, manager_view_tab2, manager_view_tab3 = st.tabs([
                "✨ 1. الطلبات اليومية الجديدة", 
                "✅ 2. كشف الطلبات المنجزة بالتفصيل",
                "🛠️ 3. إدارة المناديب والكباتن"
            ])
            
            with manager_view_tab1:
                st.markdown("#### 🔥 الطلبات الجديدة الواردة بكافة التفاصيل الحيوية للزبائن:")
                cursor.execute("SELECT * FROM orders WHERE status='بانتظار الموافقة' ORDER BY rowid DESC")
                new_orders = cursor.fetchall()
                
                if new_orders:
                    # 🚀 تم تجميع وإبراز كافة تفاصيل الزبون الجديد مباشرة وبشكل مقروء جداً للمدير هنا
                    new_orders_data = [{
                        "رقم الشحنة": row['id'],
                        "وقت وصول الطلب": row['order_time'],
                        "اسم العميل": row['name'],
                        "رقم الهاتف": row['phone'],
                        "نقطة الاستلام": row['from_loc'],
                        "قرية التوصيل": row['to_loc'],
                        "نوع وحجم الشحنة": row['type'],
                        "طريقة السداد": row['payment_method'],
                        "ملاحظات وتفاصيل طلب الزبون": row['notes'] if row['notes'] else "لا يوجد ملاحظات مكتوبة",
                        "قيمة التوصيل الميداني": f"{row['cost']:,} ريال"
                    } for row in new_orders]
                    st.dataframe(new_orders_data, use_container_width=True)
                    
                    st.markdown("#### 🎮 وحدة التوجيه والإسناد السريع للمناديب:")
                    assignable_ids = [r['id'] for r in new_orders]
                    selected_order_id = st.selectbox("اختر رقم الطلب المراد إسناده لكابتن الحركة الآن:", assignable_ids)
                    
                    cursor.execute("SELECT * FROM orders WHERE id=?", (selected_order_id,))
                    o_inf = cursor.fetchone()
                    
                    cursor.execute("SELECT * FROM drivers")
                    driver_rows_db = cursor.fetchall()
                    
                    if driver_rows_db:
                        driver_options = {r['id']: f"{r['name']} ({r['assigned_village']})" for r in driver_rows_db}
                        selected_driver_id = st.selectbox("اختر الكابتن الميداني المستهدف والمتاح للتوصيل:", list(driver_options.keys()), format_func=lambda x: driver_options[x])
                        
                        if st.button("⚡ اعتماد الشحنة وتجهيز أشعارات التوجيه الخارجية"):
                            cursor.execute("UPDATE orders SET status='جاري التوصيل', driver=? WHERE id=?", (selected_driver_id, selected_order_id))
                            conn.commit()
                            
                            cursor.execute("SELECT name, phone FROM drivers WHERE id=?", (selected_driver_id,))
                            drv_data_selected = cursor.fetchone()
                            
                            drv_msg = f"طلب جديد رقم ({selected_order_id}) من [{o_inf['from_loc']}] إلى [{o_inf['to_loc']}]. الزبون: {o_inf['name']}، هاتف: {o_inf['phone']}. الحساب: {o_inf['cost']} ريال. باشر فوراً."
                            
                            st.session_state.saved_wa_url = send_whatsapp_notification(drv_data_selected['phone'], drv_msg)
                            st.session_state.saved_sms_url = send_sms_notification(drv_data_selected['phone'], drv_msg)
                            st.session_state.saved_drv_name = drv_data_selected['name']
                            st.session_state.saved_order_id = selected_order_id
                            st.session_state.show_assignment_notif = True
                            st.rerun()
                    else:
                        st.error("❌ لا يوجد كباتن مسجلين حالياً بالموقع، اذهب لتبويب إدارة المناديب أولاً لإضافتهم.")
                else:
                    st.info("🟢 المنظومة نظيفة ومستقرة! لا توجد طلبات جديدة معلقة حالياً في المنظومة.")
                
                if st.session_state.show_assignment_notif:
                    st.markdown("---")
                    st.success(f"✅ تم تعميد الشحنة {st.session_state.saved_order_id} وإرسالها لصندوق بريد الكابتن {st.session_state.saved_drv_name} داخل واجهته بنجاح.")
                    st.markdown("##### 📢 أرسل أمر التكليف الخارجي لهاتف الكابتن الميداني عبر الموبايل الآن:")
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        st.markdown(f"<div class='whatsapp-btn'><a href='{st.session_state.saved_wa_url}' target='_blank'>💬 إرسال عبر الواتساب للمندوب</a></div>", unsafe_allow_html=True)
                    with c_col2:
                        st.markdown(f"<div class='sms-btn'><a href='{st.session_state.saved_sms_url}'>✉️ إرسال عبر رسالة نصية SMS</a></div>", unsafe_allow_html=True)
                    
                    if st.button("Clear 🧹 إخفاء خيارات هذا التكليف لمتابعة بقية الطلبات"):
                        st.session_state.show_assignment_notif = False
                        st.rerun()

            with manager_view_tab2:
                st.markdown("#### ✅ الكشف والأرشيف الكامل لكافة الطلبات اليومية المنجزة والمصفاة ماليّاً:")
                cursor.execute("SELECT * FROM orders WHERE status='تم التسليم ✅' ORDER BY rowid DESC")
                completed_orders = cursor.fetchall()
                
                if completed_orders:
                    cursor.execute("SELECT id, name FROM drivers")
                    drivers_names_map = {r['id']: r['name'] for r in cursor.fetchall()}
                    
                    completed_orders_data = [{
                        "رقم الشحنة": row['id'],
                        "وقت الطلب من الزبون": row['order_time'],
                        "وقت التسليم الفعلي": row['delivery_time'],
                        "الكابتن المنجز": drivers_names_map.get(row['driver'], row['driver']),
                        "اسم العميل": row['name'],
                        "هاتف العميل": row['phone'],
                        "منطقة الاستلام": row['from_loc'],
                        "منطقة التسليم": row['to_loc'],
                        "آلية الدفع والتصفية": row['payment_method'],
                        "المبلغ المصفى": f"{row['cost']:,} ريال"
                    } for row in completed_orders]
                    
                    st.dataframe(completed_orders_data, use_container_width=True)
                else:
                    st.info("ℹ️ لم يتم تصفية وتسليم أي طلبات في الميدان حتى هذه اللحظة.")

            with manager_view_tab3:
                st.markdown("### 🛵 لوحة التحكم في المناديب وكباتن الحركة")
                m_drv_tab1, m_drv_tab2 = st.tabs(["➕ إضافة مندوب جديد", "📋 إدارة وتعديل الكباتن الحاليين"])
                
                with m_drv_tab1:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    new_d_id = st.text_input("كود المعرف للمندوب (مثال: DRV-103):").strip()
                    new_d_name = st.text_input("اسم الكابتن الكامل:").strip()
                    new_d_phone = st.text_input("رقم هاتف المندوب (9 أرقام):", max_chars=9).strip()
                    new_d_village = st.selectbox("منطقة أو قرية التغطية الرئيسية للتسليم:", list(to_locations_db.keys()), key="new_d_village")
                    new_d_pass = st.text_input("تعيين كلمة السر الخاصة بالدخول للمندوب:", type="password", value="1234")
                    
                    if st.button("✨ تسجيل واعتماد المندوب في النظام"):
                        if not new_d_id or not new_d_name or not new_d_phone.isdigit() or len(new_d_phone) < 9:
                            st.error("❌ يرجى تعبئة جميع حقول المندوب ورقم الهاتف بشكل صحيح المكون من 9 أرقام.")
                        else:
                            cursor.execute("SELECT id FROM drivers WHERE id=?", (new_d_id,))
                            if cursor.fetchone():
                                st.error("❌ كود معرف المندوب هذا مسجل مسبقاً لمندوب آخر.")
                            else:
                                hashed_drv_pwd = hash_password(new_d_pass)
                                cursor.execute("INSERT INTO drivers VALUES (?, ?, ?, ?, ?)", (new_d_id, new_d_name, new_d_phone, new_d_village, hashed_drv_pwd))
                                conn.commit()
                                st.success(f"🎉 تم تسجيل المندوب {new_d_name} بنجاح!")
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with m_drv_tab2:
                    cursor.execute("SELECT * FROM drivers")
                    current_drivers_list = cursor.fetchall()
                    if current_drivers_list:
                        for drv_row in current_drivers_list:
                            st.markdown(f"""
                            <div class='card' style='border-right: 5px solid #16a34a;'>
                            <b>🪪 كود المندوب:</b> {drv_row['id']} | <b>👤 الاسم:</b> {drv_row['name']}<br>
                            <b>📞 رقم الهاتف الميداني:</b> {drv_row['phone']} | <b>📍 نطاق التغطية:</b> {drv_row['assigned_village']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            drv_edit_col1, drv_edit_col2 = st.columns(2)
                            with drv_edit_col1:
                                new_village_edit = st.selectbox(f"تعديل تغطية {drv_row['name']}:", list(to_locations_db.keys()), index=list(to_locations_db.keys()).index(drv_row['assigned_village']) if drv_row['assigned_village'] in to_locations_db else 0, key=f"edit_v_{drv_row['id']}")
                                if st.button(f"⚙️ حفظ تعديل المنطقة لـ {drv_row['id']}", key=f"save_v_btn_{drv_row['id']}"):
                                    cursor.execute("UPDATE drivers SET assigned_village=? WHERE id=?", (new_village_edit, drv_row['id']))
                                    conn.commit()
                                    st.success("✅ تم تعديل نطاق التغطية بنجاح.")
                                    st.rerun()
                            with drv_edit_col2:
                                if st.button(f"❌ حذف المندوب {drv_row['name']} نهائياً", key=f"del_drv_{drv_row['id']}"):
                                    cursor.execute("DELETE FROM drivers WHERE id=?", (drv_row['id'],))
                                    conn.commit()
                                    st.success("🗑️ تم حذف المندوب بنجاح من قاعدة البيانات.")
                                    st.rerun()
                    else:
                        st.info("ℹ️ لا يوجد مناديب مسجلين لتعديلهم حالياً.")
                        
