"""
image_processor.py — FitChecker Image Handling
===============================================
PURPOSE:
  Validate, resize, correct orientation, and extract colors from uploaded
  garment photos.  Saves processed images locally with unique filenames.

FEATURES:
  1. File validation (type, size)
  2. EXIF orientation correction (so phone photos aren't rotated)
  3. Resizing to a standard thumbnail size
  4. Dominant color extraction using K-Means clustering

ALGORITHM — Color Extraction:
  We use K-Means clustering on the pixel colors of the image.
  K-Means groups similar colors together. The center of each group
  (the "centroid") represents a dominant color.
  We run it with K = NUM_DOMINANT_COLORS (default 3).

BEGINNER NOTE:
  K-Means is an unsupervised machine learning algorithm.
  Here we use it practically: find the 3 most prominent colors in a photo.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageOps, ExifTags

from config.settings import (
    MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_TYPES,
    THUMBNAIL_SIZE, NUM_DOMINANT_COLORS, IMAGES_DIR
)
from src.color_compatibility import COLOR_RGB


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_image_file(filepath: str) -> tuple[bool, str]:
    """
    Check if the file at `filepath` is a valid image for the app.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    p = Path(filepath)
    if not p.exists():
        return False, "File not found."
    ext = p.suffix.lower()
    if ext not in ALLOWED_IMAGE_TYPES:
        return False, f"File type '{ext}' is not supported. Use: {ALLOWED_IMAGE_TYPES}"
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"File is {size_mb:.1f} MB. Maximum allowed is {MAX_IMAGE_SIZE_MB} MB."
    try:
        with Image.open(filepath) as img:
            img.verify()
    except Exception:
        return False, "File could not be opened as an image. It may be corrupted."
    return True, ""


def validate_image_bytes(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """Validate image provided as raw bytes (from Streamlit file uploader)."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_TYPES:
        return False, f"File type '{ext}' is not supported. Use: {ALLOWED_IMAGE_TYPES}"
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"File is {size_mb:.1f} MB. Maximum allowed is {MAX_IMAGE_SIZE_MB} MB."
    try:
        import io
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        return False, "File could not be opened as an image."
    return True, ""


# ─────────────────────────────────────────────
# ORIENTATION CORRECTION
# ─────────────────────────────────────────────

def fix_orientation(img: Image.Image) -> Image.Image:
    """
    Correct image rotation using EXIF metadata.
    Phone cameras embed rotation information in EXIF tags.
    Without correction, portrait photos appear rotated 90°.
    """
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img


# ─────────────────────────────────────────────
# RESIZE
# ─────────────────────────────────────────────

def resize_image(img: Image.Image, max_size: tuple = THUMBNAIL_SIZE) -> Image.Image:
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    Uses LANCZOS resampling for high quality.
    """
    img.thumbnail(max_size, Image.LANCZOS)
    return img


# ─────────────────────────────────────────────
# BACKGROUND REMOVAL (Clean E-Commerce Cutout)
# ─────────────────────────────────────────────

def remove_background(image_input, margin_pct: float = 0.04, iter_count: int = 5) -> Image.Image:
    """
    Remove background from garment photo using adaptive multi-cluster analysis,
    border-sample background modeling, cavity/inter-leg negative space clearance,
    and GrabCut segmentation. Produces a clean, transparent RGBA PIL Image isolating the garment.
    """
    import cv2
    import io
    from sklearn.cluster import KMeans

    if isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_input, str):
        img = cv2.imread(str(image_input))
    elif isinstance(image_input, Image.Image):
        rgb_img = image_input.convert("RGB")
        img = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
    else:
        raise ValueError("Unsupported image input type")

    if img is None:
        raise ValueError("Could not decode image")

    h, w = img.shape[:2]

    # Handle edge cases (tiny or uniform images)
    if h < 10 or w < 10 or np.std(img) < 2.0:
        b, g, r = cv2.split(img)
        alpha = np.full((h, w), 255, dtype=np.uint8)
        rgba = cv2.merge([r, g, b, alpha])
        return Image.fromarray(rgba, mode="RGBA")

    try:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

        # 1. Outer Border Background Analysis
        bx = max(int(w * margin_pct), 3)
        by = max(int(h * margin_pct), 3)
        border_mask = np.zeros((h, w), dtype=bool)
        border_mask[:by, :] = True
        border_mask[-by:, :] = True
        border_mask[:, :bx] = True
        border_mask[:, -bx:] = True

        border_pixels = lab[border_mask].reshape(-1, 3).astype(float)
        bg_mean = np.median(border_pixels, axis=0)
        dist_to_bg = np.linalg.norm(lab.astype(float) - bg_mean, axis=2)

        # 2. Sample Central ROI for Garment Color Profile
        roi_h_start, roi_h_end = int(h * 0.22), int(h * 0.78)
        roi_w_start, roi_w_end = int(w * 0.20), int(w * 0.80)
        roi = lab[roi_h_start:roi_h_end, roi_w_start:roi_w_end].reshape(-1, 3).astype(float)

        # Exclude obvious border background pixels from ROI before clustering
        roi_not_bg = roi[np.linalg.norm(roi - bg_mean, axis=1) > 22]
        sample_pool = roi_not_bg if len(roi_not_bg) > 80 else roi

        n_clusters = min(4, max(1, len(sample_pool) // 80))
        km = KMeans(n_clusters=n_clusters, n_init=3, random_state=42)
        km.fit(sample_pool)

        counts = np.bincount(km.labels_, minlength=n_clusters)
        dom_idx = np.argmax(counts)
        dom_center = km.cluster_centers_[dom_idx]

        # Valid clusters: must be color-coherent with dominant fabric (delta E <= 42)
        valid_centers = []
        outlier_centers = []
        for i, center in enumerate(km.cluster_centers_):
            d_dom = np.linalg.norm(center - dom_center)
            d_bg = np.linalg.norm(center - bg_mean)
            if d_dom <= 42 and d_bg > 18:
                valid_centers.append(center)
            else:
                outlier_centers.append(center)

        if not valid_centers:
            valid_centers = [dom_center]

        # Perceptual distance to valid garment centers
        dists_valid = [np.linalg.norm(lab.astype(float) - c, axis=2) for c in valid_centers]
        min_dist_valid = np.minimum.reduce(dists_valid)

        # Mask initialization
        mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
        mask[border_mask] = cv2.GC_BGD

        # Obvious background matching borders
        mask[dist_to_bg < 18] = cv2.GC_BGD

        # Outlier color clusters (e.g. cyan shirt, contrasting objects behind pants)
        if outlier_centers:
            dists_outlier = [np.linalg.norm(lab.astype(float) - c, axis=2) for c in outlier_centers]
            min_dist_outlier = np.minimum.reduce(dists_outlier)
            mask[(min_dist_outlier < 22) & (min_dist_valid > 25)] = cv2.GC_BGD

        # Far from valid garment colors
        mask[min_dist_valid > 40] = cv2.GC_BGD

        # Probable foreground: close to valid centers & not border bg
        fg_candidate = (min_dist_valid < 26) & (dist_to_bg > 22) & (mask != cv2.GC_BGD)
        mask[fg_candidate] = cv2.GC_PR_FGD

        # Center core reinforcement
        core_h_start, core_h_end = int(h * 0.35), int(h * 0.65)
        core_w_start, core_w_end = int(w * 0.35), int(w * 0.65)
        core_fg = fg_candidate[core_h_start:core_h_end, core_w_start:core_w_end]
        if np.mean(core_fg) > 0.25:
            mask[core_h_start:core_h_end, core_w_start:core_w_end][core_fg] = cv2.GC_FGD

        # 3. Graph-Cut Energy Minimization (only if both BGD and FGD seeds exist)
        has_bgd = np.any((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD))
        has_fgd = np.any((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD))

        if has_bgd and has_fgd:
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            cv2.grabCut(img, mask, None, bgd_model, fgd_model, iter_count, cv2.GC_INIT_WITH_MASK)
            fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        else:
            fg = np.where(min_dist_valid < 35, 255, 0).astype(np.uint8)

        # 4. Connected Component Analysis — Retain the primary scanned garment
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(fg)
        center_y, center_x = h // 2, w // 2
        best_lbl = 0
        min_d = float('inf')
        for lbl in range(1, num_labels):
            if stats[lbl, cv2.CC_STAT_AREA] < (h * w * 0.04):
                continue
            cx, cy = centroids[lbl]
            d = np.hypot(cx - center_x, cy - center_y)
            if d < min_d:
                min_d = d
                best_lbl = lbl

        clean_fg = np.zeros_like(fg)
        if best_lbl > 0:
            clean_fg[labels == best_lbl] = 255
        else:
            clean_fg = fg

        # 5. Internal Hole Clearance (clear openings between garments, hangers, armholes)
        cnts, hier = cv2.findContours(clean_fg.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if hier is not None:
            for i in range(len(cnts)):
                if hier[0][i][3] != -1:
                    area = cv2.contourArea(cnts[i])
                    if area > (h * w * 0.003):
                        cv2.drawContours(clean_fg, [cnts[i]], -1, 0, -1)

        # 6. Inter-Leg / Crotch Cavity Clearance (for trousers & shorts)
        if clean_fg.any():
            ext_cnts, _ = cv2.findContours(clean_fg.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if ext_cnts:
                main_cnt = max(ext_cnts, key=cv2.contourArea)
                hull = cv2.convexHull(main_cnt, returnPoints=False)
                if len(hull) > 3:
                    defects = cv2.convexityDefects(main_cnt, hull)
                    if defects is not None:
                        best_defect = None
                        max_depth = 0
                        for d_idx in range(len(defects)):
                            s, e, f, depth_raw = defects[d_idx, 0]
                            start = tuple(main_cnt[s][0])
                            end = tuple(main_cnt[e][0])
                            far = tuple(main_cnt[f][0])
                            depth = depth_raw / 256.0
                            # Inter-leg cavity starts in lower half and extends upward into the crotch
                            if start[1] > h * 0.45 and end[1] > h * 0.45 and far[1] < min(start[1], end[1]) and depth > (h * 0.08):
                                if depth > max_depth:
                                    max_depth = depth
                                    best_defect = (start, end, far)

                        if best_defect:
                            start, end, far = best_defect
                            cavity_pts = np.array([
                                far,
                                start,
                                [start[0], h],
                                [end[0], h],
                                end
                            ], dtype=np.int32)
                            cv2.fillPoly(clean_fg, [cavity_pts], 0)

        # 7. Smooth Anti-Aliased Edge Feathering
        alpha = cv2.GaussianBlur(clean_fg, (5, 5), 0)

    except Exception:
        # Fallback to full alpha if segmentation encounters an unexpected error
        alpha = np.full((h, w), 255, dtype=np.uint8)

    b, g, r = cv2.split(img)
    rgba = cv2.merge([r, g, b, alpha])
    return Image.fromarray(rgba, mode="RGBA")


# ─────────────────────────────────────────────
# SAVE IMAGE
# ─────────────────────────────────────────────

def save_garment_image(
    file_bytes: bytes,
    original_filename: str,
    auto_remove_bg: bool = False
) -> tuple[str, str]:
    """
    Process and save an uploaded garment image.

    STEPS:
      1. Fix orientation.
      2. Resize.
      3. If auto_remove_bg: extract transparent cutout.
      4. Save as PNG with transparency (or JPEG fallback).

    Returns (saved_path, error_message).
    saved_path is empty string if an error occurred.
    """
    import io
    os.makedirs(IMAGES_DIR, exist_ok=True)

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = fix_orientation(img)
        img = resize_image(img)

        uid = uuid.uuid4().hex[:12]

        if auto_remove_bg:
            try:
                cutout_img = remove_background(img)
                filename = f"garment_{uid}.png"
                filepath = os.path.join(IMAGES_DIR, filename)
                cutout_img.save(filepath, format="PNG")
                return filepath, ""
            except Exception:
                pass  # Fall back to standard RGB save if cutout fails

        if img.mode not in ("RGB",):
            img = img.convert("RGB")
        filename = f"garment_{uid}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        img.save(filepath, format="JPEG", quality=85)
        return filepath, ""
    except Exception as e:
        return "", f"Error saving image: {e}"


# ─────────────────────────────────────────────
# DOMINANT COLOR EXTRACTION (K-Means)
# ─────────────────────────────────────────────

def extract_dominant_colors(
    image_source,              # Can be filepath (str) or PIL Image
    n_colors: int = NUM_DOMINANT_COLORS,
    sample_pixels: int = 3000  # Subsample for speed on large images
) -> list[dict]:
    """
    Extract the N most dominant colors from an image using K-Means.

    Returns a list of dicts, each with:
      {
        "hex":        "#RRGGBB",
        "rgb":        (R, G, B),
        "percentage": float (0-100),
        "name":       str  (nearest named color or "Unknown"),
      }

    ALGORITHM:
      1. Convert image to RGB.
      2. Flatten pixels to shape (num_pixels, 3).
      3. Randomly sample pixels to keep things fast.
      4. Run KMeans with n_clusters = n_colors.
      5. Each cluster center is a dominant color.
      6. Proportion = count of pixels in that cluster / total pixels.
    """
    try:
        from sklearn.cluster import KMeans

        if isinstance(image_source, str):
            img = Image.open(image_source)
        elif isinstance(image_source, Image.Image):
            img = image_source
        else:
            import io
            img = Image.open(io.BytesIO(image_source))

        img = resize_image(img, (200, 200))   # Downscale for speed

        if img.mode == "RGBA":
            arr = np.array(img)
            # Filter out transparent or near-transparent background pixels
            alpha_mask = arr[:, :, 3] > 60
            valid_pixels = arr[:, :, :3][alpha_mask].astype(float)
            pixels = valid_pixels if len(valid_pixels) >= 20 else arr[:, :, :3].reshape(-1, 3).astype(float)
        else:
            img = img.convert("RGB")
            pixels = np.array(img).reshape(-1, 3).astype(float)

        # Subsample
        if len(pixels) > sample_pixels:
            idx = np.random.choice(len(pixels), sample_pixels, replace=False)
            pixels = pixels[idx]

        k = min(n_colors, len(pixels))
        km = KMeans(n_clusters=k, n_init=5, random_state=42)
        labels = km.fit_predict(pixels)
        centers = km.cluster_centers_.astype(int)

        # Count pixels per cluster
        counts  = np.bincount(labels, minlength=k)
        total   = counts.sum()

        results = []
        for i in range(k):
            r, g, b = int(centers[i][0]), int(centers[i][1]), int(centers[i][2])
            hex_code = f"#{r:02X}{g:02X}{b:02X}"
            pct      = round(counts[i] / total * 100, 1)
            name     = _nearest_named_color((r, g, b))
            results.append({"hex": hex_code, "rgb": (r, g, b), "percentage": pct, "name": name})

        # Sort by dominance (most prevalent first)
        results.sort(key=lambda x: x["percentage"], reverse=True)
        return results

    except Exception as e:
        # Return a safe fallback so the app doesn't crash
        return [{"hex": "#808080", "rgb": (128, 128, 128), "percentage": 100.0, "name": "grey"}]


def _nearest_named_color(rgb: tuple) -> str:
    """
    Find the nearest named color from COLOR_RGB by Euclidean distance.

    BEGINNER NOTE:
      Euclidean distance between two RGB colors (r1,g1,b1) and (r2,g2,b2)
      is sqrt((r1-r2)² + (g1-g2)² + (b1-b2)²).
      We pick the named color with the smallest distance.
    """
    best_name = "unknown"
    best_dist = float("inf")
    r, g, b = rgb
    for name, (nr, ng, nb) in COLOR_RGB.items():
        dist = ((r - nr) ** 2 + (g - ng) ** 2 + (b - nb) ** 2) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def get_image_info(filepath: str) -> dict:
    """Return basic metadata about a saved image (size, dimensions)."""
    if not filepath or not os.path.exists(str(filepath)):
        return {}
    try:
        p = Path(filepath)
        img = Image.open(filepath)
        return {
            "filename":   p.name,
            "size_kb":    round(p.stat().st_size / 1024, 1),
            "width":      img.width,
            "height":     img.height,
            "mode":       img.mode,
        }
    except Exception:
        return {}


def convert_existing_wardrobe_cutouts() -> int:
    """
    Scan user wardrobe and convert any photos that don't have cutouts yet
    into clean transparent PNG cutouts, updating wardrobe.csv.
    Returns number of converted items.
    """
    from src.data_manager import load_wardrobe, save_wardrobe
    df = load_wardrobe()
    if df.empty or "photo_path" not in df.columns:
        return 0

    converted = 0
    for idx, row in df.iterrows():
        p = str(row.get("photo_path") or "").strip()
        if not p or not os.path.exists(p):
            continue
        if p.lower().endswith(".png"):
            continue

        try:
            cutout_p = os.path.splitext(p)[0] + "_cutout.png"
            if not os.path.exists(cutout_p):
                cutout_img = remove_background(p)
                cutout_img.save(cutout_p, format="PNG")
            df.at[idx, "photo_path"] = cutout_p
            converted += 1
        except Exception as e:
            print(f"[image_processor] Error creating cutout for {p}: {e}")

    if converted > 0:
        save_wardrobe(df)
    return converted



