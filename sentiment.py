"""News sentiment analysis using VADER over recent headlines."""
import logging

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from data_fetch import fetch_news

log = logging.getLogger(__name__)
_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(symbol: str):
    """Return (score, label, headline_count).

    score is the mean VADER compound in [-1, 1]; label is one of
    'positive' / 'neutral' / 'negative'. If no headlines are found the
    score is 0.0 and label is 'neutral'.
    """
    headlines = fetch_news(symbol)
    if not headlines:
        return 0.0, "neutral", 0

    scores = [_analyzer.polarity_scores(h)["compound"] for h in headlines]
    avg = sum(scores) / len(scores)

    if avg >= 0.15:
        label = "positive"
    elif avg <= -0.15:
        label = "negative"
    else:
        label = "neutral"
    return round(avg, 3), label, len(headlines)
