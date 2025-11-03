import os
from typing import Any, Dict, Optional

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
_API_KEY = os.getenv("CLOUDINARY_API_KEY")
_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
_SECURE = os.getenv("CLOUDINARY_SECURE", "1")

# if not (_CLOUD_NAME and _API_KEY and _API_SECRET):
#     raise RuntimeError(
#         "Cloudinary environment variables missing. Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET."
#     )

cloudinary.config(
    cloud_name=_CLOUD_NAME,
    api_key=_API_KEY,
    api_secret=_API_SECRET,
    secure=_SECURE not in {"0", "false", "False"},
)


def upload_image(
        file: Any,
        *,
        folder: Optional[str] = None,
        public_id: Optional[str] = None,
        overwrite: bool = False,
        resource_type: str = "image",
        use_upload_preset: Optional[str] = "news_aggrigator",  # Using your preset
        **options: Any,
) -> Dict[str, Any]:
    """Upload a file to Cloudinary and return the upload response.

    file can be a file path, file-like object, bytes, or remote URL.

    Args:
        file: The file to upload
        folder: The folder path where to store the image
        public_id: The public identifier for the asset
        overwrite: Whether to overwrite existing assets with the same public_id
        resource_type: The type of resource ("image", "video", "raw")
        use_upload_preset: Use your "news_aggrigator" upload preset
        **options: Additional Cloudinary upload options

    Returns:
        Dict containing the upload response from Cloudinary
    """
    params: Dict[str, Any] = {
        "overwrite": overwrite,
        "resource_type": resource_type,
        "use_filename": True,  # Based on your preset settings
    }

    if folder:
        params["folder"] = folder
    if public_id:
        params["public_id"] = public_id
    if use_upload_preset:
        params["upload_preset"] = use_upload_preset

    params.update(options)
    return cloudinary.uploader.upload(file, **params)


def upload_with_news_preset(
        file: Any,
        folder: Optional[str] = None,
        public_id: Optional[str] = None,
        **options: Any,
) -> Dict[str, Any]:
    """Convenience function specifically for news aggregator uploads using your preset."""
    return upload_image(
        file,
        folder=folder,
        public_id=public_id,
        use_upload_preset="news_aggrigator",
        **options
    )


def delete_asset(public_id: str, *, resource_type: str = "image", invalidate: bool = False) -> Dict[str, Any]:
    """Delete an asset by public_id."""
    return cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=invalidate)


def build_url(
        public_id: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: Optional[str] = "fill",
        fmt: Optional[str] = None,
        secure: bool = True,
        resource_type: str = "image",
        type: str = "upload",
        **options: Any,
) -> str:
    """Generate a transformed delivery URL for a Cloudinary asset."""
    transformation: Dict[str, Any] = {}
    if width is not None:
        transformation["width"] = width
    if height is not None:
        transformation["height"] = height
    if crop is not None:
        transformation["crop"] = crop
    if fmt is not None:
        options["format"] = fmt

    url, _ = cloudinary_url(
        public_id,
        secure=secure,
        resource_type=resource_type,
        type=type,
        transformation=transformation if transformation else None,
        **options,
    )
    return url


def get_upload_presets() -> Dict[str, Any]:
    """Get all upload presets for your account."""
    return cloudinary.api.upload_presets()


def get_news_preset_details() -> Dict[str, Any]:
    """Get details of your news_aggrigator upload preset."""
    return cloudinary.api.upload_preset("news_aggrigator")


__all__ = [
    "upload_image",
    "upload_with_news_preset",
    "delete_asset",
    "build_url",
    "get_upload_presets",
    "get_news_preset_details",
]