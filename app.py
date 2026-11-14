import streamlit as st
import sqlite3
import random

# ==========================================
# 🛑 إنشاء وتحديث قاعدة البيانات والربط الدائم
# ==========================================
def init_db():
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    
    # 1. إنشاء جدول الشحنات والطلبات
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
            payment_method TEXT
        )
    ''')
    
    # فحص لضمان مطابقة الأعمدة 100%
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'payment_method' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'دفع نقدي كاش (عند الاستلام)'")
    if 'driver' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN driver TEXT DEFAULT 'لم يحدد'")
        
    # 2. جدول إدارة المناديب الميدانيين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            assigned_village TEXT
        )
    ''')
    
    # 3. 🔐 جدول حفظ كلمة مرور الإدارة ديناميكياً
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # تعيين كلمة المرور الافتراضية إذا لم تكن موجودة مسبقاً
    cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings VALUES ('admin_password', 'admin123')")
        
    # إضافة مناديب تجريبيين إذا كان الجدول فارغاً
    cursor.execute("SELECT COUNT(*) FROM drivers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO drivers VALUES ('DRV-101', 'كابتن علي اليماني', '771111111', 'قرية المنزل')")
        cursor.execute("INSERT INTO drivers VALUES ('DRV-102', 'كابتن محمد الحاشدي', '772222222', 'قرى الصفي')")
        
    conn.commit()
    conn.close()

# تشغيل قاعدة البيانات فوراً
init_db()

# جلب كلمة المرور الحالية من قاعدة البيانات
def get_admin_password():
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
    pwd = cursor.fetchone()[0]
    conn.close()
    return pwd

# تحديث كلمة المرور في قاعدة البيانات
def update_admin_password(new_pwd):
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_pwd,))
    conn.commit()
    conn.close()

# إعدادات واجهة المستخدم
st.set_page_config(
    page_title="نظام جايا لك الذكي - الإصدار الميداني المتكامل",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تحسين المظهر بالتنسيق اليميني (RTL) والألوان الفاخرة لـ "جايا لك"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #e2e8f0; border-radius: 8px; padding: 12px 24px; font-weight: bold; color: #334155;
    }
    .stTabs [aria-selected="true"] { background-color: #0f172a !important; color: white !important; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); margin-bottom: 15px; border: 1px solid #e2e8f0; }
    .emergency-panel { background-color: #fef2f2; border-right: 6px solid #dc2626; padding: 15px; border-radius: 8px; }
    .jeeb-panel { background-color: #f0fdf4; border-right: 6px solid #0d9488; padding: 15px; border-radius: 8px; font-weight: bold; }
    .success-panel { background-color: #f0fdf4; border-right: 6px solid #16a34a; padding: 15px; border-radius: 8px; }
    .price-tag { background-color: #eff6ff; color: #1d4ed8; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 19px; border: 1px dashed #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# الهيدر الرسمي للمؤسسة
st.markdown("<h1 style='text-align: center; color: #0f172a; margin-bottom: 0;'>📦  جَايَا لَك للتوصيل</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px;'>النظام البرمجي المتكامل لإدارة اللوجستيات ونقاط البيع وبوابات الدفع الريفية</p>", unsafe_allow_html=True)
st.write("---")

tab_client, tab_manager, tab_driver, tab_pos = st.tabs(["👤 بوابة العميل", "💼 لوحة المدير والتحكم", "🛵 واجهة المندوب الميداني", "🏪 شبكة نقاط المبيعات"])

# 🛑 قاعدة بيانات القرى والأسعار الرسمية المعتمدة
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
# 1. بوابة العميل (التسعير الذكي + خيار دفع محفظة جيب)
# -------------------------------------------------------------------------
with tab_client:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📝 نموذج طلب شحنة جديدة")
    
    c_name = st.text_input("الاسم الرباعي للمرسل/المستقبل *", key="client_name_input")
    c_phone = st.text_input("رقم الهاتف (الخلوي) المكون من 9 أرقام *", max_chars=9, key="client_phone_input")
    
    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        from_loc = st.selectbox("نقطة الاستلام (من أين؟) *", list(villages_db.keys()), key="from_loc_select")
    with col_loc2:
        to_loc = st.selectbox("نقطة التسليم (إلى أين؟) *", list(villages_db.keys()), key="to_loc_select")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("⚖️ تفاصيل وحجم الشحنة الميدانية")
    weight_opt = st.selectbox("اختر حجم ونوع الشحنة:", ["📦 خفيفة", "📦 متوسطة", "📦 ثقيلة"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📱 خيارات الطلب والدفع المتقدمة")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        pay_opt = st.radio("💳 آلية تسديد رسوم التوصيل:", ["دفع نقدي كاش (عند الاستلام)", "خصم من نقاط البيع المعتمدة", "📱 عبر محفظة جيب الإلكترونية"])
    
    with col_btn2:
        st.markdown("<div class='emergency-panel'>", unsafe_allow_html=True)
        is_emergency = st.checkbox("🚨 تصنيف الطلب كـ (حالة طوارئ مستعجلة)")
        st.caption("ملاحظة: طلبات الطوارئ تحسب تلقائياً بسعر الشحنة الثقيلة لضمان السرعة الأقصى للتحرك.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if pay_opt == "📱 عبر محفظة جيب الإلكترونية":
        st.markdown("<div class='jeeb-panel'>📲 يرجى تحويل الرصيد إلى حساب جيب رقم: (541419) التابع لإدارة جايا لك، ثم أدخل رقم العملية بالأسفل للتوثيق.</div><br>", unsafe_allow_html=True)
        jeeb_tx_id = st.text_input("أدخل رقم إشعار التحويل / رقم العملية:")
        
    st.markdown("</div>", unsafe_allow_html=True)

    light_price = max(villages_db[from_loc]["light"], villages_db[to_loc]["light"])
    heavy_price = max(villages_db[from_loc]["heavy"], villages_db[to_loc]["heavy"])
    medium_price = int((light_price + heavy_price) / 2)

    if is_emergency:
        final_cost = heavy_price
        display_type = "🚨 طوارئ (معاملة ثقيلة)"
    else:
        if "خفيفة" in weight_opt:
            final_cost = light_price
            display_type = "عادي - خفيفة"
        elif "متوسطة" in weight_opt:
            final_cost = medium_price
            display_type = "عادي - متوسطة"
        else:
            final_cost = heavy_price
            display_type = "عادي - ثقيلة"

    st.markdown(f"<div class='price-tag'>💰 التكلفة المعتمدة للرحلة: {final_cost} ريال يمني</div><br>", unsafe_allow_html=True)

    if st.button("🚀 إرسال وتأكيد الطلب نهائياً"):
        if not c_name.strip():
            st.error("❌ خطأ: لا يمكن ترك حقل 'الاسم الرباعي' فارغاً.")
        elif not c_phone.isdigit() or len(c_phone) < 9:
            st.error("❌ خطأ: رقم الهاتف غير صحيح. يجب أن يتكون من 9 أرقام.")
        elif from_loc == to_loc:
            st.error("❌ تنبيه: نقطة الاستلام ونقطة التسليم متطابقتان، يرجى مراجعة المسار الجغرافي.")
        else:
            with st.spinner("جاري توثيق الشحنة وحفظها برقم مالي فريد..."):
                order_id = f"GL-{random.randint(103, 999)}"
                
                conn = sqlite3.connect('jaya_lak.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (order_id, c_name, c_phone, from_loc, to_loc, display_type, "بانتظار الموافقة", final_cost, "لم يحدد", pay_opt)
                )
                conn.commit()
                conn.close()
                
                st.balloons()
                st.markdown(f"<div class='success-panel'>🎉 تم تسجيل طلبك بنجاح! كود التتبع: {order_id} | طريقة الدفع: {pay_opt} | التكلفة: {final_cost} ريال يمني.</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. لوحة تحكم المدير (تعديل وحذف المناديب يدويآ وتغيير كلمة المرور 🔐)
# -------------------------------------------------------------------------
with tab_manager:
    st.markdown("### 💼 غُرفة العمليات والتحكم الإداري للمؤسسة")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    password_input = st.text_input("🔑 يرجى إدخال كلمة مرور الإدارة لفتح النظام:", type="password")
    st.markdown("</div>", unsafe_allow_html=True)
    
    current_saved_pwd = get_admin_password()
    
    if password_input == current_saved_pwd:
        st.success("🔓 تم التحقق بنجاح. مرحباً بك في لوحة التحكم الإدارية.")
        
        # ⚙️ قسم تعديل إعدادات كلمة المرور من التطبيق مباشرة
        with st.sidebar:
            st.markdown("### 🛠️ إعدادات الحماية المركزية")
            new_sys_pwd = st.text_input("تحديث كلمة مرور الإدارة الحالية:", value=current_saved_pwd, type="password")
            if st.button("💾 حفظ كلمة المرور الجديدة"):
                if new_sys_pwd.strip() != "":
                    update_admin_password(new_sys_pwd.strip())
                    st.success("🔄 تم تغيير كلمة المرور في قاعدة البيانات بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ لا يمكن ترك كلمة المرور فارغة.")
        
        st.write("---")
        
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
            
            orders_db.append({
                "رقم الشحنة": r[0], "العميل": r[1], "الهاتف": r[2], "من": r[3], "إلى": r[4], 
                "النوع": r[5], "الحالة": r[6], "التكلفة": r[7], "المندوب الموجه": drv_info["name"], "طريقة الدفع": p_method
            })
            if r[6] == "تم التسليم ✅":
                delivered_revenue += r[7]
                
        total_orders = len(orders_db)
        pending_orders = len([o for o in orders_db if o["الحالة"] == "بانتظار الموافقة"])
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("إجمالي طلبات النظام", f"{total_orders} طلبات")
        m_col2.metric("طلبات معلقة بانتظار ناقل", f"{pending_orders} طلبات")
        m_col3.metric("الخزنة والأرباح المحصلة فعلياً", f"{delivered_revenue:,} ريال يمني")
        
        st.write("---")
        
        # 👥 وحدة إدارة المناديب: إضافة، تعديل، وحذف يدوي بالكامل
        st.markdown("#### 👥 وحدة التحكم والفرز الخاصة بالمناديب الميدانيين")
        tab_add_drv, tab_edit_drv = st.tabs(["➕ إضافة مندوب جديد", "🛠️ تعديل وحذف مندوب حالي"])
        
        with tab_add_drv:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                new_drv_name = st.text_input("اسم الكابتن الميداني الرباعي:")
                new_drv_phone = st.text_input("رقم هاتف المندوب (9 أرقام):", max_chars=9, key="add_drv_phone")
            with col_d2:
                new_drv_village = st.selectbox("القرية الرئيسية المسؤول عنها وعن تغطيتها:", list(villages_db.keys()), key="add_drv_vil")
                
            if st.button("💾 حفظ المندوب الجديد"):
                if new_drv_name.strip() and new_drv_phone.isdigit() and len(new_drv_phone) == 9:
                    drv_id = f"DRV-{random.randint(103, 999)}"
                    cursor.execute("INSERT INTO drivers VALUES (?, ?, ?, ?)", (drv_id, new_drv_name, new_drv_phone, new_drv_village))
                    conn.commit()
                    st.success(f"✅ تم حفظ المندوب {new_drv_name} بنجاح وتعيينه لـ {new_drv_village}!")
                    st.rerun()
                else:
                    st.error("❌ خطأ: يرجى كتابة اسم المندوب ورقم هاتف صحيح مكون من 9 أرقام.")
                    
        with tab_edit_drv:
            if driver_rows_db:
                drv_select_options = {r[0]: f"{r[1]} ({r[3]})" for r in driver_rows_db}
                selected_edit_id = st.selectbox("اختر المندوب المستهدف لإجراء التعديل أو الحذف:", list(drv_select_options.keys()), format_func=lambda x: drv_select_options[x])
                
                # جلب بيانات المندوب المحدد حالياً للنموذج
                cursor.execute("SELECT * FROM drivers WHERE id=?", (selected_edit_id,))
                curr_drv_data = cursor.fetchone()
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_name = st.text_input("تعديل الاسم الرباعي:", value=curr_drv_data[1])
                    edit_phone = st.text_input("تعديل رقم الهاتف:", value=curr_drv_data[2], max_chars=9)
                with col_e2:
                    edit_village = st.selectbox("تعديل عزلة/قرية التغطية:", list(villages_db.keys()), index=list(villages_db.keys()).index(curr_drv_data[3]))
                
                col_actions = st.columns(2)
                with col_actions[0]:
                    if st.button("📝 تحديث بيانات المندوب فوراً"):
                        if edit_name.strip() and edit_phone.isdigit() and len(edit_phone) == 9:
                            cursor.execute("UPDATE drivers SET name=?, phone=?, assigned_village=? WHERE id=?", (edit_name, edit_phone, edit_village, selected_edit_id))
                            conn.commit()
                            st.success("✅ تم تحديث بيانات الكابتن بنجاح في قاعدة البيانات الميدانية.")
                            st.rerun()
                        else:
                            st.error("❌ يرجى التحقق من صحة البيانات المُدخلة.")
                            
                with col_actions[1]:
                    if st.button("🗑️ حذف المندوب نهائياً من المؤسسة"):
                        cursor.execute("DELETE FROM drivers WHERE id=?", (selected_edit_id,))
                        conn.commit()
                        st.warning("⚠️ تم حذف المندوب وتفريغ مسار تغطيته بنجاح.")
                        st.rerun()
            else:
                st.info("🟢 لا يوجد مناديب مضافين حالياً لتعديلهم أو حذفهم.")
                
        st.write("---")
        st.markdown("#### 📊 جدول فرز وإدارة الشحنات الميدانية الفوري")
        st.dataframe(orders_db, use_container_width=True)
        
        st.write("---")
        st.markdown("#### 🎮 وحدة التوجيه الفوري (إسناد المهام للمناديب)")
        assignable_orders = [o["رقم الشحنة"] for o in orders_db if o["الحالة"] == "بانتظار الموافقة"]
        
        if assignable_orders:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                selected_order_id = st.selectbox("اختر رقم الطلب المعلق لتوجيهه للقرية:", assignable_orders)
                cursor.execute("SELECT to_loc FROM orders WHERE id=?", (selected_order_id,))
                order_destination = cursor.fetchone()[0]
                st.caption(f"📍 وجهة هذه الشحنة هي: **{order_destination}**")
                
            with col_m2:
                if driver_rows_db:
                    driver_options = {r[0]: f"{r[1]} (يغطي: {r[3]})" for r in driver_rows_db}
                    selected_driver_id = st.selectbox("اختر الكابتن لتعميد الحركة له:", list(driver_options.keys()), format_func=lambda x: driver_options[x])
                else:
                    selected_driver_id = None
                    st.warning("⚠️ لا يوجد أي مندوب مضاف في النظام حالياً لتوجيهه.")
                
            if st.button("⚡ تعميد وتوجيه المندوب للموقع فوراً") and selected_driver_id:
                cursor.execute("UPDATE orders SET status='جاري التوصيل', driver=? WHERE id=?", (selected_driver_id, selected_order_id))
                conn.commit()
                st.success("✅ تم توجيه المندوب وحفظ المهمة في حسابه الميداني بنجاح.")
                conn.close()
                st.rerun()
        else:
            st.info("🟢 لا توجد أي طلبات معلقة حالياً بحاجة لتعيين يدوي.")
        conn.close()
        
    elif password_input != "":
        st.error("❌ كلمة المرور غير صحيحة! يرجى التواصل مع إدارة النظام المركزية.")

# -------------------------------------------------------------------------
# 3. واجهة المندوب الميداني
# -------------------------------------------------------------------------
with tab_driver:
    st.markdown("### 🛵 واجهة لوجستيات المندوب الميداني")
    
    conn = sqlite3.connect('jaya_lak.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers")
    drvs = cursor.fetchall()
    
    if drvs:
        drvs_choices = {r[0]: f"{r[1]} - هاتف: {r[2]}" for r in drvs}
        active_driver_id = st.selectbox("قم باختيار اسمك لتسجيل الدخول الميداني لرؤية مهامك:", list(drvs_choices.keys()), format_func=lambda x: drvs_choices[x])
        
        cursor.execute("SELECT * FROM orders WHERE status='جاري التوصيل'")
        all_active_missions = cursor.fetchall()
        
        driver_missions = [m for m in all_active_missions if len(m) > 8 and m[8] == active_driver_id]
        
        if driver_missions:
            st.warning(f"⚠️ كابتن، لديك ({len(driver_missions)}) مهمة نشطة جارية في الميدان حالياً:")
            for m in driver_missions:
                p_method_drv = m[9] if len(m) > 9 else "دفع نقدي كاش (عند الاستلام)"
                st.markdown(f"""
                <div class='card'>
                <b>🔢 رقم الشحنة:</b> {m[0]} | <b>📦 نوع وحجم الشحنة:</b> {m[5]}<br>
                <b>📍 المسار الجغرافي:</b> من [ {m[3]} ] 👈 إلى [ {m[4]} ]<br>
                <b>👤 اسم الزبون:</b> {m[1]} | <b>📞 هاتف التواصل:</b> {m[2]}<br>
                <b>💳 طريقة السداد المتفق عليها:</b> {p_method_drv}<br>
                <b>💰 المبلغ المطلوب تحصيله وتصفيته:</b> <span style='color:red; font-weight:bold;'>{m[7]:,} ريال يمني</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✅ تأكيد تسليم الشحنة {m[0]} واستلام وتحصيل المبلغ", key=f"btn_delivery_{m[0]}"):
                    cursor.execute("UPDATE orders SET status='تم التسليم ✅' WHERE id=?", (m[0],))
                    conn.commit()
                    st.success(f"🎉 عمل رائع ومحترف! تم توثيق تسليم الشحنة {m[0]} بنجاح وتحويل المبلغ للخزنة الموحدة.")
                    conn.close()
                    st.rerun()
        else:
            st.info("🟢 جدولك فارغ حالياً يا كابتن. لا توجد أي مهام معلقة في مسار حركتك.")
    else:
        st.info("ℹ️ لم يقم المدير بإضافة أي مناديب يدوياً حتى الآن. يرجى الذهاب للوحة المدير وإضافة مناديب أولاً لكي تظهر الأسماء هنا.")
    conn.close()

# -------------------------------------------------------------------------
# 4. شبكة نقاط المبيعات والمحفظة
# -------------------------------------------------------------------------
with tab_pos:
    st.markdown("### 🏪 شبكة نقاط المبيعات ومحفظة جيب الإلكترونية")
    
    st.markdown(f"""
    <div class='card' style='border-right: 6px solid #0d9488;'>
    <h5>📱 بوابة الدفع الرقمية (محفظة جيب - Jeeb)</h5>
    <b>رقم النقطة المعتمد والمربوط برمجياً لمؤسسة جايا لك:</b> <span style='color:#0d9488; font-weight:bold;'>541419</span><br>
    <b>الحالة التقنية:</b> متصل بالبوابة ومستعد لاستقبال الإشعارات والتحويلات الميدانية 🟢
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    <h5>🏪 المركز الرئيسي - إدارة جايا لك</h5>
    <b>الموقع الجغرافي:</b> وسط مدينة كتاب - بهارات حازم الهتار <br>
    <b>حالة النقطة التشغيلية:</b> نشط ومربوط بـ 18 قرية وعزلة 🟢
    </div>
    """, unsafe_allow_html=True)
