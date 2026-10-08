# Phase 12 — Hướng dẫn bàn giao và khôi phục

Phạm vi kỹ thuật mặc định là các thành phần đã triển khai: Fabric/Power BI hiện có, PySpark/Airflow độc lập và pipeline Databricks serverless. Người tiếp nhận và phạm vi vận hành cuối cùng cần được chủ dự án xác nhận. Không chuyển nguồn Power BI sang Databricks trong đợt bàn giao này.

## Bản bàn giao

Gói bàn giao cuối: `output/phase12/final/ev-analytics-handoff.zip`, kèm file `.zip.sha256`, `package_report.json` và `final_archive_verification.json`. Hai báo cáo cuối được tạo sau khi đóng ZIP và giao bên ngoài ZIP. Không đưa dữ liệu lớn vào Git. Manifest trong ZIP ghi base commit và checksum chính xác của bản code được đóng gói, bao gồm phần phase 12 chưa commit. Không dùng base commit một mình để tái tạo bản bàn giao. Bản r2 là bản dùng thử ban đầu; bản cuối sửa hướng dẫn thư mục giải nén và mô tả phương pháp quét, kèm bằng chứng bổ sung.

Gói gồm code/config/notebook/tài liệu/định nghĩa Fabric và Power BI hiện tại, backup Phase 9 release-02 nguyên trạng, snapshot Bronze/Silver/Gold Databricks `phase11_20261006T013808Z`, Gold chuẩn Phase 10, và DuckDB cho kiểm tra offline. Python interpreter, Java/Spark/Airflow và dịch vụ cloud không nằm trong ZIP.

Bản ZIP trên ổ D chưa bảo vệ được tình huống mất máy/ổ đĩa. Chủ dự án cần chỉ định nơi giữ bản sao độc lập và người quản lý, rồi xác minh checksum bản sao. Chưa có chính sách thời hạn lưu được phê duyệt; giữ các release đã nghiệm thu, không tự xóa bản cũ.

## Khôi phục từ ZIP trên Windows x64

1. Cài Python 3.13 Windows x64. So sánh SHA-256 ZIP với giá trị trong `package_report.json` hoặc sidecar đã được bàn giao qua nguồn tin cậy. Checksum bảo vệ tính toàn vẹn, không tự xác thực người phát hành.
2. Giải nén vào thư mục mới; giữ nguyên cây `handoff`. Dùng đường dẫn gốc ngắn trên Windows (ví dụ `C:/restore`) để tránh giới hạn độ dài đường dẫn của công cụ native.
3. Chạy lệnh dưới đây, thay đường dẫn theo nơi giải nén. Output phải chưa tồn tại và nằm ngoài bundle.

```powershell
Get-FileHash C:/restore/ev-analytics-handoff.zip -Algorithm SHA256
python -I -S -B C:/restore/handoff/project/scripts/phase12_restore.py --bundle C:/restore/handoff --output C:/restore/verification-01
```

Không cần credential cloud hoặc pip cho lệnh khôi phục này. Công cụ kiểm tra toàn bộ inventory, giải nén baseline Phase 9, chạy khôi phục độc lập với môi trường không truyền credential, kiểm tra publish inventory snapshot Databricks và đối chiếu đủ tám bảng Gold. Kết quả phải có `restore_report.json` và `phase11_reconciliation.json` đạt. Baseline có Python audit guard chặn mạng; lớp khôi phục ngoài không phải firewall của hệ điều hành.

## Chạy lại từ code và dữ liệu đã khôi phục

Raw CSV sau khôi phục nằm tại `verification-01/baseline/ev-analytics-backup/data/raw`. Từ `handoff/project`, cài dependencies đúng nền tảng và chạy:

```powershell
python -m pip install -r requirements.txt -r requirements/requirements_phase10.txt -r requirements/requirements_phase11.txt
# Windows: cần Java 17 và Hadoop winutils; chỉnh đường dẫn môi trường theo máy đích.
python -m src.run_pipeline --raw C:/restore/verification-01/baseline/ev-analytics-backup/data/raw --output-root C:/restore/pipeline-results --run-id handoff_01
python scripts/phase11_reconcile.py --reference-gold C:/restore/handoff/reference/phase10/gold --candidate-gold C:/restore/pipeline-results/runs/handoff_01/gold --output C:/restore/handoff_01_reconciliation.json
```

`scripts/phase10_env.ps1` hỗ trợ máy phát triển hiện tại, cần chỉnh Java/Hadoop cho máy khác; Hadoop binaries không được gói kèm release này. Hướng dẫn Airflow/Docker và DAG ở [runbook PySpark/Airflow](../pipelines/standalone_pipeline.md). Với Databricks, chạy `phase11_package.py --raw <raw-đã-khôi-phục> --output <project-mới>` rồi làm theo [phase11_databricks.md](../pipelines/phase11_databricks.md).

### Diễn tập Airflow với image đã có trên máy

Image `ev-phase10-airflow:2.10.5` đã có trên máy hiện tại, không nằm trong ZIP. Máy khác cần build image từ `docker/` theo hướng dẫn Phase 10. Ví dụ PowerShell dưới đây dùng bundle đã giải nén; `output/phase12/airflow-new` là thư mục kết quả mới:

```powershell
$handoffRoot = (Resolve-Path output/phase12/final/clean-room/handoff).Path
New-Item -ItemType Directory -Force -Path "$handoffRoot/project/output", "$handoffRoot/project/data/raw/kaggle", output/phase12/airflow-new | Out-Null
$handoffOutput = (Resolve-Path output/phase12/airflow-new).Path
docker run --rm --hostname ev-phase12 --add-host ev-phase12:127.0.0.1 --network none --entrypoint bash --mount "type=bind,source=$handoffRoot/project,target=/opt/ev,readonly" --mount "type=bind,source=$handoffRoot/snapshots/phase11/bronze/csv,target=/opt/ev/data/raw/kaggle,readonly" --mount "type=bind,source=$handoffOutput,target=/opt/ev/output" -e EV_PROJECT_ROOT=/opt/ev -e AIRFLOW__CORE__DAGS_FOLDER=/opt/ev/dags -e PYTHONDONTWRITEBYTECODE=1 -e SPARK_LOCAL_IP=127.0.0.1 -e SPARK_MASTER=local[2] -e SPARK_SHUFFLE_PARTITIONS=8 ev-phase10-airflow:2.10.5 /opt/ev/scripts/phase10_airflow_dag_test.sh
```

Các thư mục mount rỗng được tạo trước khi mount project chỉ đọc; không sửa file trong bundle. Hostname ánh xạ loopback và `SPARK_LOCAL_IP` là cần thiết trong môi trường không có mạng để tránh Java gateway lỗi phân giải tên máy. Giữ run lỗi để chẩn đoán, dùng run ID mới khi sửa cấu hình runtime.

Nếu bị ngắt nhưng code, đầu vào và artifact còn nguyên, dùng lại thư mục output đó và run ID cũ. Trong lệnh Docker trên, thay phần cuối `/opt/ev/scripts/phase10_airflow_dag_test.sh` bằng `/opt/ev/scripts/phase12_airflow_resume.sh <run_id_cũ>`. Script tạo một DagRun kiểm thử mới với cùng application run ID; từng stage kiểm lại context/inventory trước khi bỏ qua xử lý đã đạt. Không xóa marker hoặc tự tạo publish marker. Nếu context/inventory khác, dừng và chọn run ID mới để chạy lại từ đầu.

## Kiểm tra vận hành

- Với snapshot cố định: chạy theo yêu cầu, sau thay đổi code/config hoặc sau khôi phục; chưa có yêu cầu chạy hằng ngày.
- Pipeline: kiểm tra job kết thúc thành công, quality đạt, `published.json` và checksum; không chọn run lỗi làm nguồn báo cáo.
- Fabric Test: dùng danh tính Azure CLI đã có quyền, chạy `python scripts/check_test_health.py --output <health.json>` với `EV_DAX_API=json`. Kiểm tra này đọc refresh gần nhất, không kích hoạt refresh mới và không kiểm tra hình ảnh report.
- Databricks: dùng CLI mặc định đã đăng nhập. Lỗi thiếu cached credentials trong sandbox phải được kiểm tra lại trong terminal có quyền đọc cache; không lưu token vào repo hoặc ZIP.
- Kết quả chuẩn: 668665 respondents, 116779 Yes, 551886 No, orphan 0, tám bảng Gold, 35 nhóm segment.
- Log lỗi được lưu vào file; gửi thông báo tự động chưa được cấu hình. Chủ dự án chỉ định người nhận/kênh trước khi triển khai thông báo.

## Xử lý lỗi và rollback

| Tình huống | Cách xử lý |
| --- | --- |
| Checksum nguồn/package sai | Dừng; lấy lại đúng bản đã nghiệm thu, không sửa manifest để bỏ qua lỗi. |
| Quality không đạt | Giữ run lỗi và log, không publish; sửa nguyên nhân và chọn run ID mới khi input/code thay đổi. |
| Retry | Chỉ dùng lại run ID nếu context và artifact còn nguyên; xem stage marker trước khi chạy tiếp. |
| Notebook serverless import sai module | Đóng gói lại bằng `phase11_package.py`, upload vào thư mục release mới, truyền đúng `project_root`. |
| API DAX Arrow trả 401 | Dùng backend JSON đã kiểm chứng, không bỏ qua KPI check. |
| Release mới lỗi | Dùng lại package/run đã nghiệm thu trước đó; giữ cả code và dữ liệu tương ứng. Job submit một lần không tự thay đổi job cũ. |
| Fabric report/model lỗi | Theo [operations_runbook.md](operations_runbook.md), giữ item ID, kiểm tra nguồn model và binding sau rollback. |

## Phân công và giới hạn cần xác nhận

Tài khoản đang sở hữu job/schema/Volume Databricks được ghi trong `metadata/phase12/databricks_access.json`; đây không phải chứng nhận quyền tối thiểu của một người nhận khác. Người tiếp nhận, người dự phòng, thời hạn lưu backup, kênh báo lỗi và mức thời gian/chi phí chấp nhận chưa được chỉ định. Bằng chứng dịch vụ, restore và test của đợt nghiệm thu lưu tại `metadata/phase12/`; kết quả lớn ở `output/phase12/`.
