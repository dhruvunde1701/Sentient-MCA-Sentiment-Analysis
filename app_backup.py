import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sentiment_analyzer import SentimentAnalyzer
from text_summarizer import TextSummarizer
from wordcloud_generator import WordCloudGenerator

# Configure Streamlit page
st.set_page_config(
    page_title="E-Consultation Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

def load_sample_data():
    """Load sample data"""
    try:
        df = pd.read_csv('data/sample_comments.csv')
        return df
    except FileNotFoundError:
        return None

def analyze_data(df):
    """Perform complete analysis on the data"""
    # Initialize analyzers
    sentiment_analyzer = SentimentAnalyzer()
    text_summarizer = TextSummarizer()
    wordcloud_generator = WordCloudGenerator()
    
    # Analyze sentiment
    sentiment_results = sentiment_analyzer.analyze_comments_batch(df['comment_text'].values.tolist())
    
    # Merge results with original data
    analysis_df = df.copy()
    analysis_df = pd.concat([analysis_df.reset_index(drop=True), sentiment_results.reset_index(drop=True)], axis=1)
    
    # Get overall summary
    overall_summary = sentiment_analyzer.get_overall_sentiment_summary(analysis_df)
    
    # Get stakeholder analysis
    stakeholder_analysis = sentiment_analyzer.analyze_sentiment_by_stakeholder(analysis_df)
    
    # Generate text summaries
    overall_text_summary = text_summarizer.generate_overall_summary(analysis_df)
    sentiment_summaries = text_summarizer.summarize_by_sentiment(analysis_df)
    stakeholder_summaries = text_summarizer.summarize_by_stakeholder(analysis_df)
    
    # Generate word clouds
    overall_wordcloud = wordcloud_generator.generate_wordcloud(df['comment_text'].values.tolist())
    sentiment_wordclouds = wordcloud_generator.generate_sentiment_wordclouds(analysis_df)
    stakeholder_wordclouds = wordcloud_generator.generate_stakeholder_wordclouds(analysis_df)
    
    # Get word frequencies
    word_frequencies = wordcloud_generator.get_word_frequencies(df['comment_text'].values.tolist())
    
    return {
        'analysis_df': analysis_df,
        'overall_summary': overall_summary,
        'stakeholder_analysis': stakeholder_analysis,
        'overall_text_summary': overall_text_summary,
        'sentiment_summaries': sentiment_summaries,
        'stakeholder_summaries': stakeholder_summaries,
        'overall_wordcloud': overall_wordcloud,
        'sentiment_wordclouds': sentiment_wordclouds,
        'stakeholder_wordclouds': stakeholder_wordclouds,
        'word_frequencies': word_frequencies
    }

def create_sentiment_pie_chart(summary):\n    \"\"\"Create sentiment distribution pie chart\"\"\"\n    labels = ['Positive', 'Negative', 'Neutral']\n    values = [summary['positive'], summary['negative'], summary['neutral']]\n    colors = ['#2E8B57', '#DC143C', '#4682B4']\n    \n    fig = go.Figure(data=[go.Pie(\n        labels=labels,\n        values=values,\n        marker_colors=colors,\n        textinfo='label+percent+value'\n    )])\n    \n    fig.update_layout(\n        title=\"Overall Sentiment Distribution\",\n        height=400\n    )\n    \n    return fig

def create_stakeholder_sentiment_chart(stakeholder_df):\n    \"\"\"Create stakeholder sentiment analysis chart\"\"\"\n    fig = px.bar(\n        stakeholder_df,\n        x='stakeholder_type',\n        y=['positive', 'negative', 'neutral'],\n        title=\"Sentiment Distribution by Stakeholder Type\",\n        color_discrete_map={\n            'positive': '#2E8B57',\n            'negative': '#DC143C',\n            'neutral': '#4682B4'\n        }\n    )\n    \n    fig.update_layout(\n        xaxis_title=\"Stakeholder Type\",\n        yaxis_title=\"Number of Comments\",\n        height=500,\n        xaxis={'tickangle': 45}\n    )\n    \n    return fig

def display_wordcloud(wordcloud, title):\n    \"\"\"Display word cloud in Streamlit\"\"\"\n    if wordcloud:\n        wordcloud_generator = WordCloudGenerator()\n        img_base64 = wordcloud_generator.wordcloud_to_base64(wordcloud)\n        if img_base64:\n            st.markdown(f\"### {title}\")\n            st.markdown(\n                f'<img src=\"data:image/png;base64,{img_base64}\" style=\"width:100%\">',\n                unsafe_allow_html=True\n            )\n        else:\n            st.info(f\"Could not generate word cloud for {title}\")\n    else:\n        st.info(f\"No data available for {title}\")\n\ndef main():\n    # Header\n    st.title(\"📊 E-Consultation Sentiment Analysis System\")\n    st.markdown(\n        \"\"\"\n        This MVP analyzes stakeholder comments from e-consultation processes, providing:\n        - **Sentiment Analysis**: Classify comments as positive, negative, or neutral\n        - **Text Summarization**: Generate concise summaries of feedback\n        - **Word Cloud Visualization**: Show keyword density and themes\n        \"\"\"\n    )\n    \n    # Sidebar\n    st.sidebar.header(\"📁 Data Input\")\n    \n    # File upload\n    uploaded_file = st.sidebar.file_uploader(\n        \"Upload CSV file\",\n        type=['csv'],\n        help=\"Upload a CSV file with columns: id, stakeholder_type, comment_text, provision_reference, submission_date\"\n    )\n    \n    # Sample data option\n    if st.sidebar.button(\"Load Sample Data\"):\n        sample_data = load_sample_data()\n        if sample_data is not None:\n            st.session_state.data = sample_data\n            st.session_state.analysis_results = None\n            st.sidebar.success(\"Sample data loaded successfully!\")\n        else:\n            st.sidebar.error(\"Could not load sample data. Please check if data/sample_comments.csv exists.\")\n    \n    # Process uploaded file\n    if uploaded_file is not None:\n        try:\n            df = pd.read_csv(uploaded_file)\n            st.session_state.data = df\n            st.session_state.analysis_results = None\n            st.sidebar.success(f\"File uploaded successfully! {len(df)} comments loaded.\")\n        except Exception as e:\n            st.sidebar.error(f\"Error loading file: {str(e)}\")\n    \n    # Main content\n    if st.session_state.data is not None:\n        df = st.session_state.data\n        \n        # Display data info\n        st.subheader(\"📈 Data Overview\")\n        col1, col2, col3 = st.columns(3)\n        with col1:\n            st.metric(\"Total Comments\", len(df))\n        with col2:\n            st.metric(\"Stakeholder Types\", df['stakeholder_type'].nunique())\n        with col3:\n            st.metric(\"Unique Provisions\", df['provision_reference'].nunique())\n        \n        # Show sample data\n        with st.expander(\"View Sample Data\"):\n            st.dataframe(df.head())\n        \n        # Analysis button\n        if st.button(\"🔍 Run Analysis\", type=\"primary\"):\n            with st.spinner(\"Analyzing comments... This may take a few moments.\"):\n                st.session_state.analysis_results = analyze_data(df)\n            st.success(\"Analysis completed!\")\n            st.rerun()\n        \n        # Display results if analysis is complete\n        if st.session_state.analysis_results is not None:\n            results = st.session_state.analysis_results\n            \n            # Create tabs for different analyses\n            tab1, tab2, tab3, tab4 = st.tabs([\"📊 Sentiment Analysis\", \"📝 Text Summaries\", \"☁️ Word Clouds\", \"📋 Detailed Results\"])\n            \n            with tab1:\n                st.subheader(\"Sentiment Analysis Results\")\n                \n                # Overall metrics\n                summary = results['overall_summary']\n                col1, col2, col3, col4 = st.columns(4)\n                with col1:\n                    st.metric(\"Positive\", f\"{summary['positive_percentage']}%\", f\"{summary['positive']} comments\")\n                with col2:\n                    st.metric(\"Negative\", f\"{summary['negative_percentage']}%\", f\"{summary['negative']} comments\")\n                with col3:\n                    st.metric(\"Neutral\", f\"{summary['neutral_percentage']}%\", f\"{summary['neutral']} comments\")\n                with col4:\n                    st.metric(\"Avg. Sentiment\", f\"{summary['average_vader_score']}\", \"VADER Score\")\n                \n                # Charts\n                col1, col2 = st.columns(2)\n                with col1:\n                    fig_pie = create_sentiment_pie_chart(summary)\n                    st.plotly_chart(fig_pie, width=True)\n                \n                with col2:\n                    if results['stakeholder_analysis'] is not None:\n                        fig_stakeholder = create_stakeholder_sentiment_chart(results['stakeholder_analysis'])\n                        st.plotly_chart(fig_stakeholder, width=True)\n            \n            with tab2:\n                st.subheader(\"Text Summaries\")\n                \n                # Overall summary\n                st.markdown(\"### 📋 Overall Summary\")\n                overall_summary = results['overall_text_summary']\n                st.write(overall_summary['main_summary'])\n                \n                col1, col2 = st.columns(2)\n                with col1:\n                    st.markdown(\"**Key Themes:**\")\n                    for theme in overall_summary['key_themes']:\n                        st.write(f\"• {theme}\")\n                \n                with col2:\n                    st.markdown(\"**Top Keywords:**\")\n                    for word, freq in list(overall_summary['top_keywords'].items())[:5]:\n                        st.write(f\"• {word}: {freq} mentions\")\n                \n                # Sentiment-based summaries\n                st.markdown(\"### 😊 Summaries by Sentiment\")\n                for sentiment, summary_data in results['sentiment_summaries'].items():\n                    with st.expander(f\"{sentiment.title()} Comments ({summary_data['comment_count']} comments)\"):\n                        st.write(summary_data['summary'])\n                        if summary_data['key_phrases']:\n                            st.write(\"**Key phrases:**\", \", \".join([phrase[0] for phrase in summary_data['key_phrases'][:5]]))\n                \n                # Stakeholder-based summaries\n                st.markdown(\"### 👥 Summaries by Stakeholder\")\n                for stakeholder, summary_data in results['stakeholder_summaries'].items():\n                    with st.expander(f\"{stakeholder} ({summary_data['comment_count']} comments)\"):\n                        st.write(summary_data['summary'])\n                        if summary_data['key_phrases']:\n                            st.write(\"**Key phrases:**\", \", \".join([phrase[0] for phrase in summary_data['key_phrases'][:5]]))\n            \n            with tab3:\n                st.subheader(\"Word Cloud Visualizations\")\n                \n                # Overall word cloud\n                display_wordcloud(results['overall_wordcloud'], \"Overall Word Cloud\")\n                \n                # Sentiment word clouds\n                st.markdown(\"### Word Clouds by Sentiment\")\n                for sentiment, wordcloud in results['sentiment_wordclouds'].items():\n                    display_wordcloud(wordcloud, f\"{sentiment.title()} Sentiment\")\n                \n                # Stakeholder word clouds\n                st.markdown(\"### Word Clouds by Stakeholder\")\n                for stakeholder, wordcloud in results['stakeholder_wordclouds'].items():\n                    display_wordcloud(wordcloud, f\"{stakeholder}\")\n                \n                # Word frequency chart\n                st.markdown(\"### 📊 Word Frequency Analysis\")\n                if results['word_frequencies']:\n                    wordcloud_gen = WordCloudGenerator()\n                    freq_chart = wordcloud_gen.create_frequency_bar_chart(\n                        results['word_frequencies'], \n                        \"Top 15 Most Frequent Words\"\n                    )\n                    if freq_chart:\n                        st.markdown(\n                            f'<img src=\"data:image/png;base64,{freq_chart}\" style=\"width:100%\">',\n                            unsafe_allow_html=True\n                        )\n            \n            with tab4:\n                st.subheader(\"Detailed Analysis Results\")\n                \n                # Individual comment analysis\n                st.markdown(\"### Individual Comment Analysis\")\n                analysis_df = results['analysis_df']\n                \n                # Filter options\n                col1, col2 = st.columns(2)\n                with col1:\n                    sentiment_filter = st.selectbox(\n                        \"Filter by Sentiment\",\n                        ['All'] + list(analysis_df['consensus_label'].unique())\n                    )\n                with col2:\n                    stakeholder_filter = st.selectbox(\n                        \"Filter by Stakeholder\",\n                        ['All'] + list(analysis_df['stakeholder_type'].unique())\n                    )\n                \n                # Apply filters\n                filtered_df = analysis_df.copy()\n                if sentiment_filter != 'All':\n                    filtered_df = filtered_df[filtered_df['consensus_label'] == sentiment_filter]\n                if stakeholder_filter != 'All':\n                    filtered_df = filtered_df[filtered_df['stakeholder_type'] == stakeholder_filter]\n                \n                # Display filtered results\n                st.write(f\"Showing {len(filtered_df)} of {len(analysis_df)} comments\")\n                \n                display_columns = [\n                    'stakeholder_type', 'comment_text', 'consensus_label', \n                    'vader_compound', 'textblob_polarity', 'provision_reference'\n                ]\n                st.dataframe(\n                    filtered_df[display_columns],\n                    width=True,\n                    height=400\n                )\n                \n                # Download options\n                st.markdown(\"### 💾 Download Results\")\n                col1, col2 = st.columns(2)\n                \n                with col1:\n                    # Download detailed analysis\n                    csv_data = analysis_df.to_csv(index=False)\n                    st.download_button(\n                        \"Download Detailed Analysis (CSV)\",\n                        csv_data,\n                        \"sentiment_analysis_results.csv\",\n                        \"text/csv\"\n                    )\n                \n                with col2:\n                    # Download summary report\n                    summary_text = f\"\"\"\n                    E-Consultation Sentiment Analysis Summary Report\n                    \n                    Total Comments: {summary['total_comments']}\n                    Positive: {summary['positive']} ({summary['positive_percentage']}%)\n                    Negative: {summary['negative']} ({summary['negative_percentage']}%)\n                    Neutral: {summary['neutral']} ({summary['neutral_percentage']}%)\n                    \n                    Average VADER Score: {summary['average_vader_score']}\n                    Average TextBlob Score: {summary['average_textblob_score']}\n                    \n                    Overall Summary:\n                    {overall_summary['main_summary']}\n                    \n                    Key Themes: {', '.join(overall_summary['key_themes'])}\n                    \"\"\"\n                    \n                    st.download_button(\n                        \"Download Summary Report (TXT)\",\n                        summary_text,\n                        \"sentiment_summary_report.txt\",\n                        \"text/plain\"\n                    )\n    \n    else:\n        # Welcome screen\n        st.info(\n            \"\"\"\n            👆 **Get Started:**\n            1. Upload a CSV file with consultation comments using the sidebar\n            2. Or click \"Load Sample Data\" to try the system with sample data\n            3. Click \"Run Analysis\" to process the comments\n            \n            **Required CSV Format:**\n            - `id`: Unique identifier\n            - `stakeholder_type`: Type of stakeholder (e.g., Corporate Entity, Individual)\n            - `comment_text`: The actual comment/feedback text\n            - `provision_reference`: Reference to specific provision (optional)\n            - `submission_date`: Date of submission (optional)\n            \"\"\"\n        )\n        \n        # Show sample data structure\n        st.subheader(\"📋 Expected Data Format\")\n        sample_structure = pd.DataFrame({\n            'id': [1, 2, 3],\n            'stakeholder_type': ['Corporate Entity', 'Individual Lawyer', 'CA Firm'],\n            'comment_text': [\n                'The proposed amendment is well-structured...',\n                'I strongly disagree with the proposed changes...',\n                'The draft provides clarity but timeline seems aggressive...'\n            ],\n            'provision_reference': ['Section 12A', 'Section 45B', 'Section 23C'],\n            'submission_date': ['2024-01-15', '2024-01-16', '2024-01-17']\n        })\n        st.dataframe(sample_structure, width=True)\n\nif __name__ == \"__main__\":\n    main()
