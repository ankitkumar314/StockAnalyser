from typing import Optional, Dict, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.models.web_scrape import WebScrapeData, WebScrapeRequest


class WebScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _validate_url(self, url: str) -> bool:
        try:
            if url is None or url.strip() == "":
                return False
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        try:
            if soup is None:
                return None
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
            return None
        except Exception as e:
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        try:
            if soup is None:
                return None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content').strip()
            
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                return og_desc.get('content').strip()
            
            return None
        except Exception as e:
            return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> Optional[str]:
        try:
            if soup is None:
                return None
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000] if text else None
        except Exception as e:
            return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        try:
            if soup is None or base_url is None:
                return []
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    if absolute_url not in links:
                        links.append(absolute_url)
            
            return links[:100]
        except Exception as e:
            return []
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        try:
            if soup is None or base_url is None:
                return []
            
            images = []
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src:
                    absolute_url = urljoin(base_url, src)
                    if absolute_url not in images:
                        images.append(absolute_url)
            
            return images[:50]
        except Exception as e:
            return []
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        try:
            if soup is None:
                return {}
            
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            return meta_tags
        except Exception as e:
            return {}
    
    def scrape(self, url: str) -> WebScrapeData:
        try:
            if not self._validate_url(url):
                raise ValueError("Invalid URL provided")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            concall_data = self.parse_concalls(soup)
            scrape_data = WebScrapeData(
                url=url,
                title=self._extract_title(soup),
                description=self._extract_description(soup),
                text_content=self._extract_text_content(soup),
                links=self._extract_links(soup, url),
                images=self._extract_images(soup, url),
                meta_tags=self._extract_meta_tags(soup),
                headers=dict(response.headers),
                status_code=response.status_code,
                scraped_at=datetime.utcnow().isoformat(),
                concall_data=concall_data
            )
            
            return scrape_data
            
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout while scraping {url}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection error while scraping {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {e.response.status_code} while scraping {url}")
        except Exception as e:
            raise Exception(f"Error scraping URL: {str(e)}")

    def parse_concalls(self, soup) -> dict:
        result = {}

        concall_section = soup.select_one("div.documents.concalls")
        if not concall_section:
            return result

        items = concall_section.select("ul.list-links li")

        for item in items:
            # 🗓️ Date (more precise)
            date_div = item.find("div", class_="ink-600")
            if not date_div:
                continue

            date = date_div.get_text(strip=True)

            doc_data = {}

            # 🔗 All possible elements
            elements = item.select(".concall-link")

            for el in elements:
                text = el.get_text(strip=True).lower()

                url = el.get("href") if el.name == "a" else None

                if "ppt" in text and url:
                    doc_data["ppt"] = url
                elif "transcript" in text and url:
                    doc_data["transcript"] = url
                elif "rec" in text and url:
                    doc_data["rec"] = url

            if doc_data:
                if date not in result:
                    result[date] = []

                result[date].append(doc_data)

        return result

class WebScrapeService:
    def __init__(self, repository=None):
        self.repository = repository
        self.scraper = WebScraper()
    
    def scrape_url(self, request: WebScrapeRequest) -> WebScrapeData:
        try:
            if request is None or request.url is None:
                raise ValueError("Request and URL cannot be None")
            
            scrape_data = self.scraper.scrape(request.url)
            
            
            if self.repository:
                self.repository.save(scrape_data)
            
            return scrape_data
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error in scraping service: {str(e)}")
