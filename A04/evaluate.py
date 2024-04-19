import os
import pandas as pd
from sklearn.metrics import r2_score

def load_data(file_path):
    """Load a CSV file into a pandas DataFrame."""
    return pd.read_csv(file_path, low_memory=False)

def calculate_r2_scores(df_ground_truth, df_computed_avg):
    """Calculate the R2 scores for matching columns in ground truth and computed averages dataframes."""
    results = {}
    for column in df_computed_avg.columns:
        if column in df_ground_truth.columns:
            r2 = r2_score(df_ground_truth[column], df_computed_avg[column])
            results[column] = [r2, r2 > 0.9]
    return results

def save_results(results, file_path):
    """Save the R2 scores to a text file."""
    with open(file_path, 'w') as file:
        file.write(str(results))

def main():
    data_directory = 'data'
    ground_truth_directory = 'ground_truth'
    file_names = os.listdir(data_directory)

    total_results = {}

    for file_name in file_names:
        base_name, _ = os.path.splitext(file_name)
        gt_file_path = os.path.join(ground_truth_directory, f'monthly_{base_name}.csv')
        avg_file_path = os.path.join(ground_truth_directory, f'computed_avg_{base_name}.csv')

        df_ground_truth = load_data(gt_file_path)
        df_computed_avg = load_data(avg_file_path)

        print(df_ground_truth.shape, df_computed_avg.shape)
        print(df_computed_avg.columns, df_ground_truth.columns)

        results = calculate_r2_scores(df_ground_truth, df_computed_avg)
        total_results.update(results)

    results_file_path = os.path.join(ground_truth_directory, 'results.txt')
    save_results(total_results, results_file_path)

if __name__ == '__main__':
    main()
