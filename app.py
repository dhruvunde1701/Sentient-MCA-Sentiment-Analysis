import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import datetime
import json
import base64

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
    initial_sidebar_state="collapsed"  # FIX 1: Collapse sidebar by default so charts have full width
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'user_actions' not in st.session_state:
    st.session_state.user_actions = []
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.datetime.now()

def log_action(action, details=None):
    """Log user actions with timestamp"""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "action": action,
        "details": details or {}
    }
    if 'user_actions' not in st.session_state:
        st.session_state.user_actions = []
    st.session_state.user_actions.append(log_entry)
    print(f"[{timestamp}] USER ACTION: {action} - {details}")

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
    sentiment_analyzer = SentimentAnalyzer()
    text_summarizer = TextSummarizer()
    wordcloud_generator = None

    sentiment_results = sentiment_analyzer.analyze_comments_batch(df['comment_text'].values.tolist())

    analysis_df = df.copy()
    analysis_df = pd.concat([analysis_df.reset_index(drop=True), sentiment_results.reset_index(drop=True)], axis=1)

    overall_summary = sentiment_analyzer.get_overall_sentiment_summary(analysis_df)
    stakeholder_analysis = sentiment_analyzer.analyze_sentiment_by_stakeholder(analysis_df)

    overall_text_summary = text_summarizer.generate_overall_summary(analysis_df)
    sentiment_summaries = text_summarizer.summarize_by_sentiment(analysis_df)
    stakeholder_summaries = text_summarizer.summarize_by_stakeholder(analysis_df)

    # Generate word cloud artifacts separately so analysis still succeeds if
    # NLP resources for wordcloud tokenization are unavailable.
    wordcloud_results = {
        'overall_wordcloud': None,
        'sentiment_wordclouds': {},
        'overall_word_frequencies': {},
        'frequency_chart_base64': None,
        'error': None
    }
    try:
        wordcloud_generator = WordCloudGenerator()
        overall_texts = analysis_df['comment_text'].dropna().tolist()
        overall_wordcloud = wordcloud_generator.generate_wordcloud(overall_texts, max_words=80)
        sentiment_wordclouds = wordcloud_generator.generate_sentiment_wordclouds(analysis_df)
        overall_word_frequencies = wordcloud_generator.get_word_frequencies(overall_texts, top_n=20)
        frequency_chart_base64 = wordcloud_generator.create_frequency_bar_chart(
            overall_word_frequencies,
            title="Top Words Across All Comments"
        )

        wordcloud_results.update({
            'overall_wordcloud': overall_wordcloud,
            'sentiment_wordclouds': sentiment_wordclouds,
            'overall_word_frequencies': overall_word_frequencies,
            'frequency_chart_base64': frequency_chart_base64
        })
    except Exception as e:
        wordcloud_results['error'] = str(e)

    return {
        'analysis_df': analysis_df,
        'overall_summary': overall_summary,
        'stakeholder_analysis': stakeholder_analysis,
        'overall_text_summary': overall_text_summary,
        'sentiment_summaries': sentiment_summaries,
        'stakeholder_summaries': stakeholder_summaries,
        'wordcloud_results': wordcloud_results
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
        height=450,           # FIX 2: Slightly taller
        margin=dict(t=50, b=20, l=20, r=20)  # FIX 3: Tighter margins
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
        height=450,           # FIX 4: Match pie chart height
        margin=dict(t=50, b=120, l=40, r=20),  # FIX 5: Extra bottom margin for rotated labels
        xaxis={'tickangle': 35},
        legend_title="Sentiment"
    )
    return fig

def inject_custom_css():
    """Inject dashboard-like styling to match desired UI."""
    st.markdown(
        """
        <style>
            .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1250px; }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.25rem; background: #e9edf3; border-radius: 10px; padding: 4px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 38px; border-radius: 8px; font-weight: 600; color: #64748b;
            }
            .stTabs [aria-selected="true"] {
                background-color: #ffffff !important; color: #0f172a !important;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.10);
            }
            .dash-card {
                border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 12px;
                background: #ffffff; text-align: center; min-height: 108px;
            }
            .dash-card-title { font-size: 0.88rem; color: #64748b; font-weight: 600; margin-bottom: 8px; }
            .dash-card-value { font-size: 2rem; font-weight: 700; line-height: 1; margin-bottom: 8px; }
            .dash-card-sub { color: #94a3b8; font-size: 0.82rem; }
            .panel {
                border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; background: #ffffff;
            }
            .pill {
                display: inline-block; margin: 0 8px 8px 0; padding: 5px 10px; border-radius: 999px;
                background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0; font-size: 0.82rem; font-weight: 500;
            }
            .list-item-warning, .list-item-success {
                border-radius: 8px; padding: 8px 10px; margin-top: 8px; font-size: 0.92rem;
            }
            .list-item-warning { background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12; }
            .list-item-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #14532d; }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_metric_card(title, value, subtitle, color):
    st.markdown(
        f"""
        <div class="dash-card">
            <div class="dash-card-title">{title}</div>
            <div class="dash-card-value" style="color:{color};">{value}</div>
            <div class="dash-card-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def extract_representative_points(summary_data, max_points=4):
    """Extract concise phrases from summarizer output."""
    key_phrases = summary_data.get('key_phrases', [])
    points = []
    for phrase, _freq in key_phrases:
        cleaned = str(phrase).strip()
        if cleaned and cleaned.lower() not in {p.lower() for p in points}:
            points.append(cleaned.capitalize())
        if len(points) >= max_points:
            break
    return points

def main():
    inject_custom_css()

    if len(st.session_state.user_actions) == 0:
        log_action("session_started", {"timestamp": st.session_state.session_start.isoformat()})

    # Header
    st.title("E-Consultation Sentiment Analysis")
    st.markdown(
        """
        This MVP analyzes stakeholder comments from e-consultation processes, providing:
        - **Sentiment Analysis**: Classify comments as positive, negative, or neutral
        - **Text Summarization**: Generate concise summaries of feedback
        - **Stakeholder Analysis**: Break down feedback by stakeholder type
        """
    )

    # Sidebar
    st.sidebar.header("📁 Data Input")

    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="Upload a CSV file with columns: id, stakeholder_type, comment_text, provision_reference, submission_date"
    )

    if st.sidebar.button("Load Sample Data"):
        log_action("load_sample_data_clicked")
        sample_data = load_sample_data()
        if sample_data is not None:
            st.session_state.data = sample_data
            st.session_state.analysis_results = None
            st.sidebar.success("Sample data loaded successfully!")
            log_action("sample_data_loaded", {"comments_count": len(sample_data)})
        else:
            st.sidebar.error("Could not load sample data. Please check if data/sample_comments.csv exists.")
            log_action("sample_data_load_failed")

    # FIX 6: Changed `if` to `with` — the original bug causing blank screen
    with st.sidebar.expander("📊 User Actions Log", expanded=False):
        if st.session_state.user_actions:
            st.write(f"**Total Actions:** {len(st.session_state.user_actions)}")
            recent_actions = st.session_state.user_actions[-10:]
            for i, action in enumerate(reversed(recent_actions)):
                time_str = action['timestamp'].split('T')[1].split('.')[0]
                st.write(f"**{time_str}** - {action['action']}")
                if action['details']:
                    details_str = ", ".join([f"{k}: {v}" for k, v in action['details'].items() if k != 'timestamp'])
                    if details_str:
                        st.write(f"  ↳ {details_str}")
            log_data = json.dumps(st.session_state.user_actions, indent=2)
            st.download_button(
                "Download Full Action Log",
                log_data,
                "user_actions_log.json",
                "application/json"
            )
        else:
            st.write("No actions recorded yet")

    # Process uploaded file
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.data = df
            st.session_state.analysis_results = None
            st.sidebar.success(f"File uploaded successfully! {len(df)} comments loaded.")
            log_action("file_uploaded", {
                "filename": uploaded_file.name,
                "comments_count": len(df),
                "columns": list(df.columns),
                "file_size": uploaded_file.size
            })
        except Exception as e:
            st.sidebar.error(f"Error loading file: {str(e)}")
            log_action("file_upload_failed", {
                "filename": uploaded_file.name if uploaded_file else "unknown",
                "error": str(e)
            })

    # Main content
    if st.session_state.data is not None:
        df = st.session_state.data

        st.subheader("📈 Data Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Comments", len(df))
        with col2:
            st.metric("Stakeholder Types", df['stakeholder_type'].nunique())
        with col3:
            st.metric("Unique Provisions", df['provision_reference'].nunique())

        with st.expander("View Sample Data"):
            log_action("view_sample_data_expanded")
            st.dataframe(df.head(), use_container_width=True)  # FIX 7: use_container_width

        if st.button("🔍 Run Analysis", type="primary"):
            log_action("analysis_started", {
                "comments_count": len(df),
                "stakeholder_types": df['stakeholder_type'].nunique(),
                "provisions": df['provision_reference'].nunique()
            })
            with st.spinner("Analyzing comments... This may take a few moments."):
                start_time = datetime.datetime.now()
                try:
                    st.session_state.analysis_results = analyze_data(df)
                except Exception as e:
                    import traceback
                    st.error(f"Analysis failed: {e}")
                    st.code(traceback.format_exc())
                    return
                end_time = datetime.datetime.now()
                processing_time = (end_time - start_time).total_seconds()

            log_action("analysis_completed", {
                "processing_time_seconds": processing_time,
                "results_generated": st.session_state.analysis_results is not None
            })
            st.success("Analysis completed!")
            st.rerun()

        # Display results
        if st.session_state.analysis_results is not None:
            results = st.session_state.analysis_results

            log_action("results_displayed", {
                "tabs_available": ["Sentiment Analysis", "AI Summary", "Word Cloud", "Detailed Results", "Download"]
            })

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Sentiment Analysis",
                "AI Summary",
                "Word Cloud",
                "Detailed Results",
                "Download"
            ])

            with tab1:
                st.subheader("Sentiment Analysis")

                summary = results['overall_summary']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    render_metric_card("In Agreement", f"{summary['positive_percentage']}%", f"{summary['positive']} comments", "#22c55e")
                with col2:
                    render_metric_card("In Removal", f"{summary['negative_percentage']}%", f"{summary['negative']} comments", "#ef4444")
                with col3:
                    render_metric_card("In Modification", f"{summary['neutral_percentage']}%", f"{summary['neutral']} comments", "#2563eb")
                with col4:
                    render_metric_card("Avg. Sentiment", f"{summary['average_vader_score']}", "Score", "#2563eb")

                st.markdown("---")

                # FIX 8: use_container_width=True so charts fill their column properly
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
                st.subheader("AI Summary")
                overall_summary = results['overall_text_summary']
                st.markdown(f'<div class="panel">{overall_summary["main_summary"]}</div>', unsafe_allow_html=True)

                st.markdown("### Thematic Highlights")
                themes = overall_summary.get('key_themes', [])
                if themes:
                    theme_html = "".join([f'<span class="pill">{theme}</span>' for theme in themes])
                    st.markdown(theme_html, unsafe_allow_html=True)
                else:
                    st.info("No themes available.")

                concerns = extract_representative_points(results['sentiment_summaries'].get('negative', {}), max_points=4)
                recommendations = extract_representative_points(results['sentiment_summaries'].get('positive', {}), max_points=4)

                st.markdown("### Main Concerns Raised")
                if concerns:
                    for concern in concerns:
                        st.markdown(f'<div class="list-item-warning">{concern}</div>', unsafe_allow_html=True)
                else:
                    st.info("No concern points available.")

                st.markdown("### Recommendations")
                if recommendations:
                    for rec in recommendations:
                        st.markdown(f'<div class="list-item-success">{rec}</div>', unsafe_allow_html=True)
                else:
                    st.info("No recommendation points available.")

            with tab3:
                st.subheader("Word Frequency Analysis")
                wc_results = results.get('wordcloud_results', {})

                if wc_results.get('error'):
                    st.warning(
                        "Word cloud generation encountered an issue and was skipped. "
                        f"Details: {wc_results['error']}"
                    )

                overall_wordcloud = wc_results.get('overall_wordcloud')
                if overall_wordcloud is not None:
                    st.image(overall_wordcloud.to_array(), use_container_width=True)
                else:
                    st.info("No overall word cloud available for this dataset.")

                st.markdown("### Top Keywords")
                keyword_items = list(wc_results.get('overall_word_frequencies', {}).items())
                if keyword_items:
                    rows = [keyword_items[i:i+4] for i in range(0, min(len(keyword_items), 12), 4)]
                    for row in rows:
                        cols = st.columns(4)
                        for idx, (word, freq) in enumerate(row):
                            with cols[idx]:
                                st.markdown(
                                    f"""
                                    <div class="dash-card">
                                        <div class="dash-card-title">{word}</div>
                                        <div class="dash-card-sub">{freq} mentions</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                else:
                    st.info("No keyword frequencies available.")

                freq_chart = wc_results.get('frequency_chart_base64')
                if freq_chart:
                    st.markdown("### Frequency Chart")
                    st.image(base64.b64decode(freq_chart), use_container_width=True)

                sentiment_wordclouds = wc_results.get('sentiment_wordclouds', {})
                st.markdown("### Word Clouds by Sentiment")
                if sentiment_wordclouds:
                    for sentiment, cloud in sentiment_wordclouds.items():
                        with st.expander(f"{sentiment.title()}"):
                            st.image(cloud.to_array(), use_container_width=True)
                else:
                    st.info("No sentiment-specific word clouds available.")

            with tab4:
                st.subheader("Detailed Analysis Results")
                st.markdown("### Individual Comment Analysis")
                analysis_df = results['analysis_df']

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

                filtered_df = analysis_df.copy()
                if sentiment_filter != 'All':
                    filtered_df = filtered_df[filtered_df['consensus_label'] == sentiment_filter]
                if stakeholder_filter != 'All':
                    filtered_df = filtered_df[filtered_df['stakeholder_type'] == stakeholder_filter]

                st.write(f"Showing {len(filtered_df)} of {len(analysis_df)} comments")

                display_columns = [
                    'stakeholder_type', 'comment_text', 'consensus_label',
                    'vader_compound', 'textblob_polarity', 'provision_reference'
                ]
                # FIX 9: use_container_width instead of deprecated width=True
                st.dataframe(
                    filtered_df[display_columns],
                    use_container_width=True,
                    height=400
                )

            with tab5:
                st.subheader("Download Results")

                col1, col2 = st.columns(2)
                with col1:
                    csv_data = results['analysis_df'].to_csv(index=False)
                    st.download_button(
                        "Download Detailed Analysis (CSV)",
                        csv_data,
                        "sentiment_analysis_results.csv",
                        "text/csv"
                    )
                with col2:
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
                        "Download Summary Report (TXT)",
                        summary_text,
                        "sentiment_summary_report.txt",
                        "text/plain"
                    )

    else:
        st.info(
            """
            👆 **Get Started:**
            1. Upload a CSV file with consultation comments using the sidebar
            2. Or click "Load Sample Data" to try the system with sample data
            3. Click "Run Analysis" to process the comments

            **Required CSV Format:**
            - `id`: Unique identifier
            - `stakeholder_type`: Type of stakeholder (e.g., Corporate Entity, Individual)
            - `comment_text`: The actual comment/feedback text
            - `provision_reference`: Reference to specific provision (optional)
            - `submission_date`: Date of submission (optional)
            """
        )

        st.subheader("📋 Expected Data Format")
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

if __name__ == "__main__":
    main()