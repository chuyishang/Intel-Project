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
                    help='path to the dataset',
                    default='data/scraped_data.json')

# read in scraped file
scraped_filepath = parser.parse_args().filepath
scraped_json = json.load(open(scraped_filepath, 'r'))
scraped_df = pd.json_normalize(scraped_json)


# read in validation dataset
url = "data/validate.csv"
validation_df = pd.read_csv(url, error_bad_lines=True) # Ignore errors

# check expected length
deduped_df = pd.concat([scraped_df, validation_df]).drop_duplicates(keep=False)
expected_length = len(scraped_df)
actual_length = len(deduped_df)

# if no errors
if actual_length == expected_length:
    print("Passed all test cases!")
    quit()

# if error
print("Disagreement in samples.")

merged_df = validation_df.merge(scraped_df, indicator=left_only)
merged_df
"""for i in len(merged_df):
    if merged_df["_merge"][i] == "left_only":
        print merged_df"""

"""
TO DO: Implement code to check which data points are missing/incorrect. Potential approach:
- perform a Pandas merge with an indicator column: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
- this gives you a column that tells you if a datapoint is only in one of the dataframes (left or right)
- if it's only the test dataset, then print that point
"""
