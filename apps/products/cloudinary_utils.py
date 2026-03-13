"""
Cloudinary rasm optimizatsiyasi:
- Avtomatik WebP konversiya
- O'lchamni cheklash
- Lazy loading uchun thumbnail
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api


def get_optimized_url(image_url: str, width: int = 800, height: int = 800) -> str:
    """
    Cloudinary URL dan optimallashtirilgan versiya olish.
    - WebP formatiga o'tkazish
    - O'lchamni cheklash
    - Auto quality
    """
    if not image_url or "cloudinary.com" not in str(image_url):
        return str(image_url) if image_url else ""

    # Upload transformatsiya qo'shish
    url = str(image_url)
    # /upload/ dan keyin transformatsiya qo'shamiz
    if "/upload/" in url:
        transform = f"w_{width},h_{height},c_limit,q_auto,f_auto"
        url = url.replace("/upload/", f"/upload/{transform}/")
    return url


def get_thumbnail_url(image_url: str, size: int = 200) -> str:
    """Thumbnail URL (kichik rasm)"""
    return get_optimized_url(image_url, width=size, height=size)


def get_product_image_url(image_url: str) -> str:
    """Mahsulot rasmi uchun optimallashtirilgan URL (800x800)"""
    return get_optimized_url(image_url, width=800, height=800)


def get_avatar_url(image_url: str) -> str:
    """Avatar uchun optimallashtirilgan URL (200x200, yuzlari aniqlash)"""
    if not image_url or "cloudinary.com" not in str(image_url):
        return str(image_url) if image_url else ""
    url = str(image_url)
    if "/upload/" in url:
        transform = "w_200,h_200,c_thumb,g_face,q_auto,f_auto,r_max"
        url = url.replace("/upload/", f"/upload/{transform}/")
    return url
