In progress

# Project structure

config/
utils/
extractors/
transformers_project/
loaders/
pipelines/
data/
tests/
logs/


### General Design Notes

- Each **source** has its own extractor and corresponding data folder.
- Transformers are organized per source.
- Resamplers (Cython-optimized, currently **not used**) are available.
- Sentiment scores are computed **per source**.
- Resampling is available for individual sources and merged sources.


### API notes

- Alpha Vantage limitations: x per day
- Newsdata limitations: 30 requests per 15 min, x per day


### `pyproject.toml`

- Implemented and acts as the **control center** of the project.
- requirements.txt is also available
- If Cython is used, make sure it’s listed as a dependency.
- Requires rebuilding Cython with setup.py first.
- Install project in editable mode with:
  ```bash
  python3 -m pip install -e .


### `setup.py`

- Used for Cython implementation.
- Compiles .pyx files in /transformers_project/resamplers/.
- \_\_init\_\_.py present to expose resamplers as a module
- Currently supports Alpha Vantage ticker_sentiment.
- Recompile .pyx after every change in .pyx:
  ```bash
  python3 setup.py build_ext --inplace


### swifter

- Optional optimization for .apply()
- Check for bottlenecks first
- Not in use currently


### logger

- Central logging to logs/etl.log
- Source-specific and general logger implemented (in logger_2.py), but currently inactive.


### nltk

- nltk_setup.py ensures required resources are installed.
- All NLTK usage centralized in sentiment_scores.py


### `semantic_tools.py`

- Handles semantic similarity:
    - SentenceTransformer for embeddings
    - cosine_similarity from sklearn
- Used to remove duplicated sentences from texts (description) merges
- Notes: SequenceMatcher gave inconsistent results.


### `normalizers.py`

- Contains data type normalization helpers.
- Unit tests available via pytest (pytest tests/test_normalizers.py)


### `validators.py`

- Performs schema/logic validations.
- Raises exceptions on failure.
- Unit tests available via pytest (pytest tests/test_validators.py)



