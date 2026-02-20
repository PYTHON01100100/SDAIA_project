import logging
import socket
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from tools.registry import registry

# ===========================
# Web Search (Modified to print links)
# ===========================
@registry.register(
    name="search_web",
    description="Search the web for a query. Prints results with title and link.",
    category="research"
)
def search_web(query: str, max_results: int = 5) -> list[dict]:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.post(url, data={"q": query}, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Search failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for idx, result in enumerate(soup.find_all("div", class_="result", limit=max_results), start=1):
        title_tag = result.find("a", class_="result__a")
        snippet_tag = result.find("a", class_="result__snippet")
        if title_tag:
            link = title_tag.get("href", "")
            if validate_url(link):
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                result_entry = {
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "reference": f"Queried from DuckDuckGo: {link}"  # <-- هذا الرابط المرجعي
                }
                results.append(result_entry)
                print(f"[{idx}] {title}\n{link}\n{snippet}\n---\n")
    return results



# ===========================
# Read Webpage
# ===========================
@registry.register(
    name="read_webpage",
    description="Read the content of a webpage. Returns the text content.",
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
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)[:10000]
    except Exception as e:
        return f"Error reading {url}: {e}"
