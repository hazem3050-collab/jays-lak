import streamlit as st
import pandas as pd

def show_menu_manager():
    st.title("🏪 لوحة تحكم المدير - إدارة الأصناف والأسعار")
    st.markdown("---")

    # نظام لحفظ الأصناف في ذاكرة التطبيق المؤقتة (حتى لا تضيع عند تحديث الصفحة)
    if 'menu_items' not in st.session_state:
        # أصناف تجريبية مبدئية يمكن للمدير حذفها أو التعديل عليها
        st.session_state.menu_items = [
            {"الصنف": "وجبة شاورما دبل", "السعر": 25.0, "القسم": "وجبات"},
            {"الصنف": "برجر لحم فاخر", "السعر": 30.0, "القسم": "وجبات"},
            {"الصنف": "عصير برتقال فريش", "السعر": 12.0, "القسم": "مشروبات"}
        ]

    # --- القسم الأول: استمارة إضافة صنف جديد يدوياً ---
    st.subheader("➕ إضافة صنف جديد للقائمة")
    
    # نموذج (Form) لإدخال البيانات يدويًا بضغطة زر واحدة
    with st.form(key='add_item_form', clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_item_name = st.text_input("📦 اسم الصنف (مثال: بيتزا خضار):")
        with col2:
            new_item_price = st.number_input("💰 سعر الصنف (ريال/دولار):", min_value=0.0, step=0.5)
        with col3:
            new_item_category = st.selectbox("📂 القسم:", ["وجبات", "مشروبات", "مقبلات", "حلويات", "أخرى"])
            
        submit_button = st.form_submit_button(label='➕ إضافة الصنف الآن')

    # معالجة الضغط على زر الإضافة
    if submit_button:
        if new_item_name.strip() == "":
            st.error("⚠️ عذراً، لا يمكنك ترك اسم الصنف فارغاً!")
        else:
            # إضافة الصنف الجديد إلى القائمة
            st.session_state.menu_items.append({
                "الصنف": new_item_name,
                "السعر": new_item_price,
                "القسم": new_item_category
            })
            st.success(f"✅ تم إضافة الصنف '{new_item_name}' بنجاح إلى القائمة!")

    # --- القسم الثاني: عرض قائمة الأصناف الحالية والتحكم بها ---
    st.markdown("---")
    st.subheader("📋 قائمة الأصناف والأسعار الحالية")

    if len(st.session_state.menu_items) > 0:
        # تحويل القائمة إلى جدول منظم لعرضه للمدير
        df = pd.DataFrame(st.session_state.menu_items)
        
        # عرض الجدول بشكل احترافي ومرتب في واجهة التطبيق
        st.dataframe(df, use_container_width=True)
        
        # ميزة إضافية: إمكانية حذف أي صنف يدوياً إذا رغب المدير
        st.markdown("🗑️ **حذف صنف من القائمة:**")
        items_list = [item["الصنف"] for item in st.session_state.menu_items]
        item_to_delete = st.selectbox("اختر الصنف المراد حذفه:", items_list)
        
        if st.button("❌ حذف الصنف المحدد"):
            st.session_state.menu_items = [item for item in st.session_state.menu_items if item["الصنف"] != item_to_delete]
            st.warning(f"🗑️ تم حذف الصنف '{item_to_delete}' من القائمة.")
            st.rerun() # إعادة إنعاش الصفحة لتحديث الجدول فوراً
            
    else:
        st.info("ℹ️ القائمة فارغة حالياً، قم بإضافة أصناف جديدة باستخدام النموذج أعلاه.")

# لتشغيل الملف بشكل مستقل وتجربته فوراً
if __name__ == "__main__":
    show_menu_manager()