import scraper
from csv import reader
import json
import pandas as pd

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

"""
Aggregates data for TSMC for all available years, returns as a json file.
"""
tsmc_data = aggregate_company(scraper.pull, 'urls/tsmc_urls.csv', 'tsmc')
with open('tsmc_json_data.json', 'w', encoding='utf-8') as f:
    json.dump(tsmc_data, f, ensure_ascii=False, indent=4)

"""
Aggregates data for SMIC for all available years, returns as a json file.
"""
smic_data = aggregate_company(scraper.pull, 'urls/smic_urls.csv', 'smic')
with open('smic_json_data.json', 'w', encoding='utf-8') as f:
    json.dump(smic_data, f, ensure_ascii=False, indent=4)

"""
Aggregates data for UMC for all available years, returns as a json file.
"""
umc_data = aggregate_company(scraper.pull, 'urls/umc_urls.csv', 'umc')
with open('umc_json_data.json', 'w', encoding='utf-8') as f:
    json.dump(umc_data, f, ensure_ascii=False, indent=4)

"""
Aggregates data for GlobalFoundries for all available years, returns as a json file.
"""
gf_data = aggregate_company(scraper.pull, 'urls/gf_urls.csv', 'gf')
with open('gf_json_data.json', 'w', encoding='utf-8') as f:
    json.dump(gf_data, f, ensure_ascii=False, indent=4)

"""
Aggregates data for all companies for all available years, returns as a json file.
"""
data = tsmc_data + smic_data + umc_data + gf_data
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

