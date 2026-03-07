"""
BlackHole Content Engine - Generate content frameworks for blogs, LinkedIn, and Twitter.

These are structured frameworks, not AI-generated slop. Customize before publishing.
"""

import sys
from datetime import datetime

def generate_blog(args):
    if not args:
        print("Usage: python run.py content blog <topic>")
        return

    topic = " ".join(args)
    print(f"\n  === BLOG POST FRAMEWORK: {topic} ===\n")

    print(f"""  TITLE OPTIONS (pick one, customize):
  1. "How to {topic}: A Complete Guide for UAE Businesses"
  2. "I {topic} for a UAE Client - Here's What Happened"
  3. "The Ultimate Guide to {topic} in 2025"
  4. "{topic}: What Most Businesses Get Wrong"
  5. "How I Saved [Client] $X/Month with {topic}"

  ---

  STRUCTURE:

  ## Hook (2-3 sentences)
  Start with a specific result, surprising stat, or bold claim.
  Example: "Last month, I helped a Dubai restaurant chain automate their
  entire ordering process. They went from 3 staff handling orders to zero.
  Here's exactly how."

  ## The Problem (100-200 words)
  - What pain does your audience feel?
  - Make it specific and relatable
  - Use numbers: hours wasted, money lost, opportunities missed

  ## The Solution (300-500 words)
  - Step-by-step breakdown
  - Use subheadings for each step
  - Include code snippets, screenshots, or diagrams if relevant
  - Be specific enough to be useful, vague enough they still need you

  ## Results (100-150 words)
  - Concrete metrics: time saved, money earned, efficiency gained
  - Before/after comparison
  - Client quote if possible

  ## CTA (2-3 sentences)
  - "Want similar results? [Book a call / DM me / visit my site]"
  - Include link to your services

  ---

  SEO TIPS:
  - Target 1 primary keyword + 3-5 related keywords
  - Use keyword in: title, first paragraph, 2-3 subheadings, conclusion
  - Aim for 1,500-2,500 words for SEO ranking
  - Add internal links to your other content
  - Add external links to authoritative sources
  - Include an image every 300 words
  - Write meta description (150-160 chars)

  DISTRIBUTION:
  - Publish on your blog + Medium/Hashnode
  - Share on LinkedIn with a hook paragraph
  - Create a Twitter thread summarizing key points
  - Share in relevant Reddit/Facebook/WhatsApp groups
  """)

def generate_linkedin(args):
    if not args:
        print("Usage: python run.py content linkedin <topic>")
        return

    topic = " ".join(args)
    print(f"\n  === LINKEDIN POST FRAMEWORK: {topic} ===\n")

    print(f"""  FORMAT 1: The Story Post (highest engagement)

  [HOOK - surprising statement about {topic}]

  3 months ago, I [did something related to {topic}].

  Everyone said [common objection/doubt].

  Here's what actually happened:

  [STEP 1 - what you did]
  Result: [metric]

  [STEP 2 - what you did next]
  Result: [metric]

  [STEP 3 - the outcome]
  Result: [big metric]

  The lesson?
  [One-line insight about {topic}]

  If you're thinking about {topic}, here's my advice:
  -> [Tip 1]
  -> [Tip 2]
  -> [Tip 3]

  [CTA - question to drive comments]

  ---

  FORMAT 2: The List Post

  I've been [doing activity related to {topic}] for [time].

  Here are [N] things I wish I knew earlier:

  1. [Insight] - [brief explanation]
  2. [Insight] - [brief explanation]
  3. [Insight] - [brief explanation]
  4. [Insight] - [brief explanation]
  5. [Insight] - [brief explanation]

  Which one resonates most? Drop a number below.

  ---

  FORMAT 3: The Contrarian Take

  Unpopular opinion about {topic}:

  [Bold contrarian statement]

  Here's why:

  Most people think [common belief].

  But in my experience working with [N] clients in UAE:

  [Evidence 1]
  [Evidence 2]
  [Evidence 3]

  The truth is: [your actual insight]

  Agree or disagree? I'd love to hear your take.

  ---

  LINKEDIN TIPS:
  - Post between 7-9 AM UAE time (catches Asia + early Europe)
  - First 3 lines must hook (that's all people see before "see more")
  - Use line breaks liberally (easy to scan on mobile)
  - End with a question (boosts comments = boosts reach)
  - Reply to EVERY comment within 1 hour
  - No external links in the post (kills reach). Put links in comments.
  - Use 3-5 relevant hashtags
  - Tag 2-3 relevant people (but only if genuine)
  """)

def generate_twitter(args):
    if not args:
        print("Usage: python run.py content twitter <topic>")
        return

    topic = " ".join(args)
    print(f"\n  === TWITTER/X THREAD FRAMEWORK: {topic} ===\n")

    print(f"""  THREAD FORMAT:

  TWEET 1 (THE HOOK):
  I [achieved result] with {topic} in [timeframe].

  Here's the exact playbook (thread):

  ---

  TWEET 2-8 (THE STEPS):
  Step [N]: [action]

  [2-3 sentences explaining how]

  [Result or key takeaway]

  ---

  TWEET 9 (THE RESULTS):
  Results after [timeframe]:

  - [Metric 1]
  - [Metric 2]
  - [Metric 3]

  ---

  TWEET 10 (THE CTA):
  If you want help with {topic}:

  1. Follow me for more threads like this
  2. RT the first tweet to help others
  3. DM me "READY" and I'll [offer something free]

  ---

  ALTERNATIVE HOOKS (tweet 1):
  - "I spent [X hours/days] studying {topic}. Here's what 99% of people miss:"
  - "{topic} made me $[X] this month. Here's how (step by step):"
  - "Stop overcomplicating {topic}. Here's a simple framework:"
  - "A client paid me $[X] to {topic}. Here's what I did (you can too):"

  TWITTER TIPS:
  - Post threads 8-10 AM EST or 12-2 PM EST (peak engagement)
  - Number your tweets (1/, 2/, etc.)
  - Use "thread" or a thread emoji in tweet 1
  - 5-10 tweets is ideal length
  - Add an image to tweet 1 (boosts impressions 2x)
  - Reply to your own thread with a TLDR
  - Retweet your thread 8 hours later for different timezone reach
  """)

def content_calendar():
    """Generate a weekly content calendar."""
    print("\n  === WEEKLY CONTENT CALENDAR ===\n")
    print("""
  MONDAY:
    LinkedIn: Educational post (how-to, tips, framework)
    Twitter:  Thread (deep dive on one topic)
    Blog:     Start writing weekly article

  TUESDAY:
    LinkedIn: Story post (client result, personal experience)
    Twitter:  Quick tip + engage with others
    Blog:     Continue writing

  WEDNESDAY:
    LinkedIn: Contrarian take or industry observation
    Twitter:  Thread (case study or breakdown)
    Blog:     Publish article, share everywhere

  THURSDAY:
    LinkedIn: Behind-the-scenes or personal insight
    Twitter:  Quick tip + engage
    YouTube:  Film/record weekly video

  FRIDAY:
    LinkedIn: Weekend question or poll
    Twitter:  Curated thread (best things I read this week)
    YouTube:  Edit and publish

  DAILY (15 min each):
    - Reply to all comments on your posts
    - Comment on 10 posts from target audience
    - Send 5 LinkedIn DMs
    - Engage with 10 tweets in your niche

  CONTENT RATIO:
    70% Value (teach, help, inform)
    20% Authority (results, case studies, social proof)
    10% Promotion (services, products, CTAs)
  """)

def main(args):
    if not args:
        print("Usage: python run.py content <blog|linkedin|twitter|calendar> <topic>")
        return

    cmd = args[0].lower()
    if cmd == "blog":
        generate_blog(args[1:])
    elif cmd == "linkedin":
        generate_linkedin(args[1:])
    elif cmd == "twitter":
        generate_twitter(args[1:])
    elif cmd == "calendar":
        content_calendar()
    else:
        print(f"  Unknown content type: {cmd}")
