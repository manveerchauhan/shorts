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

## The "Zoink & Twist Method"

This repository implements the proven "Zoink & Twist Method" for creating successful Shorts:

1. **Find**: Discover content that's already proven to be engaging
2. **Analyze**: Identify patterns, hooks, and storytelling elements
3. **Improve**: Make it better with stronger hooks and pattern interrupts
4. **Scale**: Systematically grow from one to multiple channels

## Implementation Strategy

### Phase 1: Research & Setup (Week 1)
- Niche selection based on high-RPM topics
- Channel branding and setup
- Content analysis and pattern identification

### Phase 2: Content Production (Weeks 2-4)
- Daily posting schedule (one Short per day)
- Focus on strong hooks and high retention
- Iterate based on performance data

### Phase 3: Growth & Optimization (Months 2-3)
- Apply for YouTube Partner Program
- Implement affiliate strategies
- Optimize based on channel analytics

### Phase 4: Scaling (Months 4+)
- Maintain first channel at consistent publishing cadence
- Launch second channel once reaching $2,000/month
- Build team (editors, researchers) as income grows

## Monetization Strategies

Multiple revenue streams available:
1. **YouTube Partner Program**: Ad revenue from Shorts Fund
2. **YouTube Music Program**: Enhanced RPM by adding specific music tracks
3. **Affiliate Marketing**: Strategic product recommendations
4. **Channel Expansion**: Scale to multiple niches

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

## Content Best Practices

Based on analyzing thousands of successful Shorts:

1. **Hooks Matter**: The first 3 seconds determine success
   - Use questions, shocking statements, or unexpected claims
   - Visually show what you're talking about immediately

2. **Retention Optimization**:
   - Aim for 90%+ retention rate
   - Keep Shorts between 30-45 seconds
   - Use pattern interrupts to prevent scrolling

3. **Strategic Publishing**:
   - Start with one video per day
   - Increase frequency only after establishing momentum
   - Test different posting times to find optimal performance

4. **Analytics Focus**:
   - Swipe rate (aim for >80%)
   - Average percentage viewed (aim for >90%)
   - Retention graph (should remain flat)

## Extending The System

You can enhance this system by:

1. Adding automatic visual content generation
2. Implementing trend detection across multiple platforms
3. Creating custom voice generation for narration
4. Building automated video editing connections

## Scaling Blueprint

When your first channel hits $2,000/month:

1. Document your production process
2. Hire an editor for your main channel
3. Launch a second channel in a different niche
4. Repeat the process systematically

## Legal Considerations

Always transform content rather than copying directly. The "Zoink & Twist Method" is about inspiration and improvement, not plagiarism. Focus on adding value through:

- Better storytelling
- Improved visuals
- More engaging hooks
- Higher production quality

## Contributing

Feel free to improve these scripts or adapt them to your specific needs. Pull requests are welcome for:

- Additional content source integrations
- Improved script generation algorithms
- Enhanced analytics functionality
- Documentation improvements

---

Remember, these tools are meant to enhance your content creation process, not replace your creativity. The most successful channels combine data-driven strategies with unique perspectives and quality production.

**Happy content creating!** 🎬