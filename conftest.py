# conftest.py — shared pytest configuration for FitChecker tests
import sys
import os
import pytest
import importlib

# Ensure the project root is always on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(autouse=True)
def temp_user_data(monkeypatch, tmp_path):
    """Redirect all data files to a temp directory so tests don't touch real user data."""
    import config.settings as s
    monkeypatch.setattr(s, "USER_DATA_DIR",     str(tmp_path))
    monkeypatch.setattr(s, "WARDROBE_FILE",     str(tmp_path / "wardrobe.csv"))
    monkeypatch.setattr(s, "FEEDBACK_FILE",     str(tmp_path / "feedback.csv"))
    monkeypatch.setattr(s, "PREFERENCES_FILE",  str(tmp_path / "preferences.json"))
    monkeypatch.setattr(s, "PROFILE_FILE",      str(tmp_path / "profile.json"))
    monkeypatch.setattr(s, "WEAR_HISTORY_FILE", str(tmp_path / "wear_history.csv"))
    monkeypatch.setattr(s, "OUTFITS_FILE",      str(tmp_path / "outfits.csv"))
    monkeypatch.setattr(s, "IMAGES_DIR",        str(tmp_path / "images"))
    monkeypatch.setattr(s, "ML_MODEL_FILE",     str(tmp_path / "rf_model.joblib"))

    try:
        import streamlit as st
        st.session_state.clear()
    except Exception:
        pass

    import src.user_manager as um
    import src.data_manager as dm
    importlib.reload(um)
    importlib.reload(dm)
    yield
    importlib.reload(um)
    importlib.reload(dm)
    try:
        import streamlit as st
        st.session_state.clear()
    except Exception:
        pass
