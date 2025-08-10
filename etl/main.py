import os
import io
import pandas as pd
from flask import Flask, jsonify, request
from google.cloud import storage, bigquery

# ========== CONFIG ==========
PROJECT_ID = "interns-2025-467409"
BUCKET_NAME = os.getenv("BUCKET_NAME", "sales-bucket-ta-1-group3")
BLOB_NAME = os.getenv("BLOB_NAME", "sales.csv")
BQ_DATASET = "sales_dataset"
BQ_TABLE = os.getenv('BQ_TABLE', f'{PROJECT_ID}.{BQ_DATASET}.sales_table')
PATH_TO_FILE = os.getenv('PATH_TO_FILE', 'data/retail_sales.csv')

# ========== APP SETUP ==========
app = Flask(__name__)

# ========== HELPERS ==========
def clean_data(df):
    df = df.dropna()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Age'] = df['Age'].astype(int)
    df['Quantity'] = df['Quantity'].astype(int)
    df['Price per Unit'] = df['Price per Unit'].astype(float)
    df['Total Amount'] = df['Total Amount'].astype(float)
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year
    df = df.drop_duplicates(subset=['Transaction ID'])
    return df

def create_bucket(bucket_name):
    client = storage.Client(project=PROJECT_ID)
    try:
        client.get_bucket(bucket_name)
        print(f'Bucket {bucket_name} already exists.')
    except Exception:
        bucket = client.bucket(bucket_name)
        bucket.location = 'ASIA-SOUTHEAST1'
        client.create_bucket(bucket)
        print(f'Bucket {bucket_name} created.')

def create_dataset_bq(dataset_id):
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
    try:
        client.get_dataset(dataset_ref)
        print(f'Dataset {dataset_id} already exists.')
    except Exception:
        dataset_ref.location = 'asia-southeast1'
        client.create_dataset(dataset_ref)
        print(f'Dataset {dataset_id} created.')

def upload_file_to_gcs(bucket_name, blob_name, file_path):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    print(f"Uploaded {file_path} to gs://{bucket_name}/{blob_name}")

def download_blob(bucket_name, blob_name):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    return pd.read_csv(io.BytesIO(data))

def load_to_bq(df, table_id):
    client = bigquery.Client(project=PROJECT_ID)
    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    )
    job.result()
    print(f"Loaded {df.shape[0]} rows into {table_id}")

# ========== MAIN ETL ==========
def run_etl():
    try:
        create_bucket(BUCKET_NAME)
        create_dataset_bq(BQ_DATASET)
        df = download_blob(BUCKET_NAME, BLOB_NAME)
        df = clean_data(df)
        load_to_bq(df, BQ_TABLE)

        return {
            'status': 'success',
            'message': 'ETL process completed successfully.',
            'rows_processed': df.shape[0],
            'table': BQ_TABLE
        }
    except Exception as e:
        print(f"[ERROR] ETL failed: {e}")
        return {'status': 'error', 'message': str(e)}

# ========== FLASK ENDPOINTS ==========
@app.route('/', methods=['GET', 'POST'])
def trigger_etl():
    result = run_etl()
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "etl-sales-pipeline"}), 200

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "Flask app is running",
        "port": os.environ.get('PORT', 'not set'),
        "project_id": PROJECT_ID,
        "bucket": BUCKET_NAME
    }), 200

# ========== MAIN ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
