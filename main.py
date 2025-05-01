# (DONE)
from pipelines.run_alpha_vantage import run_pipeline as run_alpha_vantage
from pipelines.run_newsdata import run_pipeline as run_newsdata
from pipelines.run_merge_sources import run_pipeline as run_merge_sources
from utils.nltk_setup import check_nltk_resources

from config.constants import SEARCH_PARAMS
from config.settings import PARENT_FOLDERS
from utils.logger import setup_logger, clear_log_file
import argparse

logger = setup_logger(__name__)


def main(args):
    
    
    if args.source in ["1", "both"]:
        try:
            logger.info("Running Alpha Vantage pipeline...")
            symbols = [f'CRYPTO:{symbol.upper().strip()}' for symbol in args.fetch]
            run_alpha_vantage(symbols, args.last_days, args.resample, verbose=True)
        except Exception as e:
            logger.error(f"Alpha Vantage pipeline failed - {e}")
            raise
    
    if args.source in ["2", "both"]:
        try:
            logger.info("Running Newsdata pipeline...")
            search_params = SEARCH_PARAMS.get('newsdata')
            list_search_terms = [search_params.get(x.lower().strip()) for x in args.fetch]
            run_newsdata(list_search_terms, args.resample, verbose=True)
        except Exception as e:
            logger.error(f"Newsdata pipeline failed - {e}")
            raise
    
    try:
        processed_folder = PARENT_FOLDERS["parent_processed"]
        file_list = []
        for source in ["alpha_vantage", "newsdata"]:
            path = processed_folder / source / "main" / f"{source}_main.csv.gz"
            if path.exists():
                file_list.append(path)
            else:
                logger.warning(f"Missing file: {path}")
        run_merge_sources(file_list, verbose=True)
    except Exception as e:
        logger.error(f"Merge Sources pipeline failed - {e}")
    
    

if __name__ == "__main__":
    
    
    parser = argparse.ArgumentParser(
        description="Run ETL pipeline for Alpha Vantage and Newsdata news.")
    
    parser.add_argument(
        "--fetch", nargs="+", required=True, 
        help="List of symbols to extract (e.g., btc eth)")
    
    parser.add_argument(
        "--last_days", type=int, default=None, required=False, 
        help="Number of past days to fetch news for each symbol")
    
    parser.add_argument(
        "--source", choices=["1", "2", "both"], default="both",
        help="Select which pipeline to run: '1' alpha_vantage, '2' newsdata, 'both' run both")
    
    parser.add_argument(
        "--resample", action="store_true", 
        help="Resample dataframes (True of False)")
    
    args = parser.parse_args()


    check_nltk_resources()
    clear_log_file()
    main(args)
