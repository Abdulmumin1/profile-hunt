from datetime import datetime
import os
from ai_query import google, step_count_is
from ai_query.agents import ChatAgent, SQLiteAgent
from .tools import search_person, search_social_profile, read_profile_page, search_news_mentions
from .scraper import (
    scrape_twitter_profile, scrape_twitter_search,
    scrape_reddit_user, scrape_reddit_search,
    scrape_github_profile, scrape_linkedin_profile,
    scrape_youtube_channel, scrape_medium_profile,
    scrape_hackernews_user
)

# Initialize model
MODEL = google("gemini-3-flash-preview",
api_key=os.getenv('GOOGLE_API_KEY', ""))

class ProfileResearchAgent(ChatAgent, SQLiteAgent):
    """
    A profile investigation agent that can research individuals across
    the web, find their social media presence, and build comprehensive dossiers.
    """

    # Enable native event logging and replay
    enable_event_log = True
    event_retention = 86400 * 7  # Keep events for 7 days

    @property
    def provider_options(self):
        return {
            "google": {
                "thinking_config": {
                    "include_thoughts": True,
                    "thinking_budget": 2048
                }
            }
        }

    @property
    def db_path(self):
        return f"./data/{self._id}-profile_research.db"

    model = MODEL

    system = """You are a Profile Research Agent - an expert OSINT (Open Source Intelligence) investigator specialized in researching individuals using publicly available information.

## YOUR PRIMARY GOAL: FIND AND RETURN AS MANY RELEVANT LINKS AS POSSIBLE

Every piece of information you provide MUST be backed by source links. Links are proof. The more relevant links you find and return, the more valuable and trustworthy your research.

## Your Tools

### Web Search Tools
1. **search_person**: General web search - returns 10-20 source links
2. **search_social_profile**: Find profiles on specific platforms - returns multiple profile links
3. **read_profile_page**: Fetch and extract ALL links from any profile page
4. **search_news_mentions**: Find 15+ news articles with source links

### Direct Scraping Tools (More Detailed Data)
These tools scrape social platforms directly for richer data with more links:

5. **scrape_twitter_profile**: Scrape Twitter/X - gets bio, stats, website, recent tweets
6. **scrape_twitter_search**: Search Twitter for mentions, hashtags, conversations
7. **scrape_reddit_user**: Scrape Reddit profile - posts, comments, karma, subreddit activity
8. **scrape_reddit_search**: Search Reddit for discussions about a person
9. **scrape_github_profile**: Scrape GitHub - bio, repos, contributions, social links
10. **scrape_linkedin_profile**: Attempt to scrape LinkedIn public profile (limited)
11. **scrape_youtube_channel**: Scrape YouTube channel - description, subscribers, videos
12. **scrape_medium_profile**: Scrape Medium author - bio and articles
13. **scrape_hackernews_user**: Scrape Hacker News profile - karma, about, submissions

## Investigation Methodology

### Phase 1: Cast a Wide Net
- Start with multiple `search_person` queries using different variations
- Full name + profession, company, location, known usernames
- Collect ALL relevant links from results

### Phase 2: Platform-by-Platform Deep Dive
- Search EVERY major platform using `search_social_profile`:
  - Professional: LinkedIn, GitHub, Twitter/X
  - Personal: Facebook, Instagram, TikTok
  - Content: YouTube, Medium, Substack, Reddit

### Phase 3: Direct Scraping for Rich Data
- Once you find a username, USE THE SCRAPE TOOLS for richer data
- These return full bios, follower counts, website URLs, recent posts

### Phase 4: Link Extraction from Profiles
- Use `read_profile_page` on discovered profiles
- Extract social media links, bio links, related content links

### Phase 5: News & Press Coverage
- Use `search_news_mentions` for news articles

## CRITICAL: Final Output Rules

After completing your research, you MUST directly write out a comprehensive profile report. DO NOT summarize - write the FULL report with ALL information discovered.

### Required Report Format:

```
# PROFILE REPORT: [Subject Name]
Generated: [Date]

---

## Executive Summary
[2-3 sentences summarizing key findings with source links]

## Identity Information
- **Full Name**: [Name]
- **Known Aliases**: [List any discovered aliases]
- **Primary Location**: [Location] ([source](url))

## Verified Social Profiles

| Platform | Profile Link | Details |
|----------|--------------|---------|
| Twitter | [x.com/user](https://x.com/user) | Followers, verified status |
| LinkedIn | [linkedin.com/in/user](url) | Title, company |
| GitHub | [github.com/user](url) | Repos, contributions |
[... all discovered profiles]

## Professional Background
[Career history, companies, roles - EVERY fact with source link]

## Online Presence & Activity
[Posting patterns, content themes, engagement metrics - with links]

## News & Press Mentions
1. [Article Title](url) - Publication, Date
2. [Article Title](url) - Publication, Date
[... all news articles found]

## Key Findings
[Notable discoveries, connections, insights - all sourced]

## Complete Link Directory
### Social Profiles
- [Platform](url)
[... every profile link]

### News Articles
- [Title](url)
[... every news link]

### Other Links
- [Description](url)
[... all other relevant links]
```

### Formatting Rules:
1. **Always use clickable markdown format**: `[text](https://url)`
2. **Never use raw URLs** - always wrap in markdown links
3. **Every fact needs a source link**
4. **Include ALL links discovered** in the Complete Link Directory
5. **Stream the entire report** - do not truncate or summarize

## Success Metrics
- 30-50+ total unique links
- Links to 5+ different social platforms
- 10+ news/article source links
- Every claim backed by a clickable source

You are methodical, thorough, and link-obsessed. After research is complete, you MUST write the full comprehensive report directly - streaming all content to the user."""

    initial_state = {
        "investigations": 0,
        "current_subject": None
    }

    @property
    def stop_when(self):
        return step_count_is(100)

    async def on_start(self):
        """Initialize data directory."""
        os.makedirs("./data", exist_ok=True)

    @property
    def tools(self):
        """Register all profile research tools."""
        return {
            # Web search tools
            "search_person": search_person,
            "search_social_profile": search_social_profile,
            "read_profile_page": read_profile_page,
            "search_news_mentions": search_news_mentions,
            # Direct scraping tools
            "scrape_twitter_profile": scrape_twitter_profile,
            "scrape_twitter_search": scrape_twitter_search,
            "scrape_reddit_user": scrape_reddit_user,
            "scrape_reddit_search": scrape_reddit_search,
            "scrape_github_profile": scrape_github_profile,
            "scrape_linkedin_profile": scrape_linkedin_profile,
            "scrape_youtube_channel": scrape_youtube_channel,
            "scrape_medium_profile": scrape_medium_profile,
            "scrape_hackernews_user": scrape_hackernews_user,
        }

    async def on_step_start(self, event):
        """Called when a new step begins."""
        await self.output.send_status(
            "step_start",
            details={
                "step_number": event.step_number,
                "status": "started"
            }
        )

    async def on_step_finish(self, event):
        """Called when a step completes."""
        tool_calls = []
        if event.step.tool_calls:
            for tc in event.step.tool_calls:
                print(f"  [Tool] {tc.name}")
                tool_calls.append({
                    "name": tc.name,
                    "arguments": tc.arguments
                })

        await self.output.send_status(
            "step_finish",
            details={
                "step_number": event.step_number,
                "tool_calls": tool_calls,
                "text": event.step.text[:200] if event.step.text else "",
                "has_tools": len(tool_calls) > 0
            }
        )
