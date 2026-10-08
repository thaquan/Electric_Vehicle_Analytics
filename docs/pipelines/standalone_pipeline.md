# Chạy pipeline PySpark và Airflow

Luồng xử lý: `input_check -> bronze -> silver -> gold -> quality -> publish`. Chuẩn bị bốn CSV tại `data/raw/kaggle/` theo `metadata/source_manifest.json`; dữ liệu và runtime local không nằm trong Git.

## Runtime Windows

Môi trường đã kiểm chứng: Python 3.13, Microsoft OpenJDK 17.0.20.1, PySpark/Spark 3.5.9, Hadoop runtime 3.3.4 và Windows compatibility helper 3.3.5. Cài Java 17 và chuẩn bị helper phù hợp trước khi chạy. `scripts/phase10_env.ps1` tìm JDK tại `C:/Program Files/Microsoft/jdk-17*` và helper tại `.tools/hadoop-3.3.5/bin/`; chỉnh đường dẫn nếu máy khác dùng vị trí khác.

Checksum helper đã dùng:

- `winutils.exe`: `A0CA6E358357C41EF56EBDB02C38E4A4D55DA7CA7A13001678BB2EF7D644ADEA`.
- `hadoop.dll`: `D3DD64AFDC85F2A7EB5345ABF2ECAA744B0A157DE40859313337D47F81EE1C7B`.

```powershell
python -m pip install -r requirements.txt -r requirements/requirements_phase10.txt
. ./scripts/phase10_env.ps1
python -m src.run_pipeline --raw data/raw/kaggle --output-root output/local
```

Nếu PowerShell chặn script, có thể dùng `Set-ExecutionPolicy -Scope Process Bypass` trong phiên hiện tại trước khi dot-source. Airflow chạy trong Linux container, không cài native trên Windows.

## Chạy từng stage và retry

```powershell
python -m src.stage_runner input_check --run-id my_run
python -m src.stage_runner bronze --run-id my_run
python -m src.stage_runner silver --run-id my_run
python -m src.stage_runner gold --run-id my_run
python -m src.stage_runner quality --run-id my_run
python -m src.stage_runner publish --run-id my_run
```

Mặc định marker nằm tại `output/phase10/runs/<run_id>/stage_status/`. `run_context.json` giữ checksum nguồn, metadata, code và cấu hình. Retry chỉ bỏ qua stage đã đạt khi context và artifact còn nguyên. Dùng run ID mới nếu đầu vào/code/cấu hình đổi hoặc integrity không đạt; giữ run lỗi để chẩn đoán, không xóa marker để bỏ qua quality gate.

Quality kiểm đủ tám bảng, schema, khóa, orphan, KPI, 35 nhóm segment và tái dựng Gold từ Silver bằng phép so sánh đa tập hai chiều. Chỉ publish khi quality và checksum đạt. Kết quả chuẩn: 668665 respondents, 116779 Yes, 551886 No, orphan 0; năm dimension có lần lượt 45/4/16/2/30 dòng.

## Airflow

```powershell
docker build -t ev-phase10-airflow:2.10.5 -f docker/phase10_airflow/Dockerfile .
```

Image pin Airflow 2.10.5/Python 3.11, Java 17 và PySpark 3.5.9. DAG `dags/ev_analytics_phase10.py` chạy theo yêu cầu (`schedule=None`), `catchup=False`, tối đa một run, retry hai lần cách nhau hai phút. Failure callback ghi log; chưa cấu hình gửi thông báo.

Hướng dẫn mount dữ liệu, chạy sáu stage trong container và tiếp tục run bị ngắt nằm ở [diễn tập Airflow](../operations/phase12_operations.md#diễn-tập-airflow-với-image-đã-có-trên-máy). Công cụ `scripts/phase10_airflow_dag_test.sh` tạo run mới; `scripts/phase12_airflow_resume.sh` tiếp tục cùng application run ID qua integrity gate.

## Kiểm thử

```powershell
python -m pip install -r requirements/requirements_export.txt -r requirements/requirements_phase11.txt -r requirements/requirements_cd.txt
python -m unittest discover -s tests -v
. ./scripts/phase10_env.ps1
$env:EV_RUN_SPARK_TESTS = '1'
python -m unittest discover -s tests -p test_phase10_spark.py -v
```

Test renderer Airflow cần Linux image có Airflow; test recovery cần snapshot theo [recovery runbook](../recovery/recovery_runbook.md). Fresh clone không chứa snapshot. Các test skip vì thiếu runtime không được tính là passed.

Spark ghi timestamp UTC; công cụ Parquet khác có thể hiển thị độ chính xác hoặc timezone khác. Đối chiếu cross-platform bằng [công cụ Databricks reconciliation](phase11_databricks.md), giữ schema và chỉ bỏ giá trị lineage được cho phép thay đổi theo run.
