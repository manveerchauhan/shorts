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
- Support both PRAW (official Reddit API) and alternative methods

Requirements:
- praw
- pandas
- requests
- beautifulsoup4
"""

import praw
import pandas as pd
import datetime
import os
import json
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re


class RedditScraper:
    """Main class for scraping Reddit content for YouTube Shorts."""
    
    def __init__(self, config_path: str = "config/reddit_config.json"):
        """
        Initialize the Reddit scraper with configuration.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config = self._load_config(config_path)
        self.api_enabled = self.config.get("use_api", True)
        
        if self.api_enabled:
            self.reddit = self._init_reddit_api()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config["output_directory"], exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration
            return {
                "use_api": False,  # Set to False to use web scraping instead of API
                "client_id": "",  # Only needed if use_api is True
                "client_secret": "",  # Only needed if use_api is True
                "user_agent": "YouTubeShortsContentFinder/1.0",
                "subreddits": ["AskReddit", "TIFU", "AmItheAsshole", "MaliciousCompliance"],
                "minimum_score": 1000,
                "minimum_comments": 50,
                "time_filter": "week",
                "limit": 25,
                "output_directory": "data/reddit_content"
            }
    
    def _init_reddit_api(self) -> praw.Reddit:
        """Initialize Reddit API using PRAW."""
        return praw.Reddit(
            client_id=self.config["client_id"],
            client_secret=self.config["client_secret"],
            user_agent=self.config["user_agent"]
        )
    
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
            
            if self.api_enabled:
                threads = self._scrape_with_api(subreddit_name, time_filter)
            else:
                threads = self._scrape_without_api(subreddit_name, time_filter)
            
            all_threads.extend(threads)
            
            # Sleep to avoid hitting rate limits
            time.sleep(2)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_threads)
        
        # Apply filters
        if not df.empty:
            df = self._filter_threads(df)
            
            # Save the results
            self._save_results(df)
        
        return df
    
    def _scrape_with_api(self, subreddit_name: str, time_filter: str) -> List[Dict[str, Any]]:
        """Scrape subreddit using the Reddit API."""
        subreddit = self.reddit.subreddit(subreddit_name)
        threads = []
        
        for submission in subreddit.top(time_filter=time_filter, limit=self.config["limit"]):
            # Get top comments
            submission.comment_sort = "top"
            submission.comments.replace_more(limit=0)  # Don't fetch additional comments
            top_comments = [
                {
                    "comment_id": comment.id,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body,
                    "score": comment.score,
                    "is_op": comment.author == submission.author if comment.author and submission.author else False
                }
                for comment in submission.comments[:10]  # Get top 10 comments
            ]
            
            thread_data = {
                "id": submission.id,
                "title": submission.title,
                "subreddit": subreddit_name,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "created_utc": datetime.datetime.fromtimestamp(submission.created_utc),
                "author": str(submission.author) if submission.author else "[deleted]",
                "is_self": submission.is_self,
                "selftext": submission.selftext if submission.is_self else "",
                "url": submission.url,
                "permalink": f"https://www.reddit.com{submission.permalink}",
                "top_comments": top_comments
            }
            
            threads.append(thread_data)
        
        return threads
    
    def _scrape_without_api(self, subreddit_name: str, time_filter: str) -> List[Dict[str, Any]]:
        """
        Scrape subreddit without using the Reddit API (web scraping).
        This is a fallback method and might break if Reddit changes its UI.
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/top/?t={time_filter}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        threads = []
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # This is a simplified version and will need updates based on Reddit's current HTML structure
            thread_elements = soup.find_all('div', class_=re.compile('thing|Post'))
            
            for element in thread_elements[:self.config["limit"]]:
                try:
                    # Extract available info (simplified)
                    thread_id = element.get('id', '').split('_')[-1]
                    title_element = element.find('h2') or element.find('h3')
                    title = title_element.text.strip() if title_element else "Unknown Title"
                    
                    score_element = element.find('div', class_=re.compile('score|votes'))
                    score = 0
                    if score_element:
                        score_text = score_element.text.strip()
                        if 'k' in score_text.lower():
                            score = int(float(score_text.lower().replace('k', '')) * 1000)
                        else:
                            score = int(score_text) if score_text.isdigit() else 0
                    
                    permalink = element.find('a', attrs={'data-click-id': 'body'})
                    permalink_url = permalink['href'] if permalink else ""
                    
                    # If we only have a relative URL, make it absolute
                    if permalink_url.startswith('/r/'):
                        permalink_url = f"https://www.reddit.com{permalink_url}"
                    
                    thread_data = {
                        "id": thread_id,
                        "title": title,
                        "subreddit": subreddit_name,
                        "score": score,
                        "upvote_ratio": 0.0,  # Not available without API
                        "num_comments": 0,    # Not available in this simplified version
                        "created_utc": datetime.datetime.now(),  # Placeholder
                        "author": "Unknown",  # Not easily available without API
                        "is_self": True,      # Assumption
                        "selftext": "",       # Would need to visit the thread to get this
                        "url": permalink_url,
                        "permalink": permalink_url,
                        "top_comments": []    # Would need to visit the thread to get comments
                    }
                    
                    # Only fetch thread details and comments if the score is high enough
                    if score >= self.config["minimum_score"]:
                        thread_data = self._fetch_thread_details(thread_data)
                    
                    threads.append(thread_data)
                except Exception as e:
                    print(f"Error parsing thread element: {e}")
            
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {e}")
        
        return threads
    
    def _fetch_thread_details(self, thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch detailed information about a thread including comments."""
        try:
            url = thread_data["permalink"]
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get self text if available
            selftext_element = soup.find('div', class_=re.compile('selftext|Post-body'))
            if selftext_element:
                thread_data["selftext"] = selftext_element.text.strip()
            
            # Get comment count
            comment_count_element = soup.find('span', string=re.compile('comments'))
            if comment_count_element:
                count_text = comment_count_element.text.strip()
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    thread_data["num_comments"] = int(count_match.group(1))
            
            # Get top comments
            comment_elements = soup.find_all('div', class_=re.compile('Comment'))
            top_comments = []
            
            for i, comment_element in enumerate(comment_elements[:10]):
                if i >= 10:  # Limit to top 10 comments
                    break
                
                body_element = comment_element.find('div', class_=re.compile('body|RichText'))
                if not body_element:
                    continue
                
                author_element = comment_element.find('a', class_=re.compile('author'))
                
                comment_data = {
                    "comment_id": f"comment_{i}",
                    "author": author_element.text.strip() if author_element else "[deleted]",
                    "body": body_element.text.strip(),
                    "score": 0,  # Difficult to reliably extract
                    "is_op": False  # Difficult to reliably determine
                }
                
                top_comments.append(comment_data)
            
            thread_data["top_comments"] = top_comments
            
        except Exception as e:
            print(f"Error fetching thread details: {e}")
        
        return thread_data
    
    def _filter_threads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter threads based on engagement metrics."""
        # Apply minimum score filter
        filtered_df = df[df['score'] >= self.config["minimum_score"]]
        
        # Apply minimum comments filter
        filtered_df = filtered_df[filtered_df['num_comments'] >= self.config["minimum_comments"]]
        
        return filtered_df
    
    def _save_results(self, df: pd.DataFrame) -> None:
        """Save the scraped data to CSV and JSON files."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save basic info to CSV
        csv_path = os.path.join(self.config["output_directory"], f"reddit_threads_{timestamp}.csv")
        # Create a copy without the complex columns for CSV
        csv_df = df.drop(columns=['top_comments'], errors='ignore')
        csv_df.to_csv(csv_path, index=False)
        
        # Save full data to JSON
        json_path = os.path.join(self.config["output_directory"], f"reddit_threads_{timestamp}.json")
        df.to_json(json_path, orient='records', date_format='iso')
        
        print(f"Saved {len(df)} threads to:")
        print(f"- CSV: {csv_path}")
        print(f"- JSON: {json_path}")
    
    def get_viral_threads(self, min_score: int = 10000) -> pd.DataFrame:
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
            "relationship_advice", "ProRevenge", "pettyrevenge"
        ]
        
        df = self.scrape_subreddits(story_subreddits, "week")
        
        # Additional filtering for storytelling potential could be added here
        # For example, text length, emotional language, etc.
        
        return df
    
    def search_keyword_threads(self, keywords: List[str]) -> pd.DataFrame:
        """
        Search for threads containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            DataFrame of relevant threads
        """
        if not self.api_enabled:
            print("Warning: Keyword search requires Reddit API access.")
            return pd.DataFrame()
        
        results = []
        
        for keyword in keywords:
            for submission in self.reddit.subreddit("all").search(
                query=keyword, 
                sort="relevance", 
                time_filter=self.config["time_filter"],
                limit=self.config["limit"]
            ):
                # Get top comments
                submission.comment_sort = "top"
                submission.comments.replace_more(limit=0)
                top_comments = [
                    {
                        "comment_id": comment.id,
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "body": comment.body,
                        "score": comment.score,
                        "is_op": comment.author == submission.author if comment.author and submission.author else False
                    }
                    for comment in submission.comments[:10]
                ]
                
                thread_data = {
                    "id": submission.id,
                    "title": submission.title,
                    "subreddit": submission.subreddit.display_name,
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.datetime.fromtimestamp(submission.created_utc),
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "is_self": submission.is_self,
                    "selftext": submission.selftext if submission.is_self else "",
                    "url": submission.url,
                    "permalink": f"https://www.reddit.com{submission.permalink}",
                    "top_comments": top_comments,
                    "search_keyword": keyword
                }
                
                results.append(thread_data)
        
        # Convert to DataFrame and filter
        df = pd.DataFrame(results)
        if not df.empty:
            df = self._filter_threads(df)
        
        return df


def create_default_config():
    """Create default configuration file if it doesn't exist."""
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "reddit_config.json")
    
    if not os.path.exists(config_path):
        config = {
            "use_api": False,  # Set to True if you have API credentials
            "client_id": "YOUR_CLIENT_ID",  # Get from Reddit developer portal
            "client_secret": "YOUR_CLIENT_SECRET",  # Get from Reddit developer portal
            "user_agent": "YouTubeShortsContentFinder/1.0 by YourUsername",
            "subreddits": ["AskReddit", "TIFU", "AmItheAsshole", "MaliciousCompliance"],
            "minimum_score": 1000,
            "minimum_comments": 50,
            "time_filter": "week",
            "limit": 25,
            "output_directory": "data/reddit_content"
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"Created default configuration file at {config_path}")
        print("Please edit this file to add your Reddit API credentials if needed.")
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
    
    # Example 4: Search for specific keywords (requires API)
    if scraper.api_enabled:
        print("\n=== Searching for Keywords ===")
        keywords = ["unbelievable", "unexpected", "shocking"]
        keyword_df = scraper.search_keyword_threads(keywords)
        print(f"Found {len(keyword_df)} threads matching keywords")


if __name__ == "__main__":
    main()