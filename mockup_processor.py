"""Auto mockup processor — runs in background when a product is created or updated.

Whenever a product image_url / back_image_url is an external URL (http/https),
this module downloads it, removes the background with isnet-general-use,
hard-thresholds the alpha, and saves a clean transparent PNG to the mockups folder.
The DB row is then updated to point to the local file.
"""

import io
import logging
import sqlite3
from pathlib import Path

import requests as _req

logger = logging.getLogger("abac.mockup_processor")

MOCKUPS_DIR = Path(__file__).parent / "static" / "img" / "mockups"
DB_PATH     = Path(__file__).parent / "data" / "shop.db"

_rembg_session = None
_rembg_available = None


def _get_session():
    global _rembg_session, _rembg_available
    if _rembg_available is False:
        return None
    if _rembg_session is None:
        try:
            from rembg import new_session
            _rembg_session = new_session("isnet-general-use")
            _rembg_available = True
            logger.info("rembg isnet-general-use session initialised")
        except Exception as e:
            _rembg_available = False
            logger.warning(f"rembg not available — mockup auto-processing disabled: {e}")
    return _rembg_session


def _needs_processing(url: str | None) -> bool:
    """Return True if url is external and should be converted to a local transparent PNG."""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


def _process_url(url: str, dest_path: Path) -> str | None:
    """Download url, remove background, save transparent PNG. Returns web path or None on failure."""
    from rembg import remove
    import numpy as np
    from PIL import Image

    try:
        session = _get_session()
        if session is None:
            logger.warning("rembg unavailable — skipping mockup processing")
            return None
        MOCKUPS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading {url}")
        raw = _req.get(url, timeout=30).content

        from rembg import remove
        result  = remove(raw, session=session)

        rgba = Image.open(io.BytesIO(result)).convert("RGBA")
        import numpy as np
        arr = np.array(rgba)
        # Hard-threshold: semi-transparent halos → fully transparent
        arr[:, :, 3] = (arr[:, :, 3] >= 128).astype("uint8") * 255
        Image.fromarray(arr, "RGBA").save(dest_path, "PNG")
        logger.info(f"Saved mockup → {dest_path}")
        return f"/img/mockups/{dest_path.name}"
    except Exception as e:
        logger.error(f"mockup_processor failed for {url}: {e}")
        return None


def process_product(product_id: int):
    """
    Called as a background task after create/update.
    Checks both image_url and back_image_url; if either is external, converts it.
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT image_url, back_image_url FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not row:
            return

        updates = {}

        for col, view_label in [("image_url", "front"), ("back_image_url", "back")]:
            url = row[col]
            if _needs_processing(url):
                dest = MOCKUPS_DIR / f"product_{product_id}_{view_label}.png"
                new_url = _process_url(url, dest)
                if new_url:
                    updates[col] = new_url

        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(
                f"UPDATE products SET {set_clause} WHERE id=?",
                (*updates.values(), product_id),
            )
            conn.commit()
            logger.info(f"Product {product_id} mockups updated: {updates}")
    finally:
        conn.close()
