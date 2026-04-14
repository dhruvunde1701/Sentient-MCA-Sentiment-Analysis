import re
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()

    def clean_text(self, text):
        """Clean and preprocess text"""
        if pd.isna(text):
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", str(text)).strip()
        return text

    def analyze_sentiment_vader(self, text):
        """Analyze sentiment using VADER"""
        text = self.clean_text(text)
        if not text:
            return {"compound": 0, "pos": 0, "neu": 1, "neg": 0, "label": "neutral"}

        scores = self.vader_analyzer.polarity_scores(text)

        # Classify based on compound score
        if scores["compound"] >= 0.05:
            label = "positive"
        elif scores["compound"] <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "compound": scores["compound"],
            "pos": scores["pos"],
            "neu": scores["neu"],
            "neg": scores["neg"],
            "label": label,
        }

    def analyze_sentiment_textblob(self, text):
        """Analyze sentiment using TextBlob"""
        text = self.clean_text(text)
        if not text:
            return {"polarity": 0, "subjectivity": 0, "label": "neutral"}

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Classify based on polarity
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {"polarity": polarity, "subjectivity": subjectivity, "label": label}

    def analyze_comments_batch(self, comments):
        """Analyze sentiment for a batch of comments"""
        results = []

        for i, comment in enumerate(comments):
            vader_result = self.analyze_sentiment_vader(comment)
            textblob_result = self.analyze_sentiment_textblob(comment)

            # Combine results (remove comment_text to avoid duplication)
            result = {
                "comment_index": i,
                "vader_compound": vader_result["compound"],
                "vader_label": vader_result["label"],
                "textblob_polarity": textblob_result["polarity"],
                "textblob_label": textblob_result["label"],
                "consensus_label": self._get_consensus_label(
                    vader_result["label"], textblob_result["label"]
                ),
            }
            results.append(result)

        return pd.DataFrame(results)

    def _get_consensus_label(self, vader_label, textblob_label):
        """Get consensus sentiment label from both analyzers"""
        if vader_label == textblob_label:
            return vader_label
        elif "neutral" in [vader_label, textblob_label]:
            return "neutral"
        else:
            # If they disagree and neither is neutral, default to neutral
            return "neutral"

    def get_overall_sentiment_summary(self, df):
        """Get overall sentiment summary statistics"""
        sentiment_counts = df["consensus_label"].value_counts()
        total_comments = len(df)

        summary = {
            "total_comments": total_comments,
            "positive": sentiment_counts.get("positive", 0),
            "negative": sentiment_counts.get("negative", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "positive_percentage": round(
                (sentiment_counts.get("positive", 0) / total_comments) * 100, 2
            ),
            "negative_percentage": round(
                (sentiment_counts.get("negative", 0) / total_comments) * 100, 2
            ),
            "neutral_percentage": round(
                (sentiment_counts.get("neutral", 0) / total_comments) * 100, 2
            ),
            "average_vader_score": round(df["vader_compound"].mean(), 3),
            "average_textblob_score": round(df["textblob_polarity"].mean(), 3),
        }

        return summary

    def analyze_sentiment_by_stakeholder(
        self, df, stakeholder_column="stakeholder_type"
    ):
        """Analyze sentiment broken down by stakeholder type"""
        if stakeholder_column not in df.columns:
            return None

        stakeholder_analysis = []
        for stakeholder in df[stakeholder_column].unique():
            stakeholder_df = df[df[stakeholder_column] == stakeholder]
            sentiment_counts = stakeholder_df["consensus_label"].value_counts()

            analysis = {
                "stakeholder_type": stakeholder,
                "total_comments": len(stakeholder_df),
                "positive": sentiment_counts.get("positive", 0),
                "negative": sentiment_counts.get("negative", 0),
                "neutral": sentiment_counts.get("neutral", 0),
                "avg_vader_score": round(stakeholder_df["vader_compound"].mean(), 3),
                "avg_textblob_score": round(
                    stakeholder_df["textblob_polarity"].mean(), 3
                ),
            }
            stakeholder_analysis.append(analysis)

        return pd.DataFrame(stakeholder_analysis)
