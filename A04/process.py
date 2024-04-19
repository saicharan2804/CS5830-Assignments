import os
import pandas as pd

def load_common_columns(file_path):
    """Load common column names from a file."""
    with open(file_path, 'r') as file:
        columns = [line.strip() for line in file]
    return columns

def process_monthly_data(file_name, data_directory, ground_truth_directory):
    """Process the CSV file to compute monthly averages from daily data."""
    # Construct the path to the CSV file
    csv_path = os.path.join(ground_truth_directory, f'monthly_{os.path.splitext(file_name)[0]}.csv')

    # Read the CSV file
    df = pd.read_csv(csv_path, low_memory=False)

    # Identify daily data columns plus the 'MONTH' column
    day_columns = [col for col in df.columns if col.startswith('Daily')]
    day_columns.append('MONTH')

    # Filter the dataframe to include only the daily data and 'MONTH'
    day_data = df[day_columns]

    # Drop columns where all values are NaN
    day_data.dropna(axis=1, how='all', inplace=True)

    # Compute the average for each month and clean up columns
    for col in day_data.columns:
        if col != "MONTH":
            monthly_avg = day_data.groupby('MONTH')[col].mean()
            day_data[f'Month_Avg_{col}'] = day_data['MONTH'].map(monthly_avg)
            day_data.drop(col, axis=1, inplace=True)

    # Save the processed data to a new CSV file
    output_path = os.path.join(ground_truth_directory, f'computed_avg_{os.path.splitext(file_name)[0]}.csv')
    day_data.to_csv(output_path, index=False)

def main():
    data_directory = 'data'
    ground_truth_directory = 'ground_truth'
    file_names = os.listdir(data_directory)

    # Load the common columns (not used in the current script but loaded for potential future use)
    common_columns = load_common_columns(os.path.join(ground_truth_directory, 'monthly_columns.txt'))

    for file_name in file_names:
        process_monthly_data(file_name, data_directory, ground_truth_directory)

if __name__ == '__main__':
    main()
