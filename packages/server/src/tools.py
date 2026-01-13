from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from tavily import TavilyClient
import os
from ai_query import tool, Field

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))

# HTTP client for web scraping
http_client = httpx.AsyncClient(
    timeout=30.0,
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
)

# Social media platforms to search
PLATFORMS = {
    "linkedin": "site:linkedin.com/in",
    "twitter": "site:twitter.com OR site:x.com",
    "github": "site:github.com",
    "facebook": "site:facebook.com",
    "instagram": "site:instagram.com",
    "youtube": "site:youtube.com",
    "tiktok": "site:tiktok.com/@",
    "medium": "site:medium.com/@",
    "substack": "site:substack.com",
    "reddit": "site:reddit.com/user",
}

@tool(description="Search the web for information about a person. Returns multiple source links to verify information. Use specific queries for better results.")
async def search_person(
    query: str = Field(description="Search query about the person - include name and any known details"),
    max_results: int = Field(description="Number of results to return (1-20)", default=10)
) -> str:
    """
    Performs a web search focused on finding information about a person.
    """
    try:
        response = tavily_client.search(
            query=query,
            max_results=min(max_results, 20),
            include_answer=True,
            include_raw_content=False
        )

        results = []

        if response.get("answer"):
            results.append(f"**Summary:** {response['answer']}\n")

        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("content", "")[:400]

            # Detect platform from URL
            platform = "web"
            for p, _ in PLATFORMS.items():
                if p in url.lower():
                    platform = p
                    break

            results.append(f"{i}. [{platform.upper()}] **{title}**\n   🔗 Link: [{url}]({url})\n   {snippet}...\n")

        if not results:
            return "No results found for this search."

        return f"**Found {len(results)-1 if response.get('answer') else len(results)} sources with links:**\n\n" + "\n".join(results)

    except Exception as e:
        return f"Search error: {str(e)}"


@tool(description="Search for a person's social media profiles on a specific platform. Returns multiple profile links for verification.")
async def search_social_profile(
    name: str = Field(description="Full name of the person"),
    platform: str = Field(description="Platform to search: linkedin, twitter, github, facebook, instagram, youtube, tiktok, medium, reddit"),
    additional_context: str = Field(description="Additional context like company, location, profession", default="")
) -> str:
    """
    Searches for a person's profile on a specific social media platform.
    """
    platform = platform.lower()
    if platform not in PLATFORMS:
        return f"Unknown platform '{platform}'. Available: {', '.join(PLATFORMS.keys())}"

    try:
        site_filter = PLATFORMS[platform]
        query = f"{name} {additional_context} {site_filter}".strip()

        response = tavily_client.search(
            query=query,
            max_results=10,
            include_answer=False,
            include_raw_content=False
        )

        results = []
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("content", "")[:300]
            results.append(f"{i}. **{title}**\n   🔗 Profile Link: [{url}]({url})\n   {snippet}...\n")

        if not results:
            return f"No {platform} profiles found for '{name}'."

        return f"**{platform.upper()} profiles for {name} ({len(results)} links found):**\n\n" + "\n".join(results)

    except Exception as e:
        return f"Search error: {str(e)}"


@tool(description="Fetch and analyze a profile page or webpage for information about a person. Extracts all relevant links from the page for cross-referencing.")
async def read_profile_page(
    url: str = Field(description="The full URL of the profile or webpage to read"),
    extract_links: bool = Field(description="Whether to also extract links from the page", default=True)
) -> str:
    """
    Fetches a webpage and extracts profile-relevant information.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return "Invalid URL format. Please provide a full URL."

        response = await http_client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise elements
        for element in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines[:150])

        title = soup.title.string if soup.title else "No title"

        # Try to extract structured data
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag["content"]

        result = f"**Page: {title}**\n**URL:** {url}\n"
        if meta_description:
            result += f"**Description:** {meta_description}\n"
        result += f"\n**Content:**\n{content[:5000]}"

        # Extract links (useful for finding more profiles)
        if extract_links:
            social_links = []
            profile_links = []
            other_links = []

            for a in soup.find_all("a", href=True)[:50]:
                href = a["href"]
                if href.startswith("http"):
                    link_text = a.get_text(strip=True)[:60] or href
                    # Check if it's a social link
                    is_social = False
                    for platform in PLATFORMS:
                        if platform in href.lower():
                            social_links.append(f"  - [{platform.upper()}] [{link_text}]({href})")
                            is_social = True
                            break

                    if not is_social:
                        if any(keyword in href.lower() for keyword in ["profile", "about", "team", "author", "user", "people", "staff", "bio"]):
                            profile_links.append(f"  - [{link_text}]({href})")
                        elif any(keyword in href.lower() for keyword in ["blog", "post", "article", "news", "press", "media"]):
                            other_links.append(f"  - [{link_text}]({href})")

            if social_links:
                result += f"\n\n**🔗 Social Media Links Found ({len(social_links)}):**\n" + "\n".join(social_links[:15])
            if profile_links:
                result += f"\n\n**🔗 Profile/Bio Links Found ({len(profile_links)}):**\n" + "\n".join(profile_links[:10])
            if other_links:
                result += f"\n\n**🔗 Related Content Links ({len(other_links)}):**\n" + "\n".join(other_links[:10])

        return result

    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code} when fetching {url}"
    except Exception as e:
        return f"Error reading page: {str(e)}"


@tool(description="Search for news articles and press mentions about a person. Returns multiple source links for verification.")
async def search_news_mentions(
    name: str = Field(description="Full name of the person"),
    context: str = Field(description="Additional context like company or profession", default=""),
    days: int = Field(description="How many days back to search (1-365)", default=90)
) -> str:
    """
    Searches for recent news and press mentions about a person.
    """
    try:
        query = f'"{name}" {context}'.strip()
        response = tavily_client.search(
            query=query,
            max_results=15,
            topic="news",
            days=min(days, 365)
        )

        results = []
        for i, result in enumerate(response.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("content", "")[:350]
            published = result.get("published_date", "")

            results.append(f"{i}. **{title}**\n   📅 {published}\n   🔗 Source: [{url}]({url})\n   {snippet}...\n")

        if not results:
            return f"No news mentions found for '{name}'."

        return f"**News Mentions: {name} ({len(results)} sources found)**\n\n" + "\n".join(results)

    except Exception as e:
        return f"News search error: {str(e)}"
