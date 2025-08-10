import pandas as pd
from google.cloud import storage, bigquery
import os
import dotenv
dotenv.load_dotenv()
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import PROJECT_ID

def clean_data(df):
    df = df.dropna()

    # Định dạng lại kiểu dữ liệu
    df['Date'] = pd.to_datetime(df['Date'])
    df['Age'] = df['Age'].astype(int)
    df['Quantity'] = df['Quantity'].astype(int)
    df['Price per Unit'] = df['Price per Unit'].astype(float)
    df['Total Amount'] = df['Total Amount'].astype(float)

    # Tạo cột Month, Year
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year

    df = df.drop_duplicates(subset=['Transaction ID'])
    return df

def create_bucket(bucket_name):
    client = storage.Client(project=PROJECT_ID)
    try:
        client.get_bucket(bucket_name)
        print(f'Bucket {bucket_name} already exists.')
    except Exception as e:
        bucket = client.bucket(bucket_name)
        bucket.location = 'ASIA-SOUTHEAST1'
        client.create_bucket(bucket)

def create_dataset_bq(dataset_id):
    client = bigquery.Client(project=PROJECT_ID)
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
    try:
        client.get_dataset(dataset)
        print(f'Dataset {dataset_id} already exists.')
    except Exception as e:
        dataset.location = 'asia-southeast1'
        client.create_dataset(dataset)
        print(f'Dataset {dataset_id} created successfully.')


