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
# 📂 المجلدات المخصصة لحفظ الصور والأصوات والنسخ الاحتياطي
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
    conn = sqlite3.connect('jaya_lak.db', timeout=30)
    # تفعيل واجهة الفهارس بالأسماء لضمان دقة جلب معلومات الطلب وعدم حدوث خطأ ProgrammingError
    conn.row_factory = sqlite3.Row
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

# ==========================================
# 🎨 واجهة وتصميم التطبيق والخلفية الاحترافية
# ==========================================
st.set_page_config(
    page_title="مؤسسة جايا لك للتوصيل الذكي",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# نظام التحذير من انقطاع الإنترنت في الميدان لضمان عدم ضياع البيانات
st.components.v1.html("""
<script>
window.addEventListener('offline', function(e) {
    alert('⚠️ تنبيه ميداني: انقطع الاتصال بالإنترنت لديك حالياً! يرجى عدم إغلاق هذه الصفحة لضمان حفظ بيانات الشحنة المفتوحة فور عودة الشبكة.');
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
    button[title="Manage app"] {display: none !important;}
    
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
    .price-tag { background-color: rgba(239, 246, 255, 0.95); color: #1d4ed8 !important; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 22px; border: 2px dashed #3b82f6; }
    
    .driver-notif-box {
        background-color: #f0fdfa;
        border: 2px solid #0284c7;
        border-right: 8px solid #0284c7;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    
    .big-driver-btn button, .big-send-btn button, .whatsapp-btn a, .sms-btn a, .role-btn button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 60px !important;
        background-color: #16a34a !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        color: white !important;
        text-decoration: none !important;
        box-shadow: 0 10px 15px -3px rgba(22, 163, 74, 0.3) !important;
        margin-bottom: 8px !important;
    }
    .whatsapp-btn a { background-color: #25D366 !important; }
    .sms-btn a { background-color: #0284c7 !important; }
    .role-btn button { background-color: #1e293b !important; }
    .back-btn button { background-color: #64748b !important; height: 45px !important; font-size: 16px !important; }
    
    h1, h2, h3, h4, h5, h6, label, p, span, li, td, th { color: #000000 !important; font-weight: 700 !important; }
    input, select, textarea { color: #000000 !important; font-weight: bold !important; font-size: 17px !important; }
