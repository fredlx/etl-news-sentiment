try:
    from .resample_sentiment_cython import resample_sentiment_scores_cython as resample_sentiment_scores
    USING_CYTHON = True
except ImportError:
    # fallback in case cython built is missing
    from .resample_sentiment_fast import resample_sentiment_scores_fast as resample_sentiment_scores
    USING_CYTHON = False