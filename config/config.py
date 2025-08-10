import os

PROJECT_ID = "interns-2025-467409"
SERVICE_ACCOUNT_EMAIL = "service-account-group-3-nexlab@interns-2025-467409.iam.gserviceaccount.com"
BUCKET_NAME = os.getenv("BUCKET_NAME", "sales-bucket-ta-1-group3")
BLOB_NAME = os.getenv("BLOB_NAME", "sales.csv")
BQ_DATASET = BUCKET_NAME  # Dataset trùng tên bucket
BQ_TABLE = os.getenv('BQ_TABLE', f'{PROJECT_ID}.{BQ_DATASET}.sales')
PATH_TO_FILE = os.getenv('PATH_TO_FILE', '../data/retail_sales.csv')