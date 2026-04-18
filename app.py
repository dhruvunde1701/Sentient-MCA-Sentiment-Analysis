import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import datetime
import json
import io
import hashlib

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
if 'uploaded_file_id' not in st.session_state:
    st.session_state.uploaded_file_id = None

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
    labels = ['In Agreement', 'In Removal', 'In Modification']
    values = [summary['positive'], summary['negative'], summary['neutral']]
    colors = ['#22c55e', '#ef4444', '#3b82f6']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent',
        hole=0.05
    )])

    fig.update_layout(
        title="Overall Sentiment Distribution",
        height=360,
        margin=dict(t=45, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=-0.08, x=0.18)
    )
    return fig

def create_stakeholder_sentiment_chart(stakeholder_df):
    """Create stakeholder sentiment analysis chart"""
    chart_df = stakeholder_df.rename(
        columns={
            'positive': 'In Agreement',
            'negative': 'In Removal',
            'neutral': 'In Modification'
        }
    )
    fig = px.bar(
        chart_df,
        x='stakeholder_type',
        y=['In Agreement', 'In Modification', 'In Removal'],
        title="Sentiment by Stakeholder Type",
        color_discrete_map={
            'In Agreement': '#22c55e',
            'In Removal': '#ef4444',
            'In Modification': '#3b82f6'
        }
    )

    fig.update_layout(
        barmode='stack',
        xaxis_title="",
        yaxis_title="Number of Comments",
        height=360,
        margin=dict(t=45, b=100, l=25, r=10),
        xaxis={'tickangle': 48},
        legend_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=-0.14, x=0.2)
    )
    return fig

def inject_custom_styles():
    """Inject custom CSS for dashboard-style UI."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.7rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        [data-testid="stAppViewContainer"] {
            background: #f7f9fc;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] * {
            color: #1f2937;
        }
        [data-testid="stHeader"] {
            background: #f7f9fc;
            border-bottom: 1px solid #dbe2ea;
        }
        [data-testid="stToolbar"] {
            right: 0.75rem;
        }
        [data-testid="stToolbar"] button {
            color: #475569 !important;
        }
        [data-testid="stDecoration"] {
            background: #f7f9fc;
        }
        [data-testid="stSidebar"] {
            background: #f3f6fb;
            border-right: 1px solid #dbe2ea;
        }
        [data-testid="stSidebar"] * {
            color: #1f2937;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            background: #ffffff;
            border: 1px dashed #cbd5e1;
        }
        [data-testid="stSidebar"] .stButton > button {
            background: #ffffff;
            color: #1f2937;
            border: 1px solid #cbd5e1;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: #94a3b8;
            background: #f8fafc;
            color: #0f172a;
        }
        [data-testid="stExpander"] details,
        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            background: #f8fafc;
            border: 1px solid #dbe2ea;
            border-radius: 10px;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            background: #f1f5f9 !important;
            color: #1f2937 !important;
            border-radius: 10px;
        }
        [data-testid="stExpander"] summary:hover,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
            background: #e8eef6 !important;
        }
        .stDownloadButton > button,
        [data-testid="stSidebar"] .stDownloadButton > button {
            background: #ffffff !important;
            color: #1f2937 !important;
            border: 1px solid #cbd5e1 !important;
        }
        .stDownloadButton > button:hover,
        [data-testid="stSidebar"] .stDownloadButton > button:hover {
            background: #f8fafc !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"] {
            background: #ffffff !important;
            border: 1px solid #dbe2ea;
            border-radius: 12px;
        }
        [data-testid="stDataFrame"] *,
        [data-testid="stDataEditor"] * {
            color: #1f2937 !important;
        }
        [data-testid="stDataFrame"] [role="grid"],
        [data-testid="stDataEditor"] [role="grid"] {
            background: #ffffff !important;
        }
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataEditor"] [role="columnheader"] {
            background: #f8fafc !important;
            color: #334155 !important;
        }
        .app-shell {
            border: 1px solid #dde3eb;
            border-radius: 12px;
            padding: 12px;
            background: #f8fafc;
            margin-bottom: 0.9rem;
        }
        h1 {
            font-size: 1.5rem !important;
            margin-bottom: 0.25rem !important;
        }
        h2, h3 {
            color: #1f2937;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe2ea;
            border-radius: 10px;
            padding: 12px 10px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }
        [data-testid="stMetricLabel"] {
            justify-content: center;
            font-weight: 600;
            color: #6b7280;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
        }
        .chip-wrap {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin: 6px 0 10px 0;
        }
        .chip {
            background: #f3f4f6;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .panel-card {
            border: 1px solid #e6e8ee;
            border-radius: 14px;
            background: #ffffff;
            padding: 10px;
            margin-bottom: 10px;
        }
        .chart-panel {
            border: 1px solid #dbe2ea;
            border-radius: 10px;
            background: #ffffff;
            padding: 10px 14px 2px 14px;
            min-height: 430px;
        }
        .section-card {
            border: 1px solid #dbe2ea;
            border-radius: 10px;
            background: #ffffff;
            padding: 12px 14px;
            margin-top: 10px;
        }
        .list-card-warning {
            border: 1px solid #fde2c1;
            background: #fff8ef;
            color: #7c4a03;
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-size: 0.92rem;
        }
        .wordcloud-panel {
            border: 1px solid #dbe2ea;
            border-radius: 10px;
            background: radial-gradient(circle at center, #ffffff 0%, #f1f5f9 75%);
            padding: 14px;
        }
        .list-card-success {
            border: 1px solid #cfead9;
            background: #edf9f2;
            color: #14532d;
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            font-size: 0.92rem;
        }
        div[role="radiogroup"] {
            background: #dfe6ef;
            border-radius: 12px;
            padding: 4px !important;
            gap: 4px;
            border: 1px solid #d3dce7;
        }
        div[role="radiogroup"] > label {
            background: transparent;
            border-radius: 10px;
            padding: 7px 14px !important;
            border: none !important;
        }
        div[role="radiogroup"] > label[data-selected="true"] {
            background: white;
            border: 1px solid #d7dde8 !important;
        }
        .word-keyword-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 12px 0 8px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_theme_pills(themes):
    if not themes:
        return
    pills = "".join([f'<span class="chip">{theme}</span>' for theme in themes[:10]])
    st.markdown(f'<div class="chip-wrap">{pills}</div>', unsafe_allow_html=True)

def render_keyword_cards(keywords):
    if not keywords:
        st.info("No keyword data available.")
        return

    cols = st.columns(4)
    for idx, (word, freq) in enumerate(list(keywords.items())[:12]):
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div class="panel-card" style="text-align: center; border-radius: 10px; border: 1px solid #dbe2ea;">
                    <div style="font-weight: 700; font-size: 1.3rem; line-height:1.2;">{word}</div>
                    <div style="color: #94a3b8; font-size: 0.95rem;">{freq} mentions</div>
                </div>
                """,
                unsafe_allow_html=True
            )

def render_list_cards(items, card_class):
    if not items:
        st.info("No items to display.")
        return
    for item in items[:6]:
        st.markdown(f'<div class="{card_class}">{item}</div>', unsafe_allow_html=True)

def title_case_sentiment(label):
    return str(label).replace("_", " ").title()

def main():
    inject_custom_styles()
    if len(st.session_state.user_actions) == 0:
        log_action("session_started", {"timestamp": st.session_state.session_start.isoformat()})

    # Header
    st.title("📊 E-Consultation Sentiment Analysis System")
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
        current_file_bytes = uploaded_file.getvalue()
        current_file_id = (
            f"{uploaded_file.name}:{uploaded_file.size}:"
            f"{hashlib.md5(current_file_bytes).hexdigest()}"
        )
        if st.session_state.uploaded_file_id != current_file_id:
            try:
                df = pd.read_csv(io.BytesIO(current_file_bytes))
                st.session_state.data = df
                st.session_state.analysis_results = None
                st.session_state.uploaded_file_id = current_file_id
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
    else:
        st.session_state.uploaded_file_id = None

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
                "tabs_available": ["Sentiment Analysis", "AI Summary", "Word Cloud"]
            })

            selected_view = st.radio(
                "Analysis View",
                ["Sentiment Analysis", "AI Summary", "Word Cloud"],
                horizontal=True,
                label_visibility="collapsed"
            )

            if selected_view == "Sentiment Analysis":
                st.subheader("Sentiment Analysis Results")

                summary = results['overall_summary']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("In Agreement", f"{summary['positive_percentage']}%", f"{summary['positive']} comments")
                with col2:
                    st.metric("In Removal", f"{summary['negative_percentage']}%", f"{summary['negative']} comments")
                with col3:
                    st.metric("In Modification", f"{summary['neutral_percentage']}%", f"{summary['neutral']} comments")
                with col4:
                    st.metric("Avg. Sentiment", f"{summary['average_vader_score']}", "Score")

                st.markdown("---")

                # FIX 8: use_container_width=True so charts fill their column properly
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
                    fig_pie = create_sentiment_pie_chart(summary)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
                    if results['stakeholder_analysis'] is not None and len(results['stakeholder_analysis']) > 0:
                        fig_stakeholder = create_stakeholder_sentiment_chart(results['stakeholder_analysis'])
                        st.plotly_chart(fig_stakeholder, use_container_width=True)
                    else:
                        st.info("No stakeholder analysis available")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Individual Comment Analysis")
                st.caption("Detailed sentiment analysis for each stakeholder comment")
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
                    height=330
                )
                st.markdown('</div>', unsafe_allow_html=True)

            elif selected_view == "AI Summary":
                st.subheader("AI Summary")
                overall_summary = results['overall_text_summary']
                sentiment_summaries = results['sentiment_summaries']

                st.markdown("#### Primary Themes")
                render_theme_pills(overall_summary.get('key_themes', []))

                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### ⚠ Main Concerns Raised")
                st.caption("Key concerns expressed by stakeholders")
                concerns = []
                if 'negative' in sentiment_summaries and sentiment_summaries['negative'].get('key_phrases'):
                    concerns.extend([phrase[0].capitalize() for phrase in sentiment_summaries['negative']['key_phrases'][:6]])
                if not concerns:
                    concerns = [f"Concern around {theme.lower()}" for theme in overall_summary.get('key_themes', [])[:4]]
                render_list_cards(concerns, "list-card-warning")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("### ✅ Recommendations")
                st.caption("Actionable suggestions from stakeholder feedback")
                recommendations = []
                if 'positive' in sentiment_summaries and sentiment_summaries['positive'].get('key_phrases'):
                    recommendations.extend(
                        [f"Build on: {phrase[0].capitalize()}" for phrase in sentiment_summaries['positive']['key_phrases'][:6]]
                    )
                if not recommendations:
                    recommendations = [
                        "Conduct additional stakeholder consultations",
                        "Consider exemptions for specific business categories",
                        "Implement changes in phases",
                        "Provide clearer implementation guidelines"
                    ]
                render_list_cards(recommendations, "list-card-success")
                st.markdown('</div>', unsafe_allow_html=True)

            elif selected_view == "Word Cloud":
                st.subheader("Word Frequency Analysis")
                st.caption("Most frequently used words across all stakeholder comments")
                wc_results = results.get('wordcloud_results', {})

                if wc_results.get('error'):
                    st.warning(
                        "Word cloud generation encountered an issue and was skipped. "
                        f"Details: {wc_results['error']}"
                    )

                overall_wordcloud = wc_results.get('overall_wordcloud')
                if overall_wordcloud is not None:
                    st.markdown('<div class="wordcloud-panel">', unsafe_allow_html=True)
                    st.image(overall_wordcloud.to_array(), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No overall word cloud available for this dataset.")
                st.markdown('<div class="word-keyword-title">#&nbsp;&nbsp;Top Keywords</div>', unsafe_allow_html=True)
                render_keyword_cards(wc_results.get('overall_word_frequencies', {}))

                sentiment_wordclouds = wc_results.get('sentiment_wordclouds', {})
                st.markdown("### Word Clouds by Sentiment")
                if sentiment_wordclouds:
                    for sentiment, cloud in sentiment_wordclouds.items():
                        with st.expander(f"{title_case_sentiment(sentiment)}"):
                            st.image(cloud.to_array(), use_container_width=True)
                else:
                    st.info("No sentiment-specific word clouds available.")

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