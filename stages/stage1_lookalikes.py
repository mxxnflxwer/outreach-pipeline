import os
import requests
from typing import List, Dict, Optional
from utils.helpers import (
    load_from_cache,
    save_to_cache,
    retry_with_backoff,
    load_json_file,
    save_json_file,
    print_stage_summary
)

# ============================================================================
# STAGE 1: FIND LOOKALIKE COMPANIES
# ============================================================================
# This stage takes a seed domain (e.g. "stripe.com") and finds similar
# companies using the Ocean.io API. Results are cached to avoid redundant calls.

def get_lookalike_companies(seed_domain: str) -> Optional[List[Dict]]:
    """
    Finds lookalike companies for a given seed domain using Ocean.io API.
    Checks cache first, then makes API call if not found in cache.
    """
    
    # Step 1: Check if we already have this cached
    cached_result = load_from_cache("lookalikes", seed_domain)
    if cached_result is not None:
        print(f"[Cache] Hit for {seed_domain} — skipping API call")
        return cached_result.get("companies", [])
    
    # Step 2: Get the Ocean API key from environment variables
    ocean_api_key = os.getenv("OCEAN_API_KEY")
    if not ocean_api_key or ocean_api_key == "your_key_here":
        print(f"✗ Ocean API key not configured. Please set OCEAN_API_KEY in .env")
        return None
    
    # Step 3: Define the API call function
    def make_api_call():
        """Makes the actual API request to Ocean.io"""
        url = "https://api.ocean.io/v3/search/companies"
        
        # X-Api-Token is the correct header for Ocean.io v3
        headers = {
            "X-Api-Token": ocean_api_key,
            "Content-Type": "application/json"
        }
        
        # lookalikeDomains must be an array
        payload = {
            "size": 3,
            "companiesFilters": {
                "lookalikeDomains": [seed_domain]
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    
    # Step 4: Try the API call with retry logic (max 3 attempts with backoff)
    result = retry_with_backoff(make_api_call, max_retries=3)
    
    if result is None:
        print(f"✗ Failed to fetch lookalikes for {seed_domain}")
        return None
    
    # Step 5: Extract company list from response
    companies = result.get("companies") or result.get("data") or []
    
    # Step 6: Save to cache for future runs
    cache_data = {
        "seed_domain": seed_domain,
        "companies": companies,
        "count": len(companies)
    }
    save_to_cache("lookalikes", seed_domain, cache_data)
    
    return companies


def run_stage1(seed_domain: str) -> Optional[List[Dict]]:
    """
    Main entry point for Stage 1. Finds lookalike companies and saves them.
    """
    
    print(f"\n{'='*60}")
    print(f"[Stage 1] Finding Lookalike Companies")
    print(f"{'='*60}")
    print(f"Seed domain: {seed_domain}")
    
    # Step 1: Fetch lookalike companies (uses cache or API)
    companies = get_lookalike_companies(seed_domain)
    
    # Step 2: Handle failure
    if companies is None:
        print(f"✗ Stage 1 failed: Could not fetch lookalike companies")
        return None
    
    # Step 3: Handle empty result
    if len(companies) == 0:
        print(f"⚠ No lookalike companies found for {seed_domain}")
        return companies
    
    # Step 4: Format the data
    # Each item from Ocean.io has a nested "company" object inside it
    formatted_companies = []
    for item in companies:
        company = item.get("company", {})  # drill into nested object
        domain = company.get("domain") or company.get("website")
        
        if domain:
            formatted_companies.append({
                "domain": domain,
                "name": company.get("name", "Unknown"),
                "industry": company.get("industries", ["Unknown"])[0] if company.get("industries") else "Unknown",
                "country": company.get("primaryCountry", "Unknown"),
                "employees": company.get("companySize", "Unknown"),
                "linkedin": company.get("medias", {}).get("linkedin", {}).get("url", "")
            })

            
    # Step 5: Remove duplicates
    unique_domains = set()
    deduplicated = []
    for company in formatted_companies:
        if company["domain"] not in unique_domains:
            unique_domains.add(company["domain"])
            deduplicated.append(company)
    
    # Step 6: Save to data/domains.json
    success = save_json_file("data/domains.json", deduplicated)
    
    if not success:
        print(f"✗ Failed to save domains to data/domains.json")
        return None
    
    # Step 7: Print summary
    print(f"\n✓ Found {len(deduplicated)} lookalike companies")
    print(f"✓ Saved to data/domains.json")
    print_stage_summary(
        1,
        f"Found {len(deduplicated)} lookalike domains. Saved data/domains.json for the next stage."
    )
    
    return deduplicated