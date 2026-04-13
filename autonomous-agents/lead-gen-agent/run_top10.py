"""Run lead gen agent for top 10 most profitable niches in Dubai."""

import asyncio
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AGENT_DIR = Path(__file__).parent
REPO_ROOT = AGENT_DIR.parent.parent
GOOGLE_MAPS = REPO_ROOT / "mcp-servers" / "google-maps"
sys.path.insert(0, str(GOOGLE_MAPS))

from agent import run_job, save_results, generate_summary
from models import Business

TOP_10_NICHES = [
    {"niche": "real estate agency", "city": "Dubai", "max": 30},
    {"niche": "luxury car dealership", "city": "Dubai", "max": 25},
    {"niche": "immigration consultant", "city": "Dubai", "max": 25},
    {"niche": "business setup company", "city": "Dubai", "max": 25},
    {"niche": "cosmetic clinic", "city": "Dubai", "max": 25},
    {"niche": "interior design company", "city": "Dubai", "max": 25},
    {"niche": "private school", "city": "Dubai", "max": 20},
    {"niche": "wedding planner", "city": "Dubai", "max": 20},
    {"niche": "insurance broker", "city": "Dubai", "max": 25},
    {"niche": "commercial cleaning company", "city": "Dubai", "max": 20},
]


async def main():
    all_results = {}

    for i, job in enumerate(TOP_10_NICHES):
        niche = job["niche"]
        city = job["city"]
        max_results = job["max"]

        print(f"\n{'='*60}")
        print(f"[{i+1}/10] {niche} in {city}")
        print(f"{'='*60}")

        try:
            leads = await run_job(
                niche=niche,
                city=city,
                max_results=max_results,
                min_rating=0,
                enrich=True,
            )
            key = f"{niche}_{city}".replace(" ", "_").lower()
            all_results[key] = leads
        except Exception as e:
            print(f"  FAILED: {e}")

        # Delay between jobs
        if i < len(TOP_10_NICHES) - 1:
            print("  Waiting 10s before next niche...")
            await asyncio.sleep(10)

    # Save all results
    saved = save_results(all_results, "csv")
    summary = generate_summary(all_results)
    print(f"\n\n{summary}")
    print(f"\nFiles saved:")
    for f in saved:
        print(f"  {f}")


if __name__ == "__main__":
    asyncio.run(main())
