"""
MCP server implementation for Yle news RSS feeds.
"""
from typing import List
from pydantic import Field, BaseModel
import feedparser
import httpx
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("yle-news", host='127.0.0.1', port=8997)

# RSS feed URLs for different topics
RSS_FEEDS = {
	# Pää-, tuoreimmat ja luetuimmat uutiset
	"news": "https://yle.fi/rss/uutiset/paauutiset",
	"recent": "https://yle.fi/rss/uutiset/tuoreimmat",
	"most_read": "https://yle.fi/rss/uutiset/luetuimmat",

	# Uutiset, urheilu ja muut sisällöt yhdessä
	"all_content": "https://yle.fi/rss/tuoreimmat",

	# Aihekohtaiset syötteet
	"kotimaa": "https://yle.fi/rss/t/18-34837/fi",
	"ulkomaat": "https://yle.fi/rss/t/18-34953/fi",
	"talous": "https://yle.fi/rss/t/18-19274/fi",
	"politiikka": "https://yle.fi/rss/t/18-38033/fi",
	"viihde": "https://yle.fi/rss/t/18-36066/fi",
	"kulttuuri": "https://yle.fi/rss/t/18-150067/fi",
	"tiede": "https://yle.fi/rss/t/18-819/fi",
	"luonto": "https://yle.fi/rss/t/18-35354/fi",
	"terveys": "https://yle.fi/rss/t/18-35138/fi",
	"liikenne": "https://yle.fi/rss/t/18-12/fi",
	"kolumnit": "https://yle.fi/rss/t/18-215844/fi",  # was "näkökulmat"

	# Urheilu
	"urheilu": "https://yle.fi/rss/urheilu",

	# Alueuutiset (regional news)
	"etela-karjala": "https://yle.fi/rss/t/18-141372/fi",
	"etela-pohjanmaa": "https://yle.fi/rss/t/18-146311/fi",
	"etela-savo": "https://yle.fi/rss/t/18-141852/fi",
	"kainuu": "https://yle.fi/rss/t/18-141399/fi",
	"kanta-hame": "https://yle.fi/rss/t/18-138727/fi",
	"keski-pohjanmaa": "https://yle.fi/rss/t/18-135629/fi",
	"keski-suomi": "https://yle.fi/rss/t/18-148148/fi",
	"kymenlaakso": "https://yle.fi/rss/t/18-131408/fi",
	"lappi": "https://yle.fi/rss/t/18-139752/fi",
	"pirkanmaa": "https://yle.fi/rss/t/18-146831/fi",
	"pohjanmaa": "https://yle.fi/rss/t/18-148149/fi",
	"pohjois-karjala": "https://yle.fi/rss/t/18-141936/fi",
	"pohjois-pohjanmaa": "https://yle.fi/rss/t/18-148154/fi",
	"pohjois-savo": "https://yle.fi/rss/t/18-141764/fi",
	"paijat-hame": "https://yle.fi/rss/t/18-141401/fi",
	"satakunta": "https://yle.fi/rss/t/18-139772/fi",
	"uusimaa": "https://yle.fi/rss/t/18-147345/fi",
	"varsinais-suomi": "https://yle.fi/rss/t/18-135507/fi",

	# Selkouutiset
	"selkouutiset": "https://yle.fi/rss/selkouutiset",

	# Nyheter på svenska
	"svenska_senaste": "https://svenska.yle.fi/rss/senaste-nytt",
	"svenska_inrikes": "https://svenska.yle.fi/rss/inrikes",
	"svenska_utrikes": "https://svenska.yle.fi/rss/utrikes",
	"svenska_sport": "https://svenska.yle.fi/rss/sport",
	"svenska_kultur": "https://svenska.yle.fi/rss/kultur",
	"svenska_huvudstadsregionen": "https://svenska.yle.fi/rss/huvudstadsregionen",
	"svenska_osterbotten": "https://svenska.yle.fi/rss/osterbotten",
	"svenska_aboland": "https://svenska.yle.fi/rss/aboland",
	"svenska_ostnyland": "https://svenska.yle.fi/rss/ostnyland",
	"svenska_vastnyland": "https://svenska.yle.fi/rss/vastnyland",

	# Other languages
	"sapmi": "https://yle.fi/rss/sapmi",
	"english": "https://yle.fi/rss/news",
	"novosti": "https://yle.fi/rss/novosti",       # Russian
	"novyny": "https://yle.fi/rss/novyny",          # Ukrainian (new)
	"karjalakse": "https://yle.fi/rss/t/18-44136/fi",  # Karelian
}

class NewsItem(BaseModel):
    """Model for a news item."""
    title: str
    published: str
    link: str
    summary: str
    published_parsed: datetime = Field(default=None, exclude=True)

class NewsResponse(BaseModel):
    """Model for the news response."""
    items: List[NewsItem]
    topic: str
    count: int

async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Fetch and parse an RSS feed."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return feedparser.parse(response.content)

def parse_news_item(entry: feedparser.FeedParserDict) -> NewsItem:
    """Parse a feed entry into a NewsItem."""
    published_parsed = None
    if hasattr(entry, 'published_parsed'):
        published_parsed = datetime(*entry.published_parsed[:6])
    
    return NewsItem(
        title=entry.get('title', 'No title'),
        published=entry.get('published', 'No date'),
        link=entry.get('link', 'No link'),
        summary=entry.get('summary', 'No summary'),
        published_parsed=published_parsed
    )

@mcp.tool()
async def get_news(
    topic: str = Field(
        description="The news topic to fetch. Available topics: news, recent, most_read, kotimaa, ulkomaat, talous, politiikka, kulttuuri, viihde, tiede, luonto, terveys, media, liikenne, näkökulmat, urheilu, selkouutiset, english, sapmi, novosti, karjalakse",
        default="news"
    ),
    limit: int = Field(
        description="Maximum number of news items to fetch",
        default=5
    )
) -> NewsResponse:
    """
    Fetch news from Yle RSS feeds for a specific topic.
    
    Args:
        topic: The news topic to fetch
        limit: Maximum number of news items to return
        
    Returns:
        NewsResponse containing the news items sorted by publication date (newest first)
    """
    if topic not in RSS_FEEDS:
        raise ValueError(f"Invalid topic: {topic}. Available topics: {', '.join(RSS_FEEDS.keys())}")
    
    try:
        feed = await fetch_feed(RSS_FEEDS[topic])
        if not feed.entries:
            return NewsResponse(items=[], topic=topic, count=0)
        
        # Parse all items and sort by publication date
        items = [parse_news_item(entry) for entry in feed.entries]
        items.sort(key=lambda x: x.published_parsed or datetime.min, reverse=True)
        
        # Apply limit after sorting
        if limit > 0:
            items = items[:limit]
        
        return NewsResponse(
            items=items,
            topic=topic,
            count=len(items)
        )
    except Exception as e:
        raise Exception(f"Error fetching news: {str(e)}")

def run_server():
    """Run the MCP server."""
    mcp.run(transport='streamable-http')
