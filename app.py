import streamlit as st
import sqlite3
import random
import os
import hashlib
import urllib.parse
from datetime import datetime

# ==========================================
# 🛑 رفع حد رفع الملفات والصوت إلى 200 ميجابايت مع الحماية
# ==========================================
st.config.set_option("server.maxUploadSize", 200)

# ==========================================
# 📂 المجلدات المخصصة لحفظ الصور والأصوات
# ==========================================
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
    conn = sqlite3.connect('jaya_lak.db', timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def make_backup():
    try:
        today_str = datetime.now().strftime("%Y_%m_%d")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{today_str}.db")
        if not os.path.exists(backup_file) and os.path.exists('jaya_lak.db'):
            import shutil
            shutil.copyfile('jaya_lak.db', backup_file)
    except Exception as e:
        pass

def init_db():
    with get_db_connection() as conn:
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
                image_path TEXT
            )
        ''')
        
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'voice_path' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN voice_path TEXT DEFAULT ''")
        if 'image_path' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN image_path TEXT DEFAULT ''")
            
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
        else:
            cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (default_hashed,))
            
        # إضافة إعدادات رقم المدير الافتراضي لإشعارات الواتساب (يمكن تعديله من لوحة التحكم)
        cursor.execute("SELECT value FROM settings WHERE key='admin_whatsapp'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings VALUES ('admin_whatsapp', '770000000')")
            
        d_pass = hash_password("1234")
        cursor.execute("SELECT COUNT(*) FROM drivers")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO drivers VALUES ('DRV-101', 'كابتن علي اليماني', '771111111', 'مدينة كتاب', ?)", (d_pass,))
            cursor.execute("INSERT INTO drivers VALUES ('DRV-102', 'كابتن محمد الحاشدي', '772222222', 'قرى الصفي', ?)", (d_pass,))
        else:
            cursor.execute("UPDATE drivers SET password=? WHERE id IN ('DRV-101', 'DRV-102')", (d_pass,))
            
        conn.commit()
    make_backup()

init_db()

def check_admin_password(input_pwd):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        saved_hash = cursor.fetchone()[0]
    return saved_hash == hash_password(input_pwd)

def update_admin_password(new_pwd):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        new_hash = hash_password(new_pwd)
        cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_hash,))
        conn.commit()

def get_admin_whatsapp():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='admin_whatsapp'")
        res = cursor.fetchone()
        return res[0] if res else "770000000"

def update_admin_whatsapp(new_phone):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value=? WHERE key='admin_whatsapp'", (new_phone,))
        conn.commit()

# دالة ذكية لتوليد رابط الإرسال المباشر للواتساب
def send_whatsapp_notification(phone, message):
    if phone.startswith("0"):
        phone = phone[1:]
    if not phone.startswith("967"):
        phone = "967" + phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone}?text={encoded_msg}"

def play_sound_js(sound_url):
    return f"""
    <audio autoplay>
        <source src="{sound_url}" type="audio/mp3">
    </audio>
    """

# ==========================================
# 🎨 واجهة وتصميم التطبيق والخلفية الميدانية باللون الأسود
# ==========================================
st.set_page_config(
    page_title="مؤسسة جايا لك للتوصيل الذكي",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.components.v1.html("""
<script>
window.addEventListener('offline', function(e) {
    alert('⚠️ تنبيه: انقطع الاتصال بالإنترنت لديك حالياً! يرجى عدم إغلاق الصفحة لضمان حفظ بيانات الشحنة عند عودة الشبكة.');
});
</script>
""", height=0)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;600;700&display=swap');
    
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    [data-testid="stViewerToolbar"] {display: none !important;}
    iframe[title="Manage app"] {display: none !important;}
    div[data-testid="stManageAppButton"] {display: none !important;}
    button[title="Manage app"] {display: none !important;}
    .st-emotion-cache-1lb4v3s {display: none !important;}
    
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), 
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
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; background-color: rgba(255, 255, 255, 0.85); padding: 8px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: rgba(241, 245, 249, 0.95); border-radius: 8px; padding: 10px 20px; font-weight: bold; border: 1px solid #cbd5e1;
    }
    .stTabs [aria-selected="true"] { background-color: #16a34a !important; border-color: #16a34a !important; }
    .stTabs [aria-selected="true"] span { color: white !important; }
    
    .card { 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 22px; 
        border-radius: 16px; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1); 
        margin-bottom: 18px; 
        border: 1px solid rgba(255, 255, 255, 0.8); 
        backdrop-filter: blur(4px);
    }
    
    .voice-box { border: 2px dashed #16a34a; padding: 20px; background-color: rgba(240, 253, 244, 0.95); border-radius: 16px; margin-bottom: 15px; text-align: center; }
    .jeeb-panel { background-color: rgba(240, 253, 244, 0.95); border-right: 6px solid #0d9488; padding: 15px; border-radius: 8px; font-weight: bold; }
    .success-panel { background-color: rgba(240, 253, 244, 0.95); border-right: 6px solid #16a34a; padding: 15px; border-radius: 8px; }
    .price-tag { background-color: rgba(239, 246, 255, 0.95); color: #1d4ed8 !important; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 22px; border: 2px dashed #3b82f6; }
    .price-tag * { color: #1d4ed8 !important; }
    
    .big-driver-btn button, .big-send-btn button, .whatsapp-btn a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 65px !important;
        background-color: #16a34a !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        color: white !important;
        text-decoration: none !important;
        box-shadow: 0 10px 15px -3px rgba(22, 163, 74, 0.3) !important;
    }
    .whatsapp-btn a { background-color: #25D366 !important; box-shadow: 0 10px 15px -3px rgba(37, 211, 102, 0.3) !important; }
    
    .stSelectbox div[data-baseweb="select"] { font-size: 18px !important; }
    h1, h2, h3, h4, h5, h6, label, p, span, li, td, th { color: #000000 !important; font-weight: 700 !important; }
    input, select, textarea { color: #000000 !important; font-weight: bold !important; font-size: 17px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>📦 مؤسسة جَايَا لَك للتوصيل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; font-weight: bold;'>الخدمة الأسرع لتوصيل المواد الغذائية والطلبات - كِتَاب والقرى المجاورة</p>", unsafe_allow_html=True)
st.write("---")

tab_client, tab_track, tab_driver, tab_manager = st.tabs(["👤 بوابة العميل / إرسال طلب", "🔍 تتبع حالة الشحنة", "🛵 واجهة المندوب الميداني", "💼 لوحة التحكم والمدير"])

from_locations_db = {
    "المركز الرئيسي كتاب": {"light": 300, "heavy": 500},
    "مدينة كتاب": {"light": 300, "heavy": 500},
    "قرية الحزة": {"light": 300, "heavy": 500},
    "قرية رباط القلعة": {"light": 400, "heavy": 600},
    "قرية المنزل": {"light": 500, "heavy": 700},
    "قرية دخلة المسالمة": {"light": 500, "heavy": 700},
    "قرية شهصان": {"light": 500, "heavy": 700},
    "قرية الدريعاء": {"light": 500, "heavy": 700},
    "قرية الخربة": {"light": 500, "heavy": 700},
    "قرية رباط Mصرع": {"light": 700, "heavy": 1200},
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

to_locations_db = {k: v for k, v in from_locations_db.items() if k != "المركز الرئيسي كتاب"}

# -------------------------------------------------------------------------
# 1. بوابة العميل - نموذج إرسال طلب
# -------------------------------------------------------------------------
with tab_client:
    if 'client_order_success' not in st.session_state:
        st.session_state.client_order_success = False
        st.session_state.last_order_id = ""

    if st.session_state.client_order_success:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.success(f"🎉 تم استلام طلبك بنجاح! كود تتبع شحنتك الميداني هو: {st.session_state.last_order_id}")
        
        # رسالة منبثقة للعميل لتنبيه المدير فوراً خارج التطبيق
        admin_tel = get_admin_whatsapp()
        client_msg = f"🚨 تنبيه لإدارة جايا لك: قمت بإرسال طلبية جديدة في النظام برقم ({st.session_state.last_order_id})، يرجى مراجعتها وتعميد المندوب."
        wa_url = send_whatsapp_notification(admin_tel, client_msg)
        
        st.markdown(f"""
        <div class='whatsapp-btn' style='text-align:center;'>
            <a href="{wa_url}" target="_blank">💬 اضغط هنا لتنبيه الإدارة الفوري عبر الواتساب خارج التطبيق</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 إرسال طلب شحنة جديدة أخرى"):
            st.session_state.client_order_success = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#16a34a;'>👤 بياناتك الشخصية</h3>", unsafe_allow_html=True)
        cl_col1, cl_col2 = st.columns(2)
        with cl_col1:
            c_name = st.text_input("اكتب اسمك الكامل هنا *", placeholder="مثال: أحمد حازم...", key="c_name")
        with cl_col2:
            c_phone = st.text_input("رقم هاتفك للتواصل (9 أرقام) *", max_chars=9, placeholder="77XXXXXXX", key="c_phone")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#16a34a;'>📍 مسار التوصيل</h3>", unsafe_allow_html=True)
        loc_col1, loc_col2 = st.columns(2)
        with loc_col1:
            from_loc = st.selectbox("مكان استلام البضاعة (من أين؟) *", list(from_locations_db.keys()))
        with loc_col2:
            to_loc = st.selectbox("مكان تسليم البضاعة لبيتك (إلى أين؟) *", list(to_locations_db.keys()))
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='voice-box'>", unsafe_allow_html=True)
        st.markdown("<h3>🎙️ سجل تفاصيل طلبك بصوتك مباشرة</h3>", unsafe_allow_html=True)
        voice_file = st.audio_input("اضغط لبدء تسجيل صوتك المباشر:")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>✏️ حجم وتفاصيل الشحنة</h3>", unsafe_allow_html=True)
        user_notes = st.text_area("إذا تريد كتابة ملاحظة إضافية للمندوب اكتبها هنا:", placeholder="مثال: كرتون صلصة، كيس دقيق...")
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

        light_price = max(from_locations_db[from_loc]["light"], to_locations_db[to_loc]["light"])
        heavy_price = max(from_locations_db[from_loc]["heavy"], to_locations_db[to_loc]["heavy"])
        medium_price = int((light_price + heavy_price) / 2)
        final_cost = heavy_price if is_emergency else (light_price if "خفيفة" in weight_opt else (medium_price if "متوسطة" in weight_opt else heavy_price))
        display_type = "🚨 طوارئ مستعجلة" if is_emergency else f"عادي - {weight_opt}"

        st.markdown(f"<div class='price-tag'>💰 تكلفة التوصيل الإجمالية: {final_cost} ريال يمني</div><br>", unsafe_allow_html=True)

        st.markdown("<div class='big-send-btn'>", unsafe_allow_html=True)
        if st.button("🚀 إرسال وتأكيد الطلب نهائياً الآن"):
            if not c_name.strip() or not c_phone.isdigit() or len(c_phone) < 9:
                st.error("❌ خطأ: يرجى كتابة الاسم ورقم الهاتف الصحيح المكون من 9 أرقام لتواصل المندوب.")
            elif from_loc == to_loc:
                st.error("❌ تنبيه مسار جغرافي خاطئ: نقطة الاستلام ونقطة التسليم متطابقتان.")
            else:
                order_id = str(random.randint(100000, 999999))
                saved_voice_path = ""
                saved_img_path = ""
                
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
                        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (order_id, c_name.strip(), c_phone.strip(), from_loc, to_loc, display_type, "بانتظار الموافقة", final_cost, "لم يحدد", pay_opt, user_notes, saved_voice_path, saved_img_path)
                    )
                    conn.commit()
                
                st.session_state.client_order_success = True
                st.session_state.last_order_id = order_id
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. واجهة تتبع حالة الشحنة للعميل
# -------------------------------------------------------------------------
with tab_track:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 استعلم عن شحنتك وحركتها فوراً")
    track_id = st.text_input("أدخل كود تتبع الشحنة الرقمي (مثال: 583921):", key="track_input_id").strip()
    
    if track_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, from_loc, to_loc, status, driver, cost, phone FROM orders WHERE id=?", (track_id,))
            res = cursor.fetchone()
            
            if res:
                status_text = res[3]
                driver_code = res[4]
                driver_name = "لم يحدد بعد"
                if driver_code != "لم يحدد":
                    cursor.execute("SELECT name FROM drivers WHERE id=?", (driver_code,))
                    d_res = cursor.fetchone()
                    if d_res:
                        driver_name = d_res[0]
                
                st.write("---")
                st.info(f"👤 **صاحب الطلب:** {res[0]}")
                st.warning(f"📍 **المسار:** من **{res[1]}** إلى **{res[2]}**")
                st.success(f"📊 **حالة الشحنة الحالية:** {status_text}")
                st.info(f"🛵 **المندوب المسؤول ميدانياً:** {driver_name}")
                st.metric("المبلغ المطلوب تصفيتة", f"{res[5]:,} ريال")
            else:
                st.error("❌ عذراً، لم نجد أي شحنة مسجلة بهذا الكود الرقمي.")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 3. واجهة المندوب الميداني
# -------------------------------------------------------------------------
with tab_driver:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🛵 واجهة لوجستيات المندوب وكباتن الحركة")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers")
        drvs = cursor.fetchall()
    
    if drvs:
        drvs_choices = {r[0]: f"{r[1]} - التغطية: {r[3]}" for r in drvs}
        drv_col1, drv_col2 = st.columns(2)
        with drv_col1:
            active_driver_id = st.selectbox("اختر اسمك لتسجيل الدخول الفوري:", list(drvs_choices.keys()), format_func=lambda x: drvs_choices[x])
        with drv_col2:
            driver_password_input = st.text_input(f"🔐 أدخل كلمة السر:", type="password", key=f"pwd_drv_{active_driver_id}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if driver_password_input:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM drivers WHERE id=?", (active_driver_id,))
                saved_drv_hash = cursor.fetchone()[0]
                
                if saved_drv_hash == hash_password(driver_password_input):
                    cursor.execute("SELECT * FROM orders WHERE driver=? AND status='جاري التوصيل'", (active_driver_id,))
                    driver_missions = cursor.fetchall()
                    
                    if driver_missions:
                        st.warning(f"⚠️ لديك ({len(driver_missions)}) شحنات جارية قيد التوصيل:")
                        for m in driver_missions:
                            st.markdown(f"""
                            <div class='card'>
                            <h4 style='color:#0284c7 !important;'>🔢 شحنة رقم: {m[0]}</h4>
                            <b>📍 المسار الجغرافي:</b> من [ {m[3]} ] 👈 إلى [ {m[4]} ]<br>
                            <b>👤 اسم الزبون:</b> {m[1]}<br>
                            <b>📞 هاتف العميل: <span style='color:green; font-weight:bold;'>{m[2]}</span></b><br>
                            <b>💳 آلية السداد:</b> {m[9]}<br>
                            <h5 style='color:red !important;'>💰 الحساب المطلوب استلامه: {m[7]:,} ريال</h5>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if m[11] and os.path.exists(m[11]):
                                st.audio(m[11])
                            
                            # زر التحديث داخل النظام + إشعار الواتساب التلقائي للزبون خارج النظام
                            st.markdown("<div class='big-driver-btn'>", unsafe_allow_html=True)
                            if st.button(f"✅ تأكيد تسليم شحنة {m[0]} وتصفية المالي", key=f"drv_btn_{m[0]}"):
                                cursor.execute("UPDATE orders SET status='تم التسليم ✅' WHERE id=?", (m[0],))
                                conn.commit()
                                
                                # توليد رابط إشعار تسليم الشحنة للعميل على الواتساب خارج التطبيق
                                cust_msg = f"🎉 عميلنا العزيز ({m[1]}): تم تسليم شحنتك الميدانية رقم ({m[0]}) وتصفية حساب التوصيل بنجاح بواسطة مندوب جايا لك. شكراً لك ونحن في خدمتك دائماً!"
                                cust_wa_url = send_whatsapp_notification(m[2], cust_msg)
                                
                                st.success("🎉 تم الإنهاء والتصفية في النظام!")
                                st.markdown(f"""
                                <div class='whatsapp-btn' style='text-align:center;'>
                                    <a href="{cust_wa_url}" target="_blank">💬 اضغط هنا لإرسال إشعار تسليم الشحنة للزبون عبر الواتساب خارج التطبيق</a>
                                </div>
                                """, unsafe_allow_html=True)
                            st.markdown("</div><br>", unsafe_allow_html=True)
                    else:
                        st.info("🟢 لا توجد شحنات معلقة لك في الميدان حالياً.")
                else:
                    st.error("❌ خطأ: كلمة السر غير صحيحة.")
    else:
        st.info("ℹ️ لا يوجد مناديب مسجلين في النظام.")

# -------------------------------------------------------------------------
# 4. لوحة تحكم الإدارة
# -------------------------------------------------------------------------
with tab_manager:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("💼 غُرفة العمليات والتحكم المركزي")
    adm_col1, _ = st.columns([2, 1])
    with adm_col1:
        password_input = st.text_input("🔑 أدخل كلمة مرور الإدارة المركزية:", type="password", key="admin_pwd_main")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if password_input and check_admin_password(password_input):
        st.success("🔓 تم فتح البوابة بنجاح.")
        
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
            order_rows = cursor.fetchall()
            cursor.execute("SELECT * FROM drivers")
            driver_rows_db = cursor.fetchall()
            
            drivers_dict = {r[0]: {"name": r[1], "phone": r[2], "village": r[3]} for r in driver_rows_db}
            orders_db = []
            delivered_revenue = 0
            pending_orders = 0
            
            for r in order_rows:
                if r[6] == "بانتظار الموافقة":
                    pending_orders += 1
                drv_info = drivers_dict.get(r[8], {"name": "لم يحدد", "phone": "-"})
                orders_db.append({
                    "رقم الشحنة": r[0], "العميل": r[1], "الهاتف": r[2], "من": r[3], "إلى": r[4], 
                    "الحالة": r[6], "التكلفة": r[7], "المندوب": drv_info["name"]
                })
                if r[6] == "تم التسليم ✅":
                    delivered_revenue += r[7]
                    
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("إجمالي الطلبات", f"{len(orders_db)} طلبات")
            m_col2.metric("طلبات معلقة", f"{pending_orders} طلبات")
            m_col3.metric("صافي الخزنة الميدانية", f"{delivered_revenue:,} ريال")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.markdown("#### 🎮 وحدة التوجيه والإسناد الفوري للمناديب عبر الواتساب")
            assignable_orders = [o["رقم الشحنة"] for o in orders_db if o["الحالة"] == "بانتظار الموافقة"]
            
            if assignable_orders:
                selected_order_id = st.selectbox("اختر رقم الطلب لتوجيهه للمندوب:", assignable_orders)
                cursor.execute("SELECT to_loc, name, phone, cost, from_loc FROM orders WHERE id=?", (selected_order_id,))
                o_inf = cursor.fetchone()
                
                if driver_rows_db:
                    driver_options = {r[0]: f"{r[1]} ({r[3]})" for r in driver_rows_db}
                    selected_driver_id = st.selectbox("اختر الكابتن الميداني المستهدف:", list(driver_options.keys()), format_func=lambda x: driver_options[x])
                else:
                    selected_driver_id = None
                
                if st.button("⚡ اعتماد الشحنة وتجهيز إشعار المندوب الخارجي") and selected_driver_id:
                    cursor.execute("UPDATE orders SET status='جاري التوصيل', driver=? WHERE id=?", (selected_driver_id, selected_order_id))
                    conn.commit()
                    
                    # جلب بيانات هاتف المندوب المختار لإرسال رسالة التكليف له على الواتساب
                    cursor.execute("SELECT name, phone FROM drivers WHERE id=?", (selected_driver_id,))
                    drv_data_selected = cursor.fetchone()
                    
                    drv_msg = f"🛵 كابتن {drv_data_selected[0]} المحترم: تم إسناد شحنة ميدانية جديدة لك برقم ({selected_order_id}) من [ {o_inf[4]} ] إلى [ {o_inf[0]} ]. الزبون: {o_inf[1]}، هاتف: {o_inf[2]}. الحساب المطلوب تصفيتة: {o_inf[3]} ريال يمني. يرجى المباشرة فوراً."
                    drv_wa_url = send_whatsapp_notification(drv_data_selected[1], drv_msg)
                    
                    st.success(f"✅ تم تعميد الشحنة {selected_order_id} في قاعدة البيانات.")
                    st.markdown(f"""
                    <div class='whatsapp-btn' style='text-align:center;'>
                        <a href="{drv_wa_url}" target="_blank">💬 اضغط هنا لإرسال الشحنة لهاتف المندوب على الواتساب خارج التطبيق فوراً</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("🟢 لا توجد أي طلبات جديدة معلقة حالياً.")
