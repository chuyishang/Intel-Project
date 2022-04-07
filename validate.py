"""
Validates scraped data against manually collected
validation set.
"""

import argparse
import json
import pandas as pd

# parse for filepath
parser = argparse.ArgumentParser(description='Validate dataset.')
parser.add_argument('--filepath',
                    type=str,
                    help='path to the ataset',
                    default='data/scraped_data.json')

d_types = {
    'company':str,
    'quarter':str,
    'year':str,
    'metric':str,
    'value':str,
    'sub-metric':str
}

# read in scraped file
scraped_filepath = parser.parse_args().filepath
scraped_json = json.load(open(scraped_filepath, 'r'))
scraped_df = pd.json_normalize(scraped_json)

scraped_df = scraped_df.astype(d_types)

# read in validation dataset

sheet_id = "1CtlCDjvO5aZkMaUncdEMQMTAHG2QUjCUqqre4X_FZsk"
sheet_name = 'validation'
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
validation_df = pd.read_csv(url, error_bad_lines=False, thousands = ",") # Ignore errors
validation_df = validation_df.astype(d_types)



# check expected length
deduped_df = pd.concat([scraped_df, validation_df]).drop_duplicates(keep="first")
expected_length = len(scraped_df)
actual_length = len(deduped_df)

# if no errors
if actual_length == expected_length:
    print("Passed all test cases!")
    quit()

# if error
print(f"Disagreement in {actual_length - expected_length} samples.")


merged_df = validation_df.merge(scraped_df, how = 'outer', on = ['company', 'quarter', 'year', 'metric', 'sub-metric'], indicator='source')
error_df = merged_df[merged_df['source'] == 'left_only']
print(error_df)

"""for i in len(merged_df):
    if merged_df["_merge"][i] == "left_only":
        print merged_df"""

"""
TO DO: Implement code to check which data points are missing/incorrect. Potential approach:
- perform a Pandas merge with an indicator column: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
- this gives you a column that tells you if a datapoint is only in one of the dataframes (left or right)
- if it's only the test dataset, then print that point
"""
