# Project structure

(needs update)
etl-news-sentiment/
├── extractors/
│   ├── __init__.py
│   ├── alpha_vantage.py
│   └── newsdata.py
├── transformers/
│   ├── __init__.py
|   ├── alpha_vantage.py
|   ├── newsdata.py
│   └── shared_transforms.py
├── loaders/
│   ├── __init__.py
|   ├── load_to_csv.py
│   └── load_to_db.py
├── pipelines/
│   ├── __init__.py
│   ├── run_alpha_vantage.py
│   └── run_newsdata.py
├── utils/
│   ├── __init__.py
│   ├── helpers.py
│   ├── nltk_tools.py
│   └── logger.py  (missing)
├── config/
│   ├── __init__.py
|   ├── config.ini
│   └── constants.py
├── data/
|   ├── raw/
|   ├── processed/
│   └── backup/
├── notebooks/
|   ├── notebook1.ipynb
|   ├── notebook2.ipynb
│   └── (...)
├── __init__.py
├── pyproject.toml  (include = ["extractors*", "transformers*", "loaders*", "pipelines*", "utils*", "config*"])
├── README.md
└── main.py


**pyproject.toml**
- Control Center of the project
- Note: Needs to be aware of cython
- $ python3 pip install -e . (but first recompile setup.py!)

**setup.py**
- Set to find .pyx files in /transformers/resamplers/ to compile
- Run <bash> python3 setup.py build_ext --inplace on every change/update of .pyx to recompile
- /transformers/resamplers/\_\_init\_\_.py in place to run resamplers as module
- resamplers handle alpha_vantage (ticker_sentiment) for now
- $ python3 setup.py build_ext --inplace

**logger**
- All logging in one place (logs/etl.log)
- Implementation of source-based logger + general logger available but not active

**nltk**
- All nltk tools in sentimwnt_scores.py

**semantic_utils.py**
- For semantic similarity

**normalizers.py**
- functions for dtype normalization

**validators.py**
- perform validation ops and raise on errors

**my_python_tools**



