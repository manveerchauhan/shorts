"""
Reddit to YouTube Shorts Script Generator
-----------------------------------------
This module transforms scraped Reddit content into optimized YouTube Shorts scripts
using the "Zoink & Twist Method" - finding viral content and improving upon it.

Features:
- Convert Reddit threads into structured YouTube Shorts scripts
- Generate hooks, pattern interrupts, and calls to action
- Create emotion-driven content optimized for retention
- Format outputs for different content styles (story, facts, motivation)
- Score and rank script ideas by viral potential
"""

import pandas as pd
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import random
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)


class RedditToShortsConverter:
    """Converts Reddit content into YouTube Shorts scripts."""
    
    def __init__(self, config_path: str = "config/shorts_config.json"):
        """
        Initialize the converter with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
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
                "output_directory": "data/shorts_scripts",
                "max_script_length": 500,  # Characters (aim for ~40 seconds)
                "min_score_threshold": 1000,  # Minimum Reddit score to consider
                "hook_templates": [
                    "You won't believe what happened when {subject} {action}...",
                    "Watch how {subject} {action} and changed everything...",
                    "This is why {subject} will never {action} again...",
                    "{subject} thought nobody would notice when they {action}...",
                    "The real reason why {subject} decided to {action}..."
                ],
                "pattern_interrupts": [
                    "But here's where it gets interesting...",
                    "Now pay attention to what happens next...",
                    "This is the part most people miss...",
                    "You might want to see this part...",
                    "But that's not even the craziest part..."
                ],
                "call_to_actions": [
                    "Follow for more unbelievable stories",
                    "Like and follow for more content that will blow your mind",
                    "Let me know in the comments if you've experienced something similar",
                    "Share this with someone who needs to see this",
                    "Comment if you want to see more like this"
                ]
            }
    
    def create_default_config(self):
        """Create default configuration file if it doesn't exist."""
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, "shorts_config.json")
        
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            print(f"Created default shorts configuration file at {config_path}")
        else:
            print(f"Shorts configuration file already exists at {config_path}")
    
    def load_reddit_data(self, file_path: str) -> pd.DataFrame:
        """
        Load Reddit data from JSON or CSV file.
        
        Args:
            file_path: Path to the Reddit data file
            
        Returns:
            DataFrame containing Reddit data
        """
        if file_path.endswith('.json'):
            return pd.read_json(file_path)
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file format. Use JSON or CSV.")
    
    def generate_scripts_from_file(self, file_path: str, max_scripts: int = 10) -> List[Dict[str, Any]]:
        """
        Generate YouTube Shorts scripts from a Reddit data file.
        
        Args:
            file_path: Path to the Reddit data file
            max_scripts: Maximum number of scripts to generate
            
        Returns:
            List of script dictionaries
        """
        df = self.load_reddit_data(file_path)
        
        # Filter by minimum score
        df = df[df['score'] >= self.config["min_score_threshold"]]
        
        # Sort by score (descending)
        df = df.sort_values('score', ascending=False)
        
        # Limit to max_scripts
        df = df.head(max_scripts)
        
        scripts = []
        
        for _, row in df.iterrows():
            try:
                # Process thread data into script
                script = self.convert_thread_to_script(row)
                if script:
                    scripts.append(script)
            except Exception as e:
                print(f"Error processing thread {row.get('id', 'unknown')}: {e}")
        
        # Save scripts to file
        self._save_scripts(scripts)
        
        return scripts
    
    def convert_thread_to_script(self, thread_data: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Convert a Reddit thread into a YouTube Shorts script.
        
        Args:
            thread_data: Series or dict containing Reddit thread data
            
        Returns:
            Dictionary containing script data, or None if conversion failed
        """
        # Skip if data is missing crucial fields
        if not all(key in thread_data for key in ['title', 'selftext']):
            return None
        
        # Determine content type based on subreddit and content analysis
        content_type = self._determine_content_type(thread_data)
        
        # Extract relevant text content
        title = thread_data['title']
        selftext = thread_data.get('selftext', '')
        
        # Extract top comments if available
        top_comments = []
        if 'top_comments' in thread_data:
            if isinstance(thread_data['top_comments'], list):
                top_comments = thread_data['top_comments']
            elif isinstance(thread_data['top_comments'], str):
                # Try to parse JSON string
                try:
                    top_comments = json.loads(thread_data['top_comments'])
                except:
                    top_comments = []
        
        # Generate script components
        hook = self._generate_hook(thread_data, content_type)
        main_content = self._generate_main_content(thread_data, content_type, top_comments)
        pattern_interrupt = self._get_pattern_interrupt()
        conclusion = self._generate_conclusion(thread_data, content_type, top_comments)
        call_to_action = self._get_call_to_action()
        
        # Combine components into full script
        script_text = f"{hook}\n\n{main_content}\n\n{pattern_interrupt}\n\n{conclusion}\n\n{call_to_action}"
        
        # Trim to max length if needed
        if len(script_text) > self.config["max_script_length"]:
            # Preserve hook and trim the rest
            max_length = self.config["max_script_length"]
            hook_length = len(hook)
            cta_length = len(call_to_action)
            
            # Reserve space for hook, pattern interrupt, and CTA
            remaining_length = max_length - hook_length - len(pattern_interrupt) - cta_length - 8  # 8 accounts for newlines
            
            # Split the remaining length between main_content and conclusion (70%/30%)
            main_content_length = int(remaining_length * 0.7)
            conclusion_length = remaining_length - main_content_length
            
            # Trim main content and conclusion
            main_content = main_content[:main_content_length] + "..."
            conclusion = conclusion[:conclusion_length] + "..."
            
            # Reassemble script
            script_text = f"{hook}\n\n{main_content}\n\n{pattern_interrupt}\n\n{conclusion}\n\n{call_to_action}"
        
        # Calculate virality score
        virality_score = self._calculate_virality_score(thread_data, script_text)
        
        # Create script data structure
        script_data = {
            "id": thread_data.get('id', f"script_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "title": f"Shorts Script: {title[:50]}{'...' if len(title) > 50 else ''}",
            "content_type": content_type,
            "script_text": script_text,
            "word_count": len(script_text.split()),
            "character_count": len(script_text),
            "estimated_duration_seconds": len(script_text.split()) / 3,  # Rough estimate: 3 words per second
            "virality_score": virality_score,
            "source": {
                "reddit_id": thread_data.get('id', ''),
                "subreddit": thread_data.get('subreddit', ''),
                "title": title,
                "score": thread_data.get('score', 0),
                "url": thread_data.get('permalink', '')
            },
            "created_at": datetime.now().isoformat()
        }
        
        return script_data
    
    def _determine_content_type(self, thread_data: pd.Series) -> str:
        """Determine the best content type for the thread."""
        subreddit = thread_data.get('subreddit', '').lower()
        title = thread_data.get('title', '').lower()
        selftext = thread_data.get('selftext', '').lower()
        
        # Story-based subreddits
        story_subreddits = ['tifu', 'amitheasshole', 'maliciouscompliance', 'relationship_advice', 
                           'prorevenge', 'pettyrevenge', 'entitledparents']
        
        # Fact-based subreddits
        fact_subreddits = ['todayilearned', 'science', 'explainlikeimfive', 'askscience', 
                          'youshouldknow', 'lifeprotips']
        
        # Motivation subreddits
        motivation_subreddits = ['getmotivated', 'decidingtobebetter', 'selfimprovement']
        
        # Check subreddit first
        if subreddit in story_subreddits:
            return "story"
        elif subreddit in fact_subreddits:
            return "fact"
        elif subreddit in motivation_subreddits:
            return "motivation"
        
        # Check for story indicators in title
        story_indicators = ['i', 'my', 'me', 'happened', 'experience', 'story']
        if any(indicator in title.split() for indicator in story_indicators):
            return "story"
        
        # Check for fact indicators
        fact_indicators = ['why', 'how', 'what', 'fact', 'study', 'research', 'found']
        if any(indicator in title.split() for indicator in fact_indicators):
            return "fact"
        
        # Default to story as it tends to perform well
        return "story"
    
    def _generate_hook(self, thread_data: pd.Series, content_type: str) -> str:
        """Generate an attention-grabbing hook."""
        title = thread_data['title']
        
        # Extract key elements from title
        # This is a simplified extraction and could be improved with NLP
        words = title.split()
        subject = "this person"
        action = "did something unbelievable"
        
        if len(words) >= 3:
            if words[0].lower() in ['i', 'my', 'me']:
                subject = "this person"
            elif len(words) >= 4:
                subject = " ".join(words[0:2])
            
            action_start = min(2, len(words) - 1)
            action = " ".join(words[action_start:min(action_start + 4, len(words))])
        
        # Select hook template based on content type
        hook_templates = self.config["hook_templates"]
        hook_template = random.choice(hook_templates)
        
        # Fill in the template
        hook = hook_template.format(subject=subject, action=action)
        
        # Special handling for different content types
        if content_type == "fact":
            fact_hooks = [
                f"The shocking truth about {subject}...",
                f"Scientists discovered why {subject} {action}...",
                f"This is what really happens when {subject} {action}..."
            ]
            hook = random.choice(fact_hooks)
        elif content_type == "motivation":
            motivation_hooks = [
                f"This changed how {subject} approached life forever...",
                f"One decision transformed {subject}'s life...",
                f"How {subject} overcame impossible odds..."
            ]
            hook = random.choice(motivation_hooks)
        
        return hook
    
    def _generate_main_content(self, thread_data: pd.Series, 
                              content_type: str, 
                              top_comments: List[Dict[str, Any]]) -> str:
        """Generate the main content of the script."""
        title = thread_data['title']
        selftext = thread_data.get('selftext', '')
        
        # For story content type, focus on the narrative
        if content_type == "story":
            # Use the selftext as the primary content
            if selftext and len(selftext) > 50:
                # Truncate and clean the selftext
                content = self._clean_text(selftext)
                sentences = nltk.sent_tokenize(content)
                
                # Keep only the first few sentences for the main content
                main_sentences = sentences[:min(5, len(sentences))]
                return " ".join(main_sentences)
            
            # If selftext is too short, check comments for good content
            elif top_comments:
                # Find longest comment with good sentiment
                best_comment = self._find_best_comment(top_comments)
                if best_comment:
                    content = self._clean_text(best_comment.get('body', ''))
                    sentences = nltk.sent_tokenize(content)
                    main_sentences = sentences[:min(4, len(sentences))]
                    return " ".join(main_sentences)
        
        # For fact content type, focus on information
        elif content_type == "fact":
            # Start with the title as the fact
            content = f"Here's a fact that might surprise you: {title}\n\n"
            
            # Add supporting information from selftext or comments
            if selftext and len(selftext) > 50:
                sentences = nltk.sent_tokenize(self._clean_text(selftext))
                supporting_sentences = sentences[:min(3, len(sentences))]
                content += " ".join(supporting_sentences)
            elif top_comments:
                # Find an informative comment
                informative_comment = self._find_informative_comment(top_comments)
                if informative_comment:
                    content += self._clean_text(informative_comment.get('body', ''))[:200]
                    
            return content
        
        # For motivation content type, focus on inspirational content
        elif content_type == "motivation":
            content = f"{title}\n\n"
            
            if selftext and len(selftext) > 50:
                # Find the most positive sentences in the selftext
                sentences = nltk.sent_tokenize(self._clean_text(selftext))
                positive_sentences = self._find_positive_sentences(sentences, 3)
                content += " ".join(positive_sentences)
            
            return content
        
        # Default: Just use title and beginning of selftext
        if selftext:
            return f"{title}\n\n{self._clean_text(selftext[:200])}"
        return title
    
    def _generate_conclusion(self, thread_data: pd.Series, 
                            content_type: str, 
                            top_comments: List[Dict[str, Any]]) -> str:
        """Generate the conclusion of the script."""
        # For story content type, focus on the outcome or lesson
        if content_type == "story":
            selftext = thread_data.get('selftext', '')
            
            if selftext and len(selftext) > 200:
                # Get the last few sentences of the selftext
                sentences = nltk.sent_tokenize(self._clean_text(selftext))
                if len(sentences) > 2:
                    conclusion_sentences = sentences[-min(2, len(sentences)):]
                    return " ".join(conclusion_sentences)
            
            # If selftext is not suitable, check for good conclusion in comments
            if top_comments:
                op_comments = [c for c in top_comments if c.get('is_op', False)]
                if op_comments:
                    # Use OP's response as conclusion
                    content = self._clean_text(op_comments[0].get('body', ''))
                    sentences = nltk.sent_tokenize(content)
                    conclusion_sentences = sentences[:min(2, len(sentences))]
                    return " ".join(conclusion_sentences)
                
                # Otherwise use a high-scoring comment
                best_comment = self._find_best_comment(top_comments)
                if best_comment:
                    content = self._clean_text(best_comment.get('body', ''))
                    sentences = nltk.sent_tokenize(content)
                    conclusion_sentences = sentences[:min(2, len(sentences))]
                    return " ".join(conclusion_sentences)
        
        # For fact content type, provide a takeaway
        elif content_type == "fact":
            conclusions = [
                "This just goes to show how fascinating our world really is.",
                "It's incredible what we can learn when we dig deeper.",
                "The more you know, the more you realize how much is still to be discovered.",
                "Sometimes the most surprising facts are hiding right in plain sight."
            ]
            return random.choice(conclusions)
        
        # For motivation content type, provide an inspirational closer
        elif content_type == "motivation":
            conclusions = [
                "Remember, your mindset determines your reality.",
                "Small changes today create big results tomorrow.",
                "The journey of a thousand miles begins with a single step.",
                "Your future self is watching right now - make them proud."
            ]
            return random.choice(conclusions)
        
        # Default conclusion
        return "What do you think about this? Let me know in the comments."
    
    def _get_pattern_interrupt(self) -> str:
        """Get a random pattern interrupt phrase."""
        return random.choice(self.config["pattern_interrupts"])
    
    def _get_call_to_action(self) -> str:
        """Get a random call to action phrase."""
        return random.choice(self.config["call_to_actions"])
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text for readability."""
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove Reddit formatting
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove markdown links
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italics
        
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove edit notes
        text = re.sub(r'Edit:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Update:.*', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _find_best_comment(self, comments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best comment based on score and content."""
        if not comments:
            return None
        
        # Sort by score if available
        if 'score' in comments[0]:
            sorted_comments = sorted(comments, key=lambda x: x.get('score', 0), reverse=True)
        else:
            sorted_comments = comments
        
        # Filter out very short comments
        valid_comments = [c for c in sorted_comments if len(c.get('body', '')) > 50]
        
        if not valid_comments:
            return None
        
        return valid_comments[0]
    
    def _find_informative_comment(self, comments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find a comment that appears to be informative."""
        if not comments:
            return None
        
        # Keywords that suggest informative content
        info_keywords = ['actually', 'fact', 'research', 'according', 'study', 'evidence', 'expert']
        
        # Score each comment
        scored_comments = []
        for comment in comments:
            body = comment.get('body', '').lower()
            # Skip short comments
            if len(body) < 50:
                continue
                
            # Initial score is comment score if available
            score = comment.get('score', 0)
            
            # Add points for keywords
            for keyword in info_keywords:
                if keyword in body:
                    score += 2
            
            # Add points for length (up to a point)
            score += min(len(body) // 100, 5)
            
            scored_comments.append((score, comment))
        
        if not scored_comments:
            return None
        
        # Return highest scored comment
        return sorted(scored_comments, key=lambda x: x[0], reverse=True)[0][1]
    
    def _find_positive_sentences(self, sentences: List[str], count: int) -> List[str]:
        """Find the most positive sentences in a list."""
        scored_sentences = []
        
        for sentence in sentences:
            if len(sentence) < 10:  # Skip very short sentences
                continue
                
            sentiment = self.sentiment_analyzer.polarity_scores(sentence)
            scored_sentences.append((sentiment['compound'], sentence))
        
        # Sort by positivity (highest compound score first)
        sorted_sentences = sorted(scored_sentences, key=lambda x: x[0], reverse=True)
        
        # Return top positive sentences
        return [s[1] for s in sorted_sentences[:count]]
    
    def _calculate_virality_score(self, thread_data: pd.Series, script_text: str) -> float:
        """
        Calculate a virality score for the script.
        Higher scores indicate more viral potential.
        """
        score = 0.0
        
        # Reddit engagement factors (50% of score)
        reddit_score = thread_data.get('score', 0)
        num_comments = thread_data.get('num_comments', 0)
        
        # Normalize Reddit score (0-5 points)
        score += min(reddit_score / 1000, 5) * 2.5
        
        # Normalize comments (0-5 points)
        score += min(num_comments / 100, 5) * 2.5
        
        # Content factors (50% of score)
        
        # Length optimality (0-2.5 points)
        # 300-500 chars is optimal
        char_count = len(script_text)
        if 300 <= char_count <= 500:
            score += 2.5
        elif 200 <= char_count < 300 or 500 < char_count <= 600:
            score += 1.5
        else:
            score += 0.5
        
        # Emotional appeal (0-2.5 points)
        sentiment = self.sentiment_analyzer.polarity_scores(script_text)
        
        # High emotion (either positive or negative) is good for virality
        emotion_intensity = abs(sentiment['compound'])
        score += emotion_intensity * 2.5
        
        # Presence of emotion or attention words (0-2.5 points)
        attention_words = ['shocking', 'unbelievable', 'surprising', 'never', 'always', 
                          'secret', 'hidden', 'amazing', 'incredible', 'mind-blowing']
        matches = sum(1 for word in attention_words if word in script_text.lower())
        score += min(matches, 5) * 0.5
        
        # Question hooks (0-2.5 points)
        if '?' in script_text[:100]:  # Question in the hook
            score += 2.5
        
        return round(score, 2)
    
    def _save_scripts(self, scripts: List[Dict[str, Any]]) -> None:
        """Save generated scripts to JSON file."""
        if not scripts:
            print("No scripts to save.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.config["output_directory"], f"shorts_scripts_{timestamp}.json")
        
        with open(output_path, 'w') as f:
            json.dump(scripts, f, indent=4)
        
        print(f"Saved {len(scripts)} scripts to {output_path}")
        
        # Also save a formatted text version for quick review
        txt_path = os.path.join(self.config["output_directory"], f"shorts_scripts_{timestamp}.txt")
        
        with open(txt_path, 'w') as f:
            for i, script in enumerate(scripts, 1):
                f.write(f"===== SCRIPT {i} =====\n")
                f.write(f"Title: {script['title']}\n")
                f.write(f"Type: {script['content_type']}\n")
                f.write(f"Virality Score: {script['virality_score']}/20\n")
                f.write(f"Source: r/{script['source']['subreddit']} | Score: {script['source']['score']}\n")
                f.write(f"URL: {script['source']['url']}\n\n")
                f.write(f"{script['script_text']}\n\n")
                f.write(f"Word Count: {script['word_count']} | Est. Duration: {int(script['estimated_duration_seconds'])}s\n")
                f.write("=" * 50 + "\n\n")
        
        print(f"Also saved formatted scripts to {txt_path}")
    
    def batch_generate_from_directory(self, directory_path: str, max_per_file: int = 5) -> List[Dict[str, Any]]:
        """
        Generate scripts from all Reddit data files in a directory.
        
        Args:
            directory_path: Directory containing Reddit data files
            max_per_file: Maximum scripts to generate from each file
            
        Returns:
            List of all generated scripts
        """
        all_scripts = []
        
        # Find all JSON and CSV files
        files = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.json') or filename.endswith('.csv'):
                files.append(os.path.join(directory_path, filename))
        
        for file_path in files:
            print(f"Processing {file_path}...")
            try:
                scripts = self.generate_scripts_from_file(file_path, max_per_file)
                all_scripts.extend(scripts)
                print(f"Generated {len(scripts)} scripts from {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return all_scripts


def create_default_config():
    """Create default configuration file."""
    converter = RedditToShortsConverter()
    converter.create_default_config()


def main():
    """Main function to demonstrate usage."""
    # Create default config file if needed
    create_default_config()
    
    # Initialize the converter
    converter = RedditToShortsConverter()
    
    # Check if data directory exists and has files
    data_dir = "data/reddit_content"
    
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        print("No Reddit data found. Please run the reddit_scraper.py script first.")
        return
    
    # Generate scripts from all files in the directory
    scripts = converter.batch_generate_from_directory(data_dir)
    
    print(f"Generated a total of {len(scripts)} scripts.")
    
    # Show sample script
    if scripts:
        print("\n=== Sample Script ===")
        sample = scripts[0]
        print(f"Title: {sample['title']}")
        print(f"Type: {sample['content_type']}")
        print(f"Virality Score: {sample['virality_score']}/20")
        print(f"\n{sample['script_text']}\n")
        print(f"Word Count: {sample['word_count']} | Est. Duration: {int(sample['estimated_duration_seconds'])}s")


if __name__ == "__main__":
    main()