# E-Consultation Sentiment Analysis MVP

Deployed Prototype - https://sentient-sentiment-analysis.streamlit.app/

## Overview

This MVP system analyzes stakeholder comments from e-consultation processes and provides:

- **Sentiment Analysis**: Classifies comments as positive, negative, or neutral using VADER and TextBlob
- **Text Summarization**: Generates concise summaries of feedback using extractive summarization
- **Word Cloud Visualization**: Shows keyword density and themes across comments

## Features

### ✅ Implemented Features

1. **Sentiment Analysis**
   - Individual comment sentiment analysis
   - Overall sentiment distribution
   - Stakeholder-wise sentiment breakdown
   - Consensus scoring using multiple models

2. **Text Summarization** 
   - Overall summary of all comments
   - Summaries grouped by sentiment
   - Summaries grouped by stakeholder type
   - Key phrase extraction

3. **Word Cloud Visualization**
   - Overall word cloud
   - Sentiment-specific word clouds
   - Stakeholder-specific word clouds
   - Word frequency analysis

4. **Interactive Web Interface**
   - File upload for CSV data
   - Real-time analysis
   - Interactive visualizations
   - Downloadable results

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Installation

1. **Clone/Download the project**
   ```bash
   cd econsultation-sentiment-mvp
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLTK data** (if not automatically downloaded)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon'); nltk.download('brown'); nltk.download('punkt_tab')"
   ```

### Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Access the application**
   - Open your browser and go to `http://localhost:8501`
   - The application will load with a welcome screen

## Usage Guide

### Data Format

The system expects a CSV file with the following columns:

| Column | Description | Required |
|--------|-------------|----------|
| `id` | Unique identifier for each comment | Yes |
| `stakeholder_type` | Type of stakeholder (e.g., "Corporate Entity", "Individual") | Yes |
| `comment_text` | The actual comment/feedback text | Yes |
| `provision_reference` | Reference to specific provision/section | No |
| `submission_date` | Date of submission | No |

### Sample Data

A sample dataset is included in `data/sample_comments.csv` with 15 consultation comments covering various stakeholder types and sentiments.

### Using the System

1. **Load Data**
   - Click "Load Sample Data" to try with sample data, or
   - Upload your own CSV file using the file uploader

2. **Run Analysis**
   - Click "Run Analysis" button
   - Wait for processing to complete (usually takes 10-30 seconds)

3. **View Results**
   - **Sentiment Analysis Tab**: Overall metrics, pie charts, stakeholder breakdowns
   - **Text Summaries Tab**: Automated summaries by sentiment and stakeholder
   - **Word Clouds Tab**: Visual representations of key terms and themes
   - **Detailed Results Tab**: Individual comment analysis and download options

### Output Files

The system provides downloadable results:

- **Detailed Analysis CSV**: Complete analysis with sentiment scores for each comment
- **Summary Report TXT**: Executive summary with key insights and metrics

## Project Structure

```
econsultation-sentiment-mvp/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── data/
│   └── sample_comments.csv        # Sample consultation data
├── src/
│   ├── sentiment_analyzer.py      # Sentiment analysis functionality
│   ├── text_summarizer.py        # Text summarization functionality
│   └── wordcloud_generator.py    # Word cloud generation
└── venv/                         # Virtual environment (created after setup)
```

## Technical Details

### Sentiment Analysis
- **VADER**: Rule-based sentiment analyzer optimized for social media text
- **TextBlob**: Pattern-based sentiment analysis with polarity scoring
- **Consensus Method**: Combines both approaches for more reliable results

### Text Summarization
- **Extractive Summarization**: Uses LSA (Latent Semantic Analysis) and Luhn algorithms
- **Key Phrase Extraction**: Frequency-based approach with stop word filtering
- **Multiple Groupings**: Summarizes by sentiment, stakeholder type, and overall

### Word Cloud Generation
- **Custom Stop Words**: Filtered for consultation-specific terms
- **Color Coding**: Different color schemes for sentiment categories
- **Multiple Views**: Overall, by sentiment, and by stakeholder type

## Limitations and Future Enhancements

### Current Limitations
- Works with English text only
- Basic extractive summarization (no advanced abstractive methods)
- Limited to CSV file input
- No user authentication or multi-tenancy

### Potential Enhancements
- **Advanced NLP**: Integration with transformer models (BERT, RoBERTa)
- **Multi-language Support**: Support for regional languages
- **Database Integration**: PostgreSQL/MongoDB for data persistence
- **API Endpoints**: RESTful API for programmatic access
- **Real-time Processing**: Stream processing for large datasets
- **Advanced Visualizations**: Network graphs, topic modeling
- **Export Options**: PDF reports, PowerPoint presentations

## Troubleshooting

### Common Issues

1. **NLTK Data Not Found**
   ```bash
   python -c "import nltk; nltk.download('all-nltk-data')"
   ```

2. **Port Already in Use**
   ```bash
   streamlit run app.py --server.port 8502
   ```

3. **Memory Issues with Large Files**
   - Process files in smaller batches
   - Consider upgrading to cloud deployment

4. **Dependencies Issues**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

## Support and Contribution

This is an MVP built for demonstration purposes. For production deployment, consider:

- Proper error handling and logging
- Security measures for file uploads
- Performance optimization for large datasets
- User authentication and authorization
- Data backup and recovery procedures

## License

This project is developed as an MVP for the E-consultation sentiment analysis system.

---

**Built for Ministry of Corporate Affairs E-consultation Module**
