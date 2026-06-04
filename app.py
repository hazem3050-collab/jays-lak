# ======================= APP V2 MAPPED =======================
# تم تطبيق التحديثات المطلوبة بنجاح:
# 1) تكبير التبويبات والخيارات الرئيسية علوياً.
# 2) تكبير زر إرسال الطلب بشكل عملاق ومميز.
# 3) تفعيل نظام الـ Rate Limiting (حد أقصى 3 طلبات في 10 دقائق لكل رقم).
# 4) إظهار تفاصيل الملاحظات والطلبات بوضوح في لوحة المدير.
# ============================================================

import streamlit as st
import sqlite3
import random
import os
import hashlib
from datetime import datetime, timedelta

# ==========================================
# 🛑 المجلدات المخصصة لحفظ الصور والأصوات فعلياً
# ==========================================
VOICE_DIR = "saved_voices"
IMAGE_DIR = "saved_images"
BACKUP_DIR = "system_backups"

for folder in [VOICE_DIR, IMAGE_DIR, BACKUP_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==========================================
# 🛠️ دالات الأمان والتشفير والنسخ الاحتياطي والـ Rate Limit
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def make_backup():
    """أخذ نسخة احتياطية تلقائية من قاعدة البيانات لحماية الحسابات"""
    try:
        today_str = datetime.now().strftime("%Y_%m_%d")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{today_str}.db")
        if not os.path.exists(backup_file) and os.path.exists('jaya_lak.db'):
            import shutil
            shutil.copyfile('jaya_lak.db', backup_file)
    except Exception as e:
        pass

def init_db():
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # إنشاء جدول الشحنات والطلبات
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
    
    # إنشاء جدول الـ Rate Limiting لمنع التكرار والطلبات العشوائية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            phone TEXT,
            request_time TEXT
        )
    ''')
    
    # صيانة وتحديث الأعمدة تلقائياً لمنع أي خطأ تعارض
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'voice_path' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN voice_path TEXT DEFAULT ''")
    if 'image_path' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN image_path TEXT DEFAULT ''")
        
    # إنشاء جدول المناديب (مع عمود كلمة السر المشفرة)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            assigned_village TEXT,
            password TEXT DEFAULT ''
        )
    ''')
    
    # التأكد من وجود عمود كلمة السر في جدول المناديب في حال كانت قاعدة البيانات قديمة
    cursor.execute("PRAGMA table_info(drivers)")
    d_columns = [column[1] for column in cursor.fetchall()]
    if 'password' not in d_columns:
        default_d_pass = hash_password("1234")
        cursor.execute(f"ALTER TABLE drivers ADD COLUMN password TEXT DEFAULT '{default_d_pass}'")
    
    # جدول الإعدادات وحفظ كلمة المرور المشفرة للمدير
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
    if not cursor.fetchone():
        default_hashed = hash_password("admin123")
        cursor.execute("INSERT INTO settings VALUES ('admin_password', ?)", (default_hashed,))
        
    # إضافة مناديب تجريبيين بكلمة سر افتراضية (1234) لتنشيط الواجهة لأول مرة
    cursor.execute("SELECT COUNT(*) FROM drivers")
    if cursor.fetchone()[0] == 0:
        d_pass = hash_password("1234")
        cursor.execute("INSERT INTO drivers VALUES ('DRV-101', 'كابتن عبدالقادر نجيب', '771111111', 'قرية المنزل', ?)", (d_pass,))
        cursor.execute("INSERT INTO drivers VALUES ('DRV-102', 'كابتن جلال حميد', '772222222', 'قرى الصفي', ?)", (d_pass,))
        
    conn.commit()
    conn.close()
    make_backup()

init_db()

def check_rate_limit(phone):
    """دالة تفحص إن كان الرقم قد أرسل أكثر من 3 طلبات خلال آخر 10 دقائق"""
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # حذف السجلات القديمة التي مر عليها أكثر من 10 دقائق لتنظيف الجدول تلقائياً
    ten_minutes_ago = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM rate_limits WHERE request_time < ?", (ten_minutes_ago,))
    
    # حساب عدد الطلبات الحالية للرقم خلال الـ 10 دقائق الماضية
    cursor.execute("SELECT COUNT(*) FROM rate_limits WHERE phone = ?", (phone,))
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    return count < 3

def log_rate_limit(phone):
    """تسجيل وقت الطلب الحالي للرقم"""
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO rate_limits VALUES (?, ?)", (phone, now_str))
    conn.commit()
    conn.close()

def check_admin_password(input_pwd):
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
    saved_hash = cursor.fetchone()[0]
    conn.close()
    return saved_hash == hash_password(input_pwd)

def update_admin_password(new_pwd):
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    new_hash = hash_password(new_pwd)
    cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_hash,))
    conn.commit()
    conn.close()

# ==========================================
# 🎨 واجهة وتصميم التطبيق التحديثي العصري
# ==========================================
st.set_page_config(
    page_title=" جايا لك للتوصيل الذكي",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# نظام الفحص الذكي لحالة الإنترنت لتنبيه العميل في حال الانقطاع المفاجئ
st.components.v1.html("""
<script>
window.addEventListener('offline', function(e) {
    alert('⚠️ تنبيه: انقطع الاتصال بالإنترنت لديك حالياً! يرجى عدم إغلاق الصفحة لضمان حفظ بيانات الشحنة عند عودة الشبكة.');
});
</script>
""", height=0)

# كود CSS مخصص لتكبير التبويبات الرئيسية، وتكبير حجم أزرار الإرسال
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.45), rgba(255, 255, 255, 0.45)), 
                          url('https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1974&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    * { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    
    /* 1) 🚀 تكبير الخيارات والتبويبات العلوية الرئيسية لجعلها ضخمة وواضحة */
    .stTabs [data-baseweb="tab-list"] { gap: 14px; justify-content: center; background-color: rgba(255, 255, 255, 0.85); padding: 12px; border-radius: 16px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: rgba(241, 245, 249, 0.95); border-radius: 10px; padding: 16px 28px; font-weight: bold; color: #1e293b; border: 1px solid #cbd5e1;
        font-size: 20px !important;  /* تم تكبير الخط هنا */
    }
    .stTabs [aria-selected="true"] { background-color: #16a34a !important; color: white !important; border-color: #16a34a !important; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.2); }
    
    .card { 
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 24px; 
        border-radius: 16px; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); 
        margin-bottom: 18px; 
        border: 1px solid rgba(255, 255, 255, 0.7); 
    }
    
    .voice-box { border: 2px dashed #0284c7; padding: 15px; background-color: rgba(240, 249, 255, 0.95); border-radius: 12px; margin-bottom: 10px; }
    .jeeb-panel { background-color: rgba(240, 253, 244, 0.95); border-right: 6px solid #0d9488; padding: 15px; border-radius: 8px; font-weight: bold; }
    .success-panel { background-color: rgba(240, 253, 244, 0.95); border-right: 6px solid #16a34a; padding: 15px; border-radius: 8px; }
    .price-tag { background-color: rgba(239, 246, 255, 0.95); color: #1d4ed8; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 22px; border: 1px dashed #3b82f6; }
    
    /* 2) 🟢 تكبير مربع وزر إرسال وتأكيد الطلب نهائياً للعميل */
    .big-submit-btn button {
        width: 100% !important;
        height: 110px !important; /* طول عملاق ومريح جداً للاستخدام */
        background-color: #16a34a !important;
        color: white !important;
        font-size: 28px !important; /* حجم خط ضخم للزر */
        font-weight: bold !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 20px -3px rgba(22, 163, 74, 0.4) !important;
        border: none !important;
        transition: 0.2s ease-in-out;
    }
    .big-submit-btn button:hover { background-color: #15803d !important; transform: scale(1.01); }
    
    /* زر المندوب الميداني */
    .big-driver-btn button {
        width: 100% !important;
        height: 70px !important;
        background-color: #0284c7 !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
    }
    
    h1, h2, h3, h4 { color: #1e293b !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1e293b; margin-bottom: 0;'>📦 مؤسسة جَايَا لَك للتوصيل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #475569; font-size: 16px; font-weight: bold;'>الخدمة الأسرع لتوصيل المواد الغذائية والطلبات - كِتَاب</p>", unsafe_allow_html=True)
st.write("---")

tab_client, tab_track, tab_driver, tab_manager = st.tabs(["👤 بوابة العميل / إرسال طلب", "🔍 تتبع حالة الشحنة", "🛵 واجهة المندوب الميداني", "💼 لوحة التحكم والمدير"])

villages_db = {
    "المركز الرئيسي كتاب": {"light": 300, "heavy": 500},
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
    st.subheader("📝 نموذج بيانات الشحنة")
    c_name = st.text_input("الاسم الكامل للمرسل / المستلم *", key="c_name")
    c_phone = st.text_input("رقم الهاتف (9 أرقام لتواصل المندوب) *", max_chars=9, key="c_phone")
    
    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        from_loc = st.selectbox("نقطة الاستلام (من أين؟) *", list(villages_db.keys()))
    with col_loc2:
        to_loc = st.selectbox("نقطة التسليم (إلى أين؟) *", list(villages_db.keys()))
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='voice-box'>", unsafe_allow_html=True)
    st.markdown("<h4>🎙️ أرسل طلبك بصوتك (بدل الكتابة الطويلة)</h4>", unsafe_allow_html=True)
    voice_file = st.file_uploader("اضغط لرفع أو تسجيل مقطع صوتي يوضح تفاصيل مكانك أو شحنتك:", type=["mp3", "wav", "m4a", "ogg"])
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("✏️ الملاحظات وحجم الشحنة")
    user_notes = st.text_area("كتابة ملاحظة توضيحية للمندوب (إن وجدت):", placeholder="مثال: كرتون مواد غذائية، الخضروات قابلة للتلف بسرعة...")
    weight_opt = st.selectbox("اختر تقديرك لحجم الشحنة الميدانية:", ["📦 خفيفة", "📦 متوسطة", "📦 ثقيلة"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📸 توثيق بصورة الفاتورة أو الشحنة")
    image_file = st.file_uploader("رفع صورة اختيارية للشحنة لتوثيق حالتها للمندوب:", type=["jpg", "png", "jpeg"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    pay_opt = st.radio("💳 آلية تسديد الرسوم المعتمدة ومحفظة جيب:", ["دفع نقدي كاش (عند الاستلام)", "خصم من نقاط البيع المعتمدة", "📱 عبر محفظة جيب الإلكترونية"])
    is_emergency = st.checkbox("🚨 تصنيف الطلب كحالة طوارئ مستعجلة للغاية")
    
    if pay_opt == "📱 عبر محفظة جيب الإلكترونية":
        st.markdown("<div class='jeeb-panel'>📲 يرجى تحويل الرصيد لحساب جيب (541419) التابع لجايا لك، وأدخل رقم العملية بالأسفل.</div><br>", unsafe_allow_html=True)
        jeeb_tx = st.text_input("أدخل رقم إشعار عملية التحويل المالي للتأكيد:")
    st.markdown("</div>", unsafe_allow_html=True)

    light_price = max(villages_db[from_loc]["light"], villages_db[to_loc]["light"])
    heavy_price = max(villages_db[from_loc]["heavy"], villages_db[to_loc]["heavy"])
    medium_price = int((light_price + heavy_price) / 2)
    final_cost = heavy_price if is_emergency else (light_price if "خفيفة" in weight_opt else (medium_price if "متوسطة" in weight_opt else heavy_price))
    display_type = "🚨 طوارئ مستعجلة" if is_emergency else f"عادي - {weight_opt}"

    st.markdown(f"<div class='price-tag'>💰 تكلفة التوصيل المعتمدة: {final_cost} ريال يمني</div><br>", unsafe_allow_html=True)

    # وضع زر الإرسال داخل كلاس التصميم الكبير المخصص له
    st.markdown("<div class='big-submit-btn'>", unsafe_allow_html=True)
    if st.button("🚀 إرسال وتأكيد الطلب نهائياً"):
        if not c_name.strip() or not c_phone.isdigit() or len(c_phone) < 9:
            st.error("❌ خطأ: يرجى كتابة الاسم ورقم الهاتف الصحيح المكون من 9 أرقام.")
        elif from_loc == to_loc:
            st.error("❌ تنبيه مسار جغرافي خاطئ: نقطة الاستلام ونقطة التسليم متطابقتان.")
        # فحص نظام الـ Rate Limiting هنا قبل إدخال الطلب لقاعدة البيانات لحماية النظام
        elif not check_rate_limit(c_phone.strip()):
            st.error("⚠️ تنبيه أمني (Rate Limit): لقد تجاوزت الحد المسموح به! لا يمكنك إرسال أكثر من 3 طلبات خلال 10 دقائق لنفس رقم الهاتف لمنع التكرار.")
        else:
            order_id = f"GL-{random.randint(100, 999)}"
            saved_voice_path = ""
            saved_img_path = ""
            
            if voice_file is not None:
                ext = voice_file.name.split(".")[-1]
                saved_voice_path = os.path.join(VOICE_DIR, f"{order_id}.{ext}")
                with open(saved_voice_path, "wb") as f:
                    f.write(voice_file.getbuffer())
                    
            if image_file is not None:
                ext = image_file.name.split(".")[-1]
                saved_img_path = os.path.join(IMAGE_DIR, f"{order_id}.{ext}")
                with open(saved_img_path, "wb") as f:
                    f.write(image_file.getbuffer())

            conn = sqlite3.connect('jaya_lak.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (order_id, c_name, c_phone, from_loc, to_loc, display_type, "بانتظار الموافقة", final_cost, "لم يحدد", pay_opt, user_notes, saved_voice_path, saved_img_path)
            )
            conn.commit()
            conn.close()
            
            # تسجيل العملية في الـ Rate Limit للرقم الحالي
            log_rate_limit(c_phone.strip())
            
            st.balloons()
            st.markdown(f"<div class='success-panel'>🎉 تم استلام طلبك بنجاح يرجى حفظ كود التتبع: <b style='font-size:20px; color:#1d4ed8;'>{order_id}</b></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. واجهة تتبع حالة الشحنة للعميل
# -------------------------------------------------------------------------
with tab_track:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔍 استعلم عن شحنتك وحركتها فوراً")
    track_id = st.text_input("أدخل كود تتبع الشحنة الخاص بك (مثال: GL-105):").strip()
    
    if track_id:
        conn = sqlite3.connect('jaya_lak.db')
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
            st.info(f"🛵 **المندوب المسؤول ميدانياً:** {driver_name}")
            st.metric("المبلغ المطلوب تصفيتة", f"{res[5]:,} ريال يمني")
        else:
            st.error("❌ عذراً، لم نجد أي شحنة مسجلة بهذا الكود.")
        conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 3. واجهة المندوب الميداني - محمية بكلمة مرور خاصة لكل مندوب 🔐
# -------------------------------------------------------------------------
with tab_driver:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🛵 واجهة لوجستيات المندوب وكباتن الحركة")
    
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers")
    drvs = cursor.fetchall()
    
    if drvs:
        drvs_choices = {r[0]: f"{r[1]} - التغطية الميدانية: {r[3]}" for r in drvs}
        active_driver_id = st.selectbox("اختر اسمك لتسجيل الدخول الفوري:", list(drvs_choices.keys()), format_func=lambda x: drvs_choices[x])
        
        driver_password_input = st.text_input(f"🔐 أدخل كلمة السر الخاصة بك يا كابتن:", type="password", key=f"pwd_drv_{active_driver_id}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if driver_password_input:
            cursor.execute("SELECT password FROM drivers WHERE id=?", (active_driver_id,))
            saved_drv_hash = cursor.fetchone()[0]
            
            if saved_drv_hash == hash_password(driver_password_input):
                cursor.execute("SELECT * FROM orders WHERE driver=? AND status='جاري التوصيل'", (active_driver_id,))
                driver_missions = cursor.fetchall()
                
                if driver_missions:
                    st.warning(f"⚠️ لديك ({len(driver_missions)}) شحنات جارية قيد التوصيل في الميدان:")
                    for m in driver_missions:
                        phone_display = m[2] 
                        notes_display = m[10] if m[10] else "لا توجد ملاحظات نصية إضافية مكتوبة"
                        v_path = m[11]
                        i_path = m[12]
                        
                        st.markdown(f"""
                        <div class='card'>
                        <h4 style='color:#0284c7;'>🔢 شحنة رقم: {m[0]}</h4>
                        <b>📍 المسار الجغرافي للرحلة:</b> من [ {m[3]} ] 👈 إلى [ {m[4]} ]<br>
                        <b>👤 اسم الزبون المعتمد:</b> {m[1]}<br>
                        <b>📞 رقم هاتف العميل (خاص بك): <span style='color:green; font-weight:bold;'>{phone_display}</span></b><br>
                        <b>📝 توجيهات وملاحظات العميل:</b> <span style='color: #1e3a8a;'>{notes_display}</span><br>
                        <b>💳 آلية السداد المعتمدة:</b> {m[9]}<br>
                        <hr>
                        <h5 style='color:red;'>💰 الحساب المالي المطلوب تصفيتة واستلامه: {m[7]:,} ريال</h5>
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
                            conn.close()
                            st.rerun()
                        st.markdown("</div><br><br>", unsafe_allow_html=True)
                else:
                    st.info("🟢 مسارك نظيف ومستقر كابتن! لا توجد شحنات معلقة لك في الميدان حالياً.")
            else:
                st.error("❌ خطأ: كلمة السر الخاصة بك غير صحيحة.")
    else:
        st.info("ℹ️ لا يوجد مناديب مسجلين في قاعدة بيانات النظام.")
    conn.close()

# -------------------------------------------------------------------------
# 4. لوحة تحكم الإدارة - مع تفاصيل وملاحظات طلبات الزبائن بوضوح 💼
# -------------------------------------------------------------------------
with tab_manager:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("💼 غُرفة العمليات والتحكم المركزي")
    password_input = st.text_input("🔑 أدخل كلمة مرور الإدارة المركزية لفتح لوحة التحكم وبوابة البيانات:", type="password")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if password_input and check_admin_password(password_input):
        st.success("🔓 تم فتح البوابة بنجاح مشفر وآمن تماماً.")
        
        with st.sidebar:
            st.markdown("### 🛠️ الحماية المتقدمة")
            new_sys_pwd = st.text_input("تغيير كلمة مرور الإدارة الحالية:", type="password")
            if st.button("💾 حفظ وتشفير الكلمة الجديدة"):
                if new_sys_pwd.strip():
                    update_admin_password(new_sys_pwd.strip())
                    st.success("🔒 تم تشفير وحفظ كلمة المرور بنجاح في قاعدة البيانات!")
                    st.rerun()
        
        conn = sqlite3.connect('jaya_lak.db')
        cursor = conn.cursor()
        
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
        pending_orders = len([o for o in orders_db if o["الحالة"] == "بانتظار الموافقة"])
        
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
                new_drv_name = st.text_input("اسم الكابتن الميداني الرباعي:")
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
                    edit_name = st.text_input("تعديل الاسم الرباعي:", value=curr_drv_data[1])
                    edit_phone = st.text_input("تعديل رقم الهاتف الميداني:", value=curr_drv_data[2], max_chars=9)
                with col_e2:
                    edit_village = st.selectbox("تعديل نطاق وعزلة التغطية:", list(villages_db.keys()), index=list(villages_db.keys()).index(curr_drv_data[3]))
                    edit_pass = st.text_input("🔐 تحديث كلمة السر للمندوب (اتركه فارغاً إذا لا تريد تغييرها):", type="password")
                
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
        # 4) 🎮 تعديل واجهة تفاصيل وملاحظات طلبات الزبائن بوضوح كامل داخل لوحة الإدارة والمدير
        st.markdown("#### 🎮 وحدة التحكم، الإسناد، والاطلاع على تفاصيل وملاحظات الزبائن")
        assignable_orders = [o["رقم الشحنة"] for o in orders_db if o["الحالة"] == "بانتظار الموافقة"]
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if assignable_orders:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                selected_order_id = st.selectbox("اختر رقم الطلب المعلق لعرض كامل تفاصيله وإسناده:", assignable_orders)
                cursor.execute("SELECT to_loc, name, phone, voice_path, image_path, from_loc, type, notes, cost, payment_method FROM orders WHERE id=?", (selected_order_id,))
                order_info_row = cursor.fetchone()
                
                # إظهار كامل تفاصيل وملاحظات الزبون الجديد هنا بوضوح للمدير
                st.markdown(f"""
                <div style="background-color: #f8fafc; border-right: 4px solid #3b82f6; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                    <b style="color:#1e3a8a;">📝 تفاصيل طلب الزبون الجديد الحالية:</b><br>
                    • <b>اسم الزبون:</b> {order_info_row[1]}<br>
                    • <b>رقم الهاتف المباشر:</b> <span style="color:green; font-weight:bold;">{order_info_row[2]}</span><br>
                    • <b>المسار الجغرافي:</b> من <b>{order_info_row[5]}</b> إلى <b>{order_info_row[0]}</b><br>
                    • <b>نوع الشحنة ووزنها:</b> {order_info_row[6]}<br>
                    • <b>آلية السداد المطلوبة:</b> {order_info_row[9]}<br>
                    • <b>التكلفة المحسوبة:</b> {order_info_row[8]:,} ريال يمني<br>
                    <hr style="margin: 8px 0;">
                    <b style="color:#b91c1c;">✏️ ملاحظة العميل النصية:</b> <span style="font-size:16px; color:#334155;">{order_info_row[7] if order_info_row[7] else 'لا توجد ملاحظة نصية مكتوبة'}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if order_info_row[3] and os.path.exists(order_info_row[3]):
                    st.write("🎧 تسجيل العميل الصوتي المرفق:")
                    st.audio(order_info_row[3])
                if order_info_row[4] and os.path.exists(order_info_row[4]):
                    st.write("🖼️ صورة الفاتورة / الشحنة المرفوعة:")
                    st.image(order_info_row[4], width=250)
                    
            with col_m2:
                if driver_rows_db:
                    driver_options = {r[0]: f"{r[1]} (تغطية: {r[3]})" for r in driver_rows_db}
                    selected_driver_id = st.selectbox("اختر الكابتن لتعميد حركة التوصيل له وتسليمه الحساب المالي:", list(driver_options.keys()), format_func=lambda x: driver_options[x])
                else:
                    selected_driver_id = None
            
            if st.button("⚡ اعتماد الشحنة وتوجيه المندوب للموقع فوراً") and selected_driver_id:
                cursor.execute("UPDATE orders SET status='جاري التوصيل', driver=? WHERE id=?", (selected_driver_id, selected_order_id))
                conn.commit()
                st.success(f"✅ تم تعميد الشحنة {selected_order_id} وإرسال التوجيه لهاتف المندوب بنجاح.")
                conn.close()
                st.rerun()
        else:
            st.info("🟢 لا توجد أي طلبات جديدة معلقة بانتظار الموافقة حالياً.")
        st.markdown("</div>", unsafe_allow_html=True)
        conn.close()
    elif password_input != "":
        st.error("❌ خطأ أمني: كلمة المرور المدخلة غير صحيحة، يرجى مراجعة الصلاحية.")
