import scraper
from csv import reader
import json
import pandas as pd
import argparse

"""
***********************************************
Aggregates Data for All Years for All Companies
***********************************************
"""

def aggregate_company(pull_func, url_csv, company):
    """
    Aggregates data for single company for all available years, returns as a dictionary.
    """
    company_data = []
    url_df = pd.read_csv(url_csv)
    for index, row in url_df.iterrows():
        year = row['year']
        quarter = row['quarter']
        url = row['url']
        pull_data = pull_func(url, year, quarter, company)
        company_data.extend(pull_data)
    return company_data

VALID_COMPS = ['tsmc', 'smic', 'umc', 'gf']

def main():
    parser = argparse.ArgumentParser()
    add_arg = parser.add_argument
    add_arg('--all', action='store_true')
    add_arg('--comp', type=str)
    add_arg('--qtr', type=int)
    add_arg('--year', type=int)

    args = parser.parse_args()
    url_files = {
        'tsmc':'urls/tsmc_urls.csv',
        'smic':'urls/smic_urls.csv',
        'umc':'urls/umc_urls.csv',
        'gf':'urls/gf_urls.csv',
    }

    if args.all:
        all_df = pd.DataFrame()
        for comp, url_file in url_files.items():
            comp_data = aggregate_company(scraper.pull, url_file, comp)
            all_df = all_df.append(comp_data)
        quit()
    
    company = args.comp
    quarter = args.qtr
    year = args.year

    if not all([company, quarter, year]):
        raise RuntimeError('If not collecting all with --all, then --comp, --qtr, and --year must be specified.')

    if not company in VALID_COMPS:
        raise RuntimeError(f'--comp must be one of {VALID_COMPS}')

    url_file = url_files[args.comp]
    url_df = pd.read_csv(url_file)
    url = url_df[(url_df['year'] == args.year) & (url_df['quarter'] == args.qtr)].iloc[0]['url']
    print(scraper.pull(url, year, quarter, company))

if __name__ == "__main__":
    main()