import os
import nltk

# Define the NLTK data directory
NLTK_DATA_DIR = os.path.expanduser("~/nltk_data")
if NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.insert(0, NLTK_DATA_DIR)

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
        
#check_nltk_resources()