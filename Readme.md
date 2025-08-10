# 📦 Pipeline ETL Dữ Liệu Bán Hàng Hàng Ngày trên Google Cloud Platform (GCP)

## Tổng Quan Dự Án

Dự án này xây dựng một **pipeline ETL serverless end-to-end** để xử lý file CSV bán hàng hàng ngày, chuyển đổi và làm sạch dữ liệu, sau đó nạp vào BigQuery để báo cáo và phân tích. Toàn bộ quy trình được tự động hóa bằng các dịch vụ quản lý của GCP, đảm bảo khả năng mở rộng, vận hành ổn định và tiết kiệm chi phí.

---

## Sơ Đồ Kiến Trúc

```
[CSV Data] → [Cloud Storage] → [Cloud Scheduler] → [Cloud Workflows] → [Cloud Run] → [BigQuery] → [Looker Studio]
```

- **Cloud Storage (GCS):** Lưu trữ các file CSV bán hàng hàng ngày.
- **Cloud Run:** Chạy script ETL Python trong container (Flask web server).
- **Cloud Workflows:** Điều phối các bước pipeline qua HTTP call.
- **Cloud Scheduler:** Lên lịch chạy hàng ngày.
- **BigQuery:** Lưu trữ dữ liệu đã được xử lý để truy vấn và tạo dashboard.
- **Looker Studio:** Tạo dashboard từ dữ liệu BigQuery.

---

## Thành Phần & Các Bước Triển Khai

### 1. Thiết Lập Google Cloud

Xác thực và chọn project:
```bash
gcloud auth login
gcloud config set project interns-2025-467409
```

### 2. Bật Các API Cần Thiết

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  workflows.googleapis.com \
  cloudscheduler.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com
```

### 3. Cloud Storage (GCS)

- **Bucket:** `sales-bucket-ta-1-group3` (`asia-southeast1`)
- **Upload Dữ Liệu:**
  ```bash
  gcloud storage buckets create gs://sales-bucket-ta-1-group3 --location=asia-southeast1
  gcloud storage cp data/retail_sales.csv gs://sales-bucket-ta-1-group3/sales.csv
  gcloud storage ls gs://sales-bucket-ta-1-group3/
  ```
- **Mục đích:** Lưu trữ tập trung các file CSV đầu vào.

### 4. Service Account

- **Email:** `service-account-group-3-nexlab@interns-2025-467409.iam.gserviceaccount.com`
- **Quyền:** Storage, BigQuery, Cloud Run, Workflows (OIDC để gọi dịch vụ an toàn).

### 5. Build Docker & Deploy Cloud Run

- **Build Container:**
  ```bash
  gcloud builds submit --config=infra/cloudbuild.yaml .
  ```
  - Copy mã nguồn, cài dependencies (`pandas`, `google-cloud-*`, `flask`, `pyarrow`), build Docker image.
  - **Image:** `gcr.io/interns-2025-467409/etl-sales-pipeline:latest`
- **Deploy Cloud Run Service:**
  ```bash
  gcloud run deploy etl-sales-pipeline \
    --image gcr.io/interns-2025-467409/etl-sales-pipeline:latest \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 1 \
    --set-env-vars PROJECT_ID=interns-2025-467409
  ```
  - **Endpoints:**
    - `/` - Trigger ETL pipeline
    - `/health` - Kiểm tra sức khỏe
    - `/test` - Kiểm tra trạng thái

### 6. Cloud Workflows

- **Triển khai Workflow:**
  ```bash
  gcloud workflows deploy etl-sales-workflow \
    --source=infra/workflow.yaml \
    --location=asia-southeast1
  ```
  - Điều phối gọi Cloud Run.
  - Xử lý lỗi và ghi log lên Cloud Logging.

### 7. Cloud Scheduler

- **Tạo Scheduler Job:**
  ```bash
  gcloud scheduler jobs create http daily-etl-sales-pipeline \
    --location=asia-southeast1 \
    --schedule="0 9 * * *" \
    --time-zone="Asia/Saigon" \
    --uri="https://workflows.googleapis.com/v1/projects/interns-2025-467409/locations/asia-southeast1/workflows/etl-sales-workflow/executions" \
    --http-method=POST \
    --oidc-service-account-email=service-account-group-3-nexlab@interns-2025-467409.iam.gserviceaccount.com \
    --headers="Content-Type=application/json" \
    --message-body="{}" \
    --description="Daily ETL pipeline for sales data processing"
  ```
  - **Lịch:** Hàng ngày lúc 9:00 AM ICT (GMT+7).

---

## Quy Trình ETL

### Các Bước Chính

1. **Extract:** Tải file CSV từ Cloud Storage.
2. **Transform:**
   - Loại bỏ giá trị null
   - Chuyển đổi kiểu dữ liệu (ngày, số)
   - Chuẩn hóa format (thêm cột Tháng/Năm)
   - Loại bỏ trùng lặp (theo Transaction ID)
3. **Load:** Nạp dữ liệu đã xử lý vào BigQuery (`WRITE_APPEND`).

### Các Hàm Chính (`etl/main.py`)

- `clean_data()` - Làm sạch và chuyển đổi dữ liệu
- `create_bucket()` - Quản lý GCS bucket
- `create_dataset_bq()` - Tạo dataset/table BigQuery
- `download_blob()` - Tải dữ liệu từ GCS
- `load_to_bq()` - Nạp dữ liệu vào BigQuery
- `run_etl()` - Điều phối toàn bộ ETL
- Các route Flask: `/`, `/health`, `/test`

---

## Bảo Mật & Xác Thực

- **Service Account:** Dùng cho mọi dịch vụ, gọi nhau qua OIDC token.
- **Phân quyền:** Tối thiểu cần thiết (Storage, BigQuery, Workflows, Cloud Run).
- **Workflow call:** Xác thực audience/endpoint đúng.

---

## Kết Quả & Kiểm Tra

- **ETL Pipeline:** 1000+ dòng xử lý và nạp vào BigQuery.
- **Cloud Run:** Endpoint hoạt động và kiểm tra tốt.
- **Workflows:** Thời gian chạy trung bình 8.493s, có xử lý lỗi.
- **BigQuery:** Dữ liệu truy vấn được, sẵn sàng cho dashboard.
- **Scheduler:** Cron hoạt động, kiểm tra trigger thành công.
- **Container:** Build ổn định, đã fix dependency.

**Ví dụ phản hồi thành công:**
```json
{
  "message": "ETL process completed successfully.",
  "rows_processed": 1000,
  "status": "success", 
  "table": "interns-2025-467409.sales_dataset.sales_table"
}
```

---

## Theo Dõi & Logging

- **Cloud Logging:** Ghi lại các bước pipeline, lỗi để dễ kiểm tra.
- **Health Check:** Dùng endpoint `/health` để monitor runtime.

---

## Cấu Trúc Mã Nguồn

```
├── etl/
│   ├── main.py          # Logic ETL & Flask app
│   ├── requirements.txt # Thư viện Python
│   ├── utils.py         # Hàm phụ trợ
├── docker/
│   └── Dockerfile       # Cấu hình container
├── infra/
│   ├── workflow.yaml    # Điều phối Cloud Workflow
│   └── cloudbuild.yaml  # Tự động hóa Cloud Build
├── data/
│   └── sales_data.csv   # Dữ liệu mẫu
├── config/
│   └── config.py        # Biến cấu hình & env
```

---

## Ghi chú & Lưu ý

- **Port 8080:** Cloud Run yêu cầu container phải listen cổng này.
- **Lỗi xác thực:** Đảm bảo service account đủ quyền, OIDC setup đúng.
- **Format YAML:** Rất nhạy về thụt đầu dòng.
- **Tối ưu BigQuery:** Dùng partition & clustering (bonus).
- **Lưu trữ/Thông báo:** Di chuyển file đã xử lý sang folder archive hoặc gửi email qua Pub/Sub + Cloud Functions (bonus, nên áp dụng sản xuất).

---

## Trạng Thái Hệ Thống

**PRODUCTION READY - TOÀN BỘ HỆ THỐNG ĐÃ HOẠT ĐỘNG**

- Code, hạ tầng & tự động hóa đã triển khai và test
- Có monitoring & xử lý lỗi
- ETL tự động chạy mỗi ngày lúc **9:00 AM ICT**

---