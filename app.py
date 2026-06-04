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
# تم تصحيح الخطأ الإملائي هنا تماماً للعمل بدون أي مشاكل syntax
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
            with st.expander(f"📦 طلب لـ {order[1]} 📍 وجهة التوصيل: {order[4]}"):
                st.write(f"**من:** {order[3]} -> **إلى:** {order[4]}")
                st.write(f"**تفاصيل المواد:** {order[5]}")
                if order[6]:
                    st.audio(order[6])
                price_input = st.number_input(f"تحديد سعر التوصيل للطلب #{order[0]} (ريال):", min_value=0.0, step=50.0, key=f"price_{order[0]}")
                if st.button(f"قبول وتولّي الطلب #{order[0]}", key=f"accept_{order[0]}"):
                    if price_input > 0:
                        cursor.execute("UPDATE orders SET status='جاري التوصيل', driver_name=?, delivery_price=? WHERE id=?", 
                                       (st.session_state.logged_user, price_input, order[0]))
                        conn.commit()
                        st.success("تم قبول الطلب، تحرك بسلامة الله!")
                        st.rerun()
                    else:
                        st.error("يرجى تحديد سعر التوصيل أولاً قبل القبول.")
                        
    st.write("---")
    st.write("### ⏱️ طلباتك الجاري توصيلها حالياً:")
    cursor.execute("SELECT * FROM orders WHERE status='جاري التوصيل' AND driver_name=?", (st.session_state.logged_user,))
    my_orders = cursor.fetchall()
    
    for order in my_orders:
        with st.expander(f"طلب نشط #{order[0]} - للزبون {order[1]}"):
            st.write(f"**رقم هاتف العميل:** {order[2]}")
            st.write(f"**العنوان المحدد:** {order[4]}")
            st.write(f"**أجرة التوصيل المتفق عليها:** {order[10]} ريال")
            if st.button(f"🏁 تم تسليم الطلب للزبون وقبض المبلغ", key=f"done_{order[0]}"):
                # تحديث حالة الطلب وإضافة الأرباح مباشرة لمحفظة الكابتن
                cursor.execute("UPDATE orders SET status='تم التسليم' WHERE id=?", (order[0],))
                cursor.execute("UPDATE drivers SET wallet = wallet + ? WHERE username=?", (order[10], st.session_state.logged_user))
                conn.commit()
                st.success("كفو يا كابتن! تم إغلاق الطلب وإضافة الأجرة إلى محفظتك بنجاح.")
                st.rerun()
                
    conn.close()

# ----------------- 4. تسجيل دخول المدير -----------------
elif st.session_state.page == 'admin_login':
    st.subheader("📊 تسجيل دخول لوحة الإدارة (المدير)")
    if st.button("⬅️ العودة للرئيسية"):
        st.session_state.page = 'main'
        st.rerun()
        
    admin_user = st.text_input("اسم مستخدم المدير:")
    admin_pass = st.text_input("كلمة مرور المدير:", type="password")
    
    if st.button("دخول لوحة التحكم"):
        if admin_user == 'admin' and hash_password(admin_pass) == hash_password('admin123'): # كلمة مرور افتراضية لحين تغييرها برمجياً
            st.session_state.logged_user = 'admin'
            st.session_state.page = 'admin_dashboard'
            st.rerun()
        else:
            st.error("❌ بيانات دخول الإدارة غير صحيحة.")

# ----------------- 5. لوحة تحكم المدير الكاملة والمحدثة -----------------
elif st.session_state.page == 'admin_dashboard':
    st.subheader("📊 لوحة الإدارة والتحكم الشاملة - جايا لك")
    if st.button("🚪 تسجيل خروج الإدارة"):
        st.session_state.logged_user = None
        st.session_state.page = 'main'
        st.rerun()
        
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # التعديل: عرض تفاصيل طلبات الزبائن الجديدة كاملة ومفصلة في قائمة المدير لمنع الفقدان
    st.write("### 🔴 تفاصيل طلبات الزبائن الجديدة الواردة الآن:")
    cursor.execute("SELECT * FROM orders WHERE status='قيد الانتظار' ORDER BY id DESC")
    new_orders = cursor.fetchall()
    
    if not new_orders:
        st.info("لا توجد طلبات جديدة بانتظار الكباتن في الميدان حالياً.")
    else:
        for order in new_orders:
            # كرت تفصيلي كامل وجذاب يعرض جميع المعلومات الميدانية للمدير
            st.markdown(f"""
            <div class="admin-card">
                <h4 style="margin: 0; color: #EA384D;">📦 طلب جديد معلق رقم #{order[0]}</h4>
                <p style="margin: 6px 0; font-size: 15px;"><b>👤 اسم الزبون الكريم:</b> {order[1]} | <b>📞 رقم الهاتف للاتصال:</b> {order[2]}</p>
                <p style="margin: 6px 0; font-size: 15px;"><b>📍 خط سير التوصيل:</b> من <span style="color: blue;">{order[3]}</span> إلى <span style="color: red; font-weight: bold;">{order[4]}</span></p>
                <p style="margin: 6px 0; font-size: 15px;"><b>📝 تفاصيل ومواد الطلب المكتوبة:</b> {order[5] if order[5] else 'لم يكتب تفاصيل نصية (اكتفى بالصوت أو بانتظار Mندوب)'}</p>
                <p style="margin: 6px 0; color: #6B7280;"><small>📅 وقت ورود الطلب للنظام: {order[9]}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # تشغيل الملاحظة الصوتية المرفقة للطلب الجديد أسفل الكرت مباشرة إن وجدت
            if order[6]:
                st.write("🎵 **الملاحظة الصوتية المرفقة من الزبون:**")
                st.audio(order[6])
                
            if st.button(f"❌ إلغاء وحذف هذا الطلب المعلق (# {order[0]})", key=f"del_{order[0]}"):
                cursor.execute("DELETE FROM orders WHERE id=?", (order[0],))
                conn.commit()
                st.warning(f"تم حذف وإلغاء الطلب رقم #{order[0]} بنجاح.")
                st.rerun()
            st.write("---")

    # نظام إضافة وإدارة المناديب الجدد وتوزيع الصلاحيات
    st.write("### 👥 إضافة كابتن توصيل جديد للفريق:")
    with st.expander("اضغط لفتح استمارة تسجيل مندوب جديد"):
        new_driver_user = st.text_input("اسم المستخدم للكابتن الجديد (بالإنجليزي وبدون مسافات):")
        new_driver_name = st.text_input("الاسم الكامل للكابتن (العربي):")
        new_driver_pass = st.text_input("كلمة مرور الحساب الجديدة:", type="password")
        
        if st.button("تسجيل واعتماد المندوب في النظام"):
            if new_driver_user and new_driver_name and new_driver_pass:
                try:
                    cursor.execute("INSERT INTO drivers (username, password, full_name, wallet) VALUES (?, ?, ?, ?)",
                                   (new_driver_user, hash_password(new_driver_pass), new_driver_name, 0.0))
                    conn.commit()
                    st.success(f"تم تسجيل الكابتن {new_driver_name} بنجاح، ويمكنه العمل الآن!")
                except sqlite3.IntegrityError:
                    st.error("اسم المستخدم هذا مأخوذ مسبقاً لكابتن آخر، يرجى اختيارات اسم مختلف.")
            else:
                st.error("يرجى ملء جميع الحقول لتسجيل الحساب.")

    # عرض تقارير الحسابات والأرباح العامة وحركة الكباتن
    st.write("### 📈 إحصائيات حركة التوصيل العامة والأرباح:")
    cursor.execute("SELECT COUNT(*), status FROM orders GROUP BY status")
    stats = cursor.fetchall()
    for stat in stats:
        st.metric(label=f"إجمالي الطلبات بحالة ({stat[1]})", value=stat[0])
        
    st.write("### 💳 كشف حسابات محافظ المناديب الميدانية:")
    cursor.execute("SELECT username, full_name, wallet FROM drivers WHERE username != 'admin'")
    all_drivers = cursor.fetchall()
    for dr in all_drivers:
        st.write(f" الكابتن: **{dr[1]}** ({dr[0]}) — أرباح التوصيل المتراكمة: **{dr[2]} ريال**")
        
    conn.close()
