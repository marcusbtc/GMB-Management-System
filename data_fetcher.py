import pandas as pd
import time
from urllib.parse import quote
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from src.gmb_app.core.logging import get_logger

MYBUSINESS_V4_DISCOVERY_URL = "https://developers.google.com/my-business/samples/mybusiness_google_rest_v4p9.json"
POST_TOPIC_TYPES = {"STANDARD", "OFFER", "EVENT"}
POST_CTA_TYPES = {
    "BOOK",
    "ORDER",
    "SHOP",
    "LEARN_MORE",
    "SIGN_UP",
    "CALL",
}




logger = get_logger("data_fetcher")

def get_mybusiness_service(_credentials):
    """Returns a mybusiness v4 service client."""
    return build(
        "mybusiness",
        "v4",
        credentials=_credentials,
        discoveryServiceUrl=MYBUSINESS_V4_DISCOVERY_URL,
        static_discovery=False,
    )

def get_accounts(_credentials):
    """Fetches a list of accounts for the authenticated user."""
    try:
        service_account = build('mybusinessaccountmanagement', 'v1', credentials=_credentials)
        accounts_result = service_account.accounts().list().execute()
        return accounts_result.get('accounts', [])
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return []

def get_account_for_location(_credentials, location_name):
    """Gets the account ID for a location by iterating through accounts.

    Args:
        _credentials: Google API credentials
        location_name: Location name in format 'locations/{locationId}'

    Returns:
        Full location path in format 'accounts/{accountId}/locations/{locationId}' or original name
    """
    try:
        # If already in full format, return as-is
        if location_name.startswith('accounts/'):
            return location_name

        # Extract location ID
        if not location_name.startswith('locations/'):
            return location_name

        location_id = location_name.replace('locations/', '')

        # Get all accounts and try each one
        accounts = get_accounts(_credentials)
        service_business = build('mybusinessbusinessinformation', 'v1', credentials=_credentials)

        for account in accounts:
            try:
                full_path = f"{account['name']}/locations/{location_id}"
                # Try to fetch this location under this account
                service_business.accounts().locations().get(
                    name=full_path,
                    readMask="name"
                ).execute()
                # If successful, return the full path
                return full_path
            except Exception as e:
                # Location not in this account, continue to next
                continue

        # If not found in any account, return original
        return location_name
    except Exception as e:
        # On error, return original name
        return location_name

def get_all_accessible_locations(_credentials):
    """Fetches ALL locations accessible by the user using v1 APIs.

    Iterates through all accounts and fetches locations from each.

    Args:
        _credentials: Google API credentials

    Returns:
        List of location objects with full path names in v1 format
    """
    try:
        # Get all accounts using Account Management API v1
        accounts = get_accounts(_credentials)

        if not accounts:
            logger.warning("No accounts found.")
            return []

        all_locations = []
        service_business = build('mybusinessbusinessinformation', 'v1', credentials=_credentials)
        read_mask = "name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,categories,specialHours,serviceArea"

        # Fetch locations from each account
        for account in accounts:
            try:
                page_token = None

                while True:
                    request_params = {
                        'parent': account['name'],
                        'readMask': read_mask,
                        'pageSize': 100
                    }
                    if page_token:
                        request_params['pageToken'] = page_token

                    locations_result = service_business.accounts().locations().list(**request_params).execute()
                    locations = locations_result.get('locations', [])

                    # Ensure all locations have full paths
                    for loc in locations:
                        if not loc.get('name', '').startswith('accounts/'):
                            # Fix the path if it's not in full format
                            if loc.get('name', '').startswith('locations/'):
                                loc['name'] = f"{account['name']}/{loc['name']}"
                            else:
                                # It's just the ID, need both prefixes
                                loc['name'] = f"{account['name']}/locations/{loc['name']}"

                    all_locations.extend(locations)

                    page_token = locations_result.get('nextPageToken')
                    if not page_token:
                        break

            except Exception as e:
                # Skip accounts that error (user might not have location access for this account)
                continue

        return all_locations

    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []

def get_locations(_credentials, account_name=None):
    """Fetches a list of locations for the specified account, or all locations if account_name is None.

    Args:
        _credentials: Google API credentials
        account_name: Account name in format 'accounts/{accountId}', or None to fetch all locations

    """
    if account_name is None:
        # Fetch from all accounts
        return get_all_accessible_locations(_credentials)

    try:
        service_business = build('mybusinessbusinessinformation', 'v1', credentials=_credentials)
        read_mask = "name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,categories,specialHours,serviceArea"

        all_locations = []
        page_token = None

        while True:
            request_params = {
                'parent': account_name,
                'readMask': read_mask,
                'pageSize': 100
            }
            if page_token:
                request_params['pageToken'] = page_token

            locations_result = service_business.accounts().locations().list(**request_params).execute()
            locations = locations_result.get('locations', [])

            # Ensure all locations have full paths
            for loc in locations:
                if not loc.get('name', '').startswith('accounts/'):
                    # Fix the path if it's not in full format
                    if loc.get('name', '').startswith('locations/'):
                        loc['name'] = f"{account_name}/{loc['name']}"
                    else:
                        # It's just the ID, need both prefixes
                        loc['name'] = f"{account_name}/locations/{loc['name']}"

            all_locations.extend(locations)

            page_token = locations_result.get('nextPageToken')
            if not page_token:
                break

        return all_locations
    except Exception as e:
        logger.error(f"Error fetching locations from {account_name}: {e}")
        return []

def extract_location_path(location_id):
    """Extracts the locations/{locationId} part from a full path.

    Args:
        location_id: Can be in format:
            - 'accounts/{accountId}/locations/{locationId}'
            - 'locations/{locationId}'
            - '{locationId}'

    Returns:
        'locations/{locationId}' format
    """
    if location_id.startswith('accounts/'):
        # Extract locations/{locationId} from accounts/{accountId}/locations/{locationId}
        parts = location_id.split('/')
        if len(parts) >= 4 and parts[2] == 'locations':
            return f"locations/{parts[3]}"

    if location_id.startswith('locations/'):
        return location_id

    # Just the ID, add prefix
    return f"locations/{location_id}"


def resolve_location_parent(_credentials, location_id, account_name=None):
    """Resolves a location to accounts/{accountId}/locations/{locationId} format."""
    if location_id.startswith("accounts/"):
        return location_id

    if location_id.startswith("locations/"):
        if account_name:
            return f"{account_name}/{location_id}"
        full_location_path = get_account_for_location(_credentials, location_id)
        if full_location_path.startswith("accounts/"):
            return full_location_path
        raise ValueError(
            f"Could not find account for location '{location_id}'. Please provide account_name parameter."
        )

    if account_name:
        return f"{account_name}/locations/{location_id}"

    full_location_path = get_account_for_location(_credentials, f"locations/{location_id}")
    if full_location_path.startswith("accounts/"):
        return full_location_path
    raise ValueError(
        f"Could not find account for location '{location_id}'. Please provide account_name parameter."
    )


def build_local_post_payload(summary, topic_type="STANDARD", language_code="pt-BR", cta_type=None, cta_url=None, image_url=None):
    """Builds a validated local post payload for GBP API."""
    summary_clean = (summary or "").strip()
    if not summary_clean:
        raise ValueError("Summary is required.")

    topic_type_clean = (topic_type or "STANDARD").strip().upper()
    if topic_type_clean not in POST_TOPIC_TYPES:
        raise ValueError(f"Unsupported topic type: {topic_type_clean}")

    payload = {
        "languageCode": (language_code or "pt-BR").strip(),
        "summary": summary_clean,
        "topicType": topic_type_clean,
    }

    cta_type_clean = (cta_type or "").strip().upper()
    cta_url_clean = (cta_url or "").strip()
    if cta_type_clean or cta_url_clean:
        if cta_type_clean not in POST_CTA_TYPES:
            raise ValueError(
                "Invalid CTA type. Use one of: BOOK, ORDER, SHOP, LEARN_MORE, SIGN_UP, CALL."
            )
        if not (cta_url_clean.startswith("http://") or cta_url_clean.startswith("https://")):
            raise ValueError("CTA URL must start with http:// or https://")
        payload["callToAction"] = {"actionType": cta_type_clean, "url": cta_url_clean}

    image_url_clean = (image_url or "").strip()
    if image_url_clean:
        if not (image_url_clean.startswith("http://") or image_url_clean.startswith("https://")):
            raise ValueError("Image URL must start with http:// or https://")
        payload["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": image_url_clean}]

    return payload

def get_daily_metrics(_credentials, location_id, start_date, end_date):
    """Fetches daily metrics from API."""
    if not _credentials:
        logger.error("No credentials provided.")
        return pd.DataFrame()

    try:
        # Extract just the locations/{locationId} part for the performance API
        location_path = extract_location_path(location_id)

        # Use static_discovery=False to ensure we get the latest API definition
        service = build('businessprofileperformance', 'v1', credentials=_credentials, static_discovery=False)
        
        # List of metrics to fetch
        metrics_to_fetch = [
            "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
            "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
            "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
            "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
            "WEBSITE_CLICKS",
            "CALL_CLICKS",
            "BUSINESS_DIRECTION_REQUESTS",
            "BUSINESS_CONVERSATIONS",
            "BUSINESS_BOOKINGS",
            "BUSINESS_FOOD_ORDERS"
        ]
        
        # Dictionary to store aggregated data: date -> {metric: value}
        data = {}
        
        for metric in metrics_to_fetch:
            try:
                # Flatten dailyRange for GET request
                request = service.locations().getDailyMetricsTimeSeries(
                    name=location_path,
                    dailyMetric=metric,
                    dailyRange_startDate_year=start_date.year,
                    dailyRange_startDate_month=start_date.month,
                    dailyRange_startDate_day=start_date.day,
                    dailyRange_endDate_year=end_date.year,
                    dailyRange_endDate_month=end_date.month,
                    dailyRange_endDate_day=end_date.day
                )
                response = request.execute()
                
                time_series = response.get('timeSeries')
                
                if time_series and isinstance(time_series, dict):
                    # It's a single object, not a list
                    dated_values = time_series.get('datedValues', [])
                    
                    for val in dated_values:
                        date_str = f"{val['date']['year']}-{val['date']['month']}-{val['date']['day']}"
                        date = pd.to_datetime(date_str)
                        value = int(val.get('value', 0))
                        
                        if date not in data:
                            data[date] = {'date': date}
                        
                        # Store metric directly
                        data[date][metric] = value

                elif time_series and isinstance(time_series, list):
                     # Fallback if it is a list
                     for series in time_series:
                        dated_values = series.get('datedValues', [])
                        for val in dated_values:
                            date_str = f"{val['date']['year']}-{val['date']['month']}-{val['date']['day']}"
                            date = pd.to_datetime(date_str)
                            value = int(val.get('value', 0))
                            
                            if date not in data:
                                data[date] = {'date': date}
                            
                            data[date][metric] = value
                            
            except Exception as loop_e:
                # Log warning but continue with other metrics
                # logger.warning(f"Could not fetch data for {metric}: {loop_e}")
                pass

        # Convert to list and then DataFrame
        final_data = list(data.values())
        if not final_data:
             logger.info("No metrics data found for this period.")
             return pd.DataFrame()
             
        df = pd.DataFrame(final_data).sort_values('date')
        
        # Fill missing columns with 0
        for metric in metrics_to_fetch:
            if metric not in df.columns:
                df[metric] = 0
        
        return df.fillna(0)

    except Exception as e:
        logger.error(f"Error fetching daily metrics: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return pd.DataFrame()

def get_search_keywords(_credentials, location_id, start_date, end_date):
    """Fetches search keywords from API."""
    if not _credentials:
        return pd.DataFrame()

    try:
        # Extract just the locations/{locationId} part for the performance API
        location_path = extract_location_path(location_id)

        service = build('businessprofileperformance', 'v1', credentials=_credentials, static_discovery=False)

        all_keywords = []
        next_page_token = None

        while True:
            request = service.locations().searchkeywords().impressions().monthly().list(
                parent=location_path,
                monthlyRange_startMonth_year=start_date.year,
                monthlyRange_startMonth_month=start_date.month,
                monthlyRange_endMonth_year=end_date.year,
                monthlyRange_endMonth_month=end_date.month,
                pageSize=100,
                pageToken=next_page_token
            )
            response = request.execute()
            
            keywords_counts = response.get('searchKeywordsCounts', [])
            all_keywords.extend(keywords_counts)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        data = []
        for item in all_keywords:
            keyword = item.get('searchKeyword')
            insights_value = item.get('insightsValue', {})
            
            count = insights_value.get('value')
            threshold = insights_value.get('threshold')
            
            if count:
                data.append({
                    "keyword": keyword,
                    "count": int(count),
                    "display_count": str(count)
                })
            elif threshold:
                data.append({
                    "keyword": keyword,
                    "count": int(threshold), # Use threshold for sorting
                    "display_count": f"< {threshold}"
                })
            
        if not data:
            logger.info("No search keywords found for this period.")
            return pd.DataFrame(columns=['keyword', 'count', 'display_count'])
            
        return pd.DataFrame(data).sort_values("count", ascending=False)

    except Exception as e:
        logger.error(f"Error fetching keywords: {e}")
        # import traceback
        # logger.debug(traceback.format_exc())
        return pd.DataFrame()

def get_reviews(_credentials, location_id, account_name=None):
    """Fetches reviews for the specified location.

    Args:
        _credentials: Google API credentials
        location_id: Location ID in format 'locations/{locationId}' or 'accounts/{accountId}/locations/{locationId}'
        account_name: Optional account name in format 'accounts/{accountId}'
    """
    if not _credentials:
        return []

    try:
        service = get_mybusiness_service(_credentials)
        parent = resolve_location_parent(_credentials, location_id, account_name)

        reviews_result = service.accounts().locations().reviews().list(
            parent=parent,
            pageSize=50
        ).execute()

        return reviews_result.get('reviews', [])
    except Exception as e:
        logger.warning(f"Could not fetch reviews: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def reply_to_review(_credentials, review_name, comment, location_id=None, account_name=None):
    """Posts a reply to a GBP review via mybusiness v4 updateReply."""
    if not _credentials:
        raise ValueError("No credentials provided.")
    comment_clean = (comment or "").strip()
    if not comment_clean:
        raise ValueError("Reply comment is required.")

    name = (review_name or "").strip()
    if not name:
        raise ValueError("review_name is required.")

    if not name.startswith("accounts/"):
        if not location_id:
            raise ValueError(
                "review_name must be accounts/{accountId}/locations/{locationId}/reviews/{reviewId} "
                "or provide location_id so the parent path can be resolved."
            )
        parent = resolve_location_parent(_credentials, location_id, account_name)
        review_id = name.replace("reviews/", "")
        name = f"{parent}/reviews/{review_id}"

    service = get_mybusiness_service(_credentials)
    return service.accounts().locations().reviews().updateReply(
        name=name,
        body={"comment": comment_clean},
    ).execute()

def get_posts(_credentials, location_id, account_name=None):
    """Fetches local posts for the specified location.

    Args:
        _credentials: Google API credentials
        location_id: Location ID in format 'locations/{locationId}' or 'accounts/{accountId}/locations/{locationId}'
        account_name: Optional account name in format 'accounts/{accountId}'
    """
    if not _credentials:
        return []

    try:
        service = get_mybusiness_service(_credentials)
        parent = resolve_location_parent(_credentials, location_id, account_name)

        posts_result = service.accounts().locations().localPosts().list(
            parent=parent,
            pageSize=20
        ).execute()

        return posts_result.get('localPosts', [])
    except Exception as e:
        logger.warning(f"Could not fetch posts: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def create_local_post(_credentials, location_id, account_name=None, payload=None):
    """Creates a local post in Google Business Profile."""
    if not _credentials:
        raise ValueError("No credentials provided.")
    if not payload or not isinstance(payload, dict):
        raise ValueError("A valid post payload is required.")

    service = get_mybusiness_service(_credentials)
    parent = resolve_location_parent(_credentials, location_id, account_name)
    return service.accounts().locations().localPosts().create(
        parent=parent,
        body=payload,
    ).execute()


def invalidate_posts_cache():
    """Clears cached local posts so the UI can reload fresh data after publish."""
    get_posts.clear()


def upload_media_from_file(
    _credentials,
    location_id,
    account_name=None,
    file_bytes=None,
    mime_type=None,
    photo_category="ADDITIONAL",
):
    """Uploads a local image file to GBP media and returns the created media item."""
    if not _credentials:
        raise ValueError("No credentials provided.")
    if not file_bytes:
        raise ValueError("File is empty.")
    allowed_mime_types = {"image/jpeg", "image/jpg", "image/png"}
    if mime_type and mime_type.lower() not in allowed_mime_types:
        raise ValueError(
            "Unsupported image format for GBP bytes upload. Use JPG or PNG."
        )

    if _credentials.expired and _credentials.refresh_token:
        _credentials.refresh(Request())

    service = get_mybusiness_service(_credentials)
    parent = resolve_location_parent(_credentials, location_id, account_name)

    data_ref = service.accounts().locations().media().startUpload(
        parent=parent,
        body={},
    ).execute()
    resource_name = data_ref.get("resourceName")
    if not resource_name:
        raise ValueError("Could not get upload resource name from Google API.")

    upload_urls = [
        f"https://mybusiness.googleapis.com/upload/v4/{quote(resource_name, safe='/')}?uploadType=media",
        f"https://mybusiness.googleapis.com/upload/v4/{quote(resource_name, safe='')}?uploadType=media",
        f"https://mybusiness.googleapis.com/upload/v1/media/{quote(resource_name, safe='/')}?uploadType=media",
        f"https://mybusiness.googleapis.com/upload/v1/media/{quote(resource_name, safe='')}?uploadType=media",
        f"https://mybusiness.googleapis.com/upload/v1/media/{quote(resource_name, safe='/')}?upload_type=media",
    ]
    upload_errors = []
    upload_ok = False

    for upload_url in upload_urls:
        req = UrlRequest(
            upload_url,
            data=file_bytes,
            method="POST",
            headers={
                "Authorization": f"Bearer {_credentials.token}",
                "Content-Type": mime_type or "application/octet-stream",
                "Content-Length": str(len(file_bytes)),
                "X-Goog-Upload-Protocol": "raw",
                "X-Goog-Upload-File-Name": "post-image",
            },
        )
        try:
            with urlopen(req):
                upload_ok = True
                break
        except HTTPError as http_error:
            details = ""
            try:
                details = http_error.read().decode("utf-8", errors="ignore")
            except Exception:
                details = str(http_error)
            upload_errors.append(
                f"upload failed ({http_error.code}) on {upload_url}: {details[:280]}"
            )

    if not upload_ok:
        joined_errors = " | ".join(upload_errors) if upload_errors else "unknown upload error"
        raise ValueError(f"Could not upload image bytes to Google media endpoint: {joined_errors}")

    category_candidates = [photo_category, "ADDITIONAL", "EXTERIOR", "INTERIOR", "PRODUCT"]
    deduped_categories = []
    for candidate in category_candidates:
        if candidate not in deduped_categories:
            deduped_categories.append(candidate)

    media_item = None
    create_errors = []
    for category in deduped_categories:
        try:
            media_item = service.accounts().locations().media().create(
                parent=parent,
                body={
                    "mediaFormat": "PHOTO",
                    "dataRef": {"resourceName": resource_name},
                    "locationAssociation": {"category": category},
                },
            ).execute()
            break
        except HttpError as http_error:
            status_code = getattr(http_error, "status_code", None) or getattr(
                getattr(http_error, "resp", None), "status", None
            )
            details = ""
            try:
                details = http_error.content.decode("utf-8", errors="ignore")
            except Exception:
                details = str(http_error)
            create_errors.append(
                f"media.create failed ({status_code}) category={category}: {details[:280]}"
            )
            # Retry on backend/internal and validation-class errors; raise others immediately.
            if status_code not in {400, 500, 503}:
                raise

    if not media_item:
        raise ValueError(
            "Could not create media item after retries. "
            + (" | ".join(create_errors) if create_errors else "No details from API.")
        )

    # Google can take a short time to process uploaded bytes into a usable media URL.
    media_name = media_item.get("name")
    if not media_name:
        return media_item

    if media_item.get("googleUrl") or media_item.get("sourceUrl"):
        return media_item

    for _ in range(5):
        time.sleep(1)
        refreshed = service.accounts().locations().media().get(name=media_name).execute()
        if refreshed.get("googleUrl") or refreshed.get("sourceUrl"):
            return refreshed

    return media_item

def get_media(_credentials, location_id, account_name=None):
    """Fetches media items for the specified location."""
    try:
        service_media = get_mybusiness_service(_credentials)
        parent = resolve_location_parent(_credentials, location_id, account_name)
        media_result = service_media.accounts().locations().media().list(
            parent=parent,
            pageSize=50
        ).execute()
        return media_result.get('mediaItems', [])
    except Exception as e:
        # logger.warning(f"Could not fetch media: {e}")
        return []

def get_location_details(_credentials, location_id, account_name=None):
    """Fetches a single location via mybusinessbusinessinformation v1."""
    if not _credentials:
        raise ValueError("No credentials provided.")

    read_mask = (
        "name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,"
        "categories,specialHours,serviceArea,openInfo,profile"
    )
    service = build("mybusinessbusinessinformation", "v1", credentials=_credentials)

    names_to_try = []
    try:
        names_to_try.append(resolve_location_parent(_credentials, location_id, account_name))
    except ValueError:
        pass
    location_only = extract_location_path(location_id)
    if location_only not in names_to_try:
        names_to_try.append(location_only)

    last_error = None
    for name in names_to_try:
        try:
            return service.accounts().locations().get(name=name, readMask=read_mask).execute()
        except Exception as exc:
            last_error = exc

    location_suffix = extract_location_path(location_id)
    for loc in get_locations(_credentials, account_name):
        loc_name = loc.get("name", "")
        if loc_name == location_id or loc_name.endswith(location_suffix):
            return loc

    if last_error:
        raise last_error
    raise ValueError(f"Location not found: {location_id}")


# Note: Q&A API might require 'mybusinessquestions' service
def get_questions(_credentials, location_id):
    """Fetches questions for the specified location."""
    try:
        # Extract just the locations/{locationId} part
        location_path = extract_location_path(location_id)

        service_qa = build('mybusinessquestions', 'v1', credentials=_credentials)
        questions_result = service_qa.locations().questions().list(
            parent=location_path,
            pageSize=20
        ).execute()
        return questions_result.get('questions', [])
    except Exception as e:
        # logger.warning(f"Could not fetch questions: {e}")
        return []
