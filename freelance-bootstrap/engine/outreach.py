"""
BlackHole Outreach Engine - Generate personalized outreach messages.

Supports: Upwork proposals, LinkedIn messages, cold emails, follow-ups.
"""

import json
import os
import sys
from datetime import datetime

TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "emails.json")

def load_templates():
    if os.path.exists(TEMPLATES_PATH):
        with open(TEMPLATES_PATH, "r") as f:
            return json.load(f)
    return {}

def generate_upwork(args):
    if not args:
        print("Usage: python run.py outreach upwork <paste the job description>")
        return

    job_desc = " ".join(args)
    templates = load_templates()

    print("\n  === UPWORK PROPOSAL GENERATOR ===\n")
    print("  Analyzing job description...\n")

    # Extract key details to personalize
    print("  STEP 1: Copy this framework and personalize:\n")
    print("  -------------------------------------------")
    print(f"""
  Hi [Client Name],

  I just read through your project brief and [SPECIFIC DETAIL FROM JOB - mention
  something that shows you actually read it, not a generic opener].

  This is exactly the type of work I specialize in. Here's how I'd approach it:

  1. [FIRST STEP - something specific to their project]
  2. [SECOND STEP - the core delivery]
  3. [THIRD STEP - polish/testing/handoff]

  I can have a working first version ready within [X] hours of starting.

  A few relevant things about my approach:
  - I use AI-assisted development which means I deliver 3-5x faster than typical timelines
  - I'm based in the UAE so I'm available across Asia, Middle East, and Europe hours
  - I focus on clean, maintainable code with documentation

  Happy to jump on a quick call or start with a small paid trial if you'd like to
  test the fit. What works best for you?

  Best,
  [Your Name]
  """)
    print("  -------------------------------------------")
    print("\n  STEP 2: Customize these based on the job:\n")

    keywords = job_desc.lower()
    if any(w in keywords for w in ["website", "web", "frontend", "landing page", "wordpress", "shopify"]):
        print("  DETECTED: Web Development Project")
        print("  - Mention specific tech stack (React, Next.js, WordPress, etc.)")
        print("  - Offer to show similar past work")
        print("  - Include estimated timeline (usually 3-7 days)")
        print("  - Price range: $1,000-5,000 depending on complexity")

    if any(w in keywords for w in ["automat", "workflow", "zapier", "integration", "api"]):
        print("  DETECTED: Automation Project")
        print("  - Ask what tools they currently use")
        print("  - Mention specific integrations you can build")
        print("  - Emphasize ROI (hours saved, errors reduced)")
        print("  - Price range: $1,500-8,000")

    if any(w in keywords for w in ["ai", "chatbot", "gpt", "machine learning", "nlp"]):
        print("  DETECTED: AI Project")
        print("  - Mention specific AI APIs (OpenAI, Claude, etc.)")
        print("  - Show understanding of their use case")
        print("  - Offer a small demo/prototype")
        print("  - Price range: $2,000-10,000")

    if any(w in keywords for w in ["data", "scraping", "analysis", "dashboard", "report"]):
        print("  DETECTED: Data Project")
        print("  - Mention tools (Python, pandas, Beautiful Soup, etc.)")
        print("  - Ask about data sources and expected output format")
        print("  - Offer sample output")
        print("  - Price range: $500-3,000")

    if any(w in keywords for w in ["content", "writing", "blog", "copywriting", "seo"]):
        print("  DETECTED: Content Project")
        print("  - Mention SEO knowledge if relevant")
        print("  - Offer sample/outline before full delivery")
        print("  - Ask about target audience and tone")
        print("  - Price range: $200-1,000/piece")

    print("\n  TIPS:")
    print("  - Submit within 1 hour of job posting for 3x higher response rate")
    print("  - Keep proposal under 200 words (clients skim)")
    print("  - Always end with a question (drives response)")
    print("  - Attach a relevant portfolio piece if you have one")

def generate_linkedin(args):
    if len(args) < 3:
        print("Usage: python run.py outreach linkedin <name> <company> <role>")
        return

    name, company, role = args[0], args[1], args[2]

    print(f"\n  === LINKEDIN OUTREACH: {name} at {company} ===\n")

    print("  CONNECTION REQUEST (300 char limit):\n")
    print(f"""  Hi {name}, I noticed you're [doing something specific at {company}].
  I help {role}s in the UAE automate [relevant process] to save
  time and reduce costs. Would love to connect and share some ideas.
  """)

    print("\n  FOLLOW-UP MESSAGE (after they accept):\n")
    print(f"""  Thanks for connecting, {name}!

  I've been working with a few companies similar to {company} on
  [specific service - AI automation / web development / etc.].

  One thing I've noticed in the [industry] space is that most businesses
  are still [doing X manually / missing Y opportunity].

  I recently helped a client [specific result - e.g., "save 15 hours/week
  on data entry" or "increase their conversion rate by 40%"].

  Would it be useful if I shared how I did it? No pitch, just thought
  it might be relevant to what you're building at {company}.
  """)

    print("\n  SECOND FOLLOW-UP (if no response in 5 days):\n")
    print(f"""  Hi {name}, just wanted to follow up on my last message.

  I put together a quick [analysis / audit / breakdown] of how
  {company} could potentially [save time / increase revenue / automate X].

  Want me to send it over? Totally free, no strings attached.
  """)

    print("  TIPS:")
    print(f"  - Research {name}'s recent posts and reference them")
    print(f"  - Look at {company}'s website for specific pain points")
    print("  - Be genuinely helpful, not salesy")
    print("  - Voice messages get 3x higher response rate on LinkedIn")

def generate_cold_email(args):
    if len(args) < 2:
        print("Usage: python run.py outreach cold-email <company> <pain_point>")
        return

    company = args[0]
    pain_point = " ".join(args[1:])

    print(f"\n  === COLD EMAIL: {company} ===\n")

    print("  SUBJECT LINE OPTIONS:")
    print(f"  1. Quick question about {company}'s {pain_point}")
    print(f"  2. Idea for {company} (re: {pain_point})")
    print(f"  3. {company} + [your expertise] = ?")
    print(f"  4. Noticed something about {company}'s [website/process]")

    print(f"""
  ---

  OPTION A: The Value-First Email

  Subject: Quick idea for {company}

  Hi [Name],

  I was looking at {company}'s [website/operations/social media] and
  noticed [specific observation about their {pain_point}].

  I recently helped [similar company] solve a similar challenge by
  [brief solution description]. The result: [specific metric].

  I put together a quick [3-minute video / one-page doc / mockup]
  showing how this could work for {company}. Want me to send it over?

  Best,
  [Your Name]

  ---

  OPTION B: The Curious Email

  Subject: Question about {pain_point} at {company}

  Hi [Name],

  Quick question - how is {company} currently handling {pain_point}?

  I ask because I work with [similar companies] in the UAE and most
  are spending [X hours/week or $X/month] on this when it could be
  [automated / streamlined / eliminated].

  If this is on your radar, I'd love to share what's working for others
  in your space. If not, no worries at all.

  Cheers,
  [Your Name]

  ---

  OPTION C: The Results Email

  Subject: How [similar company] solved {pain_point}

  Hi [Name],

  [Similar company] had the exact same {pain_point} challenge that
  I noticed {company} might be facing.

  Here's what we did:
  - [Step 1]: [Result]
  - [Step 2]: [Result]
  - [Step 3]: [Result]

  Net result: [Big metric - hours saved, revenue gained, cost cut].

  Would something like this be useful for {company}? Happy to walk
  you through it in 15 minutes.

  Best,
  [Your Name]
  """)

    print("  SENDING TIPS:")
    print("  - Send Tuesday-Thursday, 9-11 AM recipient's timezone")
    print("  - Follow up after 3 days, then 7 days (max 3 follow-ups)")
    print("  - Personalize the first line - generic emails get deleted")
    print("  - Keep under 150 words. Shorter = higher response rate")

def generate_followup(args):
    if not args:
        print("Usage: python run.py outreach followup <crm_id>")
        return

    from engine.crm import get_db
    client_id = int(args[0])
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()

    if not client:
        print(f"  Client #{client_id} not found.")
        return

    status = client['status']
    company = client['company']
    contact = client['contact_name']

    print(f"\n  === FOLLOW-UP: {company} (Status: {status}) ===\n")

    if status == "lead":
        print(f"""  Initial outreach not yet sent. Use one of:
    python run.py outreach linkedin "{contact}" "{company}" "[role]"
    python run.py outreach cold-email "{company}" "[pain point]"
  """)
    elif status == "contacted":
        print(f"""  FOLLOW-UP MESSAGE:

  Hi {contact},

  Just circling back on my previous message. I know things get busy.

  I actually spent a few minutes looking deeper into {company}'s
  [website/operations], and I had a specific idea about how you could
  [specific improvement].

  Would a quick 10-minute call this week make sense? I promise to
  keep it focused and practical.

  Best,
  [Your Name]
  """)
    elif status == "proposal":
        print(f"""  PROPOSAL FOLLOW-UP:

  Hi {contact},

  Wanted to check in on the proposal I sent for {company}. I know
  these decisions take time, so no rush.

  A few clients asked me similar questions, so I wanted to clarify:
  - [Address a common objection: timeline, price, scope]
  - [Offer something extra: a small bonus deliverable]

  Is there anything I can clarify or adjust to make this a better fit?

  Best,
  [Your Name]
  """)
    elif status == "negotiation":
        print(f"""  NEGOTIATION FOLLOW-UP:

  Hi {contact},

  Great chatting about the project. To summarize what we discussed:

  - Scope: [what you agreed on]
  - Timeline: [delivery date]
  - Investment: [price]

  I can start [specific date] and have the first milestone ready by
  [date]. I'll send over a simple agreement to get things rolling.

  Does this capture everything correctly?

  Best,
  [Your Name]
  """)
    elif status in ("won", "delivered"):
        print(f"""  POST-DELIVERY / UPSELL:

  Hi {contact},

  Hope you're getting great results from [what you delivered].

  I noticed [related opportunity or improvement] that could help
  {company} even further. Many of my clients have seen [result]
  from adding this on.

  Would you be interested in exploring this? Also, if you know
  anyone else who could use similar help, I'd really appreciate
  an introduction.

  Best,
  [Your Name]

  ---

  Also ask for a testimonial:

  "If you're happy with the work, would you mind writing a quick
  2-3 sentence testimonial I could use? A LinkedIn recommendation
  would be amazing too."
  """)

    # Update follow-up date
    from datetime import timedelta
    next_followup = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    conn.execute("UPDATE clients SET follow_up_date = ? WHERE id = ?", (next_followup, client_id))
    conn.execute(
        "INSERT INTO activities (client_id, activity_type, description) VALUES (?, ?, ?)",
        (client_id, "followup", f"Follow-up generated for {status} stage")
    )
    conn.commit()
    print(f"  Next follow-up set: {next_followup}")
    conn.close()

def main(args):
    if not args:
        print("Usage: python run.py outreach <upwork|linkedin|cold-email|followup> [args]")
        return

    cmd = args[0].lower()

    if cmd == "upwork":
        generate_upwork(args[1:])
    elif cmd == "linkedin":
        generate_linkedin(args[1:])
    elif cmd in ("cold-email", "coldemail", "email"):
        generate_cold_email(args[1:])
    elif cmd == "followup":
        generate_followup(args[1:])
    else:
        print(f"  Unknown outreach type: {cmd}")
