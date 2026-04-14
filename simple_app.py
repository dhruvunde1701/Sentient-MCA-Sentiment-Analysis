import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sentiment_analyzer import SentimentAnalyzer
from text_summarizer import TextSummarizer

# Configure Streamlit page
st.set_page_config(
    page_title="E-Consultation Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
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
    
    return {
        'analysis_df': analysis_df,
        'overall_summary': overall_summary,
        'stakeholder_analysis': stakeholder_analysis,
        'overall_text_summary': overall_text_summary,
        'sentiment_summaries': sentiment_summaries,
        'stakeholder_summaries': stakeholder_summaries
    }

def create_sentiment_pie_chart(summary):
    """Create sentiment distribution pie chart"""
    labels = ['Positive', 'Negative', 'Neutral']
    values = [summary['positive'], summary['negative'], summary['neutral']]
    colors = ['#2E8B57', '#DC143C', '#4682B4']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent+value'
    )])
    
    fig.update_layout(
        title="Overall Sentiment Distribution",
        height=400
    )
    
    return fig

def create_stakeholder_sentiment_chart(stakeholder_df):
    """Create stakeholder sentiment analysis chart"""
    fig = px.bar(
        stakeholder_df,
        x='stakeholder_type',
        y=['positive', 'negative', 'neutral'],
        title="Sentiment Distribution by Stakeholder Type",
        color_discrete_map={
            'positive': '#2E8B57',
            'negative': '#DC143C',
            'neutral': '#4682B4'
        }
    )
    
    fig.update_layout(
        xaxis_title="Stakeholder Type",
        yaxis_title="Number of Comments",
        height=500,
        xaxis={'tickangle': 45}
    )
    
    return fig

# Main app
st.title("📊 E-Consultation Sentiment Analysis System")
st.markdown("""
This system analyzes stakeholder comments from e-consultation processes, providing:
- **Sentiment Analysis**: Classify comments as positive, negative, or neutral
- **Text Summarization**: Generate concise summaries of feedback  
- **Stakeholder Analysis**: Break down feedback by stakeholder type
""")

# Step 1: Data Input
st.header("Step 1: Load Your Data")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose your CSV file",
        type=['csv'],
        help="Upload a CSV file with columns: id, stakeholder_type, comment_text, provision_reference, submission_date"
    )

with col2:
    st.subheader("📝 Use Sample Data")
    if st.button("Load Sample Data", type="secondary"):
        sample_data = load_sample_data()
        if sample_data is not None:
            st.session_state['data'] = sample_data
            st.success(f"✅ Sample data loaded! {len(sample_data)} comments")
        else:
            st.error("❌ Could not load sample data")

# Process data
data = None
if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file)
        st.session_state['data'] = data
        st.success(f"✅ File uploaded successfully! {len(data)} comments loaded")
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")

if 'data' in st.session_state:
    data = st.session_state['data']

# Step 2: Preview Data (if data is loaded)
if data is not None:
    st.header("Step 2: Preview Your Data")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", len(data))
    with col2:
        st.metric("Stakeholder Types", data['stakeholder_type'].nunique())
    with col3:
        st.metric("Unique Provisions", data['provision_reference'].nunique())
    
    with st.expander("View Sample Data"):
        st.dataframe(data.head())
    
    # Step 3: Run Analysis
    st.header("Step 3: Run Analysis")
    
    if st.button("🔍 Run Sentiment Analysis", type="primary"):
        with st.spinner("Analyzing comments... This may take a few moments."):
            results = analyze_data(data)
            st.session_state['results'] = results
        st.success("✅ Analysis completed!")
        st.rerun()

# Step 4: Display Results (if analysis is complete)
if 'results' in st.session_state and st.session_state['results'] is not None:
    results = st.session_state['results']
    
    st.header("Step 4: View Results")
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Sentiment Analysis", "📝 Text Summaries", "📋 Detailed Results", "📥 Download"])
    
    with tab1:
        st.subheader("Sentiment Analysis Results")
        
        # Overall metrics
        summary = results['overall_summary']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Positive", f"{summary['positive_percentage']}%", f"{summary['positive']} comments")
        with col2:
            st.metric("Negative", f"{summary['negative_percentage']}%", f"{summary['negative']} comments")
        with col3:
            st.metric("Neutral", f"{summary['neutral_percentage']}%", f"{summary['neutral']} comments")
        with col4:
            st.metric("Avg. Sentiment", f"{summary['average_vader_score']}", "VADER Score")
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = create_sentiment_pie_chart(summary)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if results['stakeholder_analysis'] is not None and len(results['stakeholder_analysis']) > 0:
                fig_stakeholder = create_stakeholder_sentiment_chart(results['stakeholder_analysis'])
                st.plotly_chart(fig_stakeholder, use_container_width=True)
            else:
                st.info("No stakeholder analysis available")
    
    with tab2:
        st.subheader("Text Summaries")
        
        # Overall summary
        st.markdown("### 📋 Overall Summary")
        overall_summary = results['overall_text_summary']
        st.write(overall_summary['main_summary'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Key Themes:**")
            for theme in overall_summary['key_themes']:
                st.write(f"• {theme}")
        
        with col2:
            st.markdown("**Top Keywords:**")
            for word, freq in list(overall_summary['top_keywords'].items())[:5]:
                st.write(f"• {word}: {freq} mentions")
        
        # Sentiment-based summaries
        st.markdown("### 😊 Summaries by Sentiment")
        for sentiment, summary_data in results['sentiment_summaries'].items():
            with st.expander(f"{sentiment.title()} Comments ({summary_data['comment_count']} comments)"):
                st.write(summary_data['summary'])
                if summary_data['key_phrases']:
                    st.write("**Key phrases:**", ", ".join([phrase[0] for phrase in summary_data['key_phrases'][:5]]))
        
        # Stakeholder-based summaries
        st.markdown("### 👥 Summaries by Stakeholder")
        for stakeholder, summary_data in results['stakeholder_summaries'].items():
            with st.expander(f"{stakeholder} ({summary_data['comment_count']} comments)"):
                st.write(summary_data['summary'])
                if summary_data['key_phrases']:
                    st.write("**Key phrases:**", ", ".join([phrase[0] for phrase in summary_data['key_phrases'][:5]]))
    
    with tab3:
        st.subheader("Detailed Analysis Results")
        
        # Individual comment analysis
        st.markdown("### Individual Comment Analysis")
        analysis_df = results['analysis_df']
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            sentiment_filter = st.selectbox(
                "Filter by Sentiment",
                ['All'] + list(analysis_df['consensus_label'].unique())
            )
        with col2:
            stakeholder_filter = st.selectbox(
                "Filter by Stakeholder",
                ['All'] + list(analysis_df['stakeholder_type'].unique())
            )
        
        # Apply filters
        filtered_df = analysis_df.copy()
        if sentiment_filter != 'All':
            filtered_df = filtered_df[filtered_df['consensus_label'] == sentiment_filter]
        if stakeholder_filter != 'All':
            filtered_df = filtered_df[filtered_df['stakeholder_type'] == stakeholder_filter]
        
        # Display filtered results
        st.write(f"Showing {len(filtered_df)} of {len(analysis_df)} comments")
        
        display_columns = [
            'stakeholder_type', 'comment_text', 'consensus_label', 
            'vader_compound', 'textblob_polarity', 'provision_reference'
        ]
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            height=400
        )
    
    with tab4:
        st.subheader("Download Results")
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            # Download detailed analysis
            csv_data = results['analysis_df'].to_csv(index=False)
            st.download_button(
                "📄 Download Detailed Analysis (CSV)",
                csv_data,
                "sentiment_analysis_results.csv",
                "text/csv"
            )
        
        with col2:
            # Download summary report
            summary = results['overall_summary']
            overall_summary = results['overall_text_summary']
            
            summary_text = f"""E-Consultation Sentiment Analysis Summary Report

Total Comments: {summary['total_comments']}
Positive: {summary['positive']} ({summary['positive_percentage']}%)
Negative: {summary['negative']} ({summary['negative_percentage']}%)
Neutral: {summary['neutral']} ({summary['neutral_percentage']}%)

Average VADER Score: {summary['average_vader_score']}
Average TextBlob Score: {summary['average_textblob_score']}

Overall Summary:
{overall_summary['main_summary']}

Key Themes: {', '.join(overall_summary['key_themes'])}
"""
            
            st.download_button(
                "📑 Download Summary Report (TXT)",
                summary_text,
                "sentiment_summary_report.txt",
                "text/plain"
            )

else:
    # Welcome screen
    st.info("""
    👆 **Get Started:**
    1. **Load your data** using one of the options above
    2. **Preview your data** to make sure it loaded correctly
    3. **Run the analysis** with the big button
    4. **View your results** in the tabs that appear
    """)
    
    # Show expected data format
    st.subheader("📋 Expected CSV Format")
    sample_structure = pd.DataFrame({
        'id': [1, 2, 3],
        'stakeholder_type': ['Corporate Entity', 'Individual Lawyer', 'CA Firm'],
        'comment_text': [
            'The proposed amendment is well-structured...',
            'I strongly disagree with the proposed changes...',
            'The draft provides clarity but timeline seems aggressive...'
        ],
        'provision_reference': ['Section 12A', 'Section 45B', 'Section 23C'],
        'submission_date': ['2024-01-15', '2024-01-16', '2024-01-17']
    })
    st.dataframe(sample_structure, use_container_width=True)
