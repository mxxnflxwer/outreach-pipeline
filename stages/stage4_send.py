import os
import requests
from typing import List, Dict, Optional
from utils.helpers import (
    load_json_file,
    print_stage_summary
)

def send_email_via_brevo(email_data: Dict) -> bool:
    """
    Sends a single personalized email through Brevo.
    """
    brevo_api_key = os.getenv("BREVO_API_KEY")
    if not brevo_api_key or brevo_api_key == "your_key_here":
        print("✗ Brevo API key not configured. Please set BREVO_API_KEY in .env")
        return False

    sender_name = os.getenv("SENDER_NAME", "Mathi")
    sender_email = os.getenv("SENDER_EMAIL", "mathi@flowreach.xyz")

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": brevo_api_key,
        "Content-Type": "application/json"
    }

    # Personalized subject line using their name and company
    subject = f"Quick intro — FlowReach x {email_data.get('company_name', 'your company')}"

    # Personalized email body
    html_content = f"""
    <p>Hi {email_data.get('name', 'there')},</p>

    <p>I came across {email_data.get('company_name', 'your company')} and was genuinely impressed 
    by what you're building. I'm reaching out because I think there's a real opportunity 
    for us to work together.</p>

    <p>At FlowReach, we help companies like yours streamline their outreach and grow faster. 
    I'd love to show you how we've helped similar teams in your space.</p>

    <p>Would you be open to a quick 15-minute call this week?</p>

    <p>Best,<br>
    {sender_name}<br>
    FlowReach<br>
    {sender_email}</p>
    """

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": email_data["email"],
                "name": email_data.get("name", "")
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code >= 200 and response.status_code < 300:
        print(f"✓ Email sent to {email_data['email']}")
        return True

    print(f"✗ Brevo send failed for {email_data['email']}: {response.status_code} {response.text}")
    return False


def run_stage4(send_now: bool = False) -> Optional[List[Dict]]:
    """
    Main entry point for Stage 4. Shows final enriched list and optionally sends emails.
    """
    print(f"\n{'='*60}")
    print(f"[Stage 4] Final Review and Send")
    print(f"{'='*60}")

    records = load_json_file("data/emails.json")
    if records is None:
        print("✗ No email records available for Stage 4. Run Stage 3 first or provide data/emails.json.")
        return None

    if len(records) == 0:
        print("⚠ No records found in data/emails.json. Nothing to send.")
        return []

    # Print final enriched list
    print(f"\nFinal enriched list ({len(records)} records):")
    print("Name | Company | Email | LinkedIn")
    print("-" * 80)
    for record in records:
        name = record.get("name", "Unknown")
        company = record.get("company_name", record.get("company_domain", "Unknown"))
        email = record.get("email", "No email")
        linkedin = record.get("linkedin_url", "No LinkedIn")
        print(f"{name} | {company} | {email} | {linkedin}")

    print_stage_summary(4, f"Loaded {len(records)} records from data/emails.json.")

    if not send_now:
        print("\nDry run mode: no emails were sent.")
        return records

    print("\nReady to send emails through Brevo.")
    send_count = 0
    failed_count = 0

    for record in records:
        email = record.get("email")
        if not email:
            failed_count += 1
            continue

        email_data = {
            "email": email,
            "name": record.get("name", ""),
            "company_name": record.get("company_name", ""),
            "title": record.get("title", "")
        }

        success = send_email_via_brevo(email_data)
        if success:
            send_count += 1
        else:
            failed_count += 1

    print(f"\n✓ Emails sent: {send_count}")
    print(f"✗ Emails failed: {failed_count}")
    return records