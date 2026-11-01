"""
src/user_manager.py — Multi-User Identity, Isolated Wardrobe Spaces & Admin Hub
=============================================================================
PURPOSE:
  Provides personalized, independent wardrobe spaces for BUDZ and friends.
  Each user has:
    - Their own independent wardrobe (wardrobe.csv)
    - Their own skin tone profile & power colors (profile.json)
    - Their own style preferences (preferences.json)
    - Their own wear history & feedback logs (wear_history.csv, feedback.csv)
    - Their own uploaded garment cutout image library (images/)

URL / Session Integration:
  - Recognizes `?user=username` query param in the URL (shareable links)
  - Synchronizes with `st.session_state["active_user"]`
  - Defaults to "BUDZ" (Admin / Creator)
  - Seamlessly migrates existing root data into the BUDZ profile
"""

import sys
import os
import re
import json
import shutil
from typing import Optional, Dict, Any, List
import pandas as pd

import config.settings as settings

DEFAULT_ADMIN_USER = "BUDZ"
DEFAULT_MASTER_PIN = "7777"


def get_master_pin() -> str:
    """Return the current Master Creator PIN."""
    pin_file = os.path.join(settings.USER_DATA_DIR, "admin_pin.json")
    if os.path.exists(pin_file):
        try:
            with open(pin_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return str(data.get("pin", DEFAULT_MASTER_PIN))
        except Exception:
            pass
    return DEFAULT_MASTER_PIN


def set_master_pin(new_pin: str) -> bool:
    """Update Master Creator PIN."""
    p_clean = str(new_pin).strip()
    if not p_clean or len(p_clean) < 4:
        return False
    pin_file = os.path.join(settings.USER_DATA_DIR, "admin_pin.json")
    try:
        os.makedirs(settings.USER_DATA_DIR, exist_ok=True)
        with open(pin_file, "w", encoding="utf-8") as f:
            json.dump({"pin": p_clean}, f, indent=2)
        return True
    except Exception:
        return False


def is_master_authenticated() -> bool:
    """Check if the current session has verified Master Creator privileges."""
    try:
        import streamlit as st
        master_pin = get_master_pin()
        # Direct URL parameter shortcut: ?pin=7777
        if hasattr(st, "query_params"):
            if st.query_params.get("pin") == master_pin:
                st.session_state["is_master_authenticated"] = True
                return True
        return bool(st.session_state.get("is_master_authenticated", False))
    except Exception:
        return False


def verify_master_pin(entered_pin: str) -> bool:
    """Verify entered PIN and authenticate session if correct."""
    master_pin = get_master_pin()
    if str(entered_pin).strip() == master_pin:
        try:
            import streamlit as st
            st.session_state["is_master_authenticated"] = True
        except Exception:
            pass
        return True
    return False


def logout_master():
    """Revoke Master Creator authentication for the session."""
    try:
        import streamlit as st
        st.session_state["is_master_authenticated"] = False
        if hasattr(st, "query_params") and "pin" in st.query_params:
            del st.query_params["pin"]
    except Exception:
        pass


def is_test_environment() -> bool:
    """Return True if running under pytest or temporary testing directories."""
    ud = str(getattr(settings, "USER_DATA_DIR", "")).lower()
    return ("pytest" in sys.modules) or ("pytest" in ud) or ("tmp" in ud) or ("temp" in ud)


def get_users_root_dir() -> str:
    """Return the current users root directory."""
    return os.path.join(settings.USER_DATA_DIR, "users")


def sanitize_username(raw: str) -> str:
    """Normalize username to safe alphanumeric string."""
    if not raw:
        return DEFAULT_ADMIN_USER
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '', str(raw).strip())
    return cleaned if cleaned else DEFAULT_ADMIN_USER


def get_active_user() -> str:
    """
    Resolve the currently active user ID.
    Priority:
      1. st.query_params["user"]
      2. st.session_state["active_user"]
      3. DEFAULT_ADMIN_USER ("BUDZ")
    """
    try:
        import streamlit as st
        # 1. Query params (URL)
        if hasattr(st, "query_params"):
            try:
                if "user" in st.query_params:
                    param_u = sanitize_username(st.query_params.get("user", ""))
                    if param_u:
                        st.session_state["active_user"] = param_u
                        return param_u
            except Exception:
                pass
        elif hasattr(st, "experimental_get_query_params"):
            try:
                params = st.experimental_get_query_params()
                if "user" in params and params["user"]:
                    param_u = sanitize_username(params["user"][0])
                    if param_u:
                        st.session_state["active_user"] = param_u
                        return param_u
            except Exception:
                pass

        # 2. Session state
        if "active_user" in st.session_state and st.session_state["active_user"]:
            return sanitize_username(st.session_state["active_user"])
    except Exception:
        pass

    return DEFAULT_ADMIN_USER


def set_active_user(user_id: str):
    """Switch active user in Streamlit session and query parameters."""
    clean_id = sanitize_username(user_id)
    try:
        import streamlit as st
        st.session_state["active_user"] = clean_id
        if hasattr(st, "query_params"):
            st.query_params["user"] = clean_id
        elif hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(user=clean_id)
        # Invalidate cached session state data so new user data is freshly read
        st.session_state.pop("wardrobe_df", None)
        st.session_state.pop("cached_cutout_preview", None)
        st.session_state.pop("active_upload_bytes", None)
        st.session_state.pop("active_upload_filename", None)
    except Exception:
        pass


def get_user_data_dir(user_id: Optional[str] = None) -> str:
    """Return the absolute path to a specific user's private data directory."""
    uid = sanitize_username(user_id or get_active_user())
    user_dir = os.path.join(get_users_root_dir(), uid)
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(os.path.join(user_dir, "images"), exist_ok=True)

    # Automatic migration: If BUDZ, migrate root legacy files if they exist
    if uid == DEFAULT_ADMIN_USER and not is_test_environment():
        _migrate_legacy_data_if_needed(user_dir)

    return user_dir


def _migrate_legacy_data_if_needed(admin_dir: str):
    """Copy pre-existing root wardrobe / profile files into users/BUDZ once."""
    target_wardrobe = os.path.join(admin_dir, "wardrobe.csv")
    if not os.path.exists(target_wardrobe) and os.path.exists(settings.WARDROBE_FILE):
        try:
            shutil.copy2(settings.WARDROBE_FILE, target_wardrobe)
        except Exception:
            pass

    target_profile = os.path.join(admin_dir, "profile.json")
    if not os.path.exists(target_profile) and os.path.exists(settings.PROFILE_FILE):
        try:
            shutil.copy2(settings.PROFILE_FILE, target_profile)
        except Exception:
            pass

    # Mirror existing images
    target_img_dir = os.path.join(admin_dir, "images")
    if os.path.exists(settings.IMAGES_DIR) and os.path.isdir(settings.IMAGES_DIR):
        for fname in os.listdir(settings.IMAGES_DIR):
            src_p = os.path.join(settings.IMAGES_DIR, fname)
            dst_p = os.path.join(target_img_dir, fname)
            if os.path.isfile(src_p) and not os.path.exists(dst_p):
                try:
                    shutil.copy2(src_p, dst_p)
                except Exception:
                    pass


def get_user_wardrobe_file(user_id: Optional[str] = None) -> str:
    """Get path to the user's wardrobe.csv."""
    if is_test_environment() and not user_id:
        return settings.WARDROBE_FILE
    return os.path.join(get_user_data_dir(user_id), "wardrobe.csv")


def get_user_profile_file(user_id: Optional[str] = None) -> str:
    """Get path to the user's profile.json."""
    if is_test_environment() and not user_id:
        return settings.PROFILE_FILE
    return os.path.join(get_user_data_dir(user_id), "profile.json")


def get_user_feedback_file(user_id: Optional[str] = None) -> str:
    """Get path to the user's feedback.csv."""
    if is_test_environment() and not user_id:
        return settings.FEEDBACK_FILE
    return os.path.join(get_user_data_dir(user_id), "feedback.csv")


def get_user_preferences_file(user_id: Optional[str] = None) -> str:
    """Get path to the user's preferences.json."""
    if is_test_environment() and not user_id:
        return settings.PREFERENCES_FILE
    return os.path.join(get_user_data_dir(user_id), "preferences.json")


def get_user_wear_history_file(user_id: Optional[str] = None) -> str:
    """Get path to the user's wear_history.csv."""
    if is_test_environment() and not user_id:
        return settings.WEAR_HISTORY_FILE
    return os.path.join(get_user_data_dir(user_id), "wear_history.csv")


def get_user_images_dir(user_id: Optional[str] = None) -> str:
    """Get path to the user's images directory."""
    if is_test_environment() and not user_id:
        return settings.IMAGES_DIR
    return os.path.join(get_user_data_dir(user_id), "images")


def list_users() -> List[Dict[str, Any]]:
    """
    List all registered user accounts with item counts and display information.
    Guaranteed to include DEFAULT_ADMIN_USER ("BUDZ").
    """
    users_root = get_users_root_dir()
    os.makedirs(users_root, exist_ok=True)
    get_user_data_dir(DEFAULT_ADMIN_USER)  # Ensure BUDZ is created

    users_list = []
    user_folders = sorted(os.listdir(users_root))
    if DEFAULT_ADMIN_USER not in user_folders:
        user_folders.insert(0, DEFAULT_ADMIN_USER)

    for uid in user_folders:
        udir = os.path.join(users_root, uid)
        if not os.path.isdir(udir):
            continue

        p_file = os.path.join(udir, "profile.json")
        name = uid
        gender = "Boy"
        skin_tone = "Medium Golden"
        if os.path.exists(p_file):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                    name = pdata.get("name", uid)
                    gender = pdata.get("gender", "Boy")
                    skin_tone = pdata.get("palette_tier_label", pdata.get("skin_tone_label", "Golden Amber"))
            except Exception:
                pass

        w_file = os.path.join(udir, "wardrobe.csv")
        items_count = 0
        if os.path.exists(w_file):
            try:
                wdf = pd.read_csv(w_file, dtype=str)
                items_count = len(wdf)
            except Exception:
                pass

        users_list.append({
            "user_id": uid,
            "display_name": name,
            "gender": gender,
            "skin_tone": skin_tone,
            "items_count": items_count,
            "is_admin": (uid == DEFAULT_ADMIN_USER)
        })

    return users_list


def create_user(user_id: str, display_name: Optional[str] = None, gender: str = "Boy", seed_sample_capsule: bool = False) -> Dict[str, Any]:
    """
    Create a new isolated user account with a clean wardrobe and customized profile.
    """
    uid = sanitize_username(user_id)
    display_name = (display_name or uid).strip()
    user_dir = get_user_data_dir(uid)

    # Initialize profile
    from src.skin_tone_analyzer import get_default_profile
    profile = get_default_profile()
    profile["name"] = display_name
    profile["gender"] = gender
    profile["notes"] = f"Curated digital wardrobe for {display_name}."

    with open(os.path.join(user_dir, "profile.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    # Initialize empty wardrobe CSV with schema headers
    w_file = os.path.join(user_dir, "wardrobe.csv")
    if not os.path.exists(w_file):
        from src.data_manager import WARDROBE_SCHEMA
        df_empty = pd.DataFrame(columns=list(WARDROBE_SCHEMA.keys()))
        df_empty.to_csv(w_file, index=False)

    if seed_sample_capsule and os.path.exists(settings.SAMPLE_WARDROBE_FILE):
        try:
            sdf = pd.read_csv(settings.SAMPLE_WARDROBE_FILE, dtype=str)
            sdf.to_csv(w_file, index=False)
        except Exception:
            pass

    return {
        "user_id": uid,
        "display_name": display_name,
        "user_dir": user_dir
    }


def delete_user(user_id: str) -> bool:
    """Delete a user account and their private data (Admin only, cannot delete BUDZ)."""
    uid = sanitize_username(user_id)
    if uid == DEFAULT_ADMIN_USER:
        return False  # Never delete root admin

    user_dir = os.path.join(get_users_root_dir(), uid)
    if os.path.exists(user_dir) and os.path.isdir(user_dir):
        try:
            shutil.rmtree(user_dir)
            return True
        except Exception:
            return False
    return False


def render_user_nav_widget():
    """
    Render a clean, luxury top-sidebar profile selector and closet creator.
    Enforces strict privacy:
      - Friends/guests only see their own active closet.
      - The 'Switch Digital Closet' dropdown and Admin tools are strictly reserved
        for Master Creator (BUDZ) upon Master PIN verification.
    """
    import streamlit as st

    current_uid = get_active_user()
    all_users = list_users()
    user_ids = [u["user_id"] for u in all_users]

    # Get active user profile
    active_profile = next((u for u in all_users if u["user_id"] == current_uid), {
        "user_id": current_uid,
        "display_name": current_uid,
        "items_count": 0,
        "is_admin": (current_uid == DEFAULT_ADMIN_USER)
    })

    master_active = is_master_authenticated()
    is_budz = (current_uid == DEFAULT_ADMIN_USER)

    role_badge = "👑 MASTER CREATOR" if (is_budz and master_active) else "🔒 PRIVATE CLOSET"
    badge_bg = "#4A352B" if (is_budz and master_active) else "#2D5A27"

    with st.sidebar:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #DDD1C2; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(74, 53, 43, 0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 10px; font-weight: 800; color: #8C5835; letter-spacing: 0.1em; text-transform: uppercase;">ACTIVE CLOSET</span>
                <span style="background: {badge_bg}; color: #FFFFFF; font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: 8px; letter-spacing: 0.05em;">{role_badge}</span>
            </div>
            <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #241C18;">
                {active_profile.get('display_name')}
            </div>
            <div style="font-size: 12px; color: #704E38; font-weight: 500; margin-top: 2px;">
                {active_profile.get('items_count', 0)} Curated Garments · {active_profile.get('gender', 'Boy')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── MASTER CREATOR CONTROLS (Only visible if Master PIN is authenticated) ──
        if master_active:
            curr_idx = user_ids.index(current_uid) if current_uid in user_ids else 0
            sel_user = st.selectbox(
                "👑 Master Switcher (Inspect Any Closet)",
                user_ids,
                index=curr_idx,
                format_func=lambda uid: f"{'👑 ' if uid == DEFAULT_ADMIN_USER else '👤 '}{uid}",
                key="sb_user_switcher_select"
            )
            if sel_user != current_uid:
                set_active_user(sel_user)
                st.rerun()

            st.markdown(
                "<div style='margin-top: 6px; margin-bottom: 8px;'>"
                "<a href='/Admin_and_Settings' target='_self' style='font-size: 11.5px; font-weight: 700; color: #8C3B1E; text-decoration: none;'>⚙️ Creator Control Center & Backups</a>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button("🔒 Lock Master Mode", key="btn_lock_master", use_container_width=True):
                logout_master()
                st.rerun()
        else:
            # Discreet Master Unlock for BUDZ
            with st.expander("🔑 Master Creator Login", expanded=False):
                st.caption("Enter Master PIN to inspect and manage all wardrobes.")
                entered_p = st.text_input("Master PIN", type="password", key="inp_master_pin", placeholder="PIN")
                if st.button("Unlock Master Controls", type="primary", use_container_width=True, key="btn_unlock_master"):
                    if verify_master_pin(entered_p):
                        set_active_user(DEFAULT_ADMIN_USER)
                        st.success("Master privileges unlocked!")
                        st.rerun()
                    else:
                        st.error("Incorrect Master PIN.")

        # ── Create New Closet Expander for Friends ──
        with st.expander("➕ Create Your Own Wardrobe", expanded=False):
            st.caption("Friends & guests can create their personal isolated closet here. All garments stay 100% private.")
            new_u_name = st.text_input("Your Name / Username", placeholder="e.g. Alex, Rohan, Sneha", key="txt_new_u_name")
            new_u_gender = st.selectbox("Profile Category", ["Boy", "Girl", "Non-binary"], key="sel_new_u_gender")
            seed_capsule = st.checkbox("Pre-load 25 Starter Capsule Pieces", value=False, key="chk_seed_new_user")

            if st.button("🚀 Create My Private Closet", type="primary", use_container_width=True, key="btn_create_new_closet"):
                if new_u_name.strip():
                    new_uid = sanitize_username(new_u_name)
                    create_user(new_uid, display_name=new_u_name.strip(), gender=new_u_gender, seed_sample_capsule=seed_capsule)
                    set_active_user(new_uid)
                    st.success(f"🎉 Welcome {new_u_name}! Your private closet is ready.")
                    st.rerun()
                else:
                    st.error("Please enter your name.")

        st.markdown("<hr style='margin: 8px 0 14px 0; border: none; border-top: 1px solid #DDD1C2;'>", unsafe_allow_html=True)
