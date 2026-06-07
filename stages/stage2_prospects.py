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

def get_prospects_for_domain(domain: str) -> Tuple[Optional[List[Dict]], bool]:
    cached_data = load_from_cache("prospects", domain)
    if cached_data is not None:
        print(f"[Cache] Hit for {domain} — skipping API call")
        return cached_data.get("prospects", []), True

    prospeo_api_key = os.getenv("PROSPEO_API_KEY")
    if not prospeo_api_key or prospeo_api_key == "your_key_here":
        print(f"✗ Prospeo API key not configured.")
        return None, False

    def make_api_call():
        url = "https://api.prospeo.io/search-person"
        
        headers = {
            "X-KEY": prospeo_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "page": 1,
            "filters": {
                "company": {
                    "websites": {
                        "include": [domain]
                    }
                },
                "person_seniority": {
                    "include": ["C-Suite", "Founder/Owner", "Vice President", "Director"]
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # NO_RESULTS means no people found — not a real error
        if not response.ok:
            try:
                body = response.json()
                if body.get("error_code") == "NO_RESULTS":
                    print(f"⚠ No results found for {domain} — skipping")
                    return {"results": []}
                # Rate limit — wait longer before retrying
                if body.get("error_code") == "Rate limit exceeded" or response.status_code == 429:
                    print(f"⚠ Rate limit hit for {domain} — waiting {RATE_LIMIT_SLEEP}s...")
                    time.sleep(RATE_LIMIT_SLEEP)
            except Exception:
                pass
            print(f"Prospeo error response: {response.text}")
            response.raise_for_status()
        
        return response.json()

    result = retry_with_backoff(make_api_call, max_retries=3)
    if result is None:
        print(f"✗ Failed to fetch prospects for {domain}")
        return None, False

    prospects = result.get("results") or []
    
    cache_data = {
        "domain": domain,
        "prospects": prospects,
        "count": len(prospects)
    }
    save_to_cache("prospects", domain, cache_data)
    return prospects, False


def run_stage2(domains: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
    print(f"\n{'='*60}")
    print(f"[Stage 2] Finding Decision Makers")
    print(f"{'='*60}")

    if domains is None:
        domains = load_json_file("data/domains.json")
        if domains is None:
            print("✗ No domains available. Run Stage 1 first.")
            return None

    if len(domains) == 0:
        print("⚠ No domains found for Stage 2.")
        return []

    all_prospects: List[Dict] = []
    cache_hits = 0
    fresh_lookups = 0
    failed_domains = 0

    for item in domains:
        domain = item.get("domain")
        if not domain:
            continue

        prospects, from_cache = get_prospects_for_domain(domain)
        if prospects is None:
            failed_domains += 1
            continue

        if from_cache:
            cache_hits += 1
        else:
            fresh_lookups += 1
            # Wait 10 seconds between fresh API calls to reduce rate-limit risk
            time.sleep(10)

        for prospect in prospects:
            person = prospect.get("person", prospect)
            first = person.get("first_name", "")
            last = person.get("last_name", "")
            name = f"{first} {last}".strip() or "Unknown"
            linkedin_url = person.get("linkedin_url", "")

            enriched = {
                "name": name,
                "title": person.get("current_job_title", "Unknown"),
                "company_domain": domain,
                "company_name": item.get("name", "Unknown"),
                "linkedin_url": linkedin_url,
                "email": "",
                "location": person.get("location", {}).get("country", "Unknown"),
                "person_id": person.get("person_id", "")
            }
            all_prospects.append(enriched)

    if len(all_prospects) == 0:
        print("⚠ No prospects found after Stage 2.")
        return []

    saved = save_json_file("data/prospects.json", all_prospects)
    if not saved:
        print("✗ Failed to save prospects to data/prospects.json")
        return None

    print(f"\n✓ Found {len(all_prospects)} prospects")
    print(f"✓ Saved to data/prospects.json")
    print_stage_summary(
        2,
        f"Found {len(all_prospects)} prospects across {len(domains)} domains. "
        f"{cache_hits} from cache, {fresh_lookups} fresh, {failed_domains} failed."
    )

    return all_prospects