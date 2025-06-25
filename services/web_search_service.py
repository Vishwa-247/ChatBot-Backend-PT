import json
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.max_results = 5
        self.timeout = 10
        
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using DuckDuckGo Instant Answer API (free)"""
        try:
            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            data = response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('AbstractSource', 'DuckDuckGo'),
                    'snippet': data.get('AbstractText', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': 'instant_answer'
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:max_results]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '')[:100] + '...',
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'related_topic'
                    })
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def search_web_fallback(self, query: str, max_results: int = 3) -> List[Dict]:
        """Fallback web search using direct scraping"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')[:max_results]
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'url': url,
                        'source': 'web_search'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Web fallback search error: {e}")
            return []
    
    def search_weather_api(self, location: str) -> List[Dict]:
        """Specific weather search using multiple sources"""
        try:
            # Try weather-specific search
            weather_query = f"current weather {location} today temperature"
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(weather_query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Look for weather-specific results
            result_divs = soup.find_all('div', class_='result')[:5]
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    # Filter for weather-related results
                    if any(word in title.lower() or word in snippet.lower() 
                           for word in ['weather', 'temperature', 'forecast', 'climate']):
                        results.append({
                            'title': title,
                            'snippet': snippet,
                            'url': url,
                            'source': 'weather_search'
                        })
            
            return results[:3]
            
        except Exception as e:
            logger.error(f"Weather search error: {e}")
            return []
    
    def search(self, query: str, max_results: int = 5) -> Dict:
        """Main search function that tries multiple methods"""
        try:
            logger.info(f"🔍 Searching for: {query}")
            
            # Check if it's a weather query
            query_lower = query.lower()
            is_weather = any(word in query_lower for word in ['weather', 'temperature', 'forecast', 'climate'])
            
            results = []
            
            if is_weather:
                # Extract location if possible
                location = "current location"
                for city in ['hyderabad', 'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata']:
                    if city in query_lower:
                        location = city
                        break
                
                results = self.search_weather_api(location)
            
            # If no weather results or not weather query, try general search
            if not results:
                results = self.search_duckduckgo(query, max_results)
            
            # If still no results, try fallback method
            if not results:
                logger.info("Trying fallback search method...")
                results = self.search_web_fallback(query, max_results)
            
            if results:
                logger.info(f"✅ Found {len(results)} search results")
                return {
                    'success': True,
                    'query': query,
                    'results': results,
                    'timestamp': time.time(),
                    'used_agent': True  # Mark as agent response
                }
            else:
                logger.warning("No search results found")
                return {
                    'success': False,
                    'query': query,
                    'results': [],
                    'error': 'No results found',
                    'used_agent': False
                }
                
        except Exception as e:
            logger.error(f"Search service error: {e}")
            return {
                'success': False,
                'query': query,
                'results': [],
                'error': str(e),
                'used_agent': False
            }
    
    def format_search_results(self, search_data: Dict) -> str:
        """Format search results for AI consumption"""
        if not search_data.get('success') or not search_data.get('results'):
            return ""
        
        formatted_results = []
        for i, result in enumerate(search_data['results'], 1):
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', 'No description available')
            url = result.get('url', '')
            
            formatted_results.append(f"[Search Result {i}: {title}]\n{snippet}\nSource: {url}")
        
        return "\n\n".join(formatted_results)
