"""
pages/8_Admin_and_Settings.py — Creator Control Center & Multi-User Admin Hub
=============================================================================
PURPOSE:
  Empowers BUDZ (app creator/owner) to manage all user wardrobes, inspect closets,
  seed capsule collections, perform batch operations, export backups, and monitor
  the image processing and background removal engine.
"""

import os
import io
import sys
import json
import zipfile
import pandas as pd
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from config.settings import (
    USER_DATA_DIR, WARDROBE_SCHEMA, SAMPLE_WARDROBE_FILE
)
from src.user_manager import (
    DEFAULT_ADMIN_USER, get_active_user, set_active_user, list_users,
    create_user, delete_user, get_user_data_dir, get_user_wardrobe_file,
    get_user_images_dir, is_master_authenticated, verify_master_pin,
    get_master_pin, set_master_pin, logout_master
)
from src.data_manager import load_wardrobe, save_wardrobe, import_sample_data
from src.theme_helper import apply_editorial_theme
from src.image_processor import remove_background

st.set_page_config(
    page_title="Creator & Admin Hub — FitChecker",
    page_icon="⚙️",
    layout="wide"
)

# Apply editorial styling and sidebar user switcher
apply_editorial_theme()

# Master Security Gatekeeper: Block unauthorized access completely
if not is_master_authenticated():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #DDD1C2; border-radius: 14px; padding: 36px 28px; text-align: center; max-width: 520px; margin: 30px auto; box-shadow: 0 4px 16px rgba(74, 53, 43, 0.06);">
        <div style="font-size: 42px; margin-bottom: 12px;">🔒👑</div>
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #241C18; margin-bottom: 8px;">
            Master Creator Access Only
        </div>
        <div style="font-size: 13.5px; color: #704E38; margin-bottom: 20px; line-height: 1.5;">
            This control center oversees all user wardrobes, backups, and administrative settings. Enter your Master PIN to unlock privileges.
        </div>
    </div>
    """, unsafe_allow_html=True)
    c_p1, c_p2, c_p3 = st.columns([1, 1.6, 1])
    with c_p2:
        with st.form("admin_pin_form"):
            entered_pin = st.text_input("Master PIN", type="password", placeholder="Enter PIN")
            sub_pin = st.form_submit_button("Unlock Creator Controls", type="primary", use_container_width=True)
            if sub_pin:
                if verify_master_pin(entered_pin):
                    set_active_user(DEFAULT_ADMIN_USER)
                    st.success("Master Creator Privileges Verified!")
                    st.rerun()
                else:
                    st.error("Incorrect Master PIN.")
    st.stop()

# Page Header (Only visible to verified Master Creator)
current_user = get_active_user()
st.title("⚙️ Creator & Admin Control Center")
st.caption(f"Master administrative management and multi-user closet hub · Active Master: **{current_user}**")

st.markdown("""
<div style="background: linear-gradient(135deg, #4A352B 0%, #2E2019 100%); color: #F5EFEB; border-radius: 14px; padding: 18px 24px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(46, 32, 25, 0.15);">
    <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;">
        👑 Welcome, Master Creator (BUDZ)
    </div>
    <div style="font-size: 13.5px; opacity: 0.9; line-height: 1.5;">
        You have master administrative privileges to oversee all friend and guest wardrobes, push updates, seed sample capsules, inspect cutouts, and manage system backups.
    </div>
</div>
""", unsafe_allow_html=True)

tab_users, tab_ops, tab_diag, tab_system = st.tabs([
    "👥 User Wardrobes Overview",
    "⚡ Batch Operations & Seeding",
    "✂️ Background Cutout Diagnostic",
    "📊 System Health & Storage"
])

# ─────────────────────────────────────────────
# TAB 1: USER CLOSETS OVERVIEW
# ─────────────────────────────────────────────
with tab_users:
    st.subheader("All Registered Digital Wardrobes")
    st.markdown("Every friend or guest who creates a wardrobe gets a 100% isolated private directory with their own garments, images, and skin-tone profile.")

    all_users = list_users()

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    total_closets = len(all_users)
    total_items = sum(u.get("items_count", 0) for u in all_users)
    m1.metric("Total Digital Closets", total_closets)
    m2.metric("Total Garments Across All Closets", total_items)
    m3.metric("Creator Account", DEFAULT_ADMIN_USER)

    st.markdown("---")

    # User Cards / Management Table
    for u in all_users:
        uid = u["user_id"]
        dname = u.get("display_name", uid)
        item_cnt = u.get("items_count", 0)
        gender = u.get("gender", "Boy")
        skin_tone = u.get("skin_tone", "Standard")
        is_u_admin = (uid == DEFAULT_ADMIN_USER)
        is_active = (uid == current_user)

        badge = "👑 CREATOR / ADMIN" if is_u_admin else "👤 GUEST CLOSET"
        badge_color = "#8C3B1E" if is_u_admin else "#2D5A27"
        border_color = "#8C3B1E" if is_active else "#E5E0D8"
        bg_color = "#FFFDF9" if is_active else "#FFFFFF"

        st.markdown(f"""
        <div style="background: {bg_color}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(74, 53, 43, 0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #241C18;">{dname}</span>
                    <span style="font-size: 12px; color: #704E38; margin-left: 8px;">(@{uid})</span>
                    <span style="background: {badge_color}; color: #FFFFFF; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">{badge}</span>
                    { '<span style="background: #D4AF37; color: #241C18; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px; margin-left: 6px;">CURRENTLY ACTIVE</span>' if is_active else '' }
                </div>
                <div style="font-size: 13px; font-weight: 600; color: #4A352B;">
                    {item_cnt} Garments · {gender} · {skin_tone}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.8, 1.5, 1.2])

        with col_act1:
            if not is_active:
                if st.button(f"🔍 Switch to {dname}", key=f"btn_switch_{uid}"):
                    set_active_user(uid)
                    st.success(f"Switched active closet to {dname}!")
                    st.rerun()
            else:
                st.button("✅ Active Closet", disabled=True, key=f"btn_act_{uid}")

        with col_act2:
            if st.button(f"✨ Seed 25 Pieces to {uid}", key=f"btn_seed_{uid}"):
                num = import_sample_data(user_id=uid)
                if num > 0:
                    st.success(f"Added {num} starter pieces to {dname}'s closet!")
                else:
                    st.info(f"{dname}'s closet already has garments or is not empty.")
                st.rerun()

        with col_act3:
            wdf = load_wardrobe(user_id=uid)
            csv_bytes = wdf.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Export CSV",
                data=csv_bytes,
                file_name=f"wardrobe_{uid}.csv",
                mime="text/csv",
                key=f"dl_csv_{uid}"
            )

        with col_act4:
            if not is_u_admin:
                if st.button(f"🗑️ Delete", key=f"btn_del_{uid}", help="Delete this user and their private data"):
                    if delete_user(uid):
                        st.success(f"Deleted user @{uid}.")
                        st.rerun()
                    else:
                        st.error("Could not delete user.")

    st.markdown("---")
    st.markdown("### ➕ Create a New Closet for a Friend")
    with st.form("admin_create_user_form"):
        ac_name = st.text_input("Friend's Name", placeholder="e.g. Sneha, Arjun, Kabir")
        ac_gender = st.selectbox("Style Profile", ["Boy", "Girl", "Non-binary"])
        ac_seed = st.checkbox("Pre-load with 25 Starter Capsule Items", value=False)
        ac_submit = st.form_submit_button("Create Friend's Wardrobe", type="primary")

        if ac_submit:
            if ac_name.strip():
                new_u = create_user(ac_name.strip(), display_name=ac_name.strip(), gender=ac_gender, seed_sample_capsule=ac_seed)
                st.success(f"Created new closet for {ac_name}! (ID: `{new_u['user_id']}`)")
                st.rerun()
            else:
                st.error("Please enter a name.")


# ─────────────────────────────────────────────
# TAB 2: BATCH OPERATIONS & SYSTEM ACTIONS
# ─────────────────────────────────────────────
with tab_ops:
    st.subheader("⚡ Master Batch Operations")
    st.markdown("Execute administrative tasks across all digital wardrobes.")

    col_op1, col_op2 = st.columns(2)

    with col_op1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px solid #DDD1C2; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 16px; font-weight: 700; color: #241C18; margin-bottom: 6px;">
                📦 Backup All User Data (ZIP Archive)
            </div>
            <div style="font-size: 13px; color: #704E38; margin-bottom: 14px;">
                Creates a single archive containing all user wardrobes, skin tone profiles, preferences, wear logs, and processed cutout images.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Build ZIP archive in memory
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(USER_DATA_DIR):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, USER_DATA_DIR)
                    zf.write(full_p, arcname=rel_p)
        zip_buf.seek(0)

        st.download_button(
            label="📥 Download Master Backup (.zip)",
            data=zip_buf,
            file_name="fitchecker_master_backup.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

    with col_op2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px solid #DDD1C2; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
            <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 16px; font-weight: 700; color: #241C18; margin-bottom: 6px;">
                ✂️ Universal Cutout Clean-Up
            </div>
            <div style="font-size: 13px; color: #704E38; margin-bottom: 14px;">
                Batch re-processes all uploaded images across all users using the latest pure-white background GrabCut segmentation engine.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Re-Run Cutouts for Active User", type="secondary", use_container_width=True):
            active_df = load_wardrobe()
            cleaned = 0
            with st.spinner("Processing cutouts onto pure white background..."):
                for it in active_df.to_dict("records"):
                    p = str(it.get("photo_path", "")).strip()
                    if p and os.path.exists(p):
                        try:
                            clean_img = remove_background(p)
                            clean_img.save(p, format="PNG")
                            cleaned += 1
                        except Exception:
                            pass
            st.success(f"Re-processed {cleaned} images onto pure solid white backgrounds!")


# ─────────────────────────────────────────────
# TAB 3: BACKGROUND CUTOUT DIAGNOSTIC
# ─────────────────────────────────────────────
with tab_diag:
    st.subheader("✂️ Real-Time Background Removal Engine Tester")
    st.markdown("Test the GrabCut segmentation engine on any garment photo to confirm pure solid white `#FFFFFF` output with no room or wall artifacts.")

    diag_upload = st.file_uploader("Upload a photo to test background cutout", type=["jpg", "jpeg", "png", "webp"], key="diag_uploader")
    if diag_upload:
        raw_bytes = diag_upload.getvalue()
        c_orig, c_cut = st.columns(2)
        with c_orig:
            st.markdown("**Original Scanned Photo**")
            st.image(raw_bytes, use_column_width=True)

        with c_cut:
            st.markdown("**Processed Studio Cutout (Pure White Background)**")
            with st.spinner("Extracting garment onto pure white background..."):
                cutout_res = remove_background(raw_bytes)
                st.image(cutout_res.convert("RGB"), use_column_width=True)
                st.success("✅ Cutout composited onto solid white background!")


# ─────────────────────────────────────────────
# TAB 4: SYSTEM HEALTH & STORAGE
# ─────────────────────────────────────────────
with tab_system:
    st.subheader("📊 System Health & Storage Usage")

    h1, h2, h3, h4 = st.columns(4)
    import cv2
    h1.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    h2.metric("OpenCV Version", cv2.__version__)
    h3.metric("Streamlit Version", st.__version__)
    h4.metric("Active OS", sys.platform)

    st.markdown("---")
    st.markdown("### User Storage Utilization")
    user_storage_rows = []
    users = list_users()
    for u in users:
        uid = u["user_id"]
        udir = get_user_data_dir(uid)
        total_size = 0
        file_cnt = 0
        for root, dirs, files in os.walk(udir):
            for f in files:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                file_cnt += 1
        user_storage_rows.append({
            "User ID": uid,
            "Display Name": u.get("display_name", uid),
            "Files": file_cnt,
            "Storage (KB)": round(total_size / 1024, 1),
            "Storage (MB)": round(total_size / (1024 * 1024), 2),
            "Garment Items": u.get("items_count", 0)
        })

    st.dataframe(pd.DataFrame(user_storage_rows), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔐 Master Creator Security PIN")
    st.caption("Change the PIN used to unlock administrative privileges and switch between closets.")
    col_p1, _ = st.columns([1.5, 2])
    with col_p1:
        with st.form("change_pin_form"):
            new_p1 = st.text_input("New Master PIN (at least 4 digits)", type="password")
            new_p2 = st.text_input("Confirm New Master PIN", type="password")
            btn_save_p = st.form_submit_button("Update Master PIN", type="primary")
            if btn_save_p:
                if not new_p1 or len(new_p1.strip()) < 4:
                    st.error("PIN must be at least 4 characters long.")
                elif new_p1 != new_p2:
                    st.error("PINs do not match.")
                else:
                    if set_master_pin(new_p1.strip()):
                        st.success("Master PIN updated successfully!")
                    else:
                        st.error("Failed to update Master PIN.")
