import argparse
import os
from dotenv import load_dotenv

from stages.stage1_lookalikes import run_stage1
from stages.stage2_prospects import run_stage2
from stages.stage3_emails import run_stage3
from stages.stage4_send import run_stage4

load_dotenv()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the automated cold outreach pipeline for a seed domain."
    )
    parser.add_argument("seed_domain", type=str)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-stage2", action="store_true",
                        help="Skip Stage 2 and use existing data/prospects.json")
    parser.add_argument("--max-domains", type=int, default=3,
                        help="Limit number of domains to process (default: 3)")
    parser.add_argument("--max-prospects", type=int, default=3,
                        help="Limit number of prospects to consider (default: 3)")
    parser.add_argument("--max-emails", type=int, default=3,
                        help="Limit number of emails to resolve/send (default: 3)")
    return parser.parse_args()


def confirm_send() -> bool:
    answer = input("Send emails? (y/n): ").strip().lower()
    return answer == "y"


def main():
    args = parse_arguments()
    seed_domain = args.seed_domain
    dry_run = args.dry_run

    print(f"\nStarting outreach pipeline for: {seed_domain}")
    print(f"Dry run: {'enabled' if dry_run else 'disabled'}")
    domains = run_stage1(seed_domain)
    if domains is None:
        print("✗ Pipeline stopped: Stage 1 failed.")
        return
    
    
    if args.max_domains and isinstance(domains, list):
        domains = domains[: args.max_domains]
    if args.skip_stage2:
        print("\n[Stage 2] Skipping — using existing data/prospects.json")
        from utils.helpers import load_json_file
        prospects = load_json_file("data/prospects.json")
    else:
        prospects = run_stage2(domains)
        if prospects is None:
            print("✗ Pipeline stopped: Stage 2 failed.")
            return
    
    if args.max_prospects and isinstance(prospects, list):
        prospects = prospects[: args.max_prospects]
    enriched_emails = run_stage3(prospects)
    if enriched_emails is None:
        print("✗ Pipeline stopped: Stage 3 failed.")
        return
    
    if args.max_emails and isinstance(enriched_emails, list):
        from utils.helpers import save_json_file
        enriched_emails = enriched_emails[: args.max_emails]
        save_json_file("data/emails.json", enriched_emails)

    print(f"\nPipeline complete. {len(domains)} domains, {len(prospects)} prospects, {len(enriched_emails)} enriched email records.")

    if dry_run:
        print("\nDry run mode activated. Emails will not be sent.")
        run_stage4(send_now=False)
        return

    if confirm_send():
        run_stage4(send_now=True)
    else:
        print("\nNo emails were sent.")
        run_stage4(send_now=False)


if __name__ == "__main__":
    main()
    