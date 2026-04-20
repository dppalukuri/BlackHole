"""LinkedIn job-posting fulfillment script.

Sellable product: "Niche job-market snapshot — 200 live LinkedIn postings — $39"
Buyers: recruiters, career coaches, indie founders doing salary research,
        ATS vendors needing live job-market data for demos.

We ship the public-jobs path only (no login required). Profile/people search
needs authenticated sessions and is deliberately out-of-scope here.

CLI:
    python linkedin_jobs.py --query "ML engineer" --location "Remote" --count 100
    python linkedin_jobs.py --query "product manager" --location "Dubai" \
        --remote "On-site" --experience "Mid-Senior level" --count 50

Output: orders/order-<timestamp>-linkedin-jobs-<slug>.zip
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from common import OrderContext, mcp_path, print_done

sys.path.insert(0, str(mcp_path("linkedin")))

from scraper import LinkedInScraper  # noqa: E402


CSV_COLUMNS = [
    "title", "company", "location", "remote", "employment_type", "seniority",
    "posted_date", "applicants", "salary",
    "description", "job_url", "job_id", "company_logo",
]


async def fulfill(
    query: str, location: str, remote: str, job_type: str,
    experience: str, count: int,
) -> list[dict]:
    scraper = LinkedInScraper()
    try:
        result = await scraper.search_jobs(
            query=query, location=location, remote=remote,
            job_type=job_type, experience=experience,
            max_results=count, headed=False,
        )
        jobs = getattr(result, "results", [])
        return [j.to_dict() for j in jobs]
    finally:
        try:
            await scraper.cleanup()  # type: ignore[attr-defined]
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="LinkedIn jobs fulfillment")
    ap.add_argument("--query", required=True, help='Job keywords (e.g. "ML engineer")')
    ap.add_argument("--location", default="", help='City/region or "Remote"')
    ap.add_argument("--remote", default="", choices=["", "Remote", "On-site", "Hybrid"])
    ap.add_argument("--job-type", default="", choices=["", "Full-time", "Part-time", "Contract", "Internship"])
    ap.add_argument("--experience", default="", help='"Entry level", "Associate", "Mid-Senior level", "Director", "Executive"')
    ap.add_argument("--count", type=int, default=100, help="Max job postings (default 100)")
    args = ap.parse_args()

    order = OrderContext(
        product="linkedin-jobs",
        order_label=f"{args.query}-{args.location or 'anywhere'}-{args.count}",
        params={
            "query": args.query, "location": args.location or "(any)",
            "remote": args.remote or "(any)", "job_type": args.job_type or "(any)",
            "experience": args.experience or "(any)", "count": args.count,
        },
    )

    print(f"[start] {order.order_id}")
    print(f"        searching LinkedIn jobs for '{args.query}' in '{args.location or 'anywhere'}'...")

    rows = asyncio.run(fulfill(
        query=args.query, location=args.location, remote=args.remote,
        job_type=args.job_type, experience=args.experience, count=args.count,
    ))

    order.write_csv(rows, columns=CSV_COLUMNS)

    total = len(rows)
    by_company = {}
    by_seniority = {}
    by_type = {}
    for r in rows:
        c = r.get("company", "?")
        by_company[c] = by_company.get(c, 0) + 1
        s = r.get("seniority", "?")
        by_seniority[s] = by_seniority.get(s, 0) + 1
        t = r.get("employment_type", "?")
        by_type[t] = by_type.get(t, 0) + 1

    top_companies = sorted(by_company.items(), key=lambda x: -x[1])[:10]
    summary = (
        f"Query:         {args.query}\n"
        f"Location:      {args.location or '(any)'}\n"
        f"Postings:      {total}\n"
        f"Unique cos:    {len(by_company)}\n\n"
        "Top 10 hiring companies:\n"
        + "\n".join(f"  {i+1:2d}. {c} ({n})" for i, (c, n) in enumerate(top_companies))
        + "\n\n"
        f"By employment type: {', '.join(f'{k}={v}' for k, v in by_type.items() if k != '?')}\n"
        f"By seniority:       {', '.join(f'{k}={v}' for k, v in by_seniority.items() if k != '?')}\n\n"
        "Use this for: market-rate salary research, recruiter lead generation,\n"
        "hiring-trend reports, ATS/job-board competitive analysis."
    )

    disclaimers = [
        "Data scraped from public LinkedIn job pages — no login used.",
        "Job postings are live at delivery time; LinkedIn removes closed roles within days.",
        "LinkedIn's Terms of Service restrict bulk scraping for commercial use — confirm you have a lawful basis for your use-case.",
        "Some fields (salary, applicants) are only published by ~30-40% of posters; empty = not disclosed, not missing.",
    ]

    order.write_readme(
        product_title=f"LinkedIn Job-Market Snapshot — '{args.query}'",
        summary=summary, disclaimers=disclaimers,
    )
    zip_path = order.finalize()
    print_done(order, zip_path)


if __name__ == "__main__":
    main()
