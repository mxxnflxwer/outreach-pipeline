import os
import time
import requests
from typing import List, Dict, Optional, Tuple
from utils.helpers import (
    load_from_cache,
    save_to_cache,
    retry_with_backoff,
    load_json_file,
    save_json_file,
    print_stage_summary
)

RATE_LIMIT_SLEEP = 30

def get_email_for_person(person: Dict) -> Tuple[Optional[str], bool]:
    """
    Resolves email for a person using Prospeo's Enrich Person endpoint.
    Uses person_id if available, otherwise tries linkedin_url.
    """
    person_id = person.get("person_id", "")
    linkedin_url = person.get("linkedin_url", "")
    
    cache_key = person_id if person_id else linkedin_url
    if not cache_key:
        return None, False

    cached = load_from_cache("emails", cache_key)
    if cached is not None:
        cached_email = cached.get("email")
        if cached_email:
            print(f"[Cache] Hit for {person.get('name')} — skipping API call")
            return cached_email, True
        print(f"[Cache] Entry for {person.get('name')} has no email — attempting fresh lookup")

    prospeo_api_key = os.getenv("PROSPEO_API_KEY")
    if not prospeo_api_key or prospeo_api_key == "your_key_here":
        print(f"✗ Prospeo API key not configured.")
        return None, False

    def make_api_call():
        url = "https://api.prospeo.io/enrich-person"
        
        headers = {
            "X-KEY": prospeo_api_key,
            "Content-Type": "application/json"
        }
        
        if person_id:
            payload = {
                "only_verified_email": False,
                "data": {
                    "person_id": person_id
                }
            }
        else:
            payload = {
                "only_verified_email": False,
                "data": {
                    "linkedin_url": linkedin_url
                }
            }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if not response.ok:
            try:
                body = response.json()
                if body.get("error_code") == "NO_MATCH":
                    print(f"⚠ No email found for {person.get('name')}")
                    return {"person": {}}
                if body.get("error_code") == "Rate limit exceeded" or response.status_code == 429:
                    print(f"⚠ Rate limit hit for {person.get('name')} — waiting {RATE_LIMIT_SLEEP}s...")
                    time.sleep(RATE_LIMIT_SLEEP)
            except Exception:
                pass
            print(f"Prospeo enrich error: {response.text}")
            response.raise_for_status()
        return response.json()

    result = retry_with_backoff(make_api_call, max_retries=3)
    if result is None:
        return None, False

    person_data = result.get("person", {})
    email_obj = person_data.get("email", {})
    
    if isinstance(email_obj, dict):
        email = email_obj.get("email", "")
    else:
        email = email_obj or ""

    save_to_cache("emails", cache_key, {"email": email, "name": person.get("name")})
    return email, False


def run_stage3(prospects: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
    print(f"\n{'='*60}")
    print(f"[Stage 3] Resolving Emails")
    print(f"{'='*60}")

    if prospects is None:
        prospects = load_json_file("data/prospects.json")
        if prospects is None:
            print("✗ No prospects available. Run Stage 2 first.")
            return None

    if len(prospects) == 0:
        print("⚠ No prospects found for Stage 3.")
        return []

    enriched: List[Dict] = []
    cache_hits = 0
    fresh_resolves = 0
    failed_resolves = 0

    for prospect in prospects:
        email, from_cache = get_email_for_person(prospect)
        
        if email is None:
            failed_resolves += 1
            continue

        if from_cache:
            cache_hits += 1
        else:
            fresh_resolves += 1

        if not email:
            print(f"⚠ No email found for {prospect.get('name')} — skipping")
            continue

        enriched.append({
            "name": prospect.get("name", "Unknown"),
            "title": prospect.get("title", "Unknown"),
            "company_domain": prospect.get("company_domain", ""),
            "company_name": prospect.get("company_name", ""),
            "linkedin_url": prospect.get("linkedin_url", ""),
            "email": email,
            "location": prospect.get("location", "")
        })

    if len(enriched) == 0:
        print("⚠ No emails resolved in Stage 3.")
        return []

    saved = save_json_file("data/emails.json", enriched)
    if not saved:
        print("✗ Failed to save to data/emails.json")
        return None

    print(f"\n✓ Resolved {len(enriched)} email addresses")
    print(f"✓ Saved to data/emails.json")
    print_stage_summary(
        3,
        f"Resolved {len(enriched)} emails. {cache_hits} from cache, "
        f"{fresh_resolves} fresh, {failed_resolves} failed."
    )

    return enriched