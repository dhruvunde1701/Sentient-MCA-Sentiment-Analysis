import streamlit as st
import pandas as pd
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sentiment_analyzer import SentimentAnalyzer
from text_summarizer import TextSummarizer

st.title("🔍 Debug E-Consultation Sentiment Analysis")

# Load sample data
@st.cache_data
def load_sample_data():
    try:
        df = pd.read_csv('data/sample_comments.csv')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Test analysis function
def debug_analyze_data(df):
    st.write("🔄 Starting analysis...")
    
    try:
        # Initialize analyzers
        st.write("✅ Initializing analyzers...")
        sentiment_analyzer = SentimentAnalyzer()
        text_summarizer = TextSummarizer()
        
        # Analyze sentiment
        st.write("✅ Running sentiment analysis...")
        sentiment_results = sentiment_analyzer.analyze_comments_batch(df['comment_text'].values.tolist())
        st.write(f"✅ Sentiment analysis completed: {sentiment_results.shape}")
        
        # Merge results
        st.write("✅ Merging results...")
        analysis_df = df.copy()
        analysis_df = pd.concat([analysis_df.reset_index(drop=True), sentiment_results.reset_index(drop=True)], axis=1)
        st.write(f"✅ Merged data shape: {analysis_df.shape}")
        
        # Get overall summary
        st.write("✅ Getting overall summary...")
        overall_summary = sentiment_analyzer.get_overall_sentiment_summary(analysis_df)
        
        # Get stakeholder analysis
        st.write("✅ Getting stakeholder analysis...")
        stakeholder_analysis = sentiment_analyzer.analyze_sentiment_by_stakeholder(analysis_df)
        
        # Generate text summaries
        st.write("✅ Generating text summaries...")
        overall_text_summary = text_summarizer.generate_overall_summary(analysis_df)
        sentiment_summaries = text_summarizer.summarize_by_sentiment(analysis_df)
        stakeholder_summaries = text_summarizer.summarize_by_stakeholder(analysis_df)
        
        st.write("🎉 Analysis completed successfully!")
        
        return {
            'analysis_df': analysis_df,
            'overall_summary': overall_summary,
            'stakeholder_analysis': stakeholder_analysis,
            'overall_text_summary': overall_text_summary,
            'sentiment_summaries': sentiment_summaries,
            'stakeholder_summaries': stakeholder_summaries
        }
        
    except Exception as e:
        st.error(f"Error in analysis: {e}")
        st.write("Traceback:")
        import traceback
        st.code(traceback.format_exc())
        return None

# Main app
df = load_sample_data()
if df is not None:
    st.success(f"✅ Loaded {len(df)} comments")
    
    # Show sample data
    st.subheader("Sample Data")
    st.dataframe(df.head())
    
    if st.button("🚀 Run Debug Analysis"):
        with st.spinner("Analyzing..."):
            # Test with first 10 comments for speed
            test_df = df.head(10)
            st.write(f"Testing with {len(test_df)} comments")
            
            results = debug_analyze_data(test_df)
            
            if results:
                st.subheader("📊 Results")
                
                # Display overall summary
                st.write("**Overall Summary:**")
                st.json(results['overall_summary'])
                
                # Display sentiment distribution
                summary = results['overall_summary']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Positive", f"{summary['positive_percentage']}%", f"{summary['positive']} comments")
                with col2:
                    st.metric("Negative", f"{summary['negative_percentage']}%", f"{summary['negative']} comments")
                with col3:
                    st.metric("Neutral", f"{summary['neutral_percentage']}%", f"{summary['neutral']} comments")
                
                # Display text summaries
                if results['sentiment_summaries']:
                    st.subheader("Text Summaries by Sentiment")
                    for sentiment, summary_data in results['sentiment_summaries'].items():
                        with st.expander(f"{sentiment.title()} ({summary_data['comment_count']} comments)"):
                            st.write(summary_data['summary'])
                
                # Display detailed results
                st.subheader("Detailed Analysis")
                display_columns = ['stakeholder_type', 'comment_text', 'consensus_label', 'vader_compound', 'textblob_polarity']
                st.dataframe(results['analysis_df'][display_columns])
else:
    st.error("Failed to load sample data")
