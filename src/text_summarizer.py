import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from collections import Counter
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

class TextSummarizer:
    def __init__(self, language='english'):
        self.language = language
        self.stop_words = set(stopwords.words(language))
        self.stemmer = Stemmer(language)
        
    def clean_text(self, text):
        """Clean and preprocess text"""
        if pd.isna(text):
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', str(text)).strip()
        # Remove special characters but keep punctuation for sentence structure
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        return text
    
    def extract_key_phrases(self, texts, top_n=10):
        """Extract key phrases from a collection of texts"""
        combined_text = ' '.join([self.clean_text(str(text)) for text in texts])
        
        # Tokenize and remove stopwords
        words = word_tokenize(combined_text.lower())
        filtered_words = [word for word in words if word.isalnum() and word not in self.stop_words and len(word) > 2]
        
        # Get frequency distribution
        freq_dist = FreqDist(filtered_words)
        key_phrases = freq_dist.most_common(top_n)
        
        return key_phrases
    
    def summarize_individual_comment(self, text, max_sentences=2):
        """Summarize an individual comment"""
        text = self.clean_text(text)
        if not text or len(text.split()) < 10:
            return text
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer(self.language))
            summarizer = LsaSummarizer(self.stemmer)
            summarizer.stop_words = get_stop_words(self.language)
            
            summary = summarizer(parser.document, max_sentences)
            return ' '.join([str(sentence) for sentence in summary])
        except:
            # Fallback to simple truncation if summarization fails
            sentences = sent_tokenize(text)
            return ' '.join(sentences[:max_sentences])
    
    def summarize_by_sentiment(self, df, sentiment_col='consensus_label', text_col='comment_text'):
        """Generate summaries grouped by sentiment"""
        summaries = {}
        
        for sentiment in df[sentiment_col].unique():
            sentiment_comments = df[df[sentiment_col] == sentiment][text_col].values.tolist()
            combined_text = ' '.join([self.clean_text(str(comment)) for comment in sentiment_comments])
            
            if combined_text.strip():
                summary = self.generate_extractive_summary(combined_text, max_sentences=3)
                key_phrases = self.extract_key_phrases(sentiment_comments, top_n=5)
                
                summaries[sentiment] = {
                    'summary': summary,
                    'key_phrases': key_phrases,
                    'comment_count': len(sentiment_comments)
                }
            else:
                summaries[sentiment] = {
                    'summary': 'No significant content found.',
                    'key_phrases': [],
                    'comment_count': len(sentiment_comments)
                }
        
        return summaries
    
    def summarize_by_stakeholder(self, df, stakeholder_col='stakeholder_type', text_col='comment_text'):
        """Generate summaries grouped by stakeholder type"""
        summaries = {}
        
        for stakeholder in df[stakeholder_col].unique():
            stakeholder_comments = df[df[stakeholder_col] == stakeholder][text_col].values.tolist()
            combined_text = ' '.join([self.clean_text(str(comment)) for comment in stakeholder_comments])
            
            if combined_text.strip():
                summary = self.generate_extractive_summary(combined_text, max_sentences=2)
                key_phrases = self.extract_key_phrases(stakeholder_comments, top_n=5)
                
                summaries[stakeholder] = {
                    'summary': summary,
                    'key_phrases': key_phrases,
                    'comment_count': len(stakeholder_comments)
                }
            else:
                summaries[stakeholder] = {
                    'summary': 'No significant content found.',
                    'key_phrases': [],
                    'comment_count': len(stakeholder_comments)
                }
        
        return summaries
    
    def generate_extractive_summary(self, text, max_sentences=3):
        """Generate extractive summary using multiple algorithms"""
        text = self.clean_text(text)
        if not text or len(text.split()) < 20:
            return text
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer(self.language))
            
            # Try LSA summarizer first
            lsa_summarizer = LsaSummarizer(self.stemmer)
            lsa_summarizer.stop_words = get_stop_words(self.language)
            lsa_summary = lsa_summarizer(parser.document, max_sentences)
            
            if lsa_summary:
                return ' '.join([str(sentence) for sentence in lsa_summary])
            
            # Fallback to Luhn summarizer
            luhn_summarizer = LuhnSummarizer(self.stemmer)
            luhn_summarizer.stop_words = get_stop_words(self.language)
            luhn_summary = luhn_summarizer(parser.document, max_sentences)
            
            return ' '.join([str(sentence) for sentence in luhn_summary])
            
        except Exception as e:
            # Fallback to simple sentence extraction
            sentences = sent_tokenize(text)
            return ' '.join(sentences[:max_sentences])
    
    def generate_overall_summary(self, df, text_col='comment_text', max_sentences=5):
        """Generate an overall summary of all comments"""
        all_comments = df[text_col].values.tolist()
        combined_text = ' '.join([self.clean_text(str(comment)) for comment in all_comments])
        
        # Generate main summary
        main_summary = self.generate_extractive_summary(combined_text, max_sentences)
        
        # Extract key themes
        key_phrases = self.extract_key_phrases(all_comments, top_n=10)
        
        # Get sentiment distribution
        sentiment_dist = df['consensus_label'].value_counts().to_dict() if 'consensus_label' in df.columns else {}
        
        return {
            'main_summary': main_summary,
            'key_themes': [phrase[0] for phrase in key_phrases[:5]],
            'sentiment_distribution': sentiment_dist,
            'total_comments': len(df),
            'top_keywords': dict(key_phrases[:10])
        }
    
    def identify_common_concerns(self, df, text_col='comment_text', min_frequency=2):
        """Identify common concerns or topics mentioned across comments"""
        # Define concern-related keywords
        concern_keywords = [
            'concern', 'worried', 'issue', 'problem', 'difficulty', 'challenge',
            'oppose', 'disagree', 'against', 'negative', 'harmful', 'detrimental',
            'burden', 'cost', 'expensive', 'unfair', 'unjust', 'inappropriate'
        ]
        
        concerns = []
        for _, row in df.iterrows():
            text = self.clean_text(str(row[text_col])).lower()
            for keyword in concern_keywords:
                if keyword in text:
                    # Extract sentence containing the concern
                    sentences = sent_tokenize(row[text_col])
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            concerns.append(sentence.strip())
                            break
        
        # Count frequency of similar concerns (simple approach)
        concern_counter = Counter(concerns)
        common_concerns = [concern for concern, count in concern_counter.items() if count >= min_frequency]
        
        return common_concerns[:10]  # Return top 10 common concerns
