# (DONE) Some cleaning

import pandas as pd
import numpy as np
import re
#import os
#import nltk
#from nltk.data import find
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer

'''
# Define the NLTK data directory
NLTK_DATA_DIR = os.path.expanduser("~/nltk_data")
if NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.insert(0, NLTK_DATA_DIR)

# ntlk resources check!
def check_nltk_resources():
    """Checks for necessary NLTK resources and downloads if missing"""
    required = [
        "vader_lexicon",  # For SentimentIntensityAnalyzer
        "stopwords",   # For stopwords
        "punkt",       # For word_tokenize
        "punkt_tab",  # fixes error...
        "wordnet",  # For WordNetLemmatizer
        "omw-1.4"   # WordNet’s synonyms & lemmatization support
        ]

    for resource in required:
        #print(f"Checking nltk resource: {resource}")
        nltk.download(resource, download_dir=NLTK_DATA_DIR, quiet=True)
        
check_nltk_resources()
'''

# Load resources once at module level
stop_words = set(stopwords.words('english'))   # stopwords
lemmatizer = WordNetLemmatizer()               # for lemmatization
analyzer = SentimentIntensityAnalyzer()        # VADER for sentiment analysis
stemmer = PorterStemmer()                           # for stemming


def preprocess_text(
    text, 
    stop_words=stop_words, 
    lemmatizer=lemmatizer, 
    stemmer=stemmer, 
    method="lemmatize"
    ):
    """
    Methods: "lemmatize", "stem"
    Usage: df["title"].apply(preprocess_text)
    """
    
    tokens = word_tokenize(text.lower())
    filtered_tokens = [token for token in tokens if token not in stop_words]
    if method == "lemmatize":
        tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    elif method == "stem":
        tokens = [stemmer.stem(token) for token in filtered_tokens]
    return ' '.join(tokens)


def get_sentiment_score(text, analyzer=analyzer):
    """
    Takes a pandas Series of text, preprocesses it, and returns a Series of sentiment scores.
    Handles missing values.
    
    Usage: get_sentiment_score(df["title"])
    """
    # fill na and clean text
    text = text.fillna('').astype(str)
    text_cleaned = text.apply(preprocess_text, method="lemmatize")
    
    # get compound scores
    scores = text_cleaned.apply(lambda text: analyzer.polarity_scores(text)['compound'])
    return scores


def get_sentiment_label(score):
    """Usage: .apply(get_sentiment_label)"""
    if score >= 0.05:
        label = "Positive"
    elif score <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return label


def get_sentiment_score_average(title, description):
    """
    Returns average score if scores are not zero, else select non zero value
    Usage: get_sentiment_score_average(df['title'], df['description'])
    """
    t_scores = get_sentiment_score(title).astype(float)
    d_scores = get_sentiment_score(description).astype(float)
    
    average = np.where(
        (t_scores != 0) & (d_scores != 0), (t_scores + d_scores) / 2,
        np.where(t_scores != 0, t_scores, np.where(d_scores != 0, d_scores, np.nan))
        )
    return pd.Series(average, index=title.index).fillna(0.0)
     

def update_sentiment_scores(df, mask):
    
    # Only work on the subset once
    #mask = df['was_merged']  # "was_merged" is boolean
    to_update = df[mask].copy()   

    # Compute sentiment scores and labels
    to_update['sentiment_score_nltk'] = get_sentiment_score_average(to_update['title'], to_update['description'])
    to_update['sentiment_label_nltk'] = to_update['sentiment_score_nltk'].apply(get_sentiment_label)

    # Assign back only the updated columns
    df.update(to_update[['sentiment_score_nltk', 'sentiment_label_nltk']])
    
    return df


# (NOTSURE) if it is being used
def find_search_terms_stem(
    titles: pd.Series, 
    search_terms: str, 
    return_search_terms: bool = True
    ) -> pd.Series:
    """
    Stemming-based (with NLTK) and fuzzy-based matching (startswith() stem) 
    Extracts matching words (search terms or matched word) from a Series of titles using stemmer.
    Usage: extract_search_terms_stem(df["title"], "bitcoin OR btc")
    """
    original_keys = [k.strip().lower() for k in search_terms.replace(" OR ", ",").replace(" AND ", ",").split(",")]
    stemmed_keys = [stemmer.stem(k) for k in original_keys]

    def match_terms(title: str) -> list:
        title_words = re.sub(r"[^\w\s]", " ", str(title).lower()).split()
        stemmed_title_words = [stemmer.stem(word) for word in title_words]

        matched = set()

        for original, stemmed_key in zip(original_keys, stemmed_keys):
            for word, stemmed_word in zip(title_words, stemmed_title_words):
                if stemmed_word.startswith(stemmed_key):
                    matched.add(original if return_search_terms else word)

        return list(matched) if matched else (original_keys if return_search_terms else [])

    return titles.apply(match_terms)


# (NOTSURE) Check if it is needed and where to put it
def find_search_terms_in_title_with_stemmer(title, search_terms, stemmer=stemmer):
    """
    Finds words stems and returns the original search keyword (p.e. "bitcoiners" returns "bitcoin")
    Alternative to word match with startswith()
    """
    
    # Normalize and stem search terms into a dict
    keywords = [k.strip().lower() for k in search_terms.replace(" OR ", ",").replace(" AND ", ",").split(",")]
    stem_to_keyword = {stemmer.stem(k): k for k in keywords}
    keywords_set = set(keywords)

    # Clean and tokenize title (but keep ticker symbols like $btc, #eth)
    def tokenize_title(title, use_nltk=True):
        if use_nltk:
            # with RegexTokenizer
            tokenizer = RegexpTokenizer(r'[\w$#]+')
            title_words = tokenizer.tokenize(title.lower())
        else:
            # with regex + split
            cleaned_title = re.sub(r"[^\w\s$#]", " ", title.lower())  # keep $ and # characters
            title_words = cleaned_title.split()
        return title_words
            
    title_words = tokenize_title(title, use_nltk=True)

    # to return original search word and not matched word
    matched_keywords = set()
    for word in title_words:
        # Exact match with symbol or abbreviation
        cleaned_word = word.lstrip("$#")  # strip $ and # for matching
        if cleaned_word in keywords_set:
            matched_keywords.add(cleaned_word)
            continue

        # Stem match
        stemmed = stemmer.stem(cleaned_word)
        if stemmed in stem_to_keyword:
            matched_keywords.add(stem_to_keyword[stemmed])

    return list(matched_keywords)