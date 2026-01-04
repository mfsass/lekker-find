import pandas as pd
import sys

# Load data
try:
    df = pd.read_csv('data-262-2025-12-26.csv')
except FileNotFoundError:
    print("CSV file not found")
    sys.exit(1)

# Normalize suburbs for grouping
# We want to group by broad areas: Somerset West, Stellenbosch, Cape Town
def get_broad_area(suburb):
    s = str(suburb).lower()
    if 'somerset' in s: return 'Somerset West'
    if 'stellenbosch' in s: return 'Stellenbosch'
    if 'cape town' in s or 'gardens' in s or 'green point' in s or 'sea point' in s or 'camps bay' in s or 'city centre' in s: return 'Cape Town'
    return 'Other'

df['BroadArea'] = df['Suburb'].apply(get_broad_area)

# Filter for the areas we care about
target_areas = ['Somerset West', 'Stellenbosch', 'Cape Town']
df_target = df[df['BroadArea'].isin(target_areas)]

print("=== Current Venue Counts by Area and Category ===")
counts = df_target.groupby(['BroadArea', 'Category']).size().unstack(fill_value=0)
print(counts.to_string())

print("\n=== Total High Rated (4.7+) with > 200 reviews in these areas ===")
high_quality = df_target[(df_target['Rating'] >= 4.7) & (df_target['Review_Count'] >= 200)]
print(high_quality.groupby(['BroadArea', 'Category']).size().unstack(fill_value=0).to_string())
