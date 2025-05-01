# (DONE) semantic_tools
import re
import pandas as pd
from sentence_transformers import SentenceTransformer  # for semantics
from sklearn.metrics.pairwise import cosine_similarity  # for semantics
from nltk.tokenize import sent_tokenize, word_tokenize

"""
Sentence Similarity (see _2.py for more)
------------------
APPROACHES:
- SequenceMatcher() --> not used
- SentenceTransformer() and cosine_similarity()
    - Models: 'all-MiniLM-L6-v2' (fast), 'all-mpnet-base-v2' (more accurate)

USAGE:
Text Versions: myfunction(text)
Series Version: df['text'].apply(myfunction)

main function: apply_semantic_cleaning(df, model, nltk_split=True, similarity_threshold=0.9, parallelism=False)
"""

# Model for semantic similarity
model_name = 'all-MiniLM-L6-v2' # 'all-mpnet-base-v2'
model = SentenceTransformer(model_name)  # load model


def split_sentences(text):
    """using regex + split"""
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

def split_sentences_nltk(text):
    """using nltk"""
    return [s.strip() for s in sent_tokenize(text) if s.strip()]

def normalize_sentence(s):
    """
    Quick string normalization:
        - Strips leading/trailing spaces
        - Lowercases everything
        - Collapses multiple spaces into one
    
    Aggresive pattern to keep only letter, number and whitespaces:
        - re.sub(r'[^a-z0-9\s]', '', s.strip().lower())
        - Removes punctuation and special symbols (like .,!?@#%)
    """
    return re.sub(r'\s+', ' ', s.strip().lower())

def normalize_sentence_nltk(s):
    tokens = word_tokenize(s.lower())
    return ' '.join(tokens)

def normalize_sentence_hybrid(s):
    """Both regex and nltk for consistency"""
    tokens = word_tokenize(s.lower())
    return re.sub(r'\s+', ' ', ' '.join(tokens)).strip()
    

# Sequence Similarity with Semantics (embeddings and cosine similarity) 
def remove_semantic_duplicates_with_count(text, nltk_split=True, model=model, similarity_threshold=0.9, return_count=True):
    """
    Removes semantically similar sentences from text.
    Returns just the cleaned text by default, or (cleaned_text, removed_count) if return_count=True.
    """
    if not isinstance(text, str) or not text.strip():
        return ("", 0) if return_count else ""

    # Sentence split (nltk, regex or hybrid - not implemented)
    if nltk_split:
        sentences = split_sentences_nltk(text)
    else:
        sentences = split_sentences(text)
    
    if not sentences:
        return ("", 0) if return_count else ""

    if model is None:
        raise ValueError("You must pass a SentenceTransformer model.")
    
    embeddings = model.encode(sentences)
    
    kept = []
    kept_embeddings = []

    for sentence, embedding in zip(sentences, embeddings):
        if not kept:
            kept.append(sentence)
            kept_embeddings.append(embedding)
        else:
            similarities = cosine_similarity([embedding], kept_embeddings)[0]
            if all(sim < similarity_threshold for sim in similarities):
                kept.append(sentence)
                kept_embeddings.append(embedding)

    removed_count = len(sentences) - len(kept)
    return (' '.join(kept), removed_count) if return_count else ' '.join(kept)

def remove_semantic_duplicates_with_batching(
    text,
    similarity_threshold=0.9,
    model=None,
    return_count=True,
    base_batch_size=16,
    max_batch_size=128
    ):
    """
    Removes semantically similar sentences using cosine similarity on embeddings.
    Automatically adjusts batch size based on sentence count.

    Parameters:
    - text: input string
    - similarity_threshold: cosine similarity threshold
    - model: SentenceTransformer instance
    - return_count: if True, returns (cleaned_text, removed_count)
    - base_batch_size: minimum batch size (default=16)
    - max_batch_size: maximum batch size (default=128)

    Returns:
    - cleaned text or (cleaned_text, removed_count)
    """
    if not isinstance(text, str) or not text.strip():
        return ("", 0) if return_count else ""

    # Step 1: Split into sentences
    sentences = split_sentences(text)
    if not sentences:
        return ("", 0) if return_count else ""

    # Step 2: Auto-adjust batch size based on number of sentences
    sentence_count = len(sentences)
    batch_size = min(max(base_batch_size, sentence_count // 2), max_batch_size)

    # Step 3: Embed with batch encoding
    if model is None:
        raise ValueError("A SentenceTransformer model must be provided.")
    embeddings = model.encode(sentences, batch_size=batch_size, show_progress_bar=False)

    # Step 4: Deduplicate
    kept = []
    kept_embeddings = []

    for sentence, embedding in zip(sentences, embeddings):
        if not kept:
            kept.append(sentence)
            kept_embeddings.append(embedding)
        else:
            similarities = cosine_similarity([embedding], kept_embeddings)[0]
            if all(sim < similarity_threshold for sim in similarities):
                kept.append(sentence)
                kept_embeddings.append(embedding)

    removed_count = len(sentences) - len(kept)
    return (' '.join(kept), removed_count) if return_count else ' '.join(kept)

# wrap-up function
def apply_semantic_cleaning(df, model=model, similarity_threshold=0.9):
    """
    Applies semantic sentence deduplication to merged rows only. 
    Requires: 'description', 'was_merged' columns.
    Returns: df with cleaned 'description' and 'removed_sent_count' columns.
    """
    result = df.copy()

    def clean_if_needed(row):
        if row['was_merged']:
            cleaned, removed = remove_semantic_duplicates_with_count(
                row['description'], 
                similarity_threshold=similarity_threshold,
                model=model,
                return_count=True  # for debugging
            )
        else:
            cleaned, removed = row['description'], 0
        return pd.Series({'description': cleaned, 'removed_sent_count': removed})

    result[['description', 'removed_sent_count']] = result.apply(clean_if_needed, axis=1)
        
    return result

