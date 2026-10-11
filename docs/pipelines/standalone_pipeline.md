# Chạy pipeline PySpark và Airflow

Luồng xử lý: `input_check -> bronze -> silver -> gold -> quality -> publish`. Chuẩn bị bốn CSV tại `data/raw/kaggle/` theo `metadata/source_manifest.json`; dữ liệu và runtime local không nằm trong Git.

## Runtime Windows

Runtime local: Python 3.13, Java 17, PySpark/Spark 3.5.9. Bản Windows trước đây đã chạy với Microsoft OpenJDK 17.0.20.1, Hadoop runtime 3.3.4 và compatibility helper 3.3.5. Xem [ma trận môi trường và dependency](../../requirements/README.md).

Cài Java 17 riêng; chuẩn bị `winutils.exe` và `hadoop.dll` trước khi chạy Spark. Repo không phân phối các binary này. Helper ưu tiên `JAVA_HOME`/`HADOOP_HOME` đã cấu hình; nếu chưa có, tìm Microsoft JDK 17 tại `C:/Program Files/Microsoft/` và helper ở `.tools/hadoop-3.3.5/`. Có thể truyền `-JavaHome <path>` và `-HadoopHome <path>` khi dot-source, không cần sửa script. Dùng nguồn binary đã được đơn vị của bạn kiểm chứng, đối chiếu checksum dưới đây nếu dùng đúng bộ helper lịch sử; hoặc chọn runtime Linux riêng ở phần Airflow. Script kiểm tra Java 17 và sự hiện diện của cả hai helper, không tự tải binary.

Checksum helper đã dùng:

- `winutils.exe`: `A0CA6E358357C41EF56EBDB02C38E4A4D55DA7CA7A13001678BB2EF7D644ADEA`.
- `hadoop.dll`: `D3DD64AFDC85F2A7EB5345ABF2ECAA744B0A157DE40859313337D47F81EE1C7B`.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/requirements_dev.txt -c requirements/constraints-local-py313.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/verify_source_download.py --directory data/raw/kaggle
. ./scripts/phase10_env.ps1 -PythonExecutable .venv/Scripts/python.exe
.venv/Scripts/python.exe -m src.run_pipeline --raw data/raw/kaggle --output-root output/local
```

Nếu PowerShell chặn script, có thể dùng `Set-ExecutionPolicy -Scope Process Bypass` trong phiên hiện tại trước khi dot-source. Airflow chạy trong Linux container, không cài native trên Windows.

## Chạy từng stage và retry

```powershell
.venv/Scripts/python.exe -m src.stage_runner input_check --run-id my_run
.venv/Scripts/python.exe -m src.stage_runner bronze --run-id my_run
.venv/Scripts/python.exe -m src.stage_runner silver --run-id my_run
.venv/Scripts/python.exe -m src.stage_runner gold --run-id my_run
.venv/Scripts/python.exe -m src.stage_runner quality --run-id my_run
.venv/Scripts/python.exe -m src.stage_runner publish --run-id my_run
```

Mặc định marker nằm tại `output/phase10/runs/<run_id>/stage_status/`. `run_context.json` giữ checksum nguồn, metadata, code và cấu hình. Retry chỉ bỏ qua stage đã đạt khi context và artifact còn nguyên. Dùng run ID mới nếu đầu vào/code/cấu hình đổi hoặc integrity không đạt; giữ run lỗi để chẩn đoán, không xóa marker để bỏ qua quality gate.

Quality kiểm đủ tám bảng, schema, khóa, orphan, KPI, 35 nhóm segment và tái dựng Gold từ Silver bằng phép so sánh đa tập hai chiều. Chỉ publish khi quality và checksum đạt. Kết quả chuẩn: 668665 respondents, 116779 Yes, 551886 No, orphan 0; năm dimension có lần lượt 45/4/16/2/30 dòng.

## Airflow

```powershell
docker build -t ev-phase10-airflow:2.10.5 -f docker/phase10_airflow/Dockerfile .
```

Image pin Airflow 2.10.5/Python 3.11, Java 17 và PySpark 3.5.9. DAG `dags/ev_analytics_phase10.py` chạy theo yêu cầu (`schedule=None`), `catchup=False`, tối đa một run, retry hai lần cách nhau hai phút. Failure callback ghi log; chưa cấu hình gửi thông báo.

Chạy từ gốc repo với dữ liệu đã chuẩn bị. Output nằm trong thư mục local được Git ignore:

```powershell
$projectRoot = (Get-Location).Path
New-Item -ItemType Directory -Force -Path output/airflow | Out-Null
$airflowOutput = (Resolve-Path output/airflow).Path
docker run --rm --hostname ev-local --add-host ev-local:127.0.0.1 --network none --entrypoint bash --mount "type=bind,source=$projectRoot,target=/opt/ev,readonly" --mount "type=bind,source=$airflowOutput,target=/opt/ev/output" -e EV_PROJECT_ROOT=/opt/ev -e AIRFLOW__CORE__DAGS_FOLDER=/opt/ev/dags -e PYTHONDONTWRITEBYTECODE=1 -e SPARK_LOCAL_IP=127.0.0.1 -e SPARK_MASTER=local[2] -e SPARK_SHUFFLE_PARTITIONS=8 ev-phase10-airflow:2.10.5 /opt/ev/scripts/phase10_airflow_dag_test.sh
```

Để tiếp tục run bị ngắt, giữ nguyên output và thay lệnh cuối bằng `/opt/ev/scripts/phase12_airflow_resume.sh <run_id>`. Từng stage kiểm lại integrity trước khi bỏ qua công việc đã đạt; chọn run ID mới khi code/metadata/input đổi.

## Kiểm thử

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
. ./scripts/phase10_env.ps1 -PythonExecutable .venv/Scripts/python.exe
$env:EV_RUN_SPARK_TESTS = '1'
.venv/Scripts/python.exe -m unittest discover -s tests -p test_phase10_spark.py -v
Remove-Item Env:EV_RUN_SPARK_TESTS
```

Test renderer Airflow cần Linux image có Airflow. Bộ test trong repo dùng fixture tạm hoặc reference được version hóa; các diễn tập phụ thuộc snapshot riêng được giữ local. Các test skip vì thiếu runtime không được tính là passed.

Spark ghi timestamp UTC; công cụ Parquet khác có thể hiển thị độ chính xác hoặc timezone khác. Đối chiếu cross-platform bằng [công cụ Databricks reconciliation](phase11_databricks.md), giữ schema và chỉ bỏ giá trị lineage được cho phép thay đổi theo run.
