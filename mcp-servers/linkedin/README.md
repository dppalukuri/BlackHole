# LinkedIn Scraper MCP

Extract profiles, job postings, and company data from LinkedIn for AI agents. Session-based authentication with persistent cookies -- log in once, scrape headlessly.

**Free alternative to Proxycurl ($50/mo), PhantomBuster ($69/mo), and Snov.io ($39/mo).**

## Why This Tool?

| Feature | This Tool | Proxycurl | PhantomBuster | Snov.io |
|---------|-----------|-----------|---------------|---------|
| Free to use | Yes | $49/mo | $69/mo | $39/mo |
| MCP server (for AI agents) | Yes | No | No | No |
| Profile scraping | Yes | Yes | Yes | Yes |
| Job search | Yes | No | Yes | No |
| Company pages | Yes | Yes | Yes | Partial |
| People search | Yes | No | Yes | Yes |
| No API key needed | Yes | No | No | No |
| Works without login (jobs) | Yes | N/A | No | N/A |

## How It Works

1. Log in to LinkedIn once via a visible browser window (your real credentials)
2. Session cookies are saved locally in `.sessions/`
3. All subsequent scraping runs headlessly using those cookies
4. Session typically lasts days/weeks before re-login needed

Job search and company pages work **without login**. People search and full profiles require a login session.

## Quick Start

### As MCP Server (Claude Desktop, Cursor, etc.)

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["/path/to/mcp-servers/linkedin/server.py"]
    }
  }
}
```

Install dependencies:

```bash
pip install "mcp[cli]" playwright playwright-stealth
playwright install chromium
```

## Tools

### `login`

Opens a browser window for manual LinkedIn login. You only need to do this once.

### `search_jobs` (no login required)

Search LinkedIn job postings with filters.

```json
{
  "query": "python developer",
  "location": "Dubai",
  "remote": "remote",
  "job_type": "full-time",
  "experience": "mid-senior",
  "max_results": 25
}
```

Example output:
```json
{
  "query": "python developer",
  "type": "jobs",
  "count": 25,
  "results": [
    {
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "Dubai, UAE (Remote)",
      "posted_date": "2 days ago",
      "job_url": "https://linkedin.com/jobs/view/..."
    }
  ]
}
```

Filters: `remote` (remote/onsite/hybrid), `job_type` (full-time/part-time/contract/internship), `experience` (entry/mid-senior/director/executive)

### `get_company` (no login required)

Get company page data.

```json
{"company_slug": "google"}
```

Output:
```json
{
  "name": "Google",
  "tagline": "Organizing the world's information...",
  "industry": "Technology, Information and Internet",
  "company_size": "10,001+ employees",
  "headquarters": "Mountain View, CA",
  "website": "https://google.com",
  "founded": "1998",
  "specialties": ["search", "advertising", "cloud computing", "AI"]
}
```

### `get_profile` (full data requires login)

Get a LinkedIn profile.

```json
{"username": "johndoe"}
```

Output:
```json
{
  "name": "John Doe",
  "headline": "Senior Software Engineer at Google",
  "location": "San Francisco Bay Area",
  "current_title": "Senior Software Engineer",
  "current_company": "Google",
  "connections": "500+",
  "skills": ["Python", "Machine Learning", "Go", "Kubernetes"],
  "profile_url": "https://linkedin.com/in/johndoe/"
}
```

### `search_people` (login required)

Search for people by keywords, company, title, or location.

```json
{
  "query": "CTO",
  "company": "startup",
  "location": "San Francisco",
  "max_results": 20
}
```

## Authentication

LinkedIn is aggressive with bot detection. This tool uses a **session-based approach**:

1. Call the `login` tool -- a browser window opens
2. Log in with your LinkedIn credentials manually
3. Close the browser -- cookies are saved to `.sessions/linkedin.json`
4. All future requests use these cookies in headless mode

**Your credentials are never stored** -- only the session cookies, which are gitignored.

Rate limiting: LinkedIn soft-blocks after ~50 pages/hour. The tool adds delays automatically, but avoid rapid-fire requests.

## What Works Without Login

| Feature | Without Login | With Login |
|---------|--------------|------------|
| Job search | Full access | Full access |
| Company pages | Full access | Full access |
| Profiles | Name, headline, location only | Full profile |
| People search | Not available | Full access |

## Use Cases

- **Recruiting**: Search for candidates by skills, location, company
- **Sales prospecting**: Find decision-makers at target companies
- **Job hunting**: Monitor job postings with specific filters
- **Competitive intelligence**: Track competitor company pages
- **Market research**: Analyze hiring trends and company growth

## License

MIT
