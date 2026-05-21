# ConfDir/ScaleRes.py
import os

# Получаем путь к папке пользователя
USER_YAMALPIXEL_RES = os.path.join(os.path.expanduser("~"), "YamalPixelRes")

RESOLUTION_MAP = {
    (1920, 1080): "logo1.png",  # Full HD
    (1920, 1200): "logo2.png",  # WUXGA
    (2048, 1080): "logo3.png",  # 2K DCI
    (2048, 1536): "logo4.png",  # QXGA
    (2560, 1440): "logo5.png",  # 2K QHD
    (2560, 1600): "logo6.png",  # WQXGA
    (3440, 1440): "logo7.png",  # UltraWide
    (3840, 2160): "logo8.png",  # 4K UHD
    (3840, 2400): "logo9.png",  # WQUXGA
}

# ДЛЯ СОВМЕСТИМОСТИ со старым кодом
ratios = {
    (1920, 1080): 1.78,  # 16:9
    (1920, 1200): 1.60,  # 16:10
    (2048, 1080): 1.90,  # ~17:9
    (2048, 1536): 1.33,  # 4:3
    (2560, 1440): 1.78,  # 16:9
    (2560, 1600): 1.60,  # 16:10
    (3440, 1440): 2.39,  # 21:9
    (3840, 2160): 1.78,  # 16:9
    (3840, 2400): 1.60,  # 16:10
}

resolution_ratios = {
    "logo1.png": 1920 / 1080,  # 1.78 (16:9)
    "logo2.png": 1920 / 1200,  # 1.60 (16:10)
    "logo3.png": 2048 / 1080,  # 1.90 (~17:9)
    "logo4.png": 2048 / 1536,  # 1.33 (4:3)
    "logo5.png": 2560 / 1440,  # 1.78 (16:9)
    "logo6.png": 2560 / 1600,  # 1.60 (16:10)
    "logo7.png": 3440 / 1440,  # 2.39 (21:9)
    "logo8.png": 3840 / 2160,  # 1.78 (16:9)
    "logo9.png": 3840 / 2400,  # 1.60 (16:10)
}

backgrounds = [
    ("Full HD (1920x1080)", "logo1.png"),
    ("WUXGA (1920x1200)", "logo2.png"),
    ("2K DCI (2048x1080)", "logo3.png"),
    ("QXGA (2048x1536)", "logo4.png"),
    ("2K QHD (2560x1440)", "logo5.png"),
    ("WQXGA (2560x1600)", "logo6.png"),
    ("UltraWide (3440x1440)", "logo7.png"),
    ("4K UHD (3840x2160)", "logo8.png"),
    ("WQUXGA (3840x2400)", "logo9.png"),
]


def find_closest_resolution(width, height):
    """
    Finds the closest resolution by aspect ratio
    """
    if width == 0 or height == 0:
        return "logo1.png"

    aspect_ratio = width / height
    print(f"Aspect ratio: {aspect_ratio:.2f} ({width}x{height})")

    # Find with smallest difference in ratio
    best_match = "logo1.png"
    min_diff = float("inf")

    for file, target_ratio in resolution_ratios.items():
        diff = abs(aspect_ratio - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_match = file

    print(f"Selected background: {best_match} (diff={min_diff:.4f})")
    return best_match


def get_background_path(filename):
    """
    Returns full path to background file.
    First searches in C:\\Users\\%USERNAME%\\YamalPixelRes,
    then in local project folder.
    """
    # Path in user folder
    user_path = os.path.join(USER_YAMALPIXEL_RES, filename)
    if os.path.exists(user_path):
        print(f"Background found in user folder: {user_path}")
        return user_path

    # Path in project folder (for development)
    local_path = os.path.join(os.getcwd(), "YamalPixelRes", filename)
    if os.path.exists(local_path):
        print(f"Background found in project folder: {local_path}")
        return local_path

    # Path relative to this file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "..", "YamalPixelRes", filename)
    if os.path.exists(script_path):
        print(f"Background found in script folder: {script_path}")
        return script_path

    print(f"Background not found: {filename}")
    return None


def ensure_backgrounds_folder():
    """
    Creates background folder in user directory if it doesn't exist.
    """
    if not os.path.exists(USER_YAMALPIXEL_RES):
        os.makedirs(USER_YAMALPIXEL_RES, exist_ok=True)
        print(f"Created backgrounds folder: {USER_YAMALPIXEL_RES}")
        print(f"Place files here: logo1.png, logo2.png, ...")
        return False
    return True

__all__ = [
    'RESOLUTION_MAP', 'ratios', 'resolution_ratios', 'backgrounds',
    'find_closest_resolution', 'get_background_path', 'ensure_backgrounds_folder',
    'USER_YAMALPIXEL_RES'
]