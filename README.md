# YouTube Shorts Content Engine 🚀

A comprehensive system for discovering, creating, and scaling profitable YouTube Shorts content using the data-driven "Zoink & Twist Method" - find what's working and make it better.

## Overview

This toolkit helps you build and scale YouTube Shorts channels with minimal investment by:

1. **Discovering Viral-Worthy Content**: Automated tools find trending topics
2. **Creating Optimized Scripts**: Generate high-retention scripts with hooks and pattern interrupts

### Content Discovery Pipeline

The `reddit_scraper.py` module finds high-potential content from Reddit:
- Scrapes viral and trending content from specified subreddits
- Filters content based on engagement metrics
- Works without requiring Reddit API access (pure web scraping)
- Identifies storytelling content with high viral potential

```bash
python shorts_workflow.py --action scrape --subreddits AskReddit TIFU AmItheAsshole --time week
```

### Script Generator

The `reddit_to_shorts.py` module transforms content into optimized scripts:
- Creates scripts with attention-grabbing hooks
- Adds pattern interrupts for better retention
- Structures content for maximum engagement
- Scores scripts by viral potential (0-20 scale)

```bash
python shorts_workflow.py --action generate --max 10
```

### Full Pipeline Workflow

The `shorts_workflow.py` orchestrates the entire process:
- Content discovery → Script generation → Production preparation
- Keyword-based content search
- Performance tracking and analytics

```bash
python shorts_workflow.py --action pipeline --keywords shocking unexpected viral
```

## Requirements

- Python 3.7+
- Required packages:
  ```
  pandas
  requests
  beautifulsoup4
  nltk
  ```

Install with: `pip install pandas requests beautifulsoup4 nltk`

## Quick Start

1. Clone this repository to your local machine
2. Create the required directories:
   ```bash
   mkdir -p config data/reddit_content data/shorts_scripts data/analytics
   ```
3. Generate default configuration files:
   ```bash
   python reddit_scraper.py
   python reddit_to_shorts.py
   ```
4. Run your first pipeline:
   ```bash
   python shorts_workflow.py --action pipeline
   ```



**Happy content creating!** 🎬