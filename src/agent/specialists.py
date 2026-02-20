import logging
import socket
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from tools.registry import registry
from agent.observable_agent import ObservableAgent
import os

logger = logging.getLogger(__name__)
DEFAULT_MODEL = os.getenv("MODEL_NAME", "z-ai/glm-4.5-air:free")


# ======================
# URL Validation
# ======================
def validate_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        ip_address = socket.gethostbyname(hostname)
        parts = ip_address.split(".")
        if parts[0] == "10" or (parts[0] == "192" and parts[1] == "168") \
           or (parts[0] == "172" and 16 <= int(parts[1]) <= 31) \
           or parts[0] == "127" or ip_address == "0.0.0.0":
            return False
        return True
    except Exception:
        return False


# ======================
# Tools
# ======================
@registry.register(
    name="search_web",
    description="Search the internet for up-to-date information. MUST be used when answer is not known.",
    category="research"
)
def search_web(query: str, max_results: int = 5) -> str:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.post(url, data={"q": query}, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search failed: {str(e)}"

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.find_all("div", class_="result", limit=max_results):
        title_tag = result.find("a", class_="result__a")
        snippet_tag = result.find("a", class_="result__snippet")
        if not title_tag:
            continue
        link = title_tag.get("href", "")
        title = title_tag.get_text(strip=True)
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        if validate_url(link):
            results.append(f"{title}\n{link}\n{snippet}")
    if not results:
        return "No relevant web results found."
    return "\n\n---\n\n".join(results)


@registry.register(
    name="read_webpage",
    description="Read full content from a webpage URL. Use after search_web.",
    category="research"
)
def read_webpage(url: str) -> str:
    if not validate_url(url):
        return "Error: Invalid or restricted URL."
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = "\n".join(line.strip() for line in soup.get_text().splitlines() if line.strip())
        return text[:8000]
    except Exception as e:
        logger.error(f"Error reading {url}: {e}")
        return f"Error reading {url}: {str(e)}"


# ======================
# Agents
# ======================


def create_researcher(model: str = None, max_steps: int = 10):
    system_prompt = (
        "You are a research agent.\n"
        "Always use search_web and read_webpage to find accurate and current information.\n"
    )
    tools = registry.get_tools_by_category("research")
    return ObservableAgent(
        model=model or DEFAULT_MODEL,
        max_steps=max_steps,
        agent_name="Researcher",
        system_prompt=system_prompt,
        tools=tools,
        verbose=True
    )


def create_analyst(model: str = None, max_steps: int = 20):
    system_prompt = (
        "You are an expert analyst.\n"
        "Critically evaluate research results, find patterns, trends, inconsistencies.\n"
    )
    tools = registry.get_tools_by_category("research")
    return ObservableAgent(
        model=model or DEFAULT_MODEL,
        max_steps=max_steps,
        agent_name="Analyst",
        system_prompt=system_prompt,
        tools=tools,
        verbose=True
    )


def create_writer(model: str = None, max_steps: int = 5):
    system_prompt = (
    "You are a professional technical writer.\n"
    "Answer only technical questions.\n"
    "Ignore religious, political, or cultural content.\n"
)

    tools = registry.get_tools_by_category("research")
    return ObservableAgent(
        model=model or DEFAULT_MODEL,
        max_steps=max_steps,
        agent_name="Writer",
        system_prompt=system_prompt,
        tools=tools,
        verbose=True
    )

