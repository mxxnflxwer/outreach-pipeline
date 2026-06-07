import json
import os
import time
from typing import Any, Dict, Callable, Optional

def get_cache_path(cache_type: str, identifier: str) -> str:
    """
    Generates the file path for a cached item.
    
    Args:
        cache_type: Type of cache ('lookalikes', 'prospects', 'emails')
        identifier: Unique identifier (domain or LinkedIn URL, sanitized for filename)
    
    Returns:
        Full file path to the cache file
    """
    safe_identifier = identifier.replace('.', '_').replace('/', '_').replace(':', '_').replace('?', '_')

    cache_dir = f"cache/{cache_type}"
    cache_file = f"{cache_dir}/{safe_identifier}.json"

    return cache_file


def load_from_cache(cache_type: str, identifier: str) -> Optional[Dict]:
    """
    Attempts to load data from cache before making an API call.
    
    Args:
        cache_type: Type of cache ('lookalikes', 'prospects', 'emails')
        identifier: Unique identifier (domain or LinkedIn URL)
    
    Returns:
        Dictionary of cached data if exists, otherwise None
    """
    cache_file = get_cache_path(cache_type, identifier)
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✓ Cache hit: {identifier}")
                return data
        except Exception as e:
            # If there's any error reading the cache, just skip it and fetch fresh
            print(f"⚠ Error reading cache for {identifier}: {e}")
            return None
    
    return None


def save_to_cache(cache_type: str, identifier: str, data: Dict) -> None:
    """
    Saves data to cache for future use.
    
    Args:
        cache_type: Type of cache ('lookalikes', 'prospects', 'emails')
        identifier: Unique identifier (domain or LinkedIn URL)
        data: Dictionary of data to cache
    """
    cache_file = get_cache_path(cache_type, identifier)
    cache_dir = os.path.dirname(cache_file)
    
    os.makedirs(cache_dir, exist_ok=True)
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Cached: {identifier}")
    except Exception as e:
        print(f"⚠ Error saving cache for {identifier}: {e}")


def retry_with_backoff(
    api_call: Callable,
    max_retries: int = 3,
    initial_wait: int = 1
) -> Optional[Any]:
    """Retries an API call up to max_retries times with exponential backoff."""
    wait_time = initial_wait
    
    for attempt in range(max_retries):
        try:
            result = api_call()
            return result
        
        except Exception as e:
            # If this is the last attempt, print error and give up
            if attempt == max_retries - 1:
                print(f"✗ Failed after {max_retries} attempts: {str(e)}")
                return None
            
            print(f"⚠ Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            wait_time *= 2  # Double the wait time for next retry (exponential backoff)
    
    return None




def load_json_file(filepath: str) -> Optional[list]:
    """Loads a JSON file from disk."""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Error loading {filepath}: {e}")
        return None


def save_json_file(filepath: str, data: Any) -> bool:
    """
    Saves data to a JSON file on disk.
    
    Args:
        filepath: Path where the JSON file should be saved
        data: Data to save (will be converted to JSON)
    
    Returns:
        True if successful, False if an error occurred
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"⚠ Error saving {filepath}: {e}")
        return False




def print_stage_header(stage_number: int, title: str) -> None:
    """Prints a formatted stage header to make output easier to read."""
    print(f"\n{'='*60}")
    print(f"[Stage {stage_number}] {title}")
    print(f"{'='*60}")


def print_stage_summary(stage_number: int, message: str) -> None:
    """Prints a summary message after a stage completes."""
    print(f"\n[Stage {stage_number} Summary] {message}")
