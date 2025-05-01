# extract
SEARCH_PARAMS = {
    
    "newsdata" : {
        "btc": "bitcoin OR btc",
        "eth": "ethereum OR eth",
        "xrp": "ripple OR xrp",
        "sol": "solana OR sol",
        "doge": "dogecoin OR doge",
        "trx": "tron OR trx",
        "ada": "cardano OR ada",
        "leo": "unus sed leo OR leo",
        "avax": "avalanche OR avax",
        "link": "chainlink OR link",
        "ltc": "litecoin OR ltc" 
    },
    
    "alpha_vantage" : {
        "btc" : "CRYPTO:BTC", 
        "eth": "CRYPTO:ETH", 
        "xrp": "CRYPTO:XRP", 
        "sol": "CRYPTO:SOL",
        "doge": "CRYPTO:DOGE", 
        "ada": "CRYPTO:ADA", 
        "trx": "CRYPTO:TRX", 
        "leo": "CRYPTO:LEO",
        "avax": "CRYPTO:AVAX",
        "link": "CRYPTO:LINK",
        "ltc": "CRYPTO:LTC"
    }
}

# extract
AVAILABLE_TOPICS = {
    
    "newsdata" : [
        "business", "top"
        ],
    
    "alpha_vantage" : [
        "blockchain", "earnings", "ipo", "mergers_and_acquisitions", "financial_markets",
        "economy_fiscal", "economy_monetary", "economy_macro", "energy_transportation",
        "finance", "life_sciences", "manufacturing", "real_estate", "retail_wholesale",
        "technology"
    ]
}

# transform
MAPPING_TICKERS = {
    
    "crypto_dict" : {
        "btc": ["bitcoin", "btc"],
        "eth": ["ethereum", "eth"],
        "xrp": ["ripple", "xrp"],
        "doge": ["dogecoin", "doge"],
        "sol": ["solana", "sol"],
        "trx": ["tron", "trx"],
        "ada": ["cardano", "ada"],
        "leo": ["unus sedo leo", "unussedoleo", "leo"],
        "link": ["chainlink", "link"],
        "avax": ["avalanche", "avax"],
        "xlm": ["stellar", "xlm"],
        "ton": ["toncoin", "ton"],
        "shiba": ["shiba inu", "shibainu", "shiba", "shib"],
        "ltc": ["litecoin", "ltc"],
        "dot": ["polkadot", "dot"],
        "hype": ["hyperliquid", "hype"]
        }
    }

# transform
FILTER_COLUMNS = {
    
    "alpha_vantage" : [
        'title', 'url', 'time_published', 'authors', 'summary', 'source', 
        'source_domain', 'topics','overall_sentiment_score', 
        'overall_sentiment_label', 'ticker_sentiment', 
        'search_terms', 'datetime'
        ], # 'category_within_source', 'banner_image'
    
    "newsdata" : [
        'title', 'link', 'creator', 'description', 'pubDate', 
        'source_name', 'source_priority', 'source_url', 'country',
        'category', 'search_terms', 'datetime'
        ],  # 'source_id', 'article_id', 'duplicate', 'keywords', 'pubDateTZ' + paid data columns
    }

# transform
RENAME_COLUMNS = {
    
    "alpha_vantage" : {
        'summary' : 'description',
        'source_domain' : 'source_url',
        'overall_sentiment_score' : 'sentiment_score_source',
        'overall_sentiment_label' : 'sentiment_label_source',
        },
    
    "newsdata" : {
        'link' : 'url',
        'creator' : 'authors',
        'source_name' : 'source',
        },
    }

# shared transform
COMMON_COLUMNS = [
    
    'title', 'url','authors', 'description', 'source', 'source_url',
    'ticker_names', 'category', 'datetime', 'search_terms', 'data_source',
    'sentiment_score_nltk', 'sentiment_label_nltk'
    ]


SOURCE_RANKING = {
    
    "alpha_vantage": 1,
    "newsdata": 2
    }


# SCANS (DEV)
# Built-in Python functions
import builtins

BUILTINS = set(dir(builtins))

# Keywords to ignore (language keywords)
KEYWORDS_TO_IGNORE = {
    "return", "if", "else", "elif", "for", "while", "try", "except", "with", 
    "def", "class", "or", "and", "not", "is", "in", "import", "from", "as", 
    "lambda", "yield", "global", "assert", "pass", "break", "continue", "del", "raise"
}

# Common methods to ignore (strings, lists, dicts, Path, pandas, etc.)
METHODS_TO_IGNORE = {
    # Basic methods
    "reload", "info", "error", "exception", "warning", "debug",

    # String/List methods
    "upper", "lower", "strip", "split", "join", "format", "replace", "encode", "decode",
    "startswith", "endswith", "isnumeric", "isdigit", "isalpha", "capitalize", "casefold",
    "find", "rfind", "zfill", "rjust", "ljust", "center", "expandtabs", "count", "sort",
    "reverse", "copy", "clear", "pop", "update", "insert", "remove", "extend", "items",
    "keys", "values", "isnull", "notna", "isna", "dropna", "fillna", "astype",

    # Pandas methods
    "to_datetime", "read_csv", "drop_duplicates", "sort_values", "value_counts", 
    "explode", "merge", "groupby", "reset_index", "set_index", "rename", "agg", "to_frame",
    "json_normalize", "is_string_dtype", "is_bool_dtype", "is_numeric_dtype",

    # Pathlib methods
    "Path", "exists", "stem", "with_suffix", "with_name", "mkdir", "resolve", "relative_to",
    "as_posix", "expanduser", "iterdir", "unlink", "is_file", "is_dir", "stat",

    # Logging related
    "getLogger", "setLevel", "setFormatter", "addHandler", "StreamHandler", "FileHandler", "Formatter",

    # Regex methods
    "match", "group", "findall", "sub",

    # OS/File system
    "walk", "abspath", "dirname", "getsize", "move",

    # False positives (variables)
    "file", "folder", "file_list", "folder_path", "trash_folder", "source_path", "destination_folder",
    "imports", "modules", "path", "saved", "base_filename_prefix", "column", "columns", "encoding",
    "returns", "only", "size", "removed", "csv", "schema",
    
    # update
    "get", "append", "write", "apply", "add", "eq", "drop", 
    "unique", "tolist", "ratio", "where", "is_datetime64_any_dtype",
}