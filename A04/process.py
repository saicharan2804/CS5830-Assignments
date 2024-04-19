import os
import pandas as pd

# Load the data
data_dir = 'data'
gt_dir = 'ground_truth'
file_names = os.listdir(data_dir)

# Load the common columns
with open(os.path.join(gt_dir, 'monthly_columns.txt'), 'r') as f:
    common_columns = [line.strip() for line in f]

for file_name in file_names:
    df = pd.read_csv(os.path.join(gt_dir, f'monthly_{os.path.splitext(file_name)[0]}.csv'), low_memory=False)

    # Extract the daily data
    day_column_names = [col for col in df.columns if col[0:5] == 'Daily']
    day_column_names.append('MONTH')

    day_data = df[day_column_names]

    # Handle the missing data, if all the values in a column are zero then drop it
    day_data.dropna(axis=1, how='all', inplace=True)

    # Compute the monthly data
    for i in day_data.columns:
        if i != "MONTH":
            avg = day_data.groupby('MONTH')[i].mean()
            day_data['Month_Avg_'+i] = day_data['MONTH'].map(avg)
            day_data.drop(i, axis=1, inplace=True)

    # Save the computed monthly data
    day_data.to_csv(os.path.join(gt_dir, f'computed_avg_{os.path.splitext(file_name)[0]}.csv'), index=False)
