import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import io
import base64

class WordCloudGenerator:
    def __init__(self, language='english'):
        self.language = language
        self.stop_words = set(stopwords.words(language))
        # Add custom stop words relevant to consultation context
        self.stop_words.update([
            'section', 'amendment', 'proposed', 'draft', 'legislation', 'provision',
            'would', 'could', 'should', 'may', 'might', 'will', 'shall', 'must',
            'one', 'two', 'three', 'also', 'however', 'therefore', 'furthermore',
            'comments', 'suggestions', 'recommendations', 'feedback'
        ])
    
    def clean_and_extract_words(self, texts):
        """Clean texts and extract meaningful words"""
        all_words = []
        
        for text in texts:
            # Handle pandas Series or numpy array elements
            try:
                if pd.isna(text):
                    continue
            except (TypeError, ValueError):
                # If pd.isna fails, check if it's None or empty
                if text is None or text == '':
                    continue
            
            # Clean text
            text = str(text).lower()
            text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
            text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
            
            # Tokenize and filter
            words = word_tokenize(text)
            filtered_words = [
                word for word in words 
                if (word.isalpha() and 
                    len(word) > 2 and 
                    word not in self.stop_words)
            ]
            all_words.extend(filtered_words)
        
        return all_words
    
    def generate_wordcloud(self, texts, width=800, height=400, max_words=100, 
                          background_color='white', colormap='viridis'):
        """Generate a word cloud from texts"""
        if not texts or len(texts) == 0:
            return None
        
        # Check if all texts are NaN
        if hasattr(texts, '__iter__'):
            try:
                # Convert to list to handle numpy arrays/pandas series
                text_list = list(texts)
                if all(pd.isna(text) for text in text_list):
                    return None
            except (TypeError, ValueError):
                # If we can't iterate or check for NaN, continue
                pass
        
        # Extract and clean words
        words = self.clean_and_extract_words(texts)
        if not words:
            return None
        
        # Create word frequency
        word_freq = Counter(words)
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=width, 
            height=height,
            background_color=background_color,
            max_words=max_words,
            colormap=colormap,
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(word_freq)
        
        return wordcloud
    
    def generate_sentiment_wordclouds(self, df, text_col='comment_text', 
                                    sentiment_col='consensus_label'):
        """Generate separate word clouds for each sentiment"""
        wordclouds = {}
        sentiment_colors = {
            'positive': 'Greens',
            'negative': 'Reds',
            'neutral': 'Blues'
        }
        
        for sentiment in df[sentiment_col].unique():
            sentiment_texts = df[df[sentiment_col] == sentiment][text_col].values.tolist()
            if sentiment_texts:
                colormap = sentiment_colors.get(sentiment, 'viridis')
                wordcloud = self.generate_wordcloud(
                    sentiment_texts, 
                    colormap=colormap,
                    max_words=50
                )
                if wordcloud:
                    wordclouds[sentiment] = wordcloud
        
        return wordclouds
    
    def generate_stakeholder_wordclouds(self, df, text_col='comment_text', 
                                      stakeholder_col='stakeholder_type'):
        """Generate word clouds for each stakeholder type"""
        wordclouds = {}
        
        for stakeholder in df[stakeholder_col].unique():
            stakeholder_texts = df[df[stakeholder_col] == stakeholder][text_col].values.tolist()
            if stakeholder_texts:
                wordcloud = self.generate_wordcloud(
                    stakeholder_texts,
                    max_words=30,
                    colormap='Set3'
                )
                if wordcloud:
                    wordclouds[stakeholder] = wordcloud
        
        return wordclouds
    
    def save_wordcloud(self, wordcloud, filepath):
        """Save word cloud to file"""
        if wordcloud:
            wordcloud.to_file(filepath)
            return True
        return False
    
    def wordcloud_to_base64(self, wordcloud):
        """Convert word cloud to base64 string for web display"""
        if not wordcloud:
            return None
        
        # Create figure
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def get_word_frequencies(self, texts, top_n=20):
        """Get word frequencies as a dictionary"""
        words = self.clean_and_extract_words(texts)
        word_freq = Counter(words)
        return dict(word_freq.most_common(top_n))
    
    def create_frequency_bar_chart(self, word_frequencies, title="Top Words"):
        """Create a bar chart of word frequencies"""
        if not word_frequencies:
            return None
        
        words = list(word_frequencies.keys())[:15]  # Top 15 words
        frequencies = list(word_frequencies.values())[:15]
        
        plt.figure(figsize=(12, 6))
        bars = plt.barh(words[::-1], frequencies[::-1])  # Reverse for better display
        plt.xlabel('Frequency')
        plt.title(title)
        plt.tight_layout()
        
        # Color bars with gradient
        colors = plt.cm.viridis(np.linspace(0, 1, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def generate_comparison_wordcloud(self, texts1, texts2, labels=('Group 1', 'Group 2')):
        """Generate a comparison word cloud between two groups"""
        words1 = self.clean_and_extract_words(texts1)
        words2 = self.clean_and_extract_words(texts2)
        
        freq1 = Counter(words1)
        freq2 = Counter(words2)
        
        # Create comparison data
        all_words = set(freq1.keys()) | set(freq2.keys())
        comparison_data = {}
        
        for word in all_words:
            f1 = freq1.get(word, 0)
            f2 = freq2.get(word, 0)
            if f1 > 0 or f2 > 0:
                # Calculate relative frequency difference
                total = f1 + f2
                if f1 > f2:
                    comparison_data[f"{word}_({labels[0]})"] = f1
                elif f2 > f1:
                    comparison_data[f"{word}_({labels[1]})"] = f2
                else:
                    comparison_data[word] = total
        
        if not comparison_data:
            return None
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            colormap='RdYlBu',
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(comparison_data)
        
        return wordcloud
    
    def analyze_word_sentiment_association(self, df, text_col='comment_text', 
                                         sentiment_col='consensus_label'):
        """Analyze which words are most associated with each sentiment"""
        sentiment_words = {}
        
        for sentiment in df[sentiment_col].unique():
            sentiment_texts = df[df[sentiment_col] == sentiment][text_col].values.tolist()
            words = self.clean_and_extract_words(sentiment_texts)
            word_freq = Counter(words)
            sentiment_words[sentiment] = word_freq
        
        # Find words unique to each sentiment
        unique_words = {}
        for sentiment in sentiment_words:
            unique_words[sentiment] = []
            for word, freq in sentiment_words[sentiment].most_common(20):
                # Check if word appears significantly more in this sentiment
                other_sentiments_freq = sum([
                    sentiment_words[other_sentiment].get(word, 0) 
                    for other_sentiment in sentiment_words 
                    if other_sentiment != sentiment
                ])
                
                if freq > other_sentiments_freq * 1.5:  # At least 1.5x more frequent
                    unique_words[sentiment].append((word, freq))
        
        return unique_words
