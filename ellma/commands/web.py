"""
ELLMa Web Commands - Web Interaction and Scraping

This module provides web-related commands for HTTP requests, web scraping,
content extraction, and web automation tasks.
"""

import re
import time
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ellma.commands.base import BaseCommand, validate_args, log_execution, timeout
from ellma.utils.logger import get_logger
from ellma.utils.error_logger import log_command_error

logger = get_logger(__name__)

# Optional dependencies with fallbacks
try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    HAS_SELENIUM = False  # Disabled by default for simplicity
except ImportError:
    HAS_SELENIUM = False


class WebCommands(BaseCommand):
    """
    Web Commands Module

    Provides comprehensive web interaction capabilities including:
    - HTTP requests (GET, POST, PUT, DELETE)
    - Web scraping and content extraction
    - Link analysis and validation
    - Basic web automation
    - API interactions
    """

    def __init__(self, agent):
        """Initialize Web Commands"""
        super().__init__(agent)
        self.name = "web"
        self.description = "Web interaction and scraping commands"

        # Setup HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Default headers
        self.session.headers.update({
            'User-Agent': 'ELLMa-Agent/1.0 (Web Command Module)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # Request cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    @validate_args(str)
    @log_execution
    @timeout(30)
    def get(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform HTTP GET request

        Args:
            url: Target URL
            headers: Optional custom headers
            params: Optional query parameters

        Returns:
            Response data including status, headers, and content
        """
        cache_key = f"GET:{url}:{json.dumps(params, sort_keys=True)}"

        # Check cache
        if cache_key in self._cache:
            cached_response, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Returning cached response for {url}")
                return cached_response

        try:
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
                allow_redirects=True
            )

            result = {
                'url': response.url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'content_length': len(response.content),
                'encoding': response.encoding,
                'elapsed': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

            # Cache successful responses
            if response.status_code == 200:
                self._cache[cache_key] = (result, time.time())

            return result

        except requests.RequestException as e:
            logger.error(f"HTTP GET failed for {url}: {e}")
            return {
                'url': url,
                'status_code': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @validate_args(str)
    @log_execution
    def post(self, url: str, data: Optional[Union[Dict, str]] = None,
             json_data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform HTTP POST request

        Args:
            url: Target URL
            data: Form data or raw string
            json_data: JSON data
            headers: Optional custom headers

        Returns:
            Response data
        """
        try:
            response = self.session.post(
                url,
                data=data,
                json=json_data,
                headers=headers,
                timeout=30
            )

            return {
                'url': response.url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'elapsed': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

        except requests.RequestException as e:
            logger.error(f"HTTP POST failed for {url}: {e}")
            return {
                'url': url,
                'status_code': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @log_execution
    def read(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Read and extract content from a web page

        Usage:
            web.read example.com
            web.read example.com extract_links true
            web.read https://example.com extract_text true extract_links true

        Args:
            args: Positional arguments where the first is the URL
            kwargs: Additional parameters (extract_text, extract_links)

        Returns:
            Dict[str, Any]: Dictionary containing extracted content and metadata
        """
        # Parse arguments
        url = None
        extract_text = True
        extract_links = False

        # First argument is the URL
        if args and isinstance(args[0], str):
            url = args[0]
        elif 'url' in kwargs:
            url = kwargs['url']
        
        if not url:
            raise ValueError("URL is required as the first argument")

        # Parse boolean flags from kwargs or remaining args
        if 'extract_text' in kwargs:
            extract_text = self._parse_bool(kwargs['extract_text'])
        elif 'extract_text' in [a.lower() for a in args[1:]]:
            idx = [a.lower() for a in args].index('extract_text') + 1
            if idx < len(args):
                extract_text = self._parse_bool(args[idx])

        if 'extract_links' in kwargs:
            extract_links = self._parse_bool(kwargs['extract_links'])
        elif 'extract_links' in [a.lower() for a in args[1:]]:
            idx = [a.lower() for a in args].index('extract_links') + 1
            if idx < len(args):
                extract_links = self._parse_bool(args[idx])

        # Add https:// if no scheme is provided
        original_url = url
        scheme_added = False
        
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            scheme_added = True
            logger.info(f"No scheme provided, using https:// - Full URL: {url}")
        
        # Get the page
        response_data = None
        try:
            response_data = self.get(url)
        except requests.exceptions.MissingSchema as e:
            # If https:// fails, try with http://
            if url.startswith('https://'):
                http_url = url.replace('https://', 'http://', 1)
                logger.info(f"HTTPS failed, trying HTTP - URL: {http_url}")
                try:
                    response_data = self.get(http_url)
                except Exception as http_error:
                    # Log both errors
                    log_command_error(
                        command=f"web.read('{original_url}')",
                        error=e,
                        context={
                            'original_url': original_url,
                            'modified_url': url,
                            'scheme_added': scheme_added,
                            'error_type': 'MissingSchema',
                            'http_fallback_attempted': True,
                            'http_fallback_error': str(http_error)
                        }
                    )
                    raise http_error from e
            else:
                # Log the original error if no fallback was attempted
                log_command_error(
                    command=f"web.read('{original_url}')",
                    error=e,
                    context={
                        'original_url': original_url,
                        'modified_url': url,
                        'scheme_added': scheme_added,
                        'error_type': 'MissingSchema',
                        'http_fallback_attempted': False
                    }
                )
                raise e

        if response_data.get('status_code') != 200:
            return response_data

        html_content = response_data['content']
        result = {
            'url': url,
            'title': '',
            'text': '',
            'links': [],
            'images': [],
            'metadata': {},
            'word_count': 0,
            'language': 'en',
            'timestamp': datetime.now().isoformat()
        }

        if not HAS_BS4:
            # Fallback without BeautifulSoup
            result['text'] = self._extract_text_simple(html_content)
            result['word_count'] = len(result['text'].split())
            return result

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                result['title'] = title_tag.get_text().strip()

            # Extract metadata
            result['metadata'] = self._extract_metadata(soup)

            # Extract text content
            if extract_text:
                result['text'] = self._extract_clean_text(soup)
                result['word_count'] = len(result['text'].split())

            # Extract links
            if extract_links:
                result['links'] = self._extract_links(soup, url)

            # Extract images
            result['images'] = self._extract_images(soup, url)

            # Detect language
            result['language'] = self._detect_language(soup)

        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            result['error'] = str(e)

        return result

    @validate_args(str, str)
    @log_execution
    def search(self, query: str, search_engine: str = "duckduckgo", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform web search

        Args:
            query: Search query
            search_engine: Search engine to use
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if search_engine.lower() == "duckduckgo":
            return self._search_duckduckgo(query, limit)
        else:
            raise ValueError(f"Unsupported search engine: {search_engine}")

    @validate_args(str)
    @log_execution
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate URL accessibility and get basic info

        Args:
            url: URL to validate

        Returns:
            Validation results
        """
        result = {
            'url': url,
            'valid': False,
            'accessible': False,
            'status_code': 0,
            'response_time': 0,
            'ssl_valid': False,
            'redirects': 0,
            'final_url': url,
            'errors': []
        }

        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                result['errors'].append("Invalid URL format")
                return result
            result['valid'] = True
        except Exception as e:
            result['errors'].append(f"URL parsing error: {e}")
            return result

        # Check accessibility
        try:
            start_time = time.time()
            response = self.session.head(url, timeout=10, allow_redirects=True)
            result['response_time'] = time.time() - start_time
            result['status_code'] = response.status_code
            result['accessible'] = response.status_code < 400
            result['final_url'] = response.url
            result['redirects'] = len(response.history)

            # Check SSL for HTTPS URLs
            if url.startswith('https://'):
                result['ssl_valid'] = True  # If we got here, SSL is working

        except requests.exceptions.SSLError as e:
            result['errors'].append(f"SSL error: {e}")
        except requests.exceptions.RequestException as e:
            result['errors'].append(f"Request error: {e}")
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")

        return result

    @validate_args(str)
    @log_execution
    def analyze_links(self, url: str) -> Dict[str, Any]:
        """
        Analyze all links on a webpage

        Args:
            url: Target URL

        Returns:
            Link analysis results
        """
        page_data = self.read(url, extract_links=True)

        if 'error' in page_data:
            return page_data

        links = page_data.get('links', [])

        analysis = {
            'url': url,
            'total_links': len(links),
            'internal_links': 0,
            'external_links': 0,
            'broken_links': 0,
            'email_links': 0,
            'phone_links': 0,
            'social_links': 0,
            'domains': set(),
            'link_details': [],
            'timestamp': datetime.now().isoformat()
        }

        base_domain = urlparse(url).netloc
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com']

        for link in links:
            link_url = link.get('url', '')
            link_domain = urlparse(link_url).netloc

            analysis['link_details'].append(link)

            # Categorize links
            if link_url.startswith('mailto:'):
                analysis['email_links'] += 1
            elif link_url.startswith('tel:'):
                analysis['phone_links'] += 1
            elif link_domain == base_domain:
                analysis['internal_links'] += 1
            else:
                analysis['external_links'] += 1
                analysis['domains'].add(link_domain)

                # Check for social media links
                if any(social in link_domain for social in social_domains):
                    analysis['social_links'] += 1

        # Convert set to list for JSON serialization
        analysis['domains'] = list(analysis['domains'])

        return analysis

    @log_execution
    def monitor_changes(self, url: str, check_interval: int = 300, max_checks: int = 10) -> List[Dict[str, Any]]:
        """
        Monitor a webpage for changes

        Args:
            url: URL to monitor
            check_interval: Check interval in seconds
            max_checks: Maximum number of checks

        Returns:
            List of change events
        """
        changes = []
        previous_content = None

        for check in range(max_checks):
            try:
                current_data = self.read(url, extract_text=True)
                current_content = current_data.get('text', '')
                current_hash = hash(current_content)

                if previous_content is not None and current_hash != hash(previous_content):
                    change_event = {
                        'timestamp': datetime.now().isoformat(),
                        'check_number': check + 1,
                        'url': url,
                        'change_detected': True,
                        'content_length_before': len(previous_content),
                        'content_length_after': len(current_content),
                        'similarity': self._calculate_similarity(previous_content, current_content)
                    }
                    changes.append(change_event)
                    logger.info(f"Change detected on {url} at check {check + 1}")

                previous_content = current_content

                if check < max_checks - 1:
                    time.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error monitoring {url}: {e}")
                break

        return changes

    # Helper methods

    def _parse_bool(self, value) -> bool:
        """Parse boolean values from various string representations"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on', 't')
        return bool(value)

    def _extract_text_simple(self, html: str) -> str:
        """Simple text extraction without BeautifulSoup"""
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_clean_text(self, soup) -> str:
        """Extract clean text content using BeautifulSoup"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()

        # Get text and clean it up
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_metadata(self, soup) -> Dict[str, str]:
        """Extract metadata from HTML"""
        metadata = {}

        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[name] = content

        # Common metadata
        if soup.find('meta', attrs={'name': 'description'}):
            metadata['description'] = soup.find('meta', attrs={'name': 'description'})['content']

        if soup.find('meta', attrs={'name': 'keywords'}):
            metadata['keywords'] = soup.find('meta', attrs={'name': 'keywords'})['content']

        return metadata

    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from HTML"""
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            links.append({
                'url': absolute_url,
                'text': link.get_text().strip(),
                'title': link.get('title', ''),
                'rel': link.get('rel', [])
            })

        return links

    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images from HTML"""
        images = []

        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_url = urljoin(base_url, src)

            images.append({
                'url': absolute_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })

        return images

    def _detect_language(self, soup) -> str:
        """Detect page language"""
        # Check html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']

        # Check meta tag
        lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_meta and lang_meta.get('content'):
            return lang_meta['content']

        return 'en'  # Default to English

    def _search_duckduckgo(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        # Note: This is a simplified implementation
        # In practice, you'd want to use official APIs or more robust scraping

        search_url = "https://duckduckgo.com/html/"
        params = {'q': query}

        try:
            response_data = self.get(search_url, params=params)

            if response_data.get('status_code') != 200:
                return []

            if not HAS_BS4:
                return [{'error': 'BeautifulSoup required for search functionality'}]

            soup = BeautifulSoup(response_data['content'], 'html.parser')
            results = []

            # Extract search results (this is simplified and may need adjustment)
            for result in soup.find_all('div', class_='result', limit=limit):
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('div', class_='result__snippet')

                if title_elem:
                    results.append({
                        'title': title_elem.get_text().strip(),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text().strip() if snippet_elem else ''
                    })

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [{'error': str(e)}]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple similarity based on common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0