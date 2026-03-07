"""
BlackHole Lead Finder - Research and qualify potential clients.

Provides research frameworks and target lists for UAE market.
"""

import sys
from datetime import datetime

# High-value industries in UAE with digital service needs
UAE_INDUSTRIES = {
    "real-estate": {
        "name": "Real Estate",
        "avg_deal": "$3,000-10,000",
        "pain_points": [
            "Manual property listing updates across platforms",
            "Poor website UX losing leads",
            "No CRM or lead tracking",
            "Social media inconsistency",
            "No virtual tour capability",
        ],
        "services_to_pitch": [
            "AI-powered property matching chatbot",
            "Automated listing syndication",
            "Lead capture and CRM setup",
            "Website redesign with IDX integration",
            "Social media automation",
        ],
        "where_to_find": [
            "Bayut.com / PropertyFinder - look for agencies with poor listings",
            "Google Maps: 'real estate agency Dubai/Abu Dhabi'",
            "LinkedIn: 'real estate manager Dubai'",
            "DLD (Dubai Land Department) registered brokers list",
        ],
    },
    "ecommerce": {
        "name": "E-Commerce",
        "avg_deal": "$2,000-8,000",
        "pain_points": [
            "Low conversion rates",
            "Manual order processing",
            "Poor SEO and organic traffic",
            "No email marketing automation",
            "Inventory management chaos",
        ],
        "services_to_pitch": [
            "Shopify/WooCommerce optimization",
            "AI product descriptions at scale",
            "Email marketing automation (abandoned cart, etc.)",
            "SEO audit and implementation",
            "Inventory automation and alerts",
        ],
        "where_to_find": [
            "Noon.com / Amazon.ae - find brands selling there",
            "Instagram: UAE-based e-commerce brands",
            "Google: 'buy [product] UAE' - find local stores",
            "LinkedIn: 'e-commerce manager UAE'",
        ],
    },
    "restaurants": {
        "name": "Restaurants & F&B",
        "avg_deal": "$1,000-5,000",
        "pain_points": [
            "Expensive delivery platform commissions (Talabat, Deliveroo)",
            "No direct ordering system",
            "Manual reservation management",
            "Inconsistent social media",
            "No customer loyalty system",
        ],
        "services_to_pitch": [
            "WhatsApp ordering bot (saves 15-30% on delivery commissions)",
            "Direct ordering website",
            "Reservation automation",
            "Social media content + scheduling",
            "Customer loyalty app/system",
        ],
        "where_to_find": [
            "Google Maps: restaurants in Business Bay, DIFC, JBR, Marina",
            "Zomato/TripAdvisor: restaurants with bad websites",
            "Instagram: restaurants with good food but poor online presence",
            "LinkedIn: 'restaurant owner Dubai'",
        ],
    },
    "healthcare": {
        "name": "Healthcare & Clinics",
        "avg_deal": "$3,000-15,000",
        "pain_points": [
            "Manual appointment booking",
            "No online presence or poor website",
            "Patient communication is fragmented",
            "No review management",
            "Paper-based processes",
        ],
        "services_to_pitch": [
            "Online booking system",
            "Patient portal / CRM",
            "WhatsApp appointment reminders",
            "Website with SEO for medical terms",
            "Review management automation",
        ],
        "where_to_find": [
            "Google Maps: clinics in Dubai/Abu Dhabi",
            "DHA (Dubai Health Authority) licensed clinics list",
            "LinkedIn: 'clinic manager Dubai'",
            "Google: '[specialty] clinic Dubai' - check websites",
        ],
    },
    "consulting": {
        "name": "Consulting & Professional Services",
        "avg_deal": "$2,000-10,000",
        "pain_points": [
            "Manual report generation",
            "No client portal",
            "Time-consuming proposal creation",
            "Poor lead generation",
            "No thought leadership content",
        ],
        "services_to_pitch": [
            "AI-powered report generation",
            "Client portal development",
            "Automated proposal system",
            "LinkedIn content strategy + ghostwriting",
            "Lead generation automation",
        ],
        "where_to_find": [
            "LinkedIn: consultants and firms in UAE",
            "DMCC / DIFC company directories",
            "Google: 'consulting firm Dubai'",
            "Networking events (virtual and in-person)",
        ],
    },
    "fitness": {
        "name": "Fitness & Wellness",
        "avg_deal": "$1,000-4,000",
        "pain_points": [
            "Manual class scheduling",
            "Member management in spreadsheets",
            "No automated billing",
            "Social media is time-consuming",
            "No member app or portal",
        ],
        "services_to_pitch": [
            "Booking and scheduling system",
            "Member management portal",
            "Automated billing and renewals",
            "Social media content automation",
            "WhatsApp class reminders and engagement",
        ],
        "where_to_find": [
            "Google Maps: gyms, yoga studios, fitness centers in UAE",
            "Instagram: fitness brands in Dubai",
            "ClassPass: studios listed there",
            "LinkedIn: 'gym owner Dubai'",
        ],
    },
}

def find_leads(args):
    if not args:
        print("Usage: python run.py leads find <industry> [location]")
        print(f"\n  Available industries:")
        for key, val in UAE_INDUSTRIES.items():
            print(f"    {key:<15} - {val['name']} (avg deal: {val['avg_deal']})")
        print(f"\n    all            - Show all industries")
        return

    industry = args[0].lower()
    location = args[1] if len(args) > 1 else "Dubai"

    if industry == "all":
        for key in UAE_INDUSTRIES:
            show_industry(key, location)
        return

    if industry not in UAE_INDUSTRIES:
        print(f"  Industry '{industry}' not found. Available: {', '.join(UAE_INDUSTRIES.keys())}")
        return

    show_industry(industry, location)

def show_industry(industry_key, location):
    ind = UAE_INDUSTRIES[industry_key]
    print(f"\n  ================================================")
    print(f"  {ind['name'].upper()} in {location}")
    print(f"  Average Deal Size: {ind['avg_deal']}")
    print(f"  ================================================")

    print(f"\n  PAIN POINTS (use these in your outreach):")
    for i, p in enumerate(ind['pain_points'], 1):
        print(f"    {i}. {p}")

    print(f"\n  SERVICES TO PITCH:")
    for i, s in enumerate(ind['services_to_pitch'], 1):
        print(f"    {i}. {s}")

    print(f"\n  WHERE TO FIND LEADS:")
    for i, w in enumerate(ind['where_to_find'], 1):
        print(f"    {i}. {w}")

    print(f"\n  RESEARCH STEPS:")
    print(f"    1. Search Google Maps: '{ind['name'].lower()} {location}'")
    print(f"    2. Visit their websites - note issues (slow, outdated, no mobile)")
    print(f"    3. Check their social media - note inconsistency or low quality")
    print(f"    4. Find the owner/manager on LinkedIn")
    print(f"    5. Add to CRM: python run.py crm add \"CompanyName\" \"Contact\" \"email\" \"{industry_key}\" [deal_value]")
    print(f"    6. Generate outreach: python run.py outreach cold-email \"CompanyName\" \"{ind['pain_points'][0]}\"")

def qualify_lead():
    """Framework for qualifying a lead."""
    print("""
  === LEAD QUALIFICATION FRAMEWORK ===

  Score each criteria 1-5, total 20+ = high priority:

  BUDGET (1-5):
    1 = Unknown/startup, 5 = Established business with clear budget

  AUTHORITY (1-5):
    1 = Junior contact, 5 = Decision maker (owner, CEO, director)

  NEED (1-5):
    1 = Nice to have, 5 = Urgent problem costing them money daily

  TIMELINE (1-5):
    1 = "Someday", 5 = "Need it yesterday"

  SCORE ACTIONS:
    20-25: DROP EVERYTHING. This is a hot lead. Respond within 1 hour.
    15-19: Strong lead. Follow up within 24 hours.
    10-14: Nurture. Add to content funnel, follow up weekly.
    5-9:   Low priority. Add to newsletter, revisit in 30 days.
    """)

def main(args):
    if not args:
        print("Usage: python run.py leads <find|qualify> [args]")
        return

    cmd = args[0].lower()
    if cmd == "find":
        find_leads(args[1:])
    elif cmd == "qualify":
        qualify_lead()
    else:
        print(f"  Unknown leads command: {cmd}")
