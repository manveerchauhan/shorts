#!/usr/bin/env python3
"""
YouTube Shorts Pipeline Workflow
--------------------------------
This script orchestrates the entire process of finding viral Reddit content,
converting it to YouTube Shorts scripts, and tracking analytics.

The workflow implements the "Zoink & Twist Method" to create high-performing
YouTube Shorts content based on proven viral patterns.

Usage:
    python shorts_workflow.py --action scrape --subreddits AskReddit TIFU --time week
    python shorts_workflow.py --action generate --max 10
    python shorts_workflow.py --action pipeline --keywords shocking viral unexpected
"""

import argparse
import os
import json
import datetime
import pandas as pd
from typing import List, Dict, Any, Optional

# Import our modules
try:
    from reddit_scraper import RedditScraper, create_default_config as create_scraper_config
    from reddit_to_shorts import RedditToShortsConverter, create_default_config as create_converter_config
except ImportError:
    print("Please ensure reddit_scraper.py and reddit_to_shorts.py are in the same directory")
    exit(1)


class ShortsWorkflow:
    """Orchestrates the full YouTube Shorts content workflow."""
    
    def __init__(self):
        """Initialize the workflow."""
        # Create directories if they don't exist
        os.makedirs("config", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/reddit_content", exist_ok=True)
        os.makedirs("data/shorts_scripts", exist_ok=True)
        os.makedirs("data/analytics", exist_ok=True)
        
        # Create default configs if they don't exist
        create_scraper_config()
        create_converter_config()
        
        # Initialize components
        self.scraper = RedditScraper()
        self.converter = RedditToShortsConverter()
        
        # Load workflow config
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load workflow configuration."""
        config_path = "config/workflow_config.json"
        
        # Default configuration
        default_config = {
            "viral_score_threshold": 12,  # Minimum virality score to consider a script good
            "tracking_file": "data/analytics/content_tracking.csv",
            "top_subreddits": ["AskReddit", "TIFU", "AmItheAsshole", "relationship_advice"],
            "content_types": ["story", "fact", "motivation"],
            "prioritize_storytelling": True,
            "auto_log_results": True
        }
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default workflow configuration at {config_path}")
            return default_config
    
    def scrape_reddit(self, subreddits: Optional[List[str]] = None, 
                    time_filter: str = "week") -> pd.DataFrame:
        """
        Scrape Reddit for content.
        
        Args:
            subreddits: List of subreddits to scrape
            time_filter: Time filter (day, week, month, year, all)
            
        Returns:
            DataFrame of scraped threads
        """
        if not subreddits:
            subreddits = self.config["top_subreddits"]
        
        print(f"Scraping Reddit for content from: {', '.join(subreddits)}")
        
        # Scrape subreddits
        df = self.scraper.scrape_subreddits(subreddits, time_filter)
        
        # If prioritizing storytelling, also scrape story-focused subreddits
        if self.config["prioritize_storytelling"]:
            story_subreddits = ["TIFU", "AmItheAsshole", "MaliciousCompliance", "ProRevenge"]
            # Only scrape subreddits we haven't already scraped
            story_subreddits = [s for s in story_subreddits if s not in subreddits]
            
            if story_subreddits:
                print(f"Also scraping storytelling subreddits: {', '.join(story_subreddits)}")
                story_df = self.scraper.scrape_subreddits(story_subreddits, time_filter)
                
                # Combine results
                if not story_df.empty:
                    df = pd.concat([df, story_df], ignore_index=True)
        
        print(f"Found {len(df)} threads that meet criteria")
        return df
    
    def search_reddit_keywords(self, keywords: List[str]) -> pd.DataFrame:
        """
        Search Reddit for specific keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            DataFrame of matching threads
        """
        if not self.scraper.api_enabled:
            print("Warning: Keyword search requires Reddit API access. Please update your config.")
            return pd.DataFrame()
        
        print(f"Searching Reddit for keywords: {', '.join(keywords)}")
        
        df = self.scraper.search_keyword_threads(keywords)
        
        print(f"Found {len(df)} threads matching keywords")
        return df
    
    def generate_scripts(self, max_scripts: int = 10) -> List[Dict[str, Any]]:
        """
        Generate YouTube Shorts scripts from the most recent Reddit data.
        
        Args:
            max_scripts: Maximum number of scripts to generate
            
        Returns:
            List of script dictionaries
        """
        # Find the most recent Reddit data file
        data_dir = "data/reddit_content"
        
        if not os.path.exists(data_dir) or not os.listdir(data_dir):
            print("No Reddit data found. Please run the scrape_reddit method first.")
            return []
        
        # Get most recent JSON file
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        if not json_files:
            print("No JSON files found. Please run the scrape_reddit method first.")
            return []
        
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(data_dir, f)))
        latest_path = os.path.join(data_dir, latest_file)
        
        print(f"Generating scripts from {latest_path}")
        
        # Generate scripts
        scripts = self.converter.generate_scripts_from_file(latest_path, max_scripts)
        
        # Filter by virality score
        good_scripts = [s for s in scripts if s["virality_score"] >= self.config["viral_score_threshold"]]
        if good_scripts:
            print(f"Generated {len(scripts)} scripts, {len(good_scripts)} with high viral potential")
        else:
            print(f"Generated {len(scripts)} scripts, but none meet the viral threshold of {self.config['viral_score_threshold']}")
        
        # Log results if enabled
        if self.config["auto_log_results"]:
            self._log_scripts(scripts)
        
        return scripts
    
    def _log_scripts(self, scripts: List[Dict[str, Any]]) -> None:
        """Log generated scripts to tracking file."""
        tracking_file = self.config["tracking_file"]
        
        # Create DataFrame from scripts
        data = []
        for script in scripts:
            row = {
                "script_id": script["id"],
                "title": script["title"],
                "content_type": script["content_type"],
                "word_count": script["word_count"],
                "character_count": script["character_count"],
                "estimated_duration": script["estimated_duration_seconds"],
                "virality_score": script["virality_score"],
                "source_subreddit": script["source"]["subreddit"],
                "source_score": script["source"]["score"],
                "source_url": script["source"]["url"],
                "generated_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "production_status": "New",
                "production_notes": "",
                "publish_date": "",
                "views": 0,
                "likes": 0,
                "comments": 0,
                "retention_rate": 0,
                "revenue": 0
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Check if tracking file exists
        if os.path.exists(tracking_file):
            # Read existing data
            existing_df = pd.read_csv(tracking_file)
            
            # Append new data
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_csv(tracking_file, index=False)
        else:
            # Create new tracking file
            df.to_csv(tracking_file, index=False)
        
        print(f"Logged {len(scripts)} scripts to {tracking_file}")
    
    def run_full_pipeline(self, keywords: Optional[List[str]] = None) -> None:
        """
        Run the full YouTube Shorts pipeline.
        
        1. Scrape Reddit for viral content
        2. If keywords provided, also search for those
        3. Generate scripts
        4. Sort and rank by virality potential
        5. Save results for production
        
        Args:
            keywords: Optional keywords to search for
        """
        print("=== Starting Full Pipeline ===")
        
        # Step 1: Scrape top subreddits
        _ = self.scrape_reddit()
        
        # Step 2: If keywords provided, also search for those
        if keywords:
            _ = self.search_reddit_keywords(keywords)
        
        # Step 3: Generate scripts from all Reddit data
        scripts = self.converter.batch_generate_from_directory("data/reddit_content", 5)
        
        # Step 4: Sort by virality score
        sorted_scripts = sorted(scripts, key=lambda x: x["virality_score"], reverse=True)
        
        # Get top scripts
        top_scripts = sorted_scripts[:10]
        
        # Step 5: Save top scripts for review
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/shorts_scripts/top_scripts_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(top_scripts, f, indent=4)
        
        # Step 6: Create production-ready TXT file
        txt_path = f"data/shorts_scripts/PRODUCTION_READY_{timestamp}.txt"
        
        with open(txt_path, 'w') as f:
            f.write("===============================================\n")
            f.write("PRODUCTION-READY YOUTUBE SHORTS SCRIPTS\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("===============================================\n\n")
            
            for i, script in enumerate(top_scripts, 1):
                f.write(f"SCRIPT #{i} - VIRALITY SCORE: {script['virality_score']}/20\n")
                f.write("===============================================\n")
                f.write(f"TITLE: {script['title']}\n")
                f.write(f"TYPE: {script['content_type']}\n")
                f.write(f"ESTIMATED DURATION: {int(script['estimated_duration_seconds'])} seconds\n")
                f.write(f"SOURCE: r/{script['source']['subreddit']} | Score: {script['source']['score']}\n")
                f.write("-----------------------------------------------\n\n")
                f.write(f"{script['script_text']}\n\n")
                f.write("-----------------------------------------------\n")
                f.write("PRODUCTION NOTES:\n")
                f.write("- Use background clips that match content emotional tone\n")
                f.write("- Ensure subtitles follow words precisely\n")
                f.write("- Consider adding pattern interrupt visual at key moment\n")
                f.write("- Keep transitions minimal, focus on content flow\n\n")
                f.write("===============================================\n\n")
        
        print(f"Saved {len(top_scripts)} top scripts to {output_path}")
        print(f"Production-ready scripts saved to {txt_path}")
        print("Full pipeline complete!")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Shorts Content Pipeline")
    parser.add_argument("--action", type=str, required=True, 
                       choices=["scrape", "generate", "pipeline"],
                       help="Action to perform")
    
    # Scrape action arguments
    parser.add_argument("--subreddits", type=str, nargs="+",
                       help="Subreddits to scrape (for scrape action)")
    parser.add_argument("--time", type=str, default="week",
                       choices=["day", "week", "month", "year", "all"],
                       help="Time filter for Reddit content (for scrape action)")
    
    # Generate action arguments
    parser.add_argument("--max", type=int, default=10,
                       help="Maximum scripts to generate (for generate action)")
    
    # Pipeline action arguments
    parser.add_argument("--keywords", type=str, nargs="+",
                       help="Keywords to search for (for pipeline action)")
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    workflow = ShortsWorkflow()
    
    if args.action == "scrape":
        workflow.scrape_reddit(args.subreddits, args.time)
    
    elif args.action == "generate":
        workflow.generate_scripts(args.max)
    
    elif args.action == "pipeline":
        workflow.run_full_pipeline(args.keywords)
    
    else:
        print(f"Unknown action: {args.action}")


if __name__ == "__main__":
    main()