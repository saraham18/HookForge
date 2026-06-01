"""Publish a photo post to Instagram via the Meta Graph API.

Instagram content publishing is a two-step flow:
  1. Create a media container referencing a PUBLIC image URL + caption.
  2. Publish that container.

Requirements (set up once on your side):
  * An Instagram Business or Creator account linked to a Facebook Page.
  * A Meta app with the instagram_basic + instagram_content_publish permissions.
  * A long-lived access token (IG_ACCESS_TOKEN) and the IG user id (IG_USER_ID).

The image MUST be reachable at a public https URL - Instagram fetches it
server-side. A convenient trick: commit the image to a public GitHub repo and
use its raw.githubusercontent.com URL. ``requests`` is imported lazily.
"""
from __future__ import annotations

from typing import Any

from ..config import Config

GRAPH_BASE = "https://graph.facebook.com/v21.0"


def _requests():
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'requests' package is required to publish to Instagram. "
            "Install it with: pip install requests"
        ) from exc
    return requests


def publish_to_instagram(
    config: Config,
    caption: str,
    image_url: str,
    *,
    session: Any | None = None,
) -> dict:
    """Publish a single-image post. Returns {'id', 'url'}.

    Pass ``session`` (anything with .post/.get returning a .json()) to test.
    """
    config.require(
        IG_ACCESS_TOKEN=config.ig_access_token,
        IG_USER_ID=config.ig_user_id,
    )
    if not image_url or not image_url.startswith("http"):
        raise ValueError(
            "Instagram needs a PUBLIC https image URL (it fetches the image "
            "server-side). Got: " + repr(image_url)
        )
    http = session or _requests()
    token = config.ig_access_token
    uid = config.ig_user_id

    # Step 1: create the media container.
    create = http.post(
        f"{GRAPH_BASE}/{uid}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
    )
    create_data = create.json()
    if "id" not in create_data:
        raise RuntimeError(f"Failed to create media container: {create_data}")
    container_id = create_data["id"]

    # Step 2: publish the container.
    publish = http.post(
        f"{GRAPH_BASE}/{uid}/media_publish",
        data={"creation_id": container_id, "access_token": token},
    )
    publish_data = publish.json()
    if "id" not in publish_data:
        raise RuntimeError(f"Failed to publish media: {publish_data}")
    media_id = publish_data["id"]
    return {"id": media_id, "url": f"https://www.instagram.com/p/{media_id}/"}
