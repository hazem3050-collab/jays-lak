import streamlit as st

# 1. خدمة العرض المطور لتفاصيل طلبات الزبائن في لوحة المدير
def car_details_admin(order):
    """
    هذه الخدمة تأخذ بيانات الطلب وترتبها داخل كرت أبيض مريح للعين 
    ومناسب للقراءة تحت أشعة الشمس في الميدان لمالك المشروع.
    """
    st.markdown(f"""
    <div class="admin-card" style="background-color: #FFFFFF; padding: 22px; border-radius: 14px; border-right: 7px solid #EA384D; margin-bottom: 18px; box-shadow: 0px 3px 10px rgba(0,0,0,0.08);">
        <h4 style="margin: 0; color: #EA384D; text-align: right;">📦 طلب معلق جديد رقم #{order[0]}</h4>
        <p style="margin: 6px 0; font-size: 16px; text-align: right; direction: rtl;"><b>👤 اسم الزبون الكريم:</b> {order[1]}</p>
        <p style="margin: 6px 0; font-size: 16px; text-align: right; direction: rtl;"><b>📞 رقم الهاتف للتواصل:</b> {order[2]}</p>
        <p style="margin: 6px 0; font-size: 16px; text-align: right; direction: rtl;"><b>📍 مسار وخريطة التوصيل:</b> من <span style="color: #10B981; font-weight: bold;">{order[3]}</span> إلى <span style="color: #EA384D; font-weight: bold;">{order[4]}</span></p>
        <p style="margin: 6px 0; font-size: 16px; text-align: right; direction: rtl;"><b>📝 تفاصيل ومواد الطلب المكتوبة:</b> {order[5] if order[5] else 'لم يكتب تفاصيل نصية (اكتفى بالملاحظة الصوتية المرفقة)'}</p>
        <p style="margin: 6px 0; color: #4B5563; font-size: 13px; text-align: right; direction: rtl;"><small>📅 وقت تاريخ إرسال الطلب للنظام: {order[9]}</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # تشغيل الملاحظة الصوتية المرفقة بالطلب تلقائياً إن وجدت
    if order[6]:
        st.write("🎵 **الملاحظة الصوتية للطلب:**")
        st.audio(order[6])

# 2. خدمة الحسابات التلقائية لتوزيع أرباح التوصيل ونسبة التطبيق
def calculate_commission(delivery_price, commission_rate=0.10):
    """
    هذه الخدمة تحتسب نسبة التطبيق (10% تلقائياً) وتفصل صافي ربح المندوب
    لضمان دقة الحسابات اليومية ومنع الاختلافات الميدانية.
    """
    app_commission = delivery_price * commission_rate
    driver_net = delivery_price - app_commission
    return driver_net, app_commission