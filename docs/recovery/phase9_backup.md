# Backup và khôi phục snapshot

## Chạy từ bản backup trên máy khác

Gói chứa raw CSV, Bronze CSV/Parquet, ba snapshot Silver, tám snapshot Gold,
code, định nghĩa Fabric, TMDL/PBIP/PBIR, cấu hình, manifest và bằng chứng nguồn.
Snapshot Gold là `20260925T152721965637Z`; Silver tương ứng là
`20260925T152449241452Z`. Các file nguồn được định danh bằng SHA-256.

Cài Python 3.13 bản Windows x64. Gói đã kèm các thư viện thực thi kiểm thử;
không cần pip, tài khoản Fabric hoặc truy cập OneLake để khôi phục.
Thư viện native kèm theo không dùng được cho hệ điều hành/kiến trúc khác.
Python và thư viện chuẩn được cung cấp bởi máy chạy.

Giải nén backup vào thư mục mới, kiểm tra SHA-256 ZIP với file sidecar được giao,
rồi chạy từ bất kỳ thư mục nào. Thay đường dẫn dưới đây bằng đường dẫn thực tế:

```powershell
python -I -S -B C:/restore/ev-analytics-backup/code/scripts/phase9_restore.py --backup C:/restore/ev-analytics-backup --output C:/restore/verification-01
```

Thư mục output phải chưa tồn tại và nằm ngoài backup. Script kiểm tra toàn bộ
inventory/checksum trước khi nạp thư viện từ gói; dừng nếu thiếu, thừa hoặc sai file.
Giữ backup nguyên trạng; không chạy script theo cách tạo `__pycache__` trong gói.

Kết quả gồm `restore_report.json`, `source_quality.json`, `input_paths.json`,
`catalog.json`, 15 bảng Parquet đã dựng lại và `ev_analytics.sqlite` để truy vấn.
Parquet giữ kiểu dữ liệu/schema; SQLite lưu decimal và timestamp dưới dạng text
để giữ chính xác giá trị. Không dùng SQLite làm bản thay thế Spark ở giai đoạn 10.

Điều kiện đạt: báo cáo `status=passed`; Respondents 668665, Yes 116779,
No 551886, orphan 0 và 35 nhóm segment khớp. Script cũng kiểm tra dữ liệu nguồn,
khóa, schema, nguồn gốc và tái dựng Silver train chính xác từ fact và dimensions.

## Phạm vi cách ly

Lệnh dùng `-I -S -B` để bỏ biến môi trường Python, site-packages và cache import.
Python audit hook chặn socket, tiến trình con và việc đọc file ngoài backup,
output và thư viện chuẩn Python; hai phép thử chủ động xác nhận mạng và đường
dẫn ngoài backup bị chặn. Không nạp credential store hay gọi API Fabric.
Đây là kiểm soát ở tiến trình Python cho script đã kiểm tra, không phải firewall
của hệ điều hành. Các trình đọc Parquet được cấp đường dẫn/file cục bộ.

## Tạo lại backup từ dữ liệu đã tải

```powershell
python scripts/phase9_backup.py --destination output/phase9/ev-analytics-backup --staging output/phase9/staging --gold output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z
```

Chọn destination mới cho mỗi lần đóng gói. Staging cần ba Delta v0 log mang tên
`train.json`, `test.json`, `original_reference.json`, các file `add` tương ứng
trong thư mục theo vai trò và `receipts.json` ghi biên nhận tải OneLake.
Trình đóng gói từ chối protocol/partition/column mapping hoặc các biến thể Delta
không hỗ trợ. Gói lưu snapshot Parquet; log Silver chỉ là bằng chứng nguồn,
không phải bản backup đầy đủ lịch sử Delta.

Raw và Bronze được đối chiếu SHA-256 với manifest nguồn trước khi đóng gói.
Gold export cũ được sao chép nguyên trạng. Notebook bỏ output; không sao chép
credential store, `.env`, `.git`, `.pbi` hoặc nhật ký output. Quét các mẫu token,
secret và private key trong tài sản dạng text; chỉ giữ tên biến xác thực cần
cấp lại nếu sau này triển khai lên dịch vụ.

TMDL, report và định nghĩa pipeline được lưu từ phiên bản hiện có trong repo;
không tuyên bố đây là một lần đồng bộ lại mọi chỉnh sửa trực tiếp trên dịch vụ.
Bằng chứng và ID Fabric cũ được giữ để truy xuất nguồn gốc. Việc chạy lại toàn bộ
Bronze → Silver → Gold bằng PySpark/Airflow, chuyển model/report sang nền tảng khác
và cài Spark/Java/Airflow được mô tả trong [runbook standalone](../pipelines/standalone_pipeline.md).

Xem [tổng kết và điều kiện nghiệm thu](../validation.md).
