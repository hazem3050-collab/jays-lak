import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime

# 1. إعداد الصفحة وتغيير ثيم التطبيق ليتناسب مع الهواتف
st.set_page_config(page_title="تطبيق جايا لك", page_icon="📦", layout="centered")

# دالة لتشفير كلمات المرور لحماية حسابات المناديب والمدير
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 2. إنشاء وإعداد قاعدة البيانات بجميع جداولها الأصلية والتجارية
def init_db():
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    # جدول الطلبات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            phone TEXT,
            from_location TEXT,
            to_location TEXT,
            order_details TEXT,
            voice_file TEXT,
            status TEXT,
            driver_name TEXT,
            order_date TEXT,
            delivery_price REAL DEFAULT 0.0
        )
    ''')
    # جدول المناديب والحسابات لتجنب الفقدان
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            username TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            wallet REAL DEFAULT 0.0
        )
    ''')
    
    # إضافة حساب افتراضي للمدير إذا لم يكن موجوداً
    cursor.execute("SELECT * FROM drivers WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO drivers (username, password, full_name, wallet) VALUES (?, ?, ?, ?)",
                       ('admin', hash_password('admin123'), 'المدير العام', 0.0))
        
    conn.commit()
    conn.close()

init_db()

# 3. تصميم واجهة التطبيق عبر CSS (خلفية المواد الغذائية والتوابل والخضروات + تكبير الأزرار)
st.markdown("""
    <style>
    /* تصميم الخلفية الشاملة: مواد غذائية، بهارات وتوابل، وخضروات زاهية */
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                          url("https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1000");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* تكبير وتنسيق أزرار القائمة الرئيسية الثلاثة */
    .big-button button {
        height: 85px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        background-color: #EA384D !important; /* الأحمر الزاهي الخاص بهوية جايا لك السريعة */
        color: white !important;
        border-radius: 18px !important;
        margin-bottom: 18px !important;
        border: 2px solid #000000 !important; /* الأسود الملكي لضمان الوضوح الكامل */
        box-shadow: 0px 4px 10px rgba(0,0,0,0.15) !important;
    }
    
    /* تكبير وتبريز زر إرسال وتأكيد الطلب للزبون */
    .submit-button button {
        height: 75px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        background-color: #10B981 !important; /* الأخضر الزاهي للتأكيد السريع */
        color: white !important;
        border-radius: 15px !important;
        width: 100% !important;
        border: 2px solid #065F46 !important;
        box-shadow: 0px 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* تنسيقات كروت تفاصيل الطلبات في لوحة المدير */
    .admin-card {
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 12px; 
        border-right: 6px solid #EA384D; 
        margin-bottom: 15px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
    }
    
    h1, h2, h3 {
        text-align: center;
        color: #111827;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>📦 تطبيق جايا لك للتوصيل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-weight:bold; color:#374151;'>أسرع خدمة توصيل في كِتاب وكافة القرى المجاورة</p>", unsafe_allow_html=True)

# نظام إدارة الصفحات والتنقل الداخلي
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None

if st.session_state.page == 'main':
    st.write("### 🏪 اختر البوابة المطلوبة للدخول:")
    
    st.markdown('<div class="big-button">', unsafe_allow_html=True)
    if st.button("🙋‍♂️ بوابة العميل (طلب جديد مباشر)", key="btn_client", use_container_width=True):
        st.session_state.page = 'client'
        st.rerun()
        
    if st.button("🚗 لوحة كباتن التوصيل (المناديب)", key="btn_driver", use_container_width=True):
        st.session_state.page = 'driver_login'
        st.rerun()
        
    if st.button("📊 لوحة الإدارة والتحكم (المدير)", key="btn_admin", use_container_width=True):
        st.session_state.page = 'admin_login'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 1. بوابة العميل الكاملة -----------------
elif st.session_state.page == 'client':
    st.subheader("🙋‍♂️ سجل طلبك الآن وسيتم توجيه أقرب مندوب لك")
    
    if st.button("⬅️ العودة للرئيسية"):
        st.session_state.page = 'main'
        st.rerun()
        
    with st.form("order_form"):
        client_name = st.text_input("اسمك الكريم:")
        phone = st.text_input("رقم هاتف للتواصل والمتابعة:")
        
        # التعديل: إلغاء القرى تماماً وتثبيت المركز الرئيسي كتاب في خانة "من أين"
        from_location = st.selectbox("من أين (موقع الاستلام المعتمد):", ["المركز الرئيسي كِتاب"])
        
        to_location = st.text_input("إلى أين (حدد اسم القرية أو المربع السكني بدقة):")
        order_details = st.text_area("تفاصيل المواد المطلوبة (اكتب طلباتك هنا بالتفصيل):")
        
        st.write("🎵 **يمكنك تسجيل أو إرفاق ملاحظة صوتية لطلبك لتسهيل الفهم:**")
        voice_file = st.file_uploader("ارفع التسجيل الصوتي للطلب (اختياري)", type=['wav', 'mp3', 'm4a'])
        
        st.markdown('<div class="submit-button">', unsafe_allow_html=True)
        submitted = st.form_submit_button("✅ إرسال وتأكيد الطلب")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if client_name and phone and to_location:
                voice_path = None
                if voice_file:
                    if not os.path.exists('saved_voices'):
                        os.makedirs('saved_voices')
                    voice_path = f"saved_voices/{datetime.now().strftime('%Y%m%d%H%M%S')}_{voice_file.name}"
                    with open(voice_path, "wb") as f:
                        f.write(voice_file.getbuffer())
                
                conn = sqlite3.connect('jaya_lak.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO orders (client_name, phone, from_location, to_location, order_details, voice_file, status, driver_name, order_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (client_name, phone, from_location, to_location, order_details, voice_path, 'قيد الانتظار', '', datetime.now().strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                conn.close()
                st.success("🎉 تم إرسال وتأكيد طلبك بنجاح! كباتن جايا لك في طريقهم لتجهيزه وتوصيله.")
            else:
                st.error("⚠️ خطأ: يرجى كتابة الاسم، الهاتف، وموقع التوصيل لضمان وصول المندوب إليك.")

# ----------------- 2. تسجيل دخول المناديب -----------------
elif st.session_state.page == 'driver_login':
    st.subheader("🚗 تسجيل دخول كباتن التوصيل")
    if st.button("⬅️ العودة للرئيسية"):
        st.session_state.page = 'main'
        st.rerun()
        
    username = st.text_input("اسم المستخدم للكابتن:")
    password = st.text_input("كلمة المرور:", type="password")
    
    if st.button("تسجيل الدخول"):
        conn = sqlite3.connect('jaya_lak.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers WHERE username=? AND password=?", (username, hash_password(password)))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            st.session_state.logged_user = username
            st.session_state.page = 'driver_dashboard'
            st.rerun()
        else:
            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة.")

# ----------------- 3. لوحة تحكم المندوب (Dashboard) -----------------
elif st.session_state.page == 'driver_dashboard':
    st.subheader(f"🚗 مرحباً بالكابتن: {st.session_state.logged_user}")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.logged_user = None
        st.session_state.page = 'main'
        st.rerun()
        
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # عرض محفظة المندوب المالية الحالية لضمان الشفافية والأرباح
    cursor.execute("SELECT wallet FROM drivers WHERE username=?", (st.session_state.logged_user,))
    wallet_balance = cursor.fetchone()[0]
    st.metric(label="💰 إجمالي أرباحك الحالية في المحفظة:", value=f"{wallet_balance} ريال")
    
    st.write("---")
    st.write("### 📌 الطلبات الجديدة المتاحة حالياً في كِتاب:")
    cursor.execute("SELECT * FROM orders WHERE status='قيد الانتظار'")
    pending_orders = cursor.fetchall()
    
    if not pending_orders:
        st.info("لا توجد طلبات جديدة بانتظار التوصيل حالياً.")
    else:
        for order in pending_orders:
            with
