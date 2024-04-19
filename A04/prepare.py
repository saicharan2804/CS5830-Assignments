import os
import pandas as pd

# Load the data
data_dir = 'data'
gt_dir = 'ground_truth'
file_names = os.listdir(data_dir)

# Initialize a set to store the common columns
common_columns = set()

for i, file_name in enumerate(file_names):
    df = pd.read_csv(os.path.join(data_dir, file_name), low_memory=False)

    # Extract the monthly data
    monthly_column_names = [col for col in df.columns if col[0:7] == 'Monthly']
    monthly_column_names.append('DATE')

    monthly_data = df[monthly_column_names]
    monthly_data['MONTH'] = monthly_data['DATE'].apply(lambda x: x[5:7])

    # Drop the date
    monthly_data.drop('DATE', axis=1, inplace=True)

    # Handle the missing data
    monthly_data.dropna(axis=1, how='all', inplace=True)

    # Calculate the mean of each column, excluding 'MONTH'
    mean_values = monthly_data.drop('MONTH', axis=1).mean()

    # Fill the missing values with the calculated mean values
    monthly_data.fillna(mean_values, inplace=True)

    # Save the monthly data with a unique name
    base_name, _ = os.path.splitext(file_name)
    monthly_data.to_csv(os.path.join(gt_dir, f'monthly_{base_name}.csv'), index=False)

    # Update the common columns
    if i == 0:
        common_columns = set(monthly_data.columns)
    else:
        common_columns = common_columns.intersection(set(monthly_data.columns))

# Remove 'MONTH' from the common columns
common_columns.discard('MONTH')

# Save the common columns to a text file
with open(os.path.join(gt_dir, 'monthly_columns.txt'), 'w') as f:
    for item in common_columns:
        f.write("%s\n" % item)
