# Reddit to YouTube Shorts Pipeline 🚀

This set of Python scripts implements an automated content discovery and generation pipeline for creating YouTube Shorts content using the **"Zoink & Twist Method"** - finding what's working and making it better.

## Overview

The system includes:

1. **Reddit Scraper** - Finds viral and trending content on Reddit
2. **Script Generator** - Converts Reddit threads into optimized YouTube Shorts scripts
3. **Pipeline Workflow** - Orchestrates the entire process from discovery to production

These tools will help you discover viral-worthy content, streamline your production workflow, and scale your YouTube Shorts channels using data-driven content creation.

## Features

- 🔍 **Smart Content Discovery** - Finds high-potential content from Reddit
- 📝 **Script Generation** - Creates optimized scripts with hooks, pattern interrupts, and CTAs
- 🧠 **Virality Scoring** - Uses algorithms to predict which content will perform best
- 📊 **Content Tracking** - Maintains a database of content ideas and performance
- 🔄 **Full Pipeline** - End-to-end workflow from discovery to production-ready scripts

## Requirements

- Python 3.7+
- Required packages:
  ```
  pandas
  praw
  requests
  beautifulsoup4
  nltk
  ```

Install with: `pip install pandas praw requests beautifulsoup4 nltk`

## Quick Start

1. Clone or download these scripts to your project
2. Create a `config` directory if it doesn't exist
3. Run any of the scripts to generate default configuration files

### For Reddit API Access (Optional)

1. Create a Reddit account
2. Go to https://www.reddit.com/prefs/apps and create a new app
3. Select "script" option
4. Note your client ID and client secret
5. Edit `config/reddit_config.json` and update with your credentials:
   ```json
   {
     "use_api": true,
     "client_id": "YOUR_CLIENT_ID",
     "client_secret": "YOUR_CLIENT_SECRET",
     "user_agent": "YouTubeShortsContentFinder/1.0 by YourUsername"
   }
   ```

## Basic Usage

### Scrape Reddit for Content

```bash
python shorts_workflow.py --action scrape --subreddits AskReddit TIFU AmItheAsshole --time week
```

### Generate Scripts from Latest Content

```bash
python shorts_workflow.py --action generate --max 10
```

### Run the Full Pipeline

```bash
python shorts_workflow.py --action pipeline --keywords shocking unexpected viral
```

## Advanced Usage

### Using the RedditScraper Directly

```python
from reddit_scraper import RedditScraper

# Initialize scraper
scraper = RedditScraper()

# Scrape specific subreddits
threads_df = scraper.scrape_subreddits(["relationship_advice", "TIFU"], "month")

# Find highly viral threads
viral_df = scraper.get_viral_threads(min_score=5000)

# Find storytelling threads
story_df = scraper.find_storytelling_threads()
```

### Using the Script Generator Directly

```python
from reddit_to_shorts import RedditToShortsConverter

# Initialize converter
converter = RedditToShortsConverter()

# Generate scripts from a specific file
scripts = converter.generate_scripts_from_file("data/reddit_content/reddit_threads_20250324.json", max_scripts=5)

# Process an entire directory
all_scripts = converter.batch_generate_from_directory("data/reddit_content", max_per_file=3)
```

## File Structure

```
youtube-shorts-system/
├── reddit_scraper.py          - Reddit scraping functionality
├── reddit_to_shorts.py        - Script generation functionality
├── shorts_workflow.py         - Full pipeline workflow
├── config/                    - Configuration files
│   ├── reddit_config.json     - Reddit scraper settings 
│   ├── shorts_config.json     - Script generator settings
│   └── workflow_config.json   - Workflow orchestration settings
├── data/                      - Data storage
│   ├── reddit_content/        - Scraped Reddit data
│   ├── shorts_scripts/        - Generated scripts
│   └── analytics/             - Performance tracking data
```

## Configuration Options

### `reddit_config.json`

- `use_api`: Set to `true` to use Reddit API, `false` for web scraping
- `subreddits`: Default subreddits to scrape
- `minimum_score`: Minimum upvotes to keep a thread
- `time_filter`: Time period to look at ("day", "week", "month", etc.)

### `shorts_config.json`

- `hook_templates`: Templates for script hooks
- `pattern_interrupts`: Phrases to use for pattern interrupts
- `call_to_actions`: Call-to-action templates
- `max_script_length`: Maximum character length for scripts

### `workflow_config.json`

- `viral_score_threshold`: Minimum score to consider a script high-potential
- `top_subreddits`: Default subreddits for the pipeline
- `prioritize_storytelling`: Whether to focus on story-based content

## Best Practices

1. **Start with storytelling subreddits** for the best viral potential
2. **Run the pipeline daily** to catch trending content early
3. **Focus on scripts with virality scores >12** for best results
4. **Track performance of published content** back to your database
5. **Review and refine scripts** before production - AI is a tool, not a replacement

## How It Works

### Content Discovery

The system scrapes Reddit either via the official API or with a web scraping fallback method to find content that's already proven to be engaging.

### Script Generation

Each Reddit thread is analyzed for:
- Topic and structure
- Emotional impact
- Storytelling potential
- Virality indicators

Then transformed into a structured script with:
- Attention-grabbing hook
- Narrative content
- Pattern interrupt
- Conclusion
- Call to action

### Content Scoring

Each script is scored on a 0-20 scale based on:
- Original engagement metrics (upvotes, comments)
- Content characteristics (length, emotion, hooks)
- Predicted viewer retention

## Integration with Your "Zoink & Twist Method"

This system automates the discovery phase of your "Zoink & Twist Method" by:

1. Finding content that's already proven viral
2. Structuring it optimally for YouTube Shorts
3. Adding your own twist through hooks and pattern interrupts
4. Scoring potential performance before you invest production time

## Extending the System

You can extend this system by:

1. Adding automatic content categorization
2. Implementing trend detection across multiple sources
3. Training a machine learning model on your channel's past performance
4. Connecting with video editing APIs for full automation

## Legal Considerations

Always rework and transform content, don't copy directly. This system is meant to help you find ideas, not plagiarize content. The "Zoink & Twist Method" is about inspiration and improvement, not copying.

## Contributing

Feel free to improve these scripts or adapt them to your specific needs. Consider integrating them with other components in your YouTube Shorts Growth Engine project.

---

Remember, these tools are meant to enhance your content creation process, not replace your creativity. The most successful channels will use these insights along with their unique perspective and quality production.

**Happy content creating!** 🎬