import streamlit as st
import sqlite3
import random
import os
import hashlib
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
# 🛠️ دالات الأمان والتشفير المحسنة وقاعدة البيانات
# ==========================================

def hash_password(password):
    # 🔒 إضافة ملح أمني معقد (Salt) لحماية كلمات المرور من التخمين
    SECRET_SALT = "JayaLak_Secure_2026_@Key"
    salted_pass = password + SECRET_SALT
    return hashlib.sha256(salted_pass.encode()).hexdigest()

def get_db_connection():
    # 💡 حل مشكلة قفل قاعدة البيانات بالتزامن وزيادة وقت الانتظار وتفعيل WAL
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
    # 💾 استخدام "with" لضمان إغلاق قاعدة البيانات تلقائياً وتفادي تسريب الذاكرة
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
        
        # 🔑 تحديث وضمان مزامنة كلمة المرور المعتمدة admin123 بالنظام الأمني الجديد تلقائياً
        default_hashed = hash_password("admin123")
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings VALUES ('admin_password', ?)", (default_hashed,))
        else:
            cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (default_hashed,))
            
        # مزامنة كباتن الحركة الافتراضيين مع الـ Salt الجديد
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
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    /* 🔒 إخفاء أيقونة جيتهاب (القط الأسود)، القائمة، والأزرار العلوية تماماً لحماية البيانات */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
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
    
    .big-driver-btn button, .big-send-btn button {
        width: 100% !important;
        height: 70px !important;
        background-color: #16a34a !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 15px -3px rgba(22, 163, 74, 0.3) !important;
    }
    .big-driver-btn button div *, .big-send-btn button div * { color: white !important; }
    
    .stSelectbox div[data-baseweb="select"] { font-size: 18px !important; }
    
    h1, h2, h3, h4, h5, h6, label, p, span, li, td, th { color: #000000 !important; font-weight: 700 !important; }
    input, select, textarea { color: #000000 !important; font-weight: bold !important; font-size: 17px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>📦 مؤسسة جَايَا لَك للتوصيل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; font-weight: bold;'>الخدمة الأسرع لتوصيل المواد الغذائية والطلبات - كِتَاب</p>", unsafe_allow_html=True)
st.write("---")

tab_client, tab_track, tab_driver, tab_manager = st.tabs(["👤 بوابة العميل / إرسال طلب", "🔍 تتبع حالة الشحنة", "🛵 واجهة المندوب الميداني", "💼 لوحة التحكم والمدير"])

# 🗺️ قاعدة البيانات الجغرافية المعدلة (تم حذف المركز الرئيسي كتاب بناء على طلبك)
villages_db = {
    "مدينة كتاب": {"light": 300, "heavy": 500},
    "قرية الحزة": {"light": 300, "heavy": 500},
    "قرية رباط القلعة": {"light": 400, "heavy": 600},
    "قرية المنزل": {"light": 500, "heavy": 700},
    "قرية دخلة المسالمة": {"light": 500, "heavy": 700},
    "قرية شهصان": {"light": 500, "heavy": 700},
    "قرية الدريعاء": {"light": 500, "heavy": 700},
    "قرية الخربة": {"light": 500, "heavy": 700},
    "قرية رباط المصرع": {"light": 700, "heavy": 1200},
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
# 1. بوابة العميل - نموذج إرسال طلب
# -------------------------------------------------------------------------
with tab_client:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#16a34a;'>👤 بياناتك الشخصية</h3>", unsafe_allow_html=True)
    
    # 📱 تنظيم المربعات بشكل عرضي متناسق للهواتف
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
        from_loc = st.selectbox("مكان استلام البضاعة (من أين؟) *", list(villages_db.keys()))
    with loc_col2:
        to_loc = st.selectbox("مكان تسليم البضاعة لبيتك (إلى أين؟) *", list(villages_db.keys()))
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='voice-box'>", unsafe_allow_html=True)
    st.markdown("<h3>🎙️ سجل تفاصيل طلبك بصوتك مباشرة</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px; font-weight:normal;'>اضغط على زر المايك بالأسفل وتكلم فوراً لتخبرنا بالمواد والطلبات التي تريدها:</p>", unsafe_allow_html=True)
    voice_file = st.audio_input("اضغط لبدء تسجيل صوتك المباشر:")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>✏️ حجم وتفاصيل الشحنة</h3>", unsafe_allow_html=True)
    
    user_notes = st.text_area("إذا تريد كتابة ملاحظة إضافية للمندوب اكتبها هنا:", placeholder="مثال: كرتون صلصة، كيس دقيق...")
    
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        weight_opt = st.selectbox("اختر ثقل وحجم شحنتك الميدانية لتحديد السعر الاقتصادية لها:", ["📦 خفيفة", "📦 متوسطة", "📦 ثقيلة"])
    with opt_col2:
        image_file = st.file_uploader("صورة الفاتورة أو الطلب (اختياري):", type=["jpg", "png", "jpeg"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    pay_opt = st.radio("💳 كيف تريد سداد قيمة التوصيل؟", ["دفع نقدي كاش (عند الاستلام)", "خصم من نقاط البيع المعتمدة", "📱 عبر محفظة جيب الإلكترونية"])
    is_emergency = st.checkbox("🚨 هذا الطلب طارئ ومستعجل جداً وتريده الآن")
    
    if pay_opt == "📱 عبر محفظة جيب الإلكترونية":
        st.markdown("<div class='jeeb-panel'>📲 يرجى تحويل الرصيد لحساب جيب (541419) التابع لجايا لك، وأدخل رقم العملية بالأسفل.</div><br>", unsafe_allow_html=True)
        jeeb_tx = st.text_input("أدخل رقم إشعار عملية التحويل المالي للتأكيد:")
    st.markdown("</div>", unsafe_allow_html=True)

    light_price = max(villages_db[from_loc]["light"], villages_db[to_loc]["light"])
    heavy_price = max(villages_db[from_loc]["heavy"], villages_db[to_loc]["heavy"])
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
            allowed_exts = ["jpg", "jpeg", "png", "wav", "mp3", "ogg"]
            v_ext = voice_file.name.split(".")[-1].lower() if voice_file else "wav"
            i_ext = image_file.name.split(".")[-1].lower() if image_file else None
            
            if image_file and i_ext not in allowed_exts:
                st.error("❌ غير مسموح برفع هذا النوع من الملفات الخبيثة!")
                st.stop()

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM orders WHERE name=? AND phone=? AND from_loc=? AND to_loc=? AND status='بانتظار الموافقة'",
                    (c_name.strip(), c_phone.strip(), from_loc, to_loc)
                )
                duplicate_check = cursor.fetchone()
                
                if duplicate_check:
                    st.error(f"⚠️ تنبيه أمني للعميل: لقد قمت بإرسال هذه الطلبية بالفعل وهي معلقة لدينا برقم ({duplicate_check[0]})! لمنع التكرار، لا حاجة لإرسالها مرة أخرى وسيتصل بك المندوب فوراً.")
                else:
                    # 🔢 كود التتبع معدل ليكون أرقام فقط مكونة من 6 خانات بناءً على طلبك
                    order_id = str(random.randint(100000, 999999))
                    saved_voice_path = ""
                    saved_img_path = ""
                    
                    if voice_file is not None:
                        saved_voice_path = os.path.join(VOICE_DIR, f"{order_id}.{v_ext}")
                        with open(saved_voice_path, "wb") as f:
                            f.write(voice_file.read())
                            
                    if image_file is not None:
                        saved_img_path = os.path.join(IMAGE_DIR, f"{order_id}.{i_ext}")
                        with open(saved_img_path, "wb") as f:
                            f.write(image_file.getbuffer())

                    cursor.execute(
                        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (order_id, c_name.strip(), c_phone.strip(), from_loc, to_loc, display_type, "بانتظار الموافقة", final_cost, "لم يحدد", pay_opt, user_notes, saved_voice_path, saved_img_path)
                    )
                    conn.commit()
                    st.balloons()
                    st.markdown(f"<div class='success-panel'>🎉 تم استلام طلبك بنجاح يا غالي! يرجى حفظ كود تتبع شحنتك المكون من أرقام: <b style='font-size:24px; color:#1d4ed8;'>{order_id}</b></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. واجهة تتبع حالة الشحنة للعميل
# -------------------------------------------------------------------------
with tab_track:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 استعلم عن شحنتك وحركتها فوراً")
    
    t_col1, _ = st.columns([2, 1])
    with t_col1:
        track_id = st.text_input("أدخل كود تتبع الشحنة الرقمي (مثال: 583921):", key="track_input_id").strip()
    
    if track_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, from_loc, to_loc, status, driver, cost FROM orders WHERE id=?", (track_id,))
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
                
                if "تم التسليم" in status_text:
                    st.components.v1.html(play_sound_js("https://assets.mixkit.co/active_storage/sfx/2019/2019-84.wav"), height=0)
                    st.balloon()
                    
                st.info(f"🛵 **المندوب المسؤول ميدانياً:** {driver_name}")
                st.metric("المبلغ المطلوب تصفيتة", f"{res[5]:,} ريال يمني")
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
        drvs_choices = {r[0]: f"{r[1]} - التغطية الميدانية: {r[3]}" for r in drvs}
        
        drv_col1, drv_col2 = st.columns(2)
        with drv_col1:
            active_driver_id = st.selectbox("اختر اسمك لتسجيل الدخول الفوري:", list(drvs_choices.keys()), format_func=lambda x: drvs_choices[x])
        with drv_col2:
            driver_password_input = st.text_input(f"🔐 أدخل كلمة السر الخاصة بك يا كابتن:", type="password", key=f"pwd_drv_{active_driver_id}")
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
                        st.components.v1.html(play_sound_js("https://assets.mixkit.co/active_storage/sfx/911/911-84.wav"), height=0)
                        st.warning(f"⚠️ لديك ({len(driver_missions)}) شحنات جارية قيد التوصيل في الميدان:")
                        
                        for m in driver_missions:
                            phone_display = m[2] 
                            notes_display = m[10] if m[10] else "لا توجد ملاحظات نصية إضافية مكتوبة"
                            v_path = m[11]
                            i_path = m[12]
                            
                            st.markdown(f"""
                            <div class='card'>
                            <h4 style='color:#0284c7 !important;'>🔢 شحنة رقم: {m[0]}</h4>
                            <b>📍 المسار الجغرافي للرحلة:</b> من [ {m[3]} ] 👈 إلى [ {m[4]} ]<br>
                            <b>👤 اسم الزبون المعتمد:</b> {m[1]}<br>
                            <b>📞 رقم هاتف العميل: <span style='color:green; font-weight:bold;'>{phone_display}</span></b><br>
                            <b>📝 توجيهات وملاحظات العميل:</b> <span style='color: #1e3a8a;'>{notes_display}</span><br>
                            <b>💳 آلية السداد المعتمدة:</b> {m[9]}<br>
                            <hr>
                            <h5 style='color:red !important;'>💰 الحساب المالي المطلوب تصفيتة واستلامه: {m[7]:,} ريال</h5>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if v_path and os.path.exists(v_path):
                                st.write("🎙️ استمع لتوجيهات الزبون الصوتية:")
                                st.audio(v_path)
                            
                            if i_path and os.path.exists(i_path):
                                st.write("📸 صورة الشحنة/الفاتورة المرفقة:")
                                st.image(i_path, use_container_width=True)
                            
                            st.markdown("<div class='big-driver-btn'>", unsafe_allow_html=True)
                            if st.button(f"✅ تأكيد تسليم شحنة {m[0]} وتصفية المالي", key=f"drv_btn_{m[0]}"):
                                cursor.execute("UPDATE orders SET status='تم التسليم ✅' WHERE id=?", (m[0],))
                                conn.commit()
                                st.success(f"🎉 تم إنهاء وتثبيت تصفية الشحنة {m[0]} بنجاح!")
                                st.invalidate_pages()
                                st.rerun()
                            st.markdown("</div><br><br>", unsafe_allow_html=True)
                    else:
                        st.info("🟢 مسارك نظيف ومستقر كابتن! لا توجد شحنات معلقة لك في الميدان حالياً.")
                else:
                    st.error("❌ خطأ: كلمة السر الخاصة بك غير صحيحة.")
    else:
        st.info("ℹ️ لا يوجد مناديب مسجلين في قاعدة بيانات النظام.")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 4. لوحة تحكم الإدارة
# -------------------------------------------------------------------------
with tab_manager:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("💼 غُرفة العمليات والتحكم المركزي")
    
    adm_col1, _ = st.columns([2, 1])
    with adm_col1:
        password_input = st.text_input("🔑 أدخل كلمة مرور الإدارة المركزية لفتح لوحة التحكم وبوابة البيانات:", type="password", key="admin_pwd_main")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if password_input and check_admin_password(password_input):
        st.success("🔓 تم فتح البوابة بنجاح مشفر وآمن تماماً.")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status='بانتظار الموافقة'")
            current_pending_count = cursor.fetchone()[0]
        
        if 'last_pending_count' not in st.session_state:
            st.session_state.last_pending_count = current_pending_count
            
        if current_pending_count > st.session_state.last_pending_count:
            st.components.v1.html(play_sound_js("https://assets.mixkit.co/active_storage/sfx/2869/2869-84.wav"), height=0)
            st.toast("🚨 تنبيه: وصل طلب جديد معلق للتو في النظام ينظر المراجعة!")
            st.session_state.last_pending_count = current_pending_count
        elif current_pending_count < st.session_state.last_pending_count:
            st.session_state.last_pending_count = current_pending_count

        # 🔄 استخدام نظام الأجزاء الآمن للتحديث التلقائي الفعال بدون جافا سكريبت ضارة
        @st.fragment(run_every="10s")
        def render_manager_dashboard():
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                with st.sidebar:
                    st.markdown("### 🛠️ الحماية المتقدمة")
                    new_sys_pwd = st.text_input("تغيير كلمة مرور الإدارة الحالية:", type="password", key="change_sys_pwd")
                    if st.button("💾 حفظ وتشفير الكلمة الجديدة"):
                        if new_sys_pwd.strip():
                            update_admin_password(new_sys_pwd.strip())
                            st.success("🔒 تم تشفير وحفظ كلمة المرور بنجاح في قاعدة البيانات!")
                            st.rerun()
                
                cursor.execute("SELECT * FROM orders")
                order_rows = cursor.fetchall()
                
                cursor.execute("SELECT * FROM drivers")
                driver_rows_db = cursor.fetchall()
                
                drivers_dict = {r[0]: {"name": r[1], "phone": r[2], "village": r[3]} for r in driver_rows_db}
                
                orders_db = []
                delivered_revenue = 0
                for r in order_rows:
                    driver_val = r[8] if len(r) > 8 else "لم يحدد"
                    drv_info = drivers_dict.get(driver_val, {"name": "لم يحدد", "phone": "-"})
                    p_method = r[9] if len(r) > 9 else "دفع نقدي كاش (عند الاستلام)"
                    n_text = r[10] if len(r) > 10 else ""
                    
                    masked_phone = r[2][:3] + "****" + r[2][-2:] if (r[2] and len(r[2])>=5) else r[2]
                    
                    orders_db.append({
                        "رقم الشحنة": r[0], "العميل": r[1], "الهاتف المحجوب": masked_phone, "من": r[3], "إلى": r[4], 
                        "النوع": r[5], "الحالة": r[6], "التكلفة": r[7], "المندوب الموجه": drv_info["name"], "الدفع": p_method, "الملاحظات": n_text
                    })
                    if r[6] == "تم التسليم ✅":
                        delivered_revenue += r[7]
                        
                total_orders = len(orders_db)
                pending_orders = current_pending_count
                
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("إجمالي طلبات النظام", f"{total_orders} طلبات")
                m_col2.metric("طلبات معلقة وتحتاج مندوب", f"{pending_orders} طلبات")
                m_col3.metric("صافي الخزنة والديون المستلمة", f"{delivered_revenue:,} ريال")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("#### 👥 فرز وإدارة المناديب والكباتن يدوياً")
                
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                tab_add_drv, tab_edit_drv = st.tabs(["➕ إضافة مندوب جديد", "🛠️ تعديل وحذف كابتن"])
                
                with tab_add_drv:
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        new_drv_name = st.text_input("اسم الكابتن الميداني :")
                        new_drv_phone = st.text_input("رقم هاتف المندوب الخاص به:", max_chars=9, key="add_phone")
                    with col_d2:
                        new_drv_village = st.selectbox("القرية أو عزلة التغطية الرئيسية له:", list(villages_db.keys()), key="add_vil")
                        new_drv_password = st.text_input("🔐 عيّن كلمة سر خاصة لهذا المندوب:", type="password", key="add_pwd")
                        
                    if st.button("💾 حفظ المندوب الجديد في النظام"):
                        if not new_drv_name.strip() or not new_drv_phone.isdigit() or len(new_drv_phone) != 9:
                            st.error("❌ يرجى إدخال اسم صحيح ورقم هاتف من 9 أرقام.")
                        elif not new_drv_password.strip():
                            st.error("❌ يرجى تعيين كلمة سر للمندوب لحماية حسابه.")
                        else:
                            drv_id = f"DRV-{random.randint(100, 999)}"
                            hashed_drv_pass = hash_password(new_drv_password.strip())
                            cursor.execute("INSERT INTO drivers VALUES (?, ?, ?, ?, ?)", (drv_id, new_drv_name, new_drv_phone, new_drv_village, hashed_drv_pass))
                            conn.commit()
                            st.success(f"✅ تم حفظ المندوب {new_drv_name} بكلمة سره المشفرة الخاصة!")
                            st.rerun()
                            
                with tab_edit_drv:
                    if driver_rows_db:
                        drv_select_options = {r[0]: f"{r[1]} ({r[3]})" for r in driver_rows_db}
                        selected_edit_id = st.selectbox("اختر المندوب المستهدف لإجراء التعديل أو الحذف:", list(drv_select_options.keys()), format_func=lambda x: drv_select_options[x])
                        
                        cursor.execute("SELECT * FROM drivers WHERE id=?", (selected_edit_id,))
                        curr_drv_data = cursor.fetchone()
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_name = st.text_input("تعديل الاسم:", value=curr_drv_data[1])
                            edit_phone = st.text_input("تعديل رقم الهاتف الميداني:", value=curr_drv_data[2], max_chars=9)
                        with col_e2:
                            edit_village = st.selectbox("تعديل نطاق وعزلة التغطية:", list(villages_db.keys()), index=list(villages_db.keys()).index(curr_drv_data[3]))
                            edit_pass = st.text_input("🔐 تحديث كلمة السر للمندوب (اتركه فارغاً إذا لا تريد تغييرها):", type="password", key="edit_drv_pass_sec")
                        
                        col_actions = st.columns(2)
                        with col_actions[0]:
                            if st.button("📝 تحديث بيانات المندوب فوراً"):
                                if edit_pass.strip():
                                    new_drv_hash = hash_password(edit_pass.strip())
                                    cursor.execute("UPDATE drivers SET name=?, phone=?, assigned_village=?, password=? WHERE id=?", (edit_name, edit_phone, edit_village, new_drv_hash, selected_edit_id))
                                else:
                                    cursor.execute("UPDATE drivers SET name=?, phone=?, assigned_village=? WHERE id=?", (edit_name, edit_phone, edit_village, selected_edit_id))
                                conn.commit()
                                st.success("✅ تم تحديث بيانات الكابتن وكلمة سره بنجاح.")
                                st.rerun()
                        with col_actions[1]:
                            if st.button("🗑️ حذف المندوب نهائياً من المؤسسة"):
                                cursor.execute("DELETE FROM drivers WHERE id=?", (selected_edit_id,))
                                conn.commit()
                                st.warning("⚠️ تم حذف المندوب بنجاح.")
                                st.rerun()
                    else:
                        st.info("🟢 لا يوجد مناديب مضافين حالياً.")
                st.markdown("</div>", unsafe_allow_html=True)
                        
                st.write("---")
                st.markdown("#### 📊 جدول فرز وحالة الشحنات المركزية الفوري")
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.dataframe(orders_db, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.write("---")
                st.markdown("#### 🎮 وحدة التوجيه الفوري والإسناد والموافقة الإدارية")
                assignable_orders = [o["رقم الشحنة"] for o in orders_db if o["الحالة"] == "بانتظار الموافقة"]
                
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                if assignable_orders:
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        selected_order_id = st.selectbox("اختر رقم الطلب المعلق لتوجيهه للقرية وتعمديه للمندوب:", assignable_orders)
                        cursor.execute("SELECT to_loc, name, phone, voice_path, image_path FROM orders WHERE id=?", (selected_order_id,))
                        order_info_row = cursor.fetchone()
                        st.caption(f"📍 وجهة الشحنة: **{order_info_row[0]}** | عميل: **{order_info_row[1]}** | هاتف: **{order_info_row[2]}**")
                        
                        if order_info_row[3] and os.path.exists(order_info_row[3]):
                            st.write("🎧 استماع لتسجيل العميل الصوتي المرفق:")
                            st.audio(order_info_row[3])
                        if order_info_row[4] and os.path.exists(order_info_row[4]):
                            st.write("🖼️ صورة الفاتورة المرفوعة:")
                            st.image(order_info_row[4], width=200)
                            
                    with col_m2:
                        if driver_rows_db:
                            driver_options = {r[0]: f"{r[1]} (تغطية: {r[3]})" for r in driver_rows_db}
                            selected_driver_id = st.selectbox("اختر الكابتن لتعميد حركة التوصيل له وتسليمه الحساب المالي:", list(driver_options.keys()), format_func=lambda x: driver_options[x])
                        else:
                            selected_driver_id = None
                    
                    if st.button("⚡ اعتماد الشحنة وتوجيه المندوب للموقع فوراً") and selected_driver_id:
                        cursor.execute("UPDATE orders SET status='جاري التوصيل', driver=? WHERE id=?", (selected_driver_id, selected_order_id))
                        conn.commit()
                        st.success(f"✅ تم تعميد الشحنة {selected_order_id} وإرسال التوجيه لهاتف المندوب.")
                        st.rerun()
                else:
                    st.info("🟢 لا توجد أي طلبات جديدة معلقة بانتظار الموافقة حالياً.")
                st.markdown("</div>", unsafe_allow_html=True)
        
        render_manager_dashboard()
        
    elif password_input != "":
        st.error("❌ خطأ أمني: كلمة المرور المدخلة غير صحيحة، يرجى مراجعة الصلاحية.")
