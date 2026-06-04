import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime

# ==========================================
# 1. إعدادات الثيم والتهيئة الأساسية للنظام
# ==========================================
st.set_page_config(
    page_title="تطبيق جايا لك للتوصيل الميداني", 
    page_icon="📦", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# دالة تشفير كلمات المرور لحماية الحسابات وقاعدة البيانات
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 2. إدارة وتأسيس قاعدة البيانات المحلية SQLite
# ==========================================
def init_db():
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # إنشاء جدول الطلبات بكافة الحقول المطلوبة للميدان
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            from_location TEXT NOT NULL,
            to_location TEXT NOT NULL,
            order_details TEXT,
            voice_file TEXT,
            status TEXT NOT NULL,
            driver_name TEXT,
            order_date TEXT NOT NULL,
            delivery_price REAL DEFAULT 0.0,
            closing_date TEXT,
            admin_notes TEXT
        )
    ''')
    
    # إنشاء جدول حسابات كباتن التوصيل والمناديب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            wallet REAL DEFAULT 0.0,
            registration_date TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # التحقق من وجود حساب المدير العام الافتراضي لحماية النظام
    cursor.execute("SELECT * FROM drivers WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO drivers (username, password, full_name, wallet, registration_date, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', hash_password('admin123'), 'المدير العام', 0.0, datetime.now().strftime('%Y-%m-%d'), 1))
        
    conn.commit()
    conn.close()

# تشغيل دالة التهيئة فوراً عند إقلاع التطبيق
init_db()

# ==========================================
# 3. تصميم واجهة المستخدم المتقدمة عبر CSS
# ==========================================
st.markdown("""
    <style>
    /* تصميم الخلفية الشاملة والمحدثة: مواد غذائية، علب بهارات وتوابل زاهية، وخضروات فريش */
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), 
                          url("https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1000");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* تكبير وتنسيق أزرار البوابات الرئيسية الثلاثة لتناسب العمل الميداني السريع */
    .big-button button {
        height: 90px !important;
        font-size: 26px !important;
        font-weight: bold !important;
        background-color: #EA384D !important; /* الأحمر الزاهي الخاص بهوية جايا لك السريعة */
        color: white !important;
        border-radius: 20px !important;
        margin-bottom: 22px !important;
        border: 2.5px solid #000000 !important; /* الأسود لضمان الوضوح الكامل تحت أشعة الشمس */
        box-shadow: 0px 5px 12px rgba(0,0,0,0.18) !important;
        transition: transform 0.2s ease-in-out;
    }
    .big-button button:hover {
        transform: scale(1.02);
    }
    
    /* تكبير وتبريز زر تأكيد وإرسال الطلب النهائي للزبون */
    .submit-button button {
        height: 80px !important;
        font-size: 26px !important;
        font-weight: bold !important;
        background-color: #10B981 !important; /* الأخضر الزاهي للتأكيد السريع المباشر */
        color: white !important;
        border-radius: 16px !important;
        width: 100% !important;
        border: 2px solid #065F46 !important;
        box-shadow: 0px 5px 15px rgba(16, 185, 129, 0.35) !important;
    }
    
    /* تنسيقات كروت تفاصيل الطلبات في لوحة تحكم الإدارة الشاملة */
    .admin-card {
        background-color: #FFFFFF; 
        padding: 22px; 
        border-radius: 14px; 
        border-right: 7px solid #EA384D; 
        margin-bottom: 18px;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
    }
    
    /* محاذاة العناوين والنصوص لتبدو كتطبيق احترافي موجه للشرق الأوسط */
    h1, h2, h3, h4 {
        text-align: center;
        color: #111827;
        font-weight: bold;
    }
    p, label, span {
        text-align: right;
        direction: rtl;
    }
    </style>
""", unsafe_allow_html=True)

# ترويسة التطبيق الرئيسية الثابتة
st.markdown("<h1>📦 تطبيق جايا لك للتوصيل الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-weight:bold; color:#4B5563; font-size:18px;'>النظام التجاري الموحد لخدمة مركز كِتاب والقرى المجاورة</p>", unsafe_allow_html=True)
st.write("---")

# ==========================================
# 4. نظام إدارة جلسات الحفظ والتنقل الداخلي
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# ==========================================
# 5. الواجهة الرئيسية (قائمة البوابات الثلاثة)
# ==========================================
if st.session_state.page == 'main':
    st.write("### 🏪 يرجى اختيار بوابة الدخول للبدء:")
    st.write("")
    
    st.markdown('<div class="big-button">', unsafe_allow_html=True)
    
    if st.button("🙋‍♂️ بوابة طلبات الزبائن (طلب جديد مباشر)", key="main_client_btn", use_container_width=True):
        st.session_state.page = 'client_portal'
        st.rerun()
        
    if st.button("🚗 لوحة كباتن التوصيل (المناديب والمحافظ)", key="main_driver_btn", use_container_width=True):
        st.session_state.page = 'driver_login_portal'
        st.rerun()
        
    if st.button("📊 لوحة التحكم والإشراف العام (المدير)", key="main_admin_btn", use_container_width=True):
        st.session_state.page = 'admin_login_portal'
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. بوابة طلبات الزبائن (واجهة الاستقبال)
# ==========================================
elif st.session_state.page == 'client_portal':
    st.subheader("🙋‍♂️ استمارة تسجيل طلب توصيل جديد")
    
    if st.button("⬅️ العودة للقائمة الرئيسية", key="back_to_main_1"):
        st.session_state.page = 'main'
        st.rerun()
        
    st.write("---")
    
    with st.form("client_order_form", clear_on_submit=True):
        client_name = st.text_input("اسمك الكريم (الاسم الثنائي أو الثلاثي):")
        phone_number = st.text_input("رقم هاتف نشط للتواصل المباشر مع المندوب:")
        
        # التعديل التجاري: إلغاء قائمة القرى في خانة الشراء وتثبيتها حصرياً على المركز الرئيسي
        from_loc = st.selectbox("من أين (موقع شراء وشحن المواد):", ["المركز الرئيسي كِتاب"])
        
        to_loc = st.text_input("إلى أين (اكتب اسم القرية، الحارة، أو المربع السكني بدقة):")
        order_text = st.text_area("تفاصيل المواد المطلوبة (اكتب هنا قائمة السلع، الأوزان، أو أي ملاحظات نصية):")
        
        st.write("🎵 **إرسال ملاحظة صوتية (إذا كنت لا تجيد الكتابة أو تريد شرح طلبك بالتفصيل):**")
        uploaded_voice = st.file_uploader("اضغط لإرفاق أو تسجيل مقطع صوتی للطلب", type=['wav', 'mp3', 'm4a', 'ogg'])
        
        st.write("")
        st.markdown('<div class="submit-button">', unsafe_allow_html=True)
        confirm_order = st.form_submit_button("✅ إرسال وتأكيد الطلب الآن")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if confirm_order:
            if client_name.strip() != "" and phone_number.strip() != "" and to_loc.strip() != "":
                saved_voice_path = None
                
                # معالجة وحفظ الملف الصوتي المرفق بداخل النظام لضمان عدم فقدانه
                if uploaded_voice is not None:
                    if not os.path.exists('saved_voices'):
                        os.makedirs('saved_voices')
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    saved_voice_path = f"saved_voices/voice_{timestamp}_{uploaded_voice.name}"
                    with open(saved_voice_path, "wb") as f:
                        f.write(uploaded_voice.getbuffer())
                
                # حفظ الطلب في قاعدة البيانات بشكل تجاري كامل
                conn = sqlite3.connect('jaya_lak.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO orders (client_name, phone, from_location, to_location, order_details, voice_file, status, driver_name, order_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (client_name, phone_number, from_loc, to_loc, order_text, saved_voice_path, 'قيد الانتظار', '', datetime.now().strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                conn.close()
                
                st.success("🎉 تم إرسال وتأكيد طلبك بنجاح! سيقوم كباتن جايا لك في مركز كِتاب بمراجعة الطلب والتحرك لتسليمه فوراً.")
            else:
                st.error("⚠️ خطأ في الإرسال: يرجى التأكد من كتابة الاسم، رقم الهاتف، وعنوان التوصيل لضمان توجيه الكابتن إليك.")

# ==========================================
# 7. بوابة تسجيل دخول المناديب (كباتن التوصيل)
# ==========================================
elif st.session_state.page == 'driver_login_portal':
    st.subheader("🚗 تسجيل دخول كباتن التوصيل المعتمدين")
    
    if st.button("⬅️ العودة للقائمة الرئيسية", key="back_to_main_2"):
        st.session_state.page = 'main'
        st.rerun()
        
    st.write("---")
    
    d_username = st.text_input("اسم مستخدم المندوب:")
    d_password = st.text_input("كلمة مرور الحساب الميداني:", type="password")
    
    if st.button("🔑 تحقق وتسجيل الدخول"):
        if d_username.strip() != "" and d_password.strip() != "":
            conn = sqlite3.connect('jaya_lak.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE username=? AND password=? AND is_active=1", (d_username, hash_password(d_password)))
            driver_account = cursor.fetchone()
            conn.close()
            
            if driver_account:
                st.session_state.logged_user = d_username
                st.session_state.user_role = 'driver'
                st.session_state.page = 'driver_dashboard_portal'
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة، أو تم إلغاء تنشيط حساب المندوب من قبل الإدارة.")
        else:
            st.warning("يرجى ملء جميع الخانات المخصصة للدخول.")

# ==========================================
# 8. لوحة تحكم المندوب الكاملة (إدارة الأرباح والطلبات)
# ==========================================
elif st.session_state.page == 'driver_dashboard_portal' and st.session_state.user_role == 'driver':
    st.subheader(f"🚗 لوحة العمل الميداني للكابتن: {st.session_state.logged_user}")
    
    if st.button("🚪 تسجيل الخروج الآمن"):
        st.session_state.logged_user = None
        st.session_state.user_role = None
        st.session_state.page = 'main'
        st.rerun()
        
    st.write("---")
    
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # عرض محفظة المندوب المالية لمراقبة أرباح التوصيل بشكل حي ومباشر
    cursor.execute("SELECT wallet, full_name FROM drivers WHERE username=?", (st.session_state.logged_user,))
    driver_data = cursor.fetchone()
    current_wallet = driver_data[0] if driver_data else 0.0
    full_driver_name = driver_data[1] if driver_data else st.session_state.logged_user
    
    st.success(f"مرحباً بك يا كابتن {full_driver_name}")
    st.metric(label="💰 إجمالي أرباحك الحالية المسجلة في محفظة جايا لك:", value=f"{current_wallet} ريال")
    
    st.write("### 📌 الطلبات الجديدة المعلقة حالياً في كِتاب:")
    cursor.execute("SELECT * FROM orders WHERE status='قيد الانتظار' ORDER BY id DESC")
    available_orders = cursor.fetchall()
    
    if not available_orders:
        st.info("ممتاز! لا توجد أي طلبات معلقة بانتظار الشحن في مركز كِتاب حالياً.")
    else:
        for order in available_orders:
            with st.expander(f"📦 طلب توصيل جديد للزبون: {order[1]} 📍 الوجهة: {order[4]}"):
                st.write(f"**نقطة الاستلام والثبات:** {order[3]}")
                st.write(f"**نقطة التوصيل الميداني:** {order[4]}")
                st.write(f"**قائمة السلع والطلبات المكتوبة:** {order[5] if order[5] else 'لا توجد تفاصيل نصية (اكتفى بالصوت)'}")
                
                # تشغيل الصوت المرفق إن وجد
                if order[6]:
                    st.write("🎵 **الملاحظة الصوتية المرفقة من الزبون:**")
                    st.audio(order[6])
                
                st.write("---")
                # تحديد أجرة التوصيل المباشرة للقرية المستهدفة
                driver_price_input = st.number_input(
                    f"حدد تكلفة وأجرة التوصيل للطلب رقم #{order[0]} (بالريال):", 
                    min_value=0.0, 
                    step=100.0, 
                    key=f"d_price_set_{order[0]}"
                )
                
                if st.button(f"🚀 قبول وتولّي شحن الطلب #{order[0]}", key=f"accept_btn_{order[0]}"):
                    if driver_price_input > 0:
                        cursor.execute('''
                            UPDATE orders 
                            SET status='جاري التوصيل', driver_name=?, delivery_price=? 
                            WHERE id=?
                        ''', (st.session_state.logged_user, driver_price_input, order[0]))
                        conn.commit()
                        st.success("تم حجز الطلب باسمك بنجاح! تحرك بسلامة الله لتسليمه.")
                        st.rerun()
                    else:
                        st.error("تنبيه: يجب عليك إدخال سعر التوصيل المتفق عليه أولاً لقبول الطلب.")
                        
    st.write("---")
    st.write("### ⏱️ طلباتك الجاري توصيلها وشحنها الآن بالميدان:")
    cursor.execute("SELECT * FROM orders WHERE status='جاري التوصيل' AND driver_name=?", (st.session_state.logged_user,))
    my_active_orders = cursor.fetchall()
    
    if not my_active_orders:
        st.info("لا تمتلك أي طلبات نشطة جاري توصيلها في هذه اللحظة.")
    else:
        for active_order in my_active_orders:
            with st.expander(f"🚚 طلب نشط رقم #{active_order[0]} — للزبون {active_order[1]}"):
                st.write(f"**رقم هاتف العميل للتنسيق:** {active_order[2]}")
                st.write(f"**العنوان ومسار الشحن الميداني:** {active_order[4]}")
                st.write(f"**أجرة التوصيل المسجلة:** {active_order[10]} ريال")
                st.write(f"**تاريخ الاستلام:** {active_order[9]}")
                
                if st.button(f"🏁 تأكيد إتمام تسليم الطلب وقبض المبلغ رقم #{active_order[0]}", key=f"close_btn_{active_order[0]}"):
                    # تحديث حالة الطلب وإرسال الأرباح المباشرة للمحفظة الإلكترونية للكابتن
                    cursor.execute("UPDATE orders SET status='تم التسليم', closing_date=? WHERE id=?", (datetime.now().strftime('%Y-%m-%d %H:%M'), active_order[0]))
                    cursor.execute("UPDATE drivers SET wallet = wallet + ? WHERE username=?", (active_order[10], st.session_state.logged_user))
                    conn.commit()
                    st.success("كفو يا كابتن! تم إغلاق الطلب بنجاح وإضافة المستحقات المالية لمحفظتك الحالية.")
                    st.rerun()
                    
    conn.close()

# ==========================================
# 9. بوابة تسجيل دخول لوحة تحكم الإدارة
# ==========================================
elif st.session_state.page == 'admin_login_portal':
    st.subheader("📊 تسجيل دخول لوحة الإدارة والتحكم (المالك)")
    
    if st.button("⬅️ العودة للقائمة الرئيسية", key="back_to_main_3"):
        st.session_state.page = 'main'
        st.rerun()
        
    st.write("---")
    
    a_username = st.text_input("اسم مستخدم المسؤول الأول:")
    a_password = st.text_input("كلمة مرور الإدارة السرية:", type="password")
    
    if st.button("🔒 تسجيل الدخول للوحة التحكم"):
        if a_username == 'admin' and hash_password(a_password) == hash_password('admin123'): # كلمة المرور الافتراضية المعتمدة لحسابك
            st.session_state.logged_user = 'admin'
            st.session_state.user_role = 'admin'
            st.session_state.page = 'admin_dashboard_portal'
            st.rerun()
        else:
            st.error("❌ خطأ: اسم المستخدم أو كلمة المرور الخاصة بالإدارة غير صحيحة.")

# ==========================================
# 10. لوحة تحكم الإدارة الشاملة (المدير العام)
# ==========================================
elif st.session_state.page == 'admin_dashboard_portal' and st.session_state.user_role == 'admin':
    st.subheader("📊 لوحة الإشراف المباشر والتحكم العام بالنظام")
    
    if st.button("🚪 تسجيل الخروج الآمن للإدارة"):
        st.session_state.logged_user = None
        st.session_state.user_role = None
        st.session_state.page = 'main'
        st.rerun()
        
    st.write("---")
    
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # التعديل التجاري المعتمد: عرض كافة تفاصيل طلبات الزبائن الجديدة بالتفصيل الكامل للمدير
    st.write("### 🔴 تفاصيل طلبات الزبائن الجديدة الواردة الآن:")
    cursor.execute("SELECT * FROM orders WHERE status='قيد الانتظار' ORDER BY id DESC")
    current_new_orders = cursor.fetchall()
    
    if not current_new_orders:
        st.info("لا توجد طلبات جديدة معلقة من قبل الزبائن في النظام حالياً.")
    else:
        for order in current_new_orders:
            # بناء كرت كامل وتفصيلي وبألوان تبرز البيانات للمالك لمنع الفقدان
            st.markdown(f"""
            <div class="admin-card">
                <h4 style="margin: 0; color: #EA384D; text-align: right;">📦 طلب معلق جديد رقم #{order[0]}</h4>
                <p style="margin: 6px 0; font-size: 16px;"><b>👤 اسم الزبون الكريم:</b> {order[1]}</p>
                <p style="margin: 6px 0; font-size: 16px;"><b>📞 رقم الهاتف للتواصل:</b> {order[2]}</p>
                <p style="margin: 6px 0; font-size: 16px;"><b>📍 مسار وخريطة التوصيل:</b> من <span style="color: #10B981; font-weight: bold;">{order[3]}</span> إلى <span style="color: #EA384D; font-weight: bold;">{order[4]}</span></p>
                <p style="margin: 6px 0; font-size: 16px;"><b>📝 تفاصيل ومواد الطلب المكتوبة:</b> {order[5] if order[5] else 'لم يكتب تفاصيل نصية (اكتفى بالملاحظة الصوتية المرفقة)'}</p>
                <p style="margin: 6px 0; color: #4B5563; font-size: 13px;"><small>📅 وقت تاريخ إرسال الطلب للنظام: {order[9]}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # تشغيل الصوت المرفق بالطلب أسفل الكرت مباشرة لسهولة المتابعة من المالك
            if order[6]:
                st.write("🎵 **الملاحظة الصوتية للطلب:**")
                st.audio(order[6])
                
            if st.button(f"❌ إلغاء وحذف هذا الطلب المعلق من السجلات (#{order[0]})", key=f"admin_del_btn_{order[0]}"):
                cursor.execute("DELETE FROM orders WHERE id=?", (order[0],))
                conn.commit()
                st.warning(f"تم حذف وإلغاء الطلب رقم #{order[0]} بنجاح من قاعدة البيانات.")
                st.rerun()
            st.write("---")

    # نظام إدارة وتسجيل كباتن التوصيل الجدد وتوزيع الصلاحيات الميدانية
    st.write("### 👥 إدارة وأرشفة طاقم المناديب (إضافة كابتن جديد):")
    with st.expander("اضغط هنا لفتح استمارة تسجيل مندوب جديد للفريق"):
        reg_username = st.text_input("اسم مستخدم الحساب الجديد (بالأحرف الإنجليزية فقط وبدون مسافات):")
        reg_full_name = st.text_input("الاسم الكامل والرباعي للكابتن الجديد:")
        reg_password = st.text_input("تعيين كلمة مرور الحساب الميداني:", type="password")
        
        if st.button("📋 اعتماد وحفظ الكابتن في النظام"):
            if reg_username.strip() != "" and reg_full_name.strip() != "" and reg_password.strip() != "":
                try:
                    cursor.execute('''
                        INSERT INTO drivers (username, password, full_name, wallet, registration_date, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (reg_username.strip(), hash_password(reg_password), reg_full_name.strip(), 0.0, datetime.now().strftime('%Y-%m-%d'), 1))
                    conn.commit()
                    st.success(f"🎉 تم تسجيل واعتماد المندوب الجديد [{reg_full_name}] في نظام جايا لك بنجاح!")
                except sqlite3.IntegrityError:
                    st.error("خطأ: اسم المستخدم بالإنجليزي مسجل مسبقاً لكابتن آخر، يرجى اختيار اسم مختلف.")
            else:
                st.error("يرجى ملء جميع الخانات المطلوبة لإتمام عملية تسجيل الحساب الميداني.")

    # الإحصائيات الشاملة والتقارير المالية لحركة المحل والتوصيل
    st.write("---")
    st.write("### 📈 إحصائيات وتقارير أداء التطبيق العام:")
    
    cursor.execute("SELECT COUNT(*), status FROM orders GROUP BY status")
    application_stats = cursor.fetchall()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📥 طلبات قيد الانتظار", value=next((x[0] for x in application_stats if x[1] == 'قيد الانتظار'), 0))
    with col2:
        st.metric(label="🚚 طلبات جاري توصيلها", value=next((x[0] for x in application_stats if x[1] == 'جاري التوصيل'), 0))
    with col3:
        st.metric(label="🏁 طلبات تم تسليمها بنجاح", value=next((x[0] for x in application_stats if x[1] == 'تم التسليم'), 0))

    st.write("### 💳 كشف حسابات ومستحقات محافظ المناديب الحالية:")
    cursor.execute("SELECT username, full_name, wallet FROM drivers WHERE username != 'admin'")
    all_active_drivers = cursor.fetchall()
    
    if not all_active_drivers:
        st.info("لا يوجد مناديب مسجلين في النظام حالياً.")
    else:
        for driver in all_active_drivers:
            st.write(f" الكابتن الميداني: **{driver[1]}** ({driver[0]}) — إجمالي مستحقاته وأرباحه بالتطبيق: **{driver[2]} ريال**")
            
    conn.close()
# ==========================================
# نهاية الكود البرمجي التجاري لملف جايا لك
# ==========================================
