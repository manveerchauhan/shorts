"""
Reddit Thread Scraper for YouTube Shorts Content Generation
-----------------------------------------------------------
This module provides functionality to scrape Reddit threads for content that can be 
transformed into YouTube Shorts using the "Zoink & Twist Method".

Features:
- Search for trending threads in specific subreddits
- Extract thread content, comments, and metadata
- Filter content based on engagement metrics
- Save results in structured format for content pipeline
- Pure web scraping approach (no API required)
"""

import pandas as pd
import datetime
import os
import json
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
import random
from urllib.parse import urljoin
import http.cookiejar


class RedditScraper:
    """Main class for scraping Reddit content for YouTube Shorts."""
    
    def __init__(self, config_path: str = "config/reddit_config.json"):
        """
        Initialize the Reddit scraper with configuration.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config = self._load_config(config_path)
        # Force use_api to False as we're removing API dependency
        self.config["use_api"] = False
        self.api_enabled = False
        
        # Create a session to maintain cookies
        self.session = requests.Session()
        self.session.cookies = http.cookiejar.CookieJar()
        
        # Try to load existing cookies if available
        self._load_cookies()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config["output_directory"], exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Force web scraping regardless of config
                config["use_api"] = False
                return config
        except FileNotFoundError:
            # Return default configuration with enhanced anti-detection
            return {
                "use_api": False,
                "subreddits": ["MaliciousCompliance", "pettyrevenge", "TIFU", "AmItheAsshole"],
                "minimum_score": 300,
                "minimum_comments": 15,
                "time_filter": "month",
                "limit": 25,
                "output_directory": "data/reddit_content",
                "use_old_reddit": True,  # Default to old Reddit which is easier to scrape
                "request_delay": [8, 15],  # More conservative delays
                "debug": True,
                "cookies_file": "reddit_cookies.json",
                "use_browser_headers": True
            }
    
    def _load_cookies(self):
        """Load cookies from file if available."""
        cookies_file = self.config.get("cookies_file", "reddit_cookies.json")
        try:
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], 
                                              domain=cookie['domain'])
                    if self.config.get("debug", False):
                        print(f"Loaded {len(cookies)} cookies from {cookies_file}")
        except Exception as e:
            if self.config.get("debug", False):
                print(f"Error loading cookies: {e}")
    
    def _save_cookies(self):
        """Save cookies to file for future sessions."""
        cookies_file = self.config.get("cookies_file", "reddit_cookies.json")
        try:
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                })
            
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=4)
                
            if self.config.get("debug", False):
                print(f"Saved {len(cookies)} cookies to {cookies_file}")
        except Exception as e:
            if self.config.get("debug", False):
                print(f"Error saving cookies: {e}")
    
    def _get_random_user_agent(self) -> str:
        """Return a random realistic user agent."""
        user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38",
            
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0"
        ]
        return random.choice(user_agents)
    
    def _get_browser_headers(self) -> Dict[str, str]:
        """Get realistic browser headers to avoid detection."""
        user_agent = self._get_random_user_agent()
        language = random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9,en-US;q=0.8", "en;q=0.9,en-US;q=0.8"])
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        
        headers = {
            "User-Agent": user_agent,
            "Accept": accept,
            "Accept-Language": language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "DNT": "1",  # Do Not Track
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-CH-UA": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"92\"",
            "Sec-CH-UA-Mobile": "?0",
            "Referer": "https://www.google.com/"
        }
        return headers
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Make a request to Reddit with enhanced anti-detection measures.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        headers = self._get_browser_headers() if self.config.get("use_browser_headers", True) else {
            "User-Agent": self._get_random_user_agent()
        }
        
        for attempt in range(max_retries):
            try:
                # Add random delay between requests
                if attempt > 0:
                    delay = random.uniform(self.config.get("request_delay", [8, 15])[0], 
                                         self.config.get("request_delay", [8, 15])[1])
                    if self.config.get("debug", False):
                        print(f"Retry attempt {attempt+1}. Waiting {delay:.2f} seconds...")
                    time.sleep(delay)
                
                # Make the request
                response = self.session.get(url, headers=headers, timeout=20)
                
                # Save cookies for future requests
                self._save_cookies()
                
                # Check for successful response
                if response.status_code == 200:
                    # Debug: save the HTML to check what we're getting
                    if self.config.get("debug", False):
                        with open("last_response.html", "w", encoding="utf-8") as f:
                            f.write(response.text)
                    
                    # Parse the page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Check for Reddit's "Too Many Requests" page or heavy load
                    if "reddit.com/static/heavy-load" in response.url:
                        print(f"Reddit is under heavy load or rate limiting. Retrying in 20-30 seconds...")
                        time.sleep(random.uniform(20, 30))
                        continue
                    
                    # Get the page title
                    title = soup.title.text if soup.title else "No title"
                    
                    # Check for captcha or login page
                    if any(term in title.lower() for term in ["captcha", "human?", "verify", "log in", "sign in"]):
                        print(f"Detected captcha or login page: '{title}'. Waiting longer...")
                        # Wait significantly longer
                        time.sleep(random.uniform(30, 60))
                        continue
                    
                    # Check if we got a Reddit page - FIXED LOGIC HERE
                    # Detection for old.reddit.com pages which have titles like "top scoring links : subreddit"
                    is_reddit_page = (
                        "reddit" in title.lower() or 
                        " : " in title or  # Old Reddit format: "top scoring links : subreddit"
                        any(sub.lower() in title.lower() for sub in self.config["subreddits"])
                    )
                    
                    if is_reddit_page:
                        if self.config.get("debug", False):
                            print(f"Successfully got Reddit page with title: '{title}'")
                        
                        # Check if we have posts on the page
                        if self.config.get("use_old_reddit", True):
                            posts = soup.find_all('div', class_='thing')
                            if posts:
                                print(f"Found {len(posts)} posts on the page")
                            else:
                                print("Warning: No posts found on the page")
                        
                        return soup
                    else:
                        print(f"Received a non-Reddit page with title: '{title}'")
                        # Try a longer delay
                        time.sleep(random.uniform(15, 25))
                else:
                    print(f"Request failed with status code: {response.status_code}")
                    
            except Exception as e:
                print(f"Error during request: {e}")
            
            # Exponential backoff for retries
            wait_time = (2 ** attempt) + random.uniform(5, 15)
            if self.config.get("debug", False):
                print(f"Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        print(f"Failed to retrieve {url} after {max_retries} attempts")
        return None
    
    def scrape_subreddits(self, 
                         subreddits: Optional[List[str]] = None, 
                         time_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Scrape top threads from specified subreddits.
        
        Args:
            subreddits: List of subreddit names to scrape
            time_filter: Time filter ('day', 'week', 'month', 'year', 'all')
            
        Returns:
            DataFrame containing thread data
        """
        subreddits = subreddits or self.config["subreddits"]
        time_filter = time_filter or self.config["time_filter"]
        
        all_threads = []
        
        for subreddit_name in subreddits:
            print(f"Scraping r/{subreddit_name}...")
            
            threads = self._scrape_without_api(subreddit_name, time_filter)
            all_threads.extend(threads)
            
            # Sleep to avoid hitting rate limits
            time.sleep(random.uniform(5, 10))
        
        # Convert to DataFrame
        if all_threads:
            df = pd.DataFrame(all_threads)
            
            # Apply filters
            df = self._filter_threads(df)
            
            # Save the results
            self._save_results(df)
            
            return df
        else:
            print("No threads were found. Try adjusting your minimum thresholds or checking different subreddits.")
            return pd.DataFrame()
    
    def _scrape_without_api(self, subreddit_name: str, time_filter: str) -> List[Dict[str, Any]]:
        """
        Scrape subreddit without using the Reddit API.
        
        Args:
            subreddit_name: Subreddit name to scrape
            time_filter: Time filter to use
            
        Returns:
            List of thread dictionaries
        """
        # Determine the URL based on old/new Reddit preference
        base_url = "https://old.reddit.com" if self.config.get("use_old_reddit", True) else "https://www.reddit.com"
        url = f"{base_url}/r/{subreddit_name}/top/?t={time_filter}"
        
        if self.config.get("debug", False):
            print(f"Requesting URL: {url}")
        
        soup = self._make_request(url)
        if not soup:
            print(f"Failed to retrieve content from r/{subreddit_name}")
            return []
        
        threads = []
        
        try:
            # Different parsing strategies based on old vs new Reddit
            if self.config.get("use_old_reddit", True):
                threads = self._parse_old_reddit(soup, subreddit_name)
            else:
                threads = self._parse_new_reddit(soup, subreddit_name)
            
            # Fetch thread details for threads that meet the minimum score
            for i, thread in enumerate(threads):
                if thread["score"] >= self.config["minimum_score"]:
                    # Add a longer delay between fetching thread details
                    if i > 0:
                        time.sleep(random.uniform(5, 10))
                    thread = self._fetch_thread_details(thread)
            
            if self.config.get("debug", False):
                print(f"Found {len(threads)} threads in r/{subreddit_name}")
                
        except Exception as e:
            print(f"Error parsing r/{subreddit_name}: {e}")
            if self.config.get("debug", False):
                import traceback
                traceback.print_exc()
        
        return threads
    
    def _parse_old_reddit(self, soup: BeautifulSoup, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Parse threads from old Reddit interface.
        
        Args:
            soup: BeautifulSoup object of the subreddit page
            subreddit_name: Name of the subreddit
            
        Returns:
            List of thread dictionaries
        """
        threads = []
        
        # Old Reddit has a simpler structure with clear 'thing' class for posts
        posts = soup.find_all('div', class_='thing')
        
        for post in posts:
            try:
                # Skip if this is a sticky, ad, or announcement
                if 'stickied' in post.get('class', []) or 'promoted' in post.get('class', []):
                    continue
                
                # Extract post ID (format: t3_postid)
                post_id = post.get('id', '').split('_')[-1]
                
                # Find the title
                title_element = post.find('a', class_='title')
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # Get score
                score_element = post.find('div', class_='score')
                score = 0
                if score_element:
                    score_text = score_element.get('title', '0')
                    try:
                        score = int(score_text)
                    except ValueError:
                        # Try to parse from visible text
                        score_text = score_element.text.strip().lower()
                        if 'k' in score_text:
                            try:
                                score = int(float(score_text.replace('k', '')) * 1000)
                            except ValueError:
                                score = self.config["minimum_score"]
                        else:
                            try:
                                score = int(re.sub(r'[^\d]', '', score_text))
                            except ValueError:
                                score = self.config["minimum_score"]
                
                # Get permalink
                permalink = title_element.get('href') if title_element else None
                if permalink and not permalink.startswith('http'):
                    permalink = f"https://www.reddit.com{permalink}" if permalink.startswith('/') else f"https://www.reddit.com/{permalink}"
                
                # Create thread data
                if permalink:
                    thread_data = {
                        "id": post_id,
                        "title": title,
                        "subreddit": subreddit_name,
                        "score": score,
                        "num_comments": 0,  # Will update when fetching details
                        "created_utc": datetime.datetime.now(),  # Placeholder
                        "permalink": permalink,
                        "url": permalink,
                        "selftext": "",  # Will be populated in fetch_thread_details
                        "top_comments": []  # Will be populated in fetch_thread_details
                    }
                    
                    threads.append(thread_data)
                
            except Exception as e:
                if self.config.get("debug", False):
                    print(f"Error parsing post: {e}")
                continue
        
        return threads
    
    def _parse_new_reddit(self, soup: BeautifulSoup, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Parse threads from new Reddit interface.
        
        Args:
            soup: BeautifulSoup object of the subreddit page
            subreddit_name: Name of the subreddit
            
        Returns:
            List of thread dictionaries
        """
        threads = []
        
        # Look for posts - they typically have post_ in the id or are in <div> with post classes
        # We'll try multiple selector approaches
        post_elements = []
        
        # Approach 1: Find by ID pattern
        post_elements = soup.find_all(lambda tag: tag.name == 'div' and 
                                     tag.get('id') and 
                                     tag['id'].startswith(('t3_', 'post_')))
        
        # Approach 2: Find by class containing "Post"
        if not post_elements:
            post_elements = soup.find_all('div', class_=lambda c: c and ('Post' in c or 'post' in c))
        
        # Approach 3: Find article elements (new Reddit sometimes uses these)
        if not post_elements:
            post_elements = soup.find_all('article')
            
        # Approach 4: Find shreddit-post elements (another format Reddit uses)
        if not post_elements:
            post_elements = soup.find_all(lambda tag: tag.name and 'shreddit-post' in tag.name)
        
        # If we still don't have posts, try looking for any links to reddit posts
        if not post_elements:
            all_links = soup.find_all('a', href=lambda h: h and '/comments/' in h)
            processed_links = set()
            
            for link in all_links:
                href = link.get('href')
                if href and '/comments/' in href and href not in processed_links:
                    processed_links.add(href)
                    
                    # Extract info from the link
                    title = link.text.strip()
                    if not title:
                        title_element = link.find('h3') or link.find('h2') or link.find('h1')
                        if title_element:
                            title = title_element.text.strip()
                    
                    # Only add if we have a title
                    if title and len(title) > 5:
                        full_url = href if href.startswith('http') else urljoin('https://www.reddit.com', href)
                        
                        # Try to extract post ID from URL
                        post_id_match = re.search(r'/comments/([a-z0-9]+)/', full_url)
                        post_id = post_id_match.group(1) if post_id_match else f"unknown_{len(threads)}"
                        
                        threads.append({
                            "id": post_id,
                            "title": title,
                            "subreddit": subreddit_name,
                            "score": self.config["minimum_score"],  # We'll update this when we fetch details
                            "num_comments": 0,  # Will update when fetching details
                            "created_utc": datetime.datetime.now(),  # Placeholder
                            "permalink": full_url,
                            "url": full_url,
                            "selftext": "",  # Will be populated in fetch_thread_details
                            "top_comments": []  # Will be populated in fetch_thread_details
                        })
        
        # Process post elements into thread data
        for post in post_elements:
            try:
                # Extract post ID
                post_id = None
                if post.get('id'):
                    id_match = re.search(r't3_([a-z0-9]+)|post_([a-z0-9]+)', post.get('id', ''))
                    if id_match:
                        post_id = id_match.group(1) or id_match.group(2)
                
                if not post_id:
                    # Try to find ID in an attribute or child element
                    for attr in post.attrs:
                        if isinstance(post[attr], str) and re.search(r't3_[a-z0-9]+', post[attr]):
                            id_match = re.search(r't3_([a-z0-9]+)', post[attr])
                            if id_match:
                                post_id = id_match.group(1)
                                break
                
                # If we still don't have an ID, try to extract from permalink
                if not post_id:
                    permalink_element = post.find('a', href=lambda h: h and '/comments/' in h)
                    if permalink_element:
                        permalink = permalink_element.get('href', '')
                        id_match = re.search(r'/comments/([a-z0-9]+)/', permalink)
                        if id_match:
                            post_id = id_match.group(1)
                
                # Fall back to a random ID if we couldn't find one
                if not post_id:
                    post_id = f"unknown_{len(threads)}"
                
                # Find the title
                title_element = post.find('h1') or post.find('h2') or post.find('h3')
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # If title element wasn't found, try finding a link with substantial text
                if title == "Unknown Title":
                    links = post.find_all('a')
                    for link in links:
                        link_text = link.text.strip()
                        if len(link_text) > 15:  # Assuming titles are at least 15 chars
                            title = link_text
                            break
                
                # Find the score
                score = self.config["minimum_score"]  # Default to minimum score
                
                # Try multiple approaches to find score
                score_text = None
                
                # Approach 1: Look for score in a <span> with "upvote" or "score" in class
                score_element = post.find('span', class_=lambda c: c and ('upvote' in c.lower() or 'score' in c.lower()))
                if score_element:
                    score_text = score_element.text.strip()
                
                # Approach 2: Look for score in any element with "score" in its class
                if not score_text:
                    score_element = post.find(class_=lambda c: c and 'score' in c.lower())
                    if score_element:
                        score_text = score_element.text.strip()
                
                # Approach 3: Look for a string that looks like a score (e.g., "1.2k", "240")
                if not score_text:
                    score_regex = re.compile(r'(\d+(\.\d+)?[km]?)\s*(points|upvotes|votes)?', re.IGNORECASE)
                    for element in post.find_all(string=True):
                        match = score_regex.search(element)
                        if match:
                            score_text = match.group(1)
                            break
                
                # Parse the score text
                if score_text:
                    score_text = score_text.lower().replace(',', '')
                    if 'k' in score_text:
                        score = int(float(score_text.replace('k', '')) * 1000)
                    elif 'm' in score_text:
                        score = int(float(score_text.replace('m', '')) * 1000000)
                    else:
                        try:
                            score = int(re.sub(r'[^\d]', '', score_text))
                        except ValueError:
                            pass
                
                # Find the permalink
                permalink = None
                permalink_element = post.find('a', href=lambda h: h and '/comments/' in h)
                if permalink_element:
                    permalink = permalink_element.get('href', '')
                    # Make sure it's an absolute URL
                    if permalink.startswith('/'):
                        permalink = f"https://www.reddit.com{permalink}"
                
                # If we couldn't find a permalink, skip this post
                if not permalink:
                    continue
                
                # Create thread data
                thread_data = {
                    "id": post_id,
                    "title": title,
                    "subreddit": subreddit_name,
                    "score": score,
                    "num_comments": 0,  # Will update when fetching details
                    "created_utc": datetime.datetime.now(),  # Placeholder
                    "permalink": permalink,
                    "url": permalink,
                    "selftext": "",  # Will be populated in fetch_thread_details
                    "top_comments": []  # Will be populated in fetch_thread_details
                }
                
                threads.append(thread_data)
                
            except Exception as e:
                if self.config.get("debug", False):
                    print(f"Error parsing post: {e}")
                continue
        
        return threads
    
    def _fetch_thread_details(self, thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch detailed information about a thread including comments.
        
        Args:
            thread_data: Basic thread data
            
        Returns:
            Thread data with additional details
        """
        url = thread_data["permalink"]
        
        # Use old Reddit for thread details too if configured
        if self.config.get("use_old_reddit", True) and "old.reddit.com" not in url:
            url = url.replace("www.reddit.com", "old.reddit.com")
        
        if self.config.get("debug", False):
            print(f"Fetching details for thread: {thread_data['id']}")
        
        soup = self._make_request(url)
        if not soup:
            print(f"Failed to retrieve thread details for {thread_data['id']}")
            return thread_data
        
        try:
            # Extract selftext if it's a text post
            # Try multiple selectors for selftext
            selftext = ""
            
            # Approach 1: Look for elements with selftext class
            selftext_element = soup.find(class_=lambda c: c and 'selftext' in c)
            if selftext_element:
                selftext = selftext_element.text.strip()
            
            # Approach 2: Look for post content in a div with specific classes
            if not selftext:
                content_selectors = [
                    soup.find(class_=lambda c: c and ('post-content' in c or 'Post-content' in c)),
                    soup.find(class_=lambda c: c and ('post-body' in c or 'Post-body' in c)),
                    soup.find(class_=lambda c: c and ('md' in c))  # Markdown content
                ]
                
                for selector in content_selectors:
                    if selector:
                        selftext = selector.text.strip()
                        break
            
            thread_data["selftext"] = selftext
            
            # Get comment count
            comment_count = 0
            
            # Try to find comment count in various places
            comment_count_selectors = [
                soup.find(class_=lambda c: c and 'comments-count' in c),
                soup.find(string=re.compile(r'\d+\s+comments', re.IGNORECASE)),
                soup.find(string=re.compile(r'comments\s+\(\d+\)', re.IGNORECASE))
            ]
            
            for selector in comment_count_selectors:
                if selector:
                    match = re.search(r'(\d+)', selector.text)
                    if match:
                        comment_count = int(match.group(1))
                        break
            
            thread_data["num_comments"] = comment_count
            
            # Extract comments
            comments = []
            
            # Different strategies for finding comments
            comment_containers = []
            
            # Approach 1: Find elements with 'Comment' in class
            comment_containers = soup.find_all(class_=lambda c: c and 'Comment' in c)
            
            # Approach 2: Find elements with 'comment' in class
            if not comment_containers:
                comment_containers = soup.find_all(class_=lambda c: c and 'comment' in c.lower())
            
            # Approach 3: In old Reddit, comments are in elements with 'thing' and type 't1'
            if not comment_containers and self.config.get("use_old_reddit", True):
                comment_containers = soup.find_all('div', class_=lambda c: c and 'thing' in c and 't1' in c)
            
            # Collect top 10 comments
            for i, comment_element in enumerate(comment_containers[:10]):
                if i >= 10:  # Limit to top 10 comments
                    break
                
                # Skip deleted comments
                if 'deleted' in comment_element.get('class', []) or 'removed' in comment_element.get('class', []):
                    continue
                
                # Extract comment body
                body = ""
                
                # Try multiple selectors for comment body
                body_selectors = [
                    comment_element.find(class_=lambda c: c and ('md' in c)),
                    comment_element.find(class_=lambda c: c and ('body' in c or 'Body' in c)),
                    comment_element.find(class_=lambda c: c and ('content' in c or 'Content' in c))
                ]
                
                for selector in body_selectors:
                    if selector:
                        body = selector.text.strip()
                        break
                
                if not body:
                    continue  # Skip if no comment body found
                
                # Extract author
                author = "[deleted]"
                author_element = comment_element.find(class_=lambda c: c and ('author' in c))
                if author_element:
                    author = author_element.text.strip()
                
                # Determine if comment is from OP
                is_op = False
                op_indicators = [
                    comment_element.find(class_=lambda c: c and ('submitter' in c or 'op' in c.lower())),
                    comment_element.find(string='OP'),
                    author_element and 'submitter' in author_element.get('class', [])
                ]
                
                if any(op_indicators):
                    is_op = True
                
                comment_data = {
                    "comment_id": f"comment_{i}",
                    "author": author,
                    "body": body,
                    "score": 0,  # Hard to consistently extract
                    "is_op": is_op
                }
                
                comments.append(comment_data)
            
            thread_data["top_comments"] = comments
            
        except Exception as e:
            print(f"Error parsing thread details: {e}")
            if self.config.get("debug", False):
                import traceback
                traceback.print_exc()
        
        return thread_data
    
    def _filter_threads(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter threads based on engagement metrics.
        
        Args:
            df: DataFrame with thread data
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
            
        # Apply minimum score filter
        filtered_df = df[df['score'] >= self.config["minimum_score"]]
        
        # Apply minimum comments filter if we have that data
        if 'num_comments' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['num_comments'] >= self.config["minimum_comments"]]
        
        return filtered_df
    
    def _save_results(self, df: pd.DataFrame) -> None:
        """
        Save the scraped data to CSV and JSON files.
        
        Args:
            df: DataFrame with thread data
        """
        if df.empty:
            print("No data to save.")
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save basic info to CSV
        csv_path = os.path.join(self.config["output_directory"], f"reddit_threads_{timestamp}.csv")
        
        # Create a copy without complex columns for CSV
        csv_df = df.copy()
        if 'top_comments' in csv_df.columns:
            csv_df = csv_df.drop(columns=['top_comments'])
        
        csv_df.to_csv(csv_path, index=False)
        
        # Save full data to JSON
        json_path = os.path.join(self.config["output_directory"], f"reddit_threads_{timestamp}.json")
        
        # Convert to records for JSON serialization
        records = df.to_dict(orient='records')
        
        # Serialize datetime objects
        for record in records:
            for key, value in record.items():
                if isinstance(value, datetime.datetime):
                    record[key] = value.isoformat()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=4, ensure_ascii=False)
        
        print(f"Saved {len(df)} threads to:")
        print(f"- CSV: {csv_path}")
        print(f"- JSON: {json_path}")
    
    def get_viral_threads(self, min_score: int = 5000) -> pd.DataFrame:
        """
        Get highly viral threads that could be good candidates for YouTube Shorts.
        
        Args:
            min_score: Minimum score (upvotes) to consider a thread viral
            
        Returns:
            DataFrame of viral threads
        """
        subreddits = self.config["subreddits"]
        
        # Use a shorter time filter for viral content
        df = self.scrape_subreddits(subreddits, "day")
        
        # Filter for highly viral threads
        viral_df = df[df['score'] >= min_score].sort_values('score', ascending=False)
        
        return viral_df
    
    def find_storytelling_threads(self) -> pd.DataFrame:
        """
        Find threads with good storytelling potential for YouTube Shorts.
        This focuses on subreddits with personal stories.
        
        Returns:
            DataFrame of threads with storytelling potential
        """
        story_subreddits = [
            "TIFU", "AmItheAsshole", "MaliciousCompliance", 
            "relationship_advice", "ProRevenge", "pettyrevenge", 
            "LetsNotMeet", "entitledparents"
        ]
        
        return self.scrape_subreddits(story_subreddits, self.config["time_filter"])
    
    def search_keyword_threads(self, keywords: List[str]) -> pd.DataFrame:
        """
        Search for threads containing specific keywords.
        Modified to work without API by using Reddit's search page.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            DataFrame of relevant threads
        """
        all_threads = []
        
        for keyword in keywords:
            print(f"Searching for keyword: {keyword}")
            
            # Construct search URL (works with both old and new Reddit)
            base_url = "https://old.reddit.com" if self.config.get("use_old_reddit", True) else "https://www.reddit.com"
            search_url = f"{base_url}/search/?q={keyword}&sort=relevance&t={self.config['time_filter']}"
            
            soup = self._make_request(search_url)
            if not soup:
                print(f"Failed to retrieve search results for {keyword}")
                continue
            
            try:
                # Parse search results differently based on old/new Reddit
                if self.config.get("use_old_reddit", True):
                    threads = self._parse_old_reddit(soup, "search")
                else:
                    threads = self._parse_new_reddit(soup, "search")
                
                # Add keyword to thread data
                for thread in threads:
                    thread["search_keyword"] = keyword
                    
                    # Fetch details for threads that meet minimum score
                    if thread["score"] >= self.config["minimum_score"]:
                        thread = self._fetch_thread_details(thread)
                
                all_threads.extend(threads)
                
                # Sleep between keyword searches
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                print(f"Error parsing search results for '{keyword}': {e}")
                if self.config.get("debug", False):
                    import traceback
                    traceback.print_exc()
        
        # Convert to DataFrame
        if all_threads:
            df = pd.DataFrame(all_threads)
            df = self._filter_threads(df)
            return df
        else:
            return pd.DataFrame()


def create_default_config():
    """Create default configuration file if it doesn't exist."""
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "reddit_config.json")
    
    if not os.path.exists(config_path):
        config = {
            "use_api": False,
            "subreddits": ["MaliciousCompliance", "pettyrevenge", "TIFU", "AmItheAsshole"],
            "minimum_score": 300,
            "minimum_comments": 15,
            "time_filter": "month",
            "limit": 25,
            "output_directory": "data/reddit_content",
            "use_old_reddit": True,
            "request_delay": [8, 15],
            "debug": True,
            "cookies_file": "reddit_cookies.json",
            "use_browser_headers": True
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"Created default configuration file at {config_path}")
    else:
        print(f"Configuration file already exists at {config_path}")


def main():
    """Main function to demonstrate usage."""
    # Create default config file if needed
    create_default_config()
    
    # Initialize the scraper
    scraper = RedditScraper()
    
    # Example 1: Scrape top threads from default subreddits
    print("\n=== Scraping Top Threads ===")
    threads_df = scraper.scrape_subreddits()
    print(f"Found {len(threads_df)} threads that meet criteria")
    
    # Example 2: Find viral threads
    print("\n=== Finding Viral Threads ===")
    viral_df = scraper.get_viral_threads(min_score=5000)  # Lower threshold for demo
    print(f"Found {len(viral_df)} viral threads")
    
    # Example 3: Find storytelling threads
    print("\n=== Finding Storytelling Threads ===")
    story_df = scraper.find_storytelling_threads()
    print(f"Found {len(story_df)} storytelling threads")
    
    # Example 4: Search for specific keywords
    print("\n=== Searching for Keywords ===")
    keywords = ["unbelievable", "unexpected", "shocking"]
    keyword_df = scraper.search_keyword_threads(keywords)
    print(f"Found {len(keyword_df)} threads matching keywords")


if __name__ == "__main__":
    main()