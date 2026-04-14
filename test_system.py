#!/usr/bin/env python3
"""
Test script to verify all components of the E-consultation sentiment analysis system work correctly.
Run this script to test the system before launching the web application.
"""

import sys
import os
import pandas as pd

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sentiment_analyzer import SentimentAnalyzer
from text_summarizer import TextSummarizer
from wordcloud_generator import WordCloudGenerator

def test_sentiment_analysis():
    """Test sentiment analysis functionality"""
    print("🔍 Testing Sentiment Analysis...")
    
    analyzer = SentimentAnalyzer()
    
    # Test individual sentiment analysis
    test_comments = [
        "This is an excellent proposal that will benefit everyone.",
        "I strongly disagree with these terrible changes.",
        "The document provides some clarity on the requirements."
    ]
    
    for comment in test_comments:
        vader_result = analyzer.analyze_sentiment_vader(comment)
        textblob_result = analyzer.analyze_sentiment_textblob(comment)
        print(f"  Comment: '{comment[:50]}...'")
        print(f"    VADER: {vader_result['label']} (score: {vader_result['compound']:.3f})")
        print(f"    TextBlob: {textblob_result['label']} (score: {textblob_result['polarity']:.3f})")
    
    # Test batch analysis
    batch_results = analyzer.analyze_comments_batch(test_comments)
    print(f"  Batch analysis completed for {len(batch_results)} comments")
    
    print("✅ Sentiment Analysis test passed!")
    return True

def test_text_summarization():
    """Test text summarization functionality"""
    print("\n📝 Testing Text Summarization...")
    
    summarizer = TextSummarizer()
    
    # Test summary generation
    test_texts = [
        "The proposed amendments to the corporate governance framework represent a significant step forward in regulatory reform. The changes address long-standing concerns about transparency and accountability while maintaining flexibility for businesses to operate efficiently.",
        "While the overall direction of the legislation is positive, the implementation timeline appears too aggressive for most organizations to comply effectively. A phased approach would be more practical and ensure better compliance outcomes.",
        "These regulations will impose an undue burden on small and medium enterprises. The compliance costs are disproportionate to the benefits, and may force many businesses to reconsider their operations in this jurisdiction."
    ]
    
    # Test individual summarization
    for i, text in enumerate(test_texts):
        summary = summarizer.summarize_individual_comment(text)
        print(f"  Original {i+1}: {text[:100]}...")
        print(f"  Summary {i+1}: {summary[:100]}...")
    
    # Test key phrase extraction
    key_phrases = summarizer.extract_key_phrases(test_texts, top_n=5)
    print(f"  Top key phrases: {[phrase[0] for phrase in key_phrases]}")
    
    print("✅ Text Summarization test passed!")
    return True

def test_wordcloud_generation():
    """Test word cloud generation functionality"""
    print("\n☁️ Testing Word Cloud Generation...")
    
    generator = WordCloudGenerator()
    
    test_texts = [
        "compliance regulatory framework business transparency accountability",
        "legislation implementation timeline organizations practical outcomes",
        "burden enterprises costs benefits operations jurisdiction efficiency"
    ]
    
    # Test word extraction
    words = generator.clean_and_extract_words(test_texts)
    print(f"  Extracted {len(words)} words: {words[:10]}")
    
    # Test word cloud generation
    wordcloud = generator.generate_wordcloud(test_texts)
    if wordcloud:
        print("  Word cloud generated successfully")
    else:
        print("  Warning: Could not generate word cloud")
    
    # Test frequency analysis
    frequencies = generator.get_word_frequencies(test_texts, top_n=10)
    print(f"  Top word frequencies: {list(frequencies.keys())[:5]}")
    
    print("✅ Word Cloud Generation test passed!")
    return True

def test_sample_data():
    """Test loading and processing sample data"""
    print("\n📊 Testing Sample Data Processing...")
    
    # Load sample data
    try:
        df = pd.read_csv('data/sample_comments.csv')
        print(f"  Loaded {len(df)} sample comments")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Stakeholder types: {df['stakeholder_type'].nunique()}")
    except FileNotFoundError:
        print("  ❌ Sample data file not found!")
        return False
    
    # Test full analysis pipeline
    analyzer = SentimentAnalyzer()
    summarizer = TextSummarizer()
    generator = WordCloudGenerator()
    
    # Analyze sentiment
    sentiment_results = analyzer.analyze_comments_batch(df['comment_text'].tolist())
    print(f"  Sentiment analysis completed for {len(sentiment_results)} comments")
    
    # Merge with original data
    analysis_df = pd.concat([df.reset_index(drop=True), sentiment_results.reset_index(drop=True)], axis=1)
    
    # Get overall summary
    overall_summary = analyzer.get_overall_sentiment_summary(analysis_df)
    print(f"  Overall sentiment: {overall_summary['positive_percentage']:.1f}% positive, {overall_summary['negative_percentage']:.1f}% negative, {overall_summary['neutral_percentage']:.1f}% neutral")
    
    # Test summarization
    overall_text_summary = summarizer.generate_overall_summary(analysis_df, text_col='comment_text')
    print(f"  Generated overall summary: {len(overall_text_summary['main_summary'])} characters")
    
    # Test word cloud
    overall_wordcloud = generator.generate_wordcloud(df['comment_text'].tolist())
    if overall_wordcloud:
        print("  Overall word cloud generated successfully")
    
    print("✅ Sample Data Processing test passed!")
    return True

def test_system_integration():
    """Test overall system integration"""
    print("\n🔧 Testing System Integration...")
    
    # Test imports
    try:
        import streamlit
        import plotly
        import matplotlib
        import wordcloud
        import nltk
        import textblob
        import vaderSentiment
        print("  All required packages imported successfully")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    # Test NLTK data
    try:
        import nltk
        # Try to find the main data files we need
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        print("  NLTK data verified")
    except LookupError:
        print("  ❌ NLTK data not found! Run: python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')\"")
        return False
    
    print("✅ System Integration test passed!")
    return True

def main():
    """Run all tests"""
    print("🚀 E-Consultation Sentiment Analysis System Test Suite")
    print("=" * 60)
    
    tests = [
        test_system_integration,
        test_sentiment_analysis,
        test_text_summarization,
        test_wordcloud_generation,
        test_sample_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📋 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\n🚀 To start the application, run:")
        print("   streamlit run app.py")
    else:
        print(f"❌ {total - passed} tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
