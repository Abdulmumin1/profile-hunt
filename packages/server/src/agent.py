from datetime import datetime
import os
from ai_query import generate_text, google, tool, Field, step_count_is
from ai_query.agents import ChatAgent, SQLiteAgent
from .tools import search_person, search_social_profile, read_profile_page, search_news_mentions
from .scraper import (
    scrape_twitter_profile, scrape_twitter_search,
    scrape_reddit_user, scrape_reddit_search,
    scrape_github_profile, scrape_linkedin_profile,
    scrape_youtube_channel, scrape_medium_profile,
    scrape_hackernews_user
)
from ai_query.agents.output import SSEOutput

# Initialize model
MODEL = google("gemini-3-flash-preview", 
api_key=os.getenv('GOOGLE_API_KEY', ""))

class ProfileResearchAgent(ChatAgent, SQLiteAgent):
    """
    A profile investigation agent that can research individuals across
    the web, find their social media presence, and build comprehensive dossiers.
    """

    # Enable native event logging and replay
    # This automatically persists all output events to the DB and allows
    # clients to reconnect and replay history using Last-Event-ID.
    enable_event_log = True
    event_retention = 86400 * 7  # Keep events for 7 days

    @property

    def provider_options(self):
        return  {
        "google": {
            "thinking_config": {
                "include_thoughts": True,
                "thinking_budget": 2048
            }
        }
    }
    
    @property
    def db_path(self):
        # Store DB in data directory
        return f"./data/{self._id}-profile_research.db"

    model = MODEL

    system = """You are a Profile Research Agent - an expert OSINT (Open Source Intelligence) investigator specialized in researching individuals using publicly available information.

## YOUR PRIMARY GOAL: FIND AND RETURN AS MANY RELEVANT LINKS AS POSSIBLE

Every piece of information you provide MUST be backed by source links. Links are proof. The more relevant links you find and return, the more valuable and trustworthy your research.

## Your Capabilities

### Web Search Tools
1. **search_person**: General web search - returns 10-20 source links
2. **search_social_profile**: Find profiles on specific platforms - returns multiple profile links
3. **read_profile_page**: Fetch and extract ALL links from any profile page
4. **search_news_mentions**: Find 15+ news articles with source links

### Direct Scraping Tools (More Detailed Data)
These tools scrape social platforms directly for richer data with more links:

5. **scrape_twitter_profile**: Scrape Twitter/X via Nitter - gets bio, stats, website, recent tweets with engagement and links
6. **scrape_twitter_search**: Search Twitter for mentions, hashtags, conversations
7. **scrape_reddit_user**: Scrape Reddit profile - posts, comments, karma, subreddit activity
8. **scrape_reddit_search**: Search Reddit for discussions about a person
9. **scrape_github_profile**: Scrape GitHub - bio, repos, contributions, social links, website
10. **scrape_linkedin_profile**: Attempt to scrape LinkedIn public profile (limited)
11. **scrape_youtube_channel**: Scrape YouTube channel - description, subscribers, recent videos
12. **scrape_medium_profile**: Scrape Medium author - bio and articles
13. **scrape_hackernews_user**: Scrape Hacker News profile - karma, about, submissions

### Data Management
14. **save_account**: Record a discovered social media account
15. **list_accounts**: View all discovered accounts for a person
16. **save_profile_data**: Store discovered profile information
17. **generate_dossier**: Create a comprehensive profile report with all links


## LINK-FIRST Investigation Methodology

Your investigation should be measured by the number of verified links you collect.

### Phase 1: Cast a Wide Net (Goal: 20+ links)
- Start with multiple `search_person` queries using different variations:
  - Full name + profession
  - Full name + company
  - Full name + location
  - Known usernames or handles
- Each search returns up to 20 results - COLLECT ALL RELEVANT LINKS

### Phase 2: Platform-by-Platform Deep Dive (Goal: 10+ profile links)
- Search EVERY major platform systematically using `search_social_profile`:
  - Professional: LinkedIn, GitHub, Twitter/X
  - Personal: Facebook, Instagram, TikTok
  - Content: YouTube, Medium, Substack, Reddit
- For each platform search, you get up to 10 profile links - save them all

### Phase 3: Direct Scraping for Rich Data (Goal: 50+ data points)
- **IMPORTANT**: Once you find a username, USE THE SCRAPE TOOLS for richer data:
  - `scrape_twitter_profile`: Full profile, bio, website, tweets with links
  - `scrape_github_profile`: Full profile, repos, contributions, social links
  - `scrape_reddit_user`: Post history, comments, subreddits
  - `scrape_youtube_channel`: Channel info, recent video links
  - `scrape_medium_profile`: Author bio, article links
  - `scrape_hackernews_user`: Tech activity, submissions
- These return MORE data than web search including:
  - Full bio text with links
  - Follower/following counts
  - Website URLs
  - Recent posts with engagement
  - Links shared in posts

### Phase 4: Link Extraction from Profiles (Goal: 20+ additional links)
- Use `read_profile_page` on each discovered profile
- This extracts:
  - Social media links
  - Profile/bio links
  - Related content links
- Cross-reference links between profiles to find MORE profiles

### Phase 5: News & Press Coverage (Goal: 15+ source links)
- Use `search_news_mentions` with 90-day window
- Returns up to 15 news source links
- Each article is proof of public activity

### Phase 6: Documentation (All links organized)
- Save EVERY discovered account with its URL using `save_account`
- Include source URLs when saving profile data
- Generate dossier that compiles ALL links in organized format

## CRITICAL: Every Response Must Be Link-Heavy

**Minimum link requirements per response:**
- Profile search result: 5+ links
- Social profile search: 3-10 links per platform
- Page read: Extract ALL available links (social, profile, content)
- News search: 10-15 source links
- Final dossier: 30+ total links organized by category

### Formatting Rules for Links:

1. **Always use clickable markdown format:**
   - ✅ `[x.com/username](https://x.com/username)`
   - ✅ `[Source: TechCrunch](https://techcrunch.com/article)`
   - ❌ `https://x.com/username` (never raw URLs)
   - ❌ `x.com/username` (never without markdown link)

2. **Social Profiles - Always as clickable links:**
   - Twitter/X: [x.com/username](https://x.com/username)
   - LinkedIn: [linkedin.com/in/username](https://linkedin.com/in/username)
   - GitHub: [github.com/username](https://github.com/username)
   - Instagram: [instagram.com/username](https://instagram.com/username)
   - YouTube: [youtube.com/@username](https://youtube.com/@username)

3. **Claims & Facts - MUST have inline source:**
   - "Founded Codedamn in 2018 ([source](https://example.com/article))"
   - "Raised $5M according to [TechCrunch](https://techcrunch.com/...)"
   - "Works at Google ([LinkedIn](https://linkedin.com/in/...))"

4. **Profile Summary Format with Links:**
```
## 👤 Professional Profile
- **Role**: Founder & CEO at [Company](https://company.com)
- **Education**: [University Name](https://university.edu) ([source](url))
- **Location**: City, Country ([source](url))

## 🔗 Verified Social Profiles
| Platform | Profile Link | Followers |
|----------|--------------|-----------|
| Twitter | [x.com/handle](https://x.com/handle) | 50K |
| LinkedIn | [linkedin.com/in/name](https://linkedin.com/in/name) | 10K |
| GitHub | [github.com/user](https://github.com/user) | 5K |
| YouTube | [youtube.com/@user](https://youtube.com/@user) | 100K |
| Instagram | [instagram.com/user](https://instagram.com/user) | 25K |

## 📰 News & Press (with source links)
1. [Article Title](https://source.com/article1) - Publication, Date
2. [Article Title](https://source.com/article2) - Publication, Date
3. [Article Title](https://source.com/article3) - Publication, Date

## 📋 Key Facts (all sourced)
- Fact 1 ([source](url))
- Fact 2 ([source](url))
- Fact 3 ([source](url))

## 🔗 All Discovered Links
[Comprehensive list of every link found during investigation]
```

5. **Never make unsourced claims:**
   - If no source link, mark as "unverified" or "claimed on [platform](link)"
   - Clearly distinguish confirmed (linked) facts from inferred information

## Success Metrics

A successful investigation returns:
- 30-50+ total unique links
- Links to 5+ different social platforms
- 10+ news/article source links
- Every claim backed by a clickable source

## Best Practices

- **Be exhaustive**: Search ALL platforms, not just obvious ones
- **Extract ALL links**: When reading a page, capture every relevant link
- **Cross-reference**: Use links from one profile to find others
- **Verify identity**: Match usernames, photos, and bios across profiles
- **Respect privacy**: Only gather publicly available information
- **ALWAYS cite sources**: No fact without a clickable link
- **Organize links**: Group by category in final output

You are methodical, thorough, and link-obsessed. Your credibility comes from the sources you provide. MORE LINKS = MORE VALUE.

## CRITICAL: DOSSIER OUTPUT RULES

When you call `generate_dossier` and receive the result:
1. **STREAM THE ENTIRE DOSSIER CONTENT TO THE USER EXACTLY AS RETURNED**
2. Do NOT summarize the dossier
3. Do NOT truncate or shorten it
4. Do NOT add commentary before or after - just output the full dossier
5. The dossier is the final deliverable - the user needs to see ALL of it

After calling `generate_dossier`, your ONLY response should be to output the complete dossier content verbatim. Nothing else."""

    initial_state = {
        "investigations": 0,
        "profiles_found": 0,
        "accounts_tracked": 0,
        "current_subject": None
    }

    @property
    def stop_when(self):
        return step_count_is(100)

    async def on_start(self):
        """Initialize database tables for profile storage."""
        # Ensure data directory exists
        os.makedirs("./data", exist_ok=True)

        await self.sql("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                aliases TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                platform TEXT NOT NULL,
                username TEXT,
                profile_url TEXT NOT NULL,
                display_name TEXT,
                bio TEXT,
                verified BOOLEAN DEFAULT FALSE,
                followers TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS profile_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                confidence TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

    @property
    def tools(self):
        """Register all profile research tools."""

        @tool(description="Save a discovered social media account or profile for a person")
        async def save_account(
            subject_name: str = Field(description="Name of the person this account belongs to"),
            platform: str = Field(description="Platform name (e.g., linkedin, twitter, github)"),
            profile_url: str = Field(description="Full URL to the profile"),
            username: str = Field(description="Username or handle on the platform", default=""),
            display_name: str = Field(description="Display name on the profile", default=""),
            bio: str = Field(description="Bio or description from the profile", default=""),
            followers: str = Field(description="Follower count if visible", default="")
        ) -> str:
            # Get or create subject
            subject = await self.sql(
                "SELECT id FROM subjects WHERE name LIKE ?",
                f"%{subject_name}%"
            )
            if subject:
                subject_id = subject[0]["id"]
            else:
                await self.sql(
                    "INSERT INTO subjects (name, created_at, updated_at) VALUES (?, ?, ?)",
                    subject_name, datetime.now().isoformat(), datetime.now().isoformat()
                )
                result = await self.sql("SELECT last_insert_rowid() as id")
                subject_id = result[0]["id"]

            # Check if account already exists
            existing = await self.sql(
                "SELECT id FROM accounts WHERE profile_url = ?",
                profile_url
            )
            if existing:
                return f"Account already saved: {profile_url}"

            await self.sql(
                """INSERT INTO accounts
                   (subject_id, platform, username, profile_url, display_name, bio, followers, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                subject_id, platform.lower(), username, profile_url, display_name, bio, followers,
                datetime.now().isoformat()
            )

            count = (await self.sql("SELECT COUNT(*) as c FROM accounts WHERE subject_id = ?", subject_id))[0]["c"]
            await self.set_state({**self.state, "accounts_tracked": count})

            return f"✓ Saved {platform} account for {subject_name}\n  URL: {profile_url}\n  Username: {username or 'N/A'}\n  Total accounts: {count}"

        @tool(description="Save a piece of profile data or finding about a person")
        async def save_profile_data(
            subject_name: str = Field(description="Name of the person"),
            category: str = Field(description="Category: personal, professional, education, contact, location, interests, connections, other"),
            content: str = Field(description="The information discovered"),
            source_url: str = Field(description="URL where this was found", default=""),
            confidence: str = Field(description="Confidence level: low, medium, high", default="medium")
        ) -> str:
            subject = await self.sql(
                "SELECT id FROM subjects WHERE name LIKE ?",
                f"%{subject_name}%"
            )
            if subject:
                subject_id = subject[0]["id"]
            else:
                await self.sql(
                    "INSERT INTO subjects (name, created_at, updated_at) VALUES (?, ?, ?)",
                    subject_name, datetime.now().isoformat(), datetime.now().isoformat()
                )
                result = await self.sql("SELECT last_insert_rowid() as id")
                subject_id = result[0]["id"]

            await self.sql(
                """INSERT INTO profile_data (subject_id, category, content, source_url, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                subject_id, category, content, source_url, confidence, datetime.now().isoformat()
            )

            count = (await self.sql("SELECT COUNT(*) as c FROM profile_data WHERE subject_id = ?", subject_id))[0]["c"]
            await self.set_state({**self.state, "profiles_found": count})

            return f"✓ Saved [{category}] data for {subject_name} ({confidence} confidence)"

        @tool(description="List all discovered accounts for a person")
        async def list_accounts(
            subject_name: str = Field(description="Name of the person to list accounts for")
        ) -> str:
            subject = await self.sql(
                "SELECT id FROM subjects WHERE name LIKE ?",
                f"%{subject_name}%"
            )
            if not subject:
                return f"No subject found matching '{subject_name}'"

            accounts = await self.sql(
                """SELECT platform, username, profile_url, display_name, followers
                   FROM accounts WHERE subject_id = ? ORDER BY platform""",
                subject[0]["id"]
            )

            if not accounts:
                return f"No accounts found for '{subject_name}'"

            result = f"**Accounts for {subject_name}:**\n\n"
            for acc in accounts:
                result += f"• **{acc['platform'].upper()}**"
                if acc['username']:
                    result += f" @{acc['username']}"
                if acc['followers']:
                    result += f" ({acc['followers']} followers)"
                result += f"\n  {acc['profile_url']}\n"
                if acc['display_name']:
                    result += f"  Name: {acc['display_name']}\n"

            return result

        @tool(description="Generate a comprehensive dossier/report for a person from all saved data")
        async def generate_dossier(
            subject_name: str = Field(description="Name of the person to generate dossier for")
        ) -> str:
            subject = await self.sql(
                "SELECT * FROM subjects WHERE name LIKE ?",
                f"%{subject_name}%"
            )
            if not subject:
                return f"No subject found matching '{subject_name}'. Start an investigation first."

            subject_id = subject[0]["id"]

            accounts = await self.sql(
                "SELECT * FROM accounts WHERE subject_id = ? ORDER BY platform",
                subject_id
            )

            profile_data = await self.sql(
                "SELECT * FROM profile_data WHERE subject_id = ? ORDER BY category, confidence DESC",
                subject_id
            )

            if not accounts and not profile_data:
                return f"No data collected for '{subject_name}'. Conduct research first."

            # Build dossier content
            dossier_input = f"Subject: {subject[0]['name']}\n\n"

            if accounts:
                dossier_input += "## Discovered Accounts\n"
                for acc in accounts:
                    dossier_input += f"- {acc['platform']}: {acc['profile_url']}"
                    if acc['username']:
                        dossier_input += f" (@{acc['username']})"
                    if acc['bio']:
                        dossier_input += f"\n  Bio: {acc['bio']}"
                    dossier_input += "\n"

            if profile_data:
                dossier_input += "\n## Collected Intelligence\n"
                current_category = None
                for data in profile_data:
                    if data['category'] != current_category:
                        current_category = data['category']
                        dossier_input += f"\n### {current_category.title()}\n"
                    dossier_input += f"- {data['content']}"
                    if data['source_url']:
                        dossier_input += f" (Source: {data['source_url']})"
                    dossier_input += f" [{data['confidence']}]\n"

            # Use LLM to synthesize into a professional dossier
            result = await generate_text(
                model=MODEL,
                system="""You are an intelligence analyst. Create a professional dossier from the provided research data.

YOUR PRIMARY OBJECTIVE: Include as many verified links as possible. Links are proof.

Structure the dossier with:
1. **Executive Summary** - Key findings in 2-3 sentences with source links
2. **Identity Information** - Name, aliases, identifiers (all linked)
3. **Digital Footprint** - ALL discovered accounts as clickable markdown links in a table
4. **Professional Profile** - Career, companies, roles (EVERY fact must have a source link)
5. **Personal Information** - Location, interests, connections (with source links)
6. **Activity Analysis** - Patterns, posting habits, interests (with source links)
7. **Key Findings** - Notable discoveries with source links
8. **Complete Link Directory** - EVERY link discovered, organized by category

CRITICAL FORMATTING RULES (NON-NEGOTIABLE):
- Every social profile MUST be a clickable markdown link: [platform.com/user](https://platform.com/user)
- Every fact MUST have a source link inline or in parentheses
- Use tables for social profiles:
  | Platform | Profile Link | Details |
  |----------|--------------|---------|
  | Twitter | [x.com/user](https://x.com/user) | 50K followers |
  | LinkedIn | [linkedin.com/in/user](https://linkedin.com/in/user) | Verified |

- Never state a fact without a source URL
- If source URL is provided in the data, you MUST include it
- Raw URLs are NOT acceptable - always use markdown link format
- Include a "Complete Link Directory" section at the end with ALL links

Example fact formatting:
- ✅ "Founder of [Company](https://company.com) since 2018 ([source](https://article.com))"
- ❌ "Founder of Company since 2018"

The value of this dossier is measured by the number of verified, clickable source links it contains.
Target: 30+ links minimum in the final dossier.

Be factual and objective. Note confidence levels. Format with clear markdown.""",
                prompt=f"Create a comprehensive dossier from this research. Include EVERY link found:\n\n{dossier_input}"
            )

            return f"# PROFILE DOSSIER\n## Subject: {subject[0]['name']}\n### Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n{result.text}"

        @tool(description="Clear all data for a subject to start fresh")
        async def clear_subject_data(
            subject_name: str = Field(description="Name of the person to clear data for"),
            confirm: bool = Field(description="Set to true to confirm deletion")
        ) -> str:
            if not confirm:
                return "Set confirm=true to delete all data for this subject."

            subject = await self.sql(
                "SELECT id FROM subjects WHERE name LIKE ?",
                f"%{subject_name}%"
            )
            if not subject:
                return f"No subject found matching '{subject_name}'"

            subject_id = subject[0]["id"]
            await self.sql("DELETE FROM accounts WHERE subject_id = ?", subject_id)
            await self.sql("DELETE FROM profile_data WHERE subject_id = ?", subject_id)
            await self.sql("DELETE FROM subjects WHERE id = ?", subject_id)

            return f"✓ Cleared all data for '{subject_name}'"

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
            # Data management
            "save_account": save_account,
            "save_profile_data": save_profile_data,
            "list_accounts": list_accounts,
            "generate_dossier": generate_dossier,
            "clear_subject_data": clear_subject_data,
        }

    async def on_step_start(self, event):
        """Called when a new step begins."""
        await self.output.send_status(
            f"step_start",
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
            f"step_finish",
            details={
                "step_number": event.step_number,
                "tool_calls": tool_calls,
                "text": event.step.text[:200] if event.step.text else "",
                "has_tools": len(tool_calls) > 0
            }
        )