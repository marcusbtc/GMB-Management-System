"""Thin JSON wrappers over data_fetcher.py and drive_helper.py.

Google API calls stay in those modules. This layer only resolves credentials,
normalizes arguments, and returns JSON-serializable dicts.
"""

import base64

import data_fetcher
import drive_helper
import health_check
from src.gmb_mcp.jsonutil import dataframe_to_records, json_ready, parse_date


def list_accounts(credentials):
    return {"accounts": json_ready(data_fetcher.get_accounts(credentials))}


def list_locations(credentials, account_name=None):
    account = (account_name or "").strip() or None
    return {"locations": json_ready(data_fetcher.get_locations(credentials, account))}


def get_daily_metrics(credentials, location_id, start_date, end_date):
    start = parse_date(start_date)
    end = parse_date(end_date)
    frame = data_fetcher.get_daily_metrics(credentials, location_id, start, end)
    return {
        "location_id": location_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "metrics": dataframe_to_records(frame),
    }


def get_search_keywords(credentials, location_id, start_date, end_date):
    start = parse_date(start_date)
    end = parse_date(end_date)
    frame = data_fetcher.get_search_keywords(credentials, location_id, start, end)
    return {
        "location_id": location_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "keywords": dataframe_to_records(frame),
    }


def list_reviews(credentials, location_id, account_name=None):
    account = (account_name or "").strip() or None
    parent = data_fetcher.resolve_location_parent(credentials, location_id, account)
    return {
        "parent": parent,
        "reviews": json_ready(data_fetcher.get_reviews(credentials, location_id, account)),
    }


def list_posts(credentials, location_id, account_name=None):
    account = (account_name or "").strip() or None
    parent = data_fetcher.resolve_location_parent(credentials, location_id, account)
    return {
        "parent": parent,
        "posts": json_ready(data_fetcher.get_posts(credentials, location_id, account)),
    }


def list_media(credentials, location_id, account_name=None):
    account = (account_name or "").strip() or None
    parent = data_fetcher.resolve_location_parent(credentials, location_id, account)
    return {
        "parent": parent,
        "media": json_ready(data_fetcher.get_media(credentials, location_id, account)),
    }


def list_questions(credentials, location_id):
    location_path = data_fetcher.extract_location_path(location_id)
    return {
        "parent": location_path,
        "questions": json_ready(data_fetcher.get_questions(credentials, location_id)),
    }


def profile_health_check(credentials, location_id, account_name=None):
    account = (account_name or "").strip() or None
    location = data_fetcher.get_location_details(credentials, location_id, account)
    reviews = data_fetcher.get_reviews(credentials, location_id, account)
    posts = data_fetcher.get_posts(credentials, location_id, account)
    media_items = data_fetcher.get_media(credentials, location_id, account)
    questions = data_fetcher.get_questions(credentials, location_id)
    checks = health_check.analyze_profile_health(location, reviews, posts, media_items, questions)
    scores = [item.get("score", 0) for item in checks if isinstance(item, dict)]
    overall = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "location_id": location.get("name", location_id),
        "overall_score": overall,
        "checks": json_ready(checks),
    }


def create_local_post(
    credentials,
    location_id,
    summary,
    account_name=None,
    topic_type="STANDARD",
    language_code="pt-BR",
    cta_type=None,
    cta_url=None,
    image_url=None,
    payload=None,
):
    account = (account_name or "").strip() or None
    parent = data_fetcher.resolve_location_parent(credentials, location_id, account)
    post_payload = payload if payload else data_fetcher.build_local_post_payload(
        summary=summary,
        topic_type=topic_type,
        language_code=language_code,
        cta_type=cta_type,
        cta_url=cta_url,
        image_url=image_url,
    )
    created = data_fetcher.create_local_post(
        credentials,
        location_id,
        account,
        payload=post_payload,
    )
    return {
        "parent": parent,
        "payload": json_ready(post_payload),
        "post": json_ready(created),
    }


def upload_image_to_drive(
    credentials,
    file_name,
    file_base64,
    mime_type,
    folder_id="root",
    make_public=True,
):
    file_bytes = _decode_image_base64(file_base64)
    uploaded = drive_helper.upload_file_to_folder(
        credentials,
        folder_id or "root",
        file_name,
        file_bytes,
        mime_type,
    )
    file_id = uploaded["id"]
    public_url = None
    public_url_ok = False
    if make_public:
        drive_helper.set_file_public(credentials, file_id)
        public_url = drive_helper.build_public_file_url(file_id)
        try:
            public_url_ok = bool(drive_helper.validate_public_url(public_url))
        except Exception:
            public_url_ok = False
        if not public_url_ok:
            raise ValueError("Drive file uploaded but the public URL is not reachable.")
    return {
        "file_id": file_id,
        "name": uploaded.get("name", file_name),
        "web_view_link": uploaded.get("webViewLink"),
        "web_content_link": uploaded.get("webContentLink"),
        "public_url": public_url,
        "public_url_ok": public_url_ok,
    }


def reply_to_review(credentials, review_name, comment, location_id=None, account_name=None):
    account = (account_name or "").strip() or None
    replied = data_fetcher.reply_to_review(
        credentials,
        review_name=review_name,
        comment=comment,
        location_id=location_id,
        account_name=account,
    )
    return {"reply": json_ready(replied)}


def _decode_image_base64(value):
    raw = (value or "").strip()
    if not raw:
        raise ValueError("file_base64 is required.")
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        decoded = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise ValueError("file_base64 must be valid base64 image data.") from exc
    if not decoded:
        raise ValueError("Decoded image is empty.")
    return decoded
