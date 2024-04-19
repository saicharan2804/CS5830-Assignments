import os
import pandas as pd

def extract_monthly_data(file_path):
    """Extracts columns that contain monthly data and appends the month extracted from the DATE column."""
    df = pd.read_csv(file_path, low_memory=False)
    monthly_columns = [col for col in df.columns if col.startswith('Monthly')]
    monthly_columns.append('DATE')
    monthly_data = df[monthly_columns]
    monthly_data['MONTH'] = monthly_data['DATE'].apply(lambda x: x[5:7])
    monthly_data.drop('DATE', axis=1, inplace=True)
    return monthly_data

def clean_and_calculate_means(monthly_data):
    """Cleans the data by dropping all-NaN columns and fills missing values with column means, excluding 'MONTH'."""
    monthly_data.dropna(axis=1, how='all', inplace=True)
    mean_values = monthly_data.drop('MONTH', axis=1).mean()
    monthly_data.fillna(mean_values, inplace=True)
    return monthly_data

def update_common_columns(common_columns, new_columns, first_iteration):
    """Updates the set of common columns based on current file's columns."""
    if first_iteration:
        return set(new_columns)
    else:
        return common_columns.intersection(set(new_columns))

def main():
    data_directory = 'data'
    ground_truth_directory = 'ground_truth'
    file_names = os.listdir(data_directory)

    common_columns = set()

    for i, file_name in enumerate(file_names):
        file_path = os.path.join(data_directory, file_name)
        monthly_data = extract_monthly_data(file_path)
        monthly_data = clean_and_calculate_means(monthly_data)

        # Save the monthly data with a unique name
        base_name, _ = os.path.splitext(file_name)
        monthly_data.to_csv(os.path.join(ground_truth_directory, f'monthly_{base_name}.csv'), index=False)

        # Update the common columns
        common_columns = update_common_columns(common_columns, monthly_data.columns, i == 0)

    # Remove 'MONTH' from the common columns
    common_columns.discard('MONTH')

    # Save the common columns to a text file
    with open(os.path.join(ground_truth_directory, 'monthly_columns.txt'), 'w') as f:
        for column in common_columns:
            f.write(f"{column}\n")

if __name__ == '__main__':
    main()
