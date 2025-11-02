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
    **options: Any,
) -> Dict[str, Any]:
    """Upload a file to Cloudinary and return the upload response.

    file can be a file path, file-like object, bytes, or remote URL.
    """
    params: Dict[str, Any] = {"overwrite": overwrite, "resource_type": resource_type}
    if folder:
        params["folder"] = folder
    if public_id:
        params["public_id"] = public_id
    params.update(options)
    return cloudinary.uploader.upload(file, **params)


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


__all__ = [
    "upload_image",
    "delete_asset",
    "build_url",
]


