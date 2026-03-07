"""
BlackHole Proposal Generator - Create professional HTML proposals.

Generates client-ready proposals that can be opened in a browser and printed to PDF.
"""

import os
import sys
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "proposals")

def create_proposal(args):
    if len(args) < 2:
        print("Usage: python run.py proposal create <client_name> <project_title> [--value AMOUNT] [--timeline DAYS]")
        return

    client = args[0]
    project = args[1]
    value = 5000
    timeline = 14

    i = 2
    while i < len(args):
        if args[i] == "--value" and i + 1 < len(args):
            value = float(args[i + 1])
            i += 2
        elif args[i] == "--timeline" and i + 1 < len(args):
            timeline = int(args[i + 1])
            i += 2
        else:
            i += 1

    # Calculate tiers
    basic = value * 0.6
    standard = value
    premium = value * 1.6

    start_date = datetime.now().strftime("%B %d, %Y")
    end_date = (datetime.now() + timedelta(days=timeline)).strftime("%B %d, %Y")
    valid_until = (datetime.now() + timedelta(days=14)).strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Proposal - {project} | {client}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1a1a2e; line-height: 1.6; background: #fff; }}
    .page {{ max-width: 800px; margin: 0 auto; padding: 60px 40px; }}
    .header {{ border-bottom: 3px solid #0f3460; padding-bottom: 30px; margin-bottom: 40px; }}
    .header h1 {{ font-size: 32px; color: #0f3460; margin-bottom: 5px; }}
    .header .subtitle {{ font-size: 16px; color: #666; }}
    .meta {{ display: flex; justify-content: space-between; margin-top: 20px; font-size: 14px; color: #444; }}
    .section {{ margin-bottom: 35px; }}
    .section h2 {{ font-size: 20px; color: #0f3460; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 1px solid #e0e0e0; }}
    .section p, .section li {{ font-size: 15px; margin-bottom: 8px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
    .pricing {{ display: flex; gap: 20px; margin-top: 20px; }}
    .tier {{ flex: 1; border: 2px solid #e0e0e0; border-radius: 10px; padding: 25px; text-align: center; }}
    .tier.recommended {{ border-color: #0f3460; background: #f8f9ff; }}
    .tier.recommended .badge {{ background: #0f3460; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: inline-block; margin-bottom: 10px; }}
    .tier h3 {{ font-size: 18px; margin-bottom: 10px; color: #0f3460; }}
    .tier .price {{ font-size: 28px; font-weight: bold; color: #0f3460; margin: 10px 0; }}
    .tier ul {{ text-align: left; font-size: 13px; list-style: none; padding: 0; }}
    .tier li {{ padding: 4px 0; padding-left: 20px; position: relative; }}
    .tier li:before {{ content: "\\2713"; position: absolute; left: 0; color: #0f3460; }}
    .timeline {{ background: #f8f9ff; border-radius: 10px; padding: 25px; }}
    .timeline-item {{ display: flex; gap: 15px; margin-bottom: 15px; }}
    .timeline-dot {{ width: 12px; height: 12px; border-radius: 50%; background: #0f3460; margin-top: 5px; flex-shrink: 0; }}
    .cta {{ background: #0f3460; color: white; text-align: center; padding: 30px; border-radius: 10px; margin-top: 40px; }}
    .cta h2 {{ color: white; border: none; margin-bottom: 10px; }}
    .cta p {{ color: #ccc; font-size: 15px; }}
    .footer {{ margin-top: 40px; text-align: center; font-size: 13px; color: #999; padding-top: 20px; border-top: 1px solid #eee; }}
    @media print {{ .page {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="page">
    <div class="header">
        <h1>{project}</h1>
        <div class="subtitle">Proposal prepared for {client}</div>
        <div class="meta">
            <span>Prepared by: [Your Name]</span>
            <span>Date: {start_date}</span>
            <span>Valid until: {valid_until}</span>
        </div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>
            This proposal outlines the approach, timeline, and investment for {project}
            for {client}. The goal is to [DESCRIBE THE CORE OUTCOME - e.g., "build a
            modern web application that automates your client onboarding process,
            reducing manual work by 80% and improving client satisfaction"].
        </p>
    </div>

    <div class="section">
        <h2>The Challenge</h2>
        <p>[Describe the client's current situation and pain points:]</p>
        <ul>
            <li>[Pain point 1 - e.g., "Manual processes consuming 20+ hours/week"]</li>
            <li>[Pain point 2 - e.g., "Inconsistent client experience"]</li>
            <li>[Pain point 3 - e.g., "No visibility into pipeline metrics"]</li>
        </ul>
    </div>

    <div class="section">
        <h2>The Solution</h2>
        <p>[Describe your proposed solution:]</p>
        <ul>
            <li>[Deliverable 1 - e.g., "Custom web application with client portal"]</li>
            <li>[Deliverable 2 - e.g., "Automated email sequences and notifications"]</li>
            <li>[Deliverable 3 - e.g., "Analytics dashboard with real-time metrics"]</li>
            <li>[Deliverable 4 - e.g., "Documentation and training session"]</li>
        </ul>
    </div>

    <div class="section">
        <h2>Investment</h2>
        <div class="pricing">
            <div class="tier">
                <h3>Starter</h3>
                <div class="price">${basic:,.0f}</div>
                <ul>
                    <li>Core functionality</li>
                    <li>Basic design</li>
                    <li>1 round of revisions</li>
                    <li>Basic documentation</li>
                    <li>7 days support</li>
                </ul>
            </div>
            <div class="tier recommended">
                <span class="badge">RECOMMENDED</span>
                <h3>Professional</h3>
                <div class="price">${standard:,.0f}</div>
                <ul>
                    <li>Full functionality</li>
                    <li>Custom design</li>
                    <li>3 rounds of revisions</li>
                    <li>Full documentation</li>
                    <li>30 days support</li>
                    <li>Performance optimization</li>
                </ul>
            </div>
            <div class="tier">
                <h3>Premium</h3>
                <div class="price">${premium:,.0f}</div>
                <ul>
                    <li>Everything in Professional</li>
                    <li>Priority development</li>
                    <li>Unlimited revisions</li>
                    <li>90 days support</li>
                    <li>Training session</li>
                    <li>Monthly maintenance</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Timeline</h2>
        <div class="timeline">
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div>
                    <strong>Phase 1: Discovery & Planning (Day 1-2)</strong><br>
                    Requirements finalization, wireframes, technical architecture
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div>
                    <strong>Phase 2: Development (Day 3-{timeline - 5})</strong><br>
                    Core build, integrations, iterative progress updates
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div>
                    <strong>Phase 3: Review & Refinement (Day {timeline - 4}-{timeline - 2})</strong><br>
                    Client review, revisions, testing
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div>
                    <strong>Phase 4: Launch & Handoff (Day {timeline - 1}-{timeline})</strong><br>
                    Deployment, documentation, training
                </div>
            </div>
        </div>
        <p style="margin-top: 15px; font-size: 14px; color: #666;">
            Estimated start: {start_date} &mdash; Estimated delivery: {end_date}
        </p>
    </div>

    <div class="section">
        <h2>Why Me</h2>
        <ul>
            <li><strong>AI-Accelerated Delivery:</strong> I use AI tools to deliver 3-5x faster than traditional timelines without compromising quality</li>
            <li><strong>UAE-Based:</strong> Local availability, understand the market, available across Asia/Middle East/Europe timezones</li>
            <li><strong>Full Transparency:</strong> Daily progress updates, no surprises</li>
            <li><strong>Results-Focused:</strong> I measure success by your business outcomes, not hours worked</li>
        </ul>
    </div>

    <div class="section">
        <h2>Payment Terms</h2>
        <ul>
            <li>50% upfront to begin work</li>
            <li>50% upon delivery and approval</li>
            <li>Payment via bank transfer (Wise) or Stripe</li>
        </ul>
    </div>

    <div class="cta">
        <h2>Ready to Get Started?</h2>
        <p>Reply to this proposal or book a call at [your Calendly link]</p>
        <p style="margin-top: 10px; font-size: 13px;">This proposal is valid until {valid_until}</p>
    </div>

    <div class="footer">
        <p>[Your Name] &bull; [your@email.com] &bull; [your phone] &bull; [your website]</p>
    </div>
</div>
</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = client.replace(" ", "_").lower()
    filename = f"proposal_{safe_name}_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  Proposal generated: {filepath}")
    print(f"  Open in browser to view/print to PDF.")
    print(f"\n  Pricing tiers:")
    print(f"    Starter:      ${basic:,.0f}")
    print(f"    Professional: ${standard:,.0f} (recommended)")
    print(f"    Premium:      ${premium:,.0f}")
    print(f"\n  Remember to customize:")
    print(f"    - Executive summary")
    print(f"    - Challenge & solution sections")
    print(f"    - Your name and contact details")

def main(args):
    if not args:
        print("Usage: python run.py proposal create <client> <project> [--value AMOUNT] [--timeline DAYS]")
        return

    cmd = args[0].lower()
    if cmd == "create":
        create_proposal(args[1:])
    else:
        print(f"  Unknown proposal command: {cmd}")
