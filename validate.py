import pandas as pd

scraped_path = 'data/data.json'
scraped_df = pd.read_json(scraped_path)

validation_path = 'data/validation.json'
validation_df = pd.read_json(validation_path)

expected_legnth = len(scraped_df)
deduped_df = pd.concat([scraped_df, validation_df]).drop_duplicates(keep=False)
if len(deduped_df) > scraped_df:
    print("Disagreement in samples.")
    