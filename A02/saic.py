from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models.param import Param
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os
import random
import urllib
import shutil


from airflow.sensors.filesystem import FileSensor
import apache_beam as beam
import pandas as pd
import geopandas as gpd
from geodatasets import get_path
import matplotlib.pyplot as plt
import numpy as np
import logging
from ast import literal_eval as make_tuple
import shutil
import os

# Constants
BASE_URL = 'https://www.ncei.noaa.gov/data/local-climatological-data/access/'
YEAR = 2002
NUM_FILES = 2
ARCHIVE_OUTPUT_DIR = '/tmp/archives'
DATA_FILE_OUTPUT_DIR = f'/tmp/data/{YEAR}/'
HTML_FILE_SAVE_DIR = '/tmp/html/'

# Default DAG configuration
default_args = {
    'owner': 'admin',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

# DAG definition
dag1 = DAG(
    dag_id="Fetch_NCEI_Data",
    default_args=default_args,
    description='DataFetch Pipeline',
    params={
        'base_url': BASE_URL,
        'year': Param(YEAR, type="integer", minimum=1901, maximum=2024),
        'num_files': NUM_FILES,
        'archive_output_dir': ARCHIVE_OUTPUT_DIR,
    },
)

# Task 1: Download HTML page containing data links for the specified year
fetch_page_task = BashOperator(
    task_id="Download_HTML_data",
    bash_command="curl {{params.base_url}}{{params.year}}/ --create-dirs -o {{params.file_save_dir}}{{params.year}}.html",
    params={
        'base_url': "{{ dag_run.conf.get('base_url', params.base_url) }}",
        'file_save_dir': HTML_FILE_SAVE_DIR,
    },
    dag=dag1,
)

# Task 2: Select random data files from the available list of files
def select_random_files(num_files, base_url, year, file_save_dir, **kwargs):
    """Selects random files from the list of available files."""
    with open(f"{file_save_dir}{year}.html", "r") as f:
        page_content = f.read()
    soup = BeautifulSoup(page_content, 'html.parser')
    file_links = [link.get('href') for link in soup.find_all('a') if ".csv" in link.get('href')]
    selected_files = random.sample(file_links, min(int(num_files), len(file_links)))
    selected_files_urls = [f"{base_url}{year}/{file}" for file in selected_files]
    return selected_files_urls

select_files_task = PythonOperator(
    task_id='select_files',
    python_callable=select_random_files,
    op_kwargs={
        'num_files': "{{ dag_run.conf.get('num_files', params.num_files) }}",
        'year': "{{ dag_run.conf.get('year', params.year) }}",
        'base_url': "{{ dag_run.conf.get('base_url', params.base_url) }}",
        'file_save_dir': HTML_FILE_SAVE_DIR,
    },
    dag=dag1,
)

# Task 3: Download the selected data files
def download_files(selected_files, csv_output_dir):
    """Downloads the selected data files."""
    os.makedirs(csv_output_dir, exist_ok=True)
    for file_url in selected_files:
        file_name = urllib.parse.unquote(os.path.basename(file_url))
        file_path = os.path.join(csv_output_dir, file_name)
        os.system(f"curl {file_url} -o {file_path}")

fetch_files_task = PythonOperator(
    task_id='fetch_files',
    python_callable=download_files,
    provide_context=True,
    op_kwargs={'csv_output_dir': DATA_FILE_OUTPUT_DIR},
    dag=dag1,
)

# Task 4: Zip the downloaded data files into an archive
def zip_files(output_dir, archive_path):
    """Zips the downloaded data files into an archive."""
    shutil.make_archive(archive_path, 'zip', output_dir)

zip_files_task = PythonOperator(
    task_id='zip_files',
    python_callable=zip_files,
    op_kwargs={
        'output_dir': DATA_FILE_OUTPUT_DIR,
        'archive_path': DATA_FILE_OUTPUT_DIR.rstrip('/'),
    },
    dag=dag1,
)

# Task 5: Move the archive to the specified location
def move_archive(archive_path, target_location):
    """Moves the archive to the specified location."""
    os.makedirs(target_location, exist_ok=True)
    shutil.move(f"{archive_path}.zip", os.path.join(target_location, f"{YEAR}.zip"))

move_archive_task = PythonOperator(
    task_id='move_archive',
    python_callable=move_archive,
    op_kwargs={
        'target_location': "{{ dag_run.conf.get('archive_output_dir', params.archive_output_dir) }}",
        'archive_path': DATA_FILE_OUTPUT_DIR.rstrip('/'),
    },
    dag=dag1,
)

# Task dependencies
fetch_page_task >> select_files_task >> fetch_files_task >> zip_files_task >> move_archive_task

# Constants
ARCHIVE_PATH = "/tmp/archives/2002.zip"
REQUIRED_FIELDS = "WindSpeed, BulbTemperature"

# DAG configuration
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag2 = DAG(
    dag_id='Analytics_Pipeline',
    default_args=default_args,
    description='Analytics pipeline',
    params={
        'archive_path': ARCHIVE_PATH,
        'required_fields': REQUIRED_FIELDS
    },
    schedule_interval='*/1 * * * *',
    catchup=False
)

# Task 2.1: Wait for the archive to be available
wait_task = FileSensor(
    task_id='wait_for_archive',
    mode="poke",
    poke_interval=5,
    timeout=5,
    filepath="{{params.archive_path}}",
    dag=dag2,
    fs_conn_id="my_file_system",
)

# Task 2.2: Unzip Archive
unzip_task = BashOperator(
    task_id='unzip_archive',
    bash_command="unzip -o {{params.archive_path}} -d /tmp/data2",
    dag=dag2,
)

# Task 2.3: Process CSV using Apache Beam
def process_csv(required_fields, **kwargs):
    required_fields = [field.strip() for field in required_fields.split(",")]
    os.makedirs('/tmp/results', exist_ok=True)
    with beam.Pipeline(runner='DirectRunner') as p:
        result = (
            p
            | 'ReadCSV' >> beam.io.ReadFromText('/tmp/data2/*.csv')
            | 'ParseData' >> beam.Map(lambda data: data.split('","'))
            | 'FilterAndCreateTuple' >> beam.ParDo(ExtractAndFilterFields(required_fields=required_fields))
            | 'CombineTuple' >> beam.GroupByKey()
            | 'UnpackTuple' >> beam.Map(lambda a: (a[0][0], a[0][1], a[1]))
        )
        result | 'WriteToText' >> beam.io.WriteToText('/tmp/results/result.txt')

process_csv_files_task = PythonOperator(
    task_id='process_csv_files',
    python_callable=process_csv,
    op_kwargs={'required_fields': "{{ params.required_fields }}"},
    dag=dag2,
)

# Task 2.4: Compute monthly averages using Apache Beam
def compute_monthly_avg(required_fields, **kwargs):
    required_fields = [field.strip() for field in required_fields.split(",")]
    os.makedirs('/tmp/results', exist_ok=True)
    with beam.Pipeline(runner='DirectRunner') as p:
        result = (
            p
            | 'ReadProcessedData' >> beam.io.ReadFromText('/tmp/data2/*.csv')
            | 'ParseData' >> beam.Map(lambda data: data.split('","'))
            | 'CreateTupleWithMonthInKey' >> beam.ParDo(ExtractFieldsWithMonth(required_fields=required_fields))
            | 'CombineTupleMonthly' >> beam.GroupByKey()
            | 'ComputeAverages' >> beam.Map(compute_avg)
            | 'CombineTuplewithAverages' >> beam.GroupByKey()
            | 'UnpackTuple' >> beam.Map(lambda a: (a[0][0], a[0][1], a[1]))
        )
        result | 'WriteAveragesToText' >> beam.io.WriteToText('/tmp/results/averages.txt')

compute_monthly_avg_task = PythonOperator(
    task_id='compute_monthly_averages',
    python_callable=compute_monthly_avg,
    op_kwargs={'required_fields': "{{ params.required_fields }}"},
    dag=dag2,
)

# Task 2.5: Create heatmap visualizations
def create_heatmap_visualization(required_fields, **kwargs):
    required_fields = [field.strip() for field in required_fields.split(",")]
    with beam.Pipeline(runner='DirectRunner') as p:
        result = (
            p
            | 'ReadProcessedData' >> beam.io.ReadFromText('/tmp/results/averages.txt*')
            | 'PreprocessParse' >> beam.Map(lambda a: make_tuple(a.replace('nan', 'None')))
            | 'GlobalAggregation' >> beam.CombineGlobally(Aggregated(required_fields=required_fields))
            | 'FlatMap' >> beam.FlatMap(lambda a: a)
            | 'PlotGeomaps' >> beam.Map(plot_geomaps)
        )

create_heatmap_task = PythonOperator(
    task_id='create_heatmap_visualization',
    python_callable=create_heatmap_visualization,
    op_kwargs={'required_fields': "{{ params.required_fields }}"},
    dag=dag2,
)

# Task 2.6: Delete CSV files after processing
delete_csv_task = PythonOperator(
    task_id='delete_csv_file',
    python_callable=lambda: shutil.rmtree('/tmp/data2'),
    dag=dag2,
)

# Task dependencies
wait_task >> unzip_task >> process_csv_files_task >> delete_csv_task
unzip_task >> compute_monthly_avg_task >> create_heatmap_task >> delete_csv_task