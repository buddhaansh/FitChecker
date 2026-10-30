"""
garment_classifier.py — FitChecker Category Suggestion
=======================================================
PURPOSE:
  Suggest a garment category from an uploaded image.
  This is an optional enhancement; the core app works without it.

APPROACH:
  We use a COLOR-PROFILE heuristic as the primary method.
  A pre-trained deep learning model (e.g. ResNet, EfficientNet) would
  give much better accuracy, but requires a large download and an
  internet connection at runtime.

  For a BTech project without a GPU or reliable internet, a color-profile
  heuristic is a practical and honest fallback.

  LIMITATION: This method can only make very rough guesses.
  It is presented as a suggestion, not a classification.
  The user must confirm or correct the prediction.

HONEST DISCLOSURE:
  This is NOT a trained image classifier.
  It uses simple rules about dominant colors and image aspect ratio
  to make educated guesses.
  The "confidence" value reflects how strongly the rules apply,
  not a real probabilistic confidence from a neural network.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CATEGORIES


def suggest_category_from_colors(
    dominant_colors: list[dict],
    image_info: dict = None,
) -> tuple[str, float, str]:
    """
    Suggest a garment category based on dominant color proportions.

    Returns:
      (suggested_category, confidence_0_to_1, explanation)

    NOTE: This is a heuristic, not a trained classifier.
    The suggestion should always be confirmed by the user.
    """
    if not dominant_colors:
        return "T-Shirt", 0.3, "No color information available; defaulting to T-Shirt."

    top_color = dominant_colors[0]
    hex_code  = top_color.get("hex", "#808080").lower()

    # Aspect ratio hint: tall images are likely tops/dresses
    tall = False
    if image_info:
        w = image_info.get("width", 1)
        h = image_info.get("height", 1)
        if h > 0 and w > 0:
            tall = (h / w) > 1.4

    # Very simple color-based rules
    # In practice a CNN would be far better — this is a placeholder
    name = top_color.get("name", "").lower()

    # Neutral colors are common across all categories
    neutrals = {"white", "black", "grey", "gray", "beige", "off white", "cream"}
    if name in neutrals:
        if tall and name in ("black", "grey", "gray"):
            suggestion = "Trousers"
            confidence = 0.42
            reason = f"Tall silhouette with {name} tones indicates Trousers or Bottoms. Please confirm."
        else:
            suggestion = "T-Shirt"
            confidence = 0.35
            reason = f"Dominant color is {name} (neutral). Category guess: T-Shirt. Please confirm."
    elif name in ("navy blue", "dark blue", "blue"):
        suggestion = "Jeans" if not tall else "Shirt"
        confidence = 0.40
        reason = f"Blue tones suggest Jeans or Shirt. Please confirm."
    elif name in ("khaki", "beige", "tan"):
        suggestion = "Chinos"
        confidence = 0.38
        reason = "Khaki/tan tones suggest Chinos or Trousers. Please confirm."
    elif name in ("brown", "dark brown"):
        suggestion = "Sandals"
        confidence = 0.35
        reason = "Brown tones can suggest shoes/sandals. Please confirm."
    else:
        suggestion = "T-Shirt"
        confidence = 0.30
        reason = f"Dominant color is {name}. Defaulting to T-Shirt — please correct if needed."

    return suggestion, confidence, reason


def get_category_confidence_display(confidence: float) -> str:
    """Convert a float confidence to a human-readable label."""
    if confidence >= 0.7:
        return "High"
    elif confidence >= 0.45:
        return "Medium"
    else:
        return "Low (please review)"
