import yaml
import os
import requests

def load_yaml(file_path):
    """Load data from a YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def ensure_directory_exists(directory):
    """Ensure that a directory exists, and if not, create it."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_file(url, file_path):
    """Download a file from a specified URL and save it to a local path."""
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download file from {url}. Status code: {response.status_code}")

def download_files(year, file_names, base_url, save_dir):
    """Download multiple files based on a list of file names and a base URL."""
    for file_name in file_names:
        url = f"{base_url}/{year}/{file_name}"
        file_path = os.path.join(save_dir, file_name)
        download_file(url, file_path)

def main():
    # Load the YAML configuration file
    data = load_yaml('params.yaml')

    # Retrieve year and file names
    year = data['year']
    file_names = data['n_locs']

    # Set the directory for saving data and ensure it exists
    data_directory = 'data'
    ensure_directory_exists(data_directory)

    # Define the base URL for file downloads
    base_url = 'https://www.ncei.noaa.gov/data/local-climatological-data/access'

    # Download all specified files
    download_files(year, file_names, base_url, data_directory)

    print("Files downloaded successfully!")

if __name__ == '__main__':
    main()
