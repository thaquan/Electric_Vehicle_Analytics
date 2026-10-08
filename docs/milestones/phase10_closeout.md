# Phase 10 Closeout — Standalone PySpark + Airflow

## 1. Mục tiêu

Phase 10 tách pipeline EV Analytics khỏi Microsoft Fabric để có thể chạy độc lập bằng PySpark, sau đó dùng Apache Airflow để điều phối thứ tự chạy, retry, log, theo dõi trạng thái và chỉ publish Gold khi quality checks đã đạt.

Luồng chuẩn:

`input_check -> bronze -> silver -> gold -> quality -> publish`

## 2. Các module độc lập khỏi Fabric

Các module chính:

- `src/bronze.py`: kiểm tra manifest/SHA/bytes, đọc source bằng Spark schema tường minh, ghi Bronze CSV/Parquet.
- `src/silver.py`: ép kiểu, xử lý nullable, tạo `will_buy_ev_flag`, bổ sung lineage, kiểm tra target leakage và ghi Silver Parquet.
- `src/gold.py`: tạo KPI, 35 segment groups và star schema gồm 5 dimensions, 1 fact, 1 KPI, 1 segment table.
- `src/quality_checks.py`: kiểm tra KPI, số lượng dimension, orphan keys, segment groups và tổng số bảng Gold.
- `src/run_pipeline.py`: chạy end-to-end độc lập bằng PySpark và chỉ tạo `published.json` sau khi quality pass.
- `src/stage_runner.py`: chạy từng stage độc lập, lưu marker trạng thái, kiểm tra dependency, hỗ trợ retry idempotent.

Các phụ thuộc Fabric-specific đã được thay bằng đường dẫn cấu hình, environment variables và helper đọc/ghi/log có thể dùng ngoài Fabric.

## 3. Chạy PySpark độc lập

Trên Windows:

```powershell
Set-Location D:\electric_vehical_sales
. .\scripts\phase10_env.ps1
python -m src.run_pipeline
```

Run đã xác minh:

- Run ID: `20261003T051746373025Z`
- Artifact: `output/phase10/runs/20261003T051746373025Z/`
- `published.json` được tạo sau quality và chứa quality snapshot đã pass.

Kết quả đối chiếu baseline Phase 9:

- respondents: `668665`
- yes: `116779`
- no: `551886`
- orphan_keys: `0`
- segment_groups: `35`
- Gold tables: `8`
- dim_demographics: `45`
- dim_income: `4`
- dim_mobility: `16`
- dim_charging: `2`
- dim_attitude_incentive: `30`

Source train SHA256 được giữ nguyên:

`141B8AC4B171CEBCE17EA7F52CF5C26F1AC5B675C24850096A3CFACA60B036D4`

## 4. Stage runner và retry/idempotence

Ví dụ:

```powershell
python -m src.stage_runner input_check --run-id my_run
python -m src.stage_runner bronze --run-id my_run
python -m src.stage_runner silver --run-id my_run
python -m src.stage_runner gold --run-id my_run
python -m src.stage_runner quality --run-id my_run
python -m src.stage_runner publish --run-id my_run
```

Mỗi stage ghi marker tại:

`output/phase10/runs/<run_id>/stage_status/<stage>.json`

Run staged đã xác minh:

- Run ID: `20261003Tphase10airflow001Z`
- Chạy lại Bronze sau khi stage đã pass trả về trạng thái `already_passed`, xác nhận cơ chế retry idempotent.
- Quality finished: `2026-10-03T05:38:22.420435+00:00`
- Publish started: `2026-10-03T05:38:26.183609+00:00`

Vì publish bắt đầu sau khi quality hoàn tất và publish stage yêu cầu quality marker có `status=passed`, Gold mới chỉ được công bố sau quality thành công.

## 5. Airflow DAG

DAG: `dags/ev_analytics_phase10.py`

Cấu hình chính:

- DAG ID: `ev_analytics_phase10`
- `schedule=None`
- `catchup=False`
- `max_active_runs=1`
- retries: `2`
- retry delay: `2 minutes`
- failure callback: ghi thông tin DAG/task/run/try vào Airflow error log
- dependency: `input_check >> bronze >> silver >> gold >> quality >> publish`

Cảnh báo hiện tại là log-based callback. Có thể nối callback này với email/Slack/Teams sau khi cấu hình Airflow connection tương ứng.

### Lỗi Jinja phát hiện trong integration test

Lần DAG test đầu tiên phát hiện `bash_command` dùng Jinja braces sai dạng `{{{{ ... }}}}`, gây `TemplateSyntaxError`. Đã sửa thành cú pháp hợp lệ:

```text
{{ dag_run.conf.get('run_id') or ts_nodash }}
```

Sau sửa, DAG test thực tế trong container chạy thành công.

## 6. Airflow container

Dockerfile: `docker/phase10_airflow/Dockerfile`

Image đã build và xác minh:

- image: `ev-phase10-airflow:2.10.5`
- Apache Airflow: `2.10.5`
- OpenJDK: `17.0.20.1`
- PySpark: `3.5.9`
- `airflow dags list-import-errors`: không có import error
- DAG `ev_analytics_phase10` được Airflow load thành công

Script integration test:

`scripts/phase10_airflow_dag_test.sh`

DAG test thực tế:

- run_id application-level: `airflow_dag_test_20261003`
- process exit code: `0`
- Airflow DagRun final state: `success`
- tất cả 6 stage markers đều `passed`

Quality kết quả:

- respondents: `668665`
- yes: `116779`
- no: `551886`
- orphan_keys: `0`
- segment_groups: `35`
- dimensions: `45 / 4 / 16 / 2 / 30`
- tables: `8`

Ordering proof của Airflow run:

- quality finished: `2026-10-03T06:45:22.918817+00:00`
- publish started: `2026-10-03T06:45:26.691848+00:00`
- published at: `2026-10-03T06:45:26.737480+00:00`

Điều này xác nhận publish không chạy trước khi quality pass.

## 7. Runtime Windows

`scripts/phase10_env.ps1` cấu hình Java/Hadoop helper cho local Spark.

Đã xác minh:

- Microsoft OpenJDK: `17.0.20.1`
- PySpark: `3.5.9`
- Spark: `3.5.9`
- Spark internal Hadoop runtime: `3.3.4`
- Hadoop Windows compatibility helper: `3.3.5`

SHA256 helper binaries:

- `winutils.exe`: `A0CA6E358357C41EF56EBDB02C38E4A4D55DA7CA7A13001678BB2EF7D644ADEA`
- `hadoop.dll`: `D3DD64AFDC85F2A7EB5345ABF2ECAA744B0A157DE40859313337D47F81EE1C7B`

`.tools/` đã được ignore trong `.gitignore`, vì vậy các binary compatibility helper không được commit vào repository.

## 8. Dependencies Phase 10

File: `requirements/requirements_phase10.txt`

```text
pyspark==3.5.9
pandas
```

Airflow được pin trong Docker image thay vì cài native trên Windows.

## 9. Evidence paths

Standalone:

- `output/phase10/runs/20261003T051746373025Z/published.json`
- `output/phase10/runs/20261003T051746373025Z/run_report.json`

Staged runner:

- `output/phase10/runs/20261003Tphase10airflow001Z/quality_report.json`
- `output/phase10/runs/20261003Tphase10airflow001Z/stage_status/quality.json`
- `output/phase10/runs/20261003Tphase10airflow001Z/stage_status/publish.json`

Real Airflow DAG test:

- `output/phase10/runs/airflow_dag_test_20261003/quality_report.json`
- `output/phase10/runs/airflow_dag_test_20261003/published.json`
- `output/phase10/runs/airflow_dag_test_20261003/stage_status/`

## 10. Kết luận

Phase 10 đã đạt mục tiêu kiến trúc: logic xử lý dữ liệu có thể chạy độc lập bằng PySpark, Airflow chỉ đảm nhiệm orchestration, retry và monitoring, và publish được chặn bằng quality gate. Kết quả standalone, staged runner và Airflow integration đều khớp snapshot chuẩn Phase 9.

## 11. Bổ sung sau review ngày 2026-10-03

Các mục 3–9 ở trên ghi lại các lần chạy trước khi bổ sung kiểm soát.

- Quality gate đọc đủ tám bảng, kiểm khóa fact/dimension, orphan, KPI, segment,
  no_count và purchase_intent_rate; không gộp các segment trùng khóa.
- Đọc lại Silver train, tái dựng các bảng Gold và đối chiếu schema cùng mọi giá trị
  bằng phép so sánh đa tập hai chiều. Kiểm tra cả lineage, thuộc tính dimension
  và thứ tự band. Số bảng báo cáo lấy từ các bảng đã đọc thực tế.
- `run_context.json` giữ checksum nguồn CSV, metadata JSON, code xử lý và cấu hình
  Spark. Marker mỗi stage giữ checksum các artifact của stage đó và các stage
  trước. Retry chỉ bỏ qua stage khi checksum vẫn khớp. Publish kiểm tra lại
  artifact đã được quality nghiệm thu.
- Nếu đầu vào/code/cấu hình thay đổi, dữ liệu thiếu/hỏng hoặc marker cũ không có
  checksum, chương trình dừng và yêu cầu run ID mới. Không tự nâng cấp marker cũ.
- Run ID chỉ nhận 1–128 ký tự ASCII chữ/số/underscore/hyphen, bắt đầu bằng chữ/số;
  chặn tên Windows dành riêng, đường dẫn vượt phạm vi và liên kết thư mục.
- Airflow truyền run ID qua biến môi trường `EV_RUN_ID`, Bash dùng giá trị đã quote.
  Script integration tạo UUID mới mỗi lần, không tái sử dụng marker của lần trước.
- Spark xử lý timestamp theo UTC. Parquet do Spark ghi có thể được PyArrow đọc
  thành `timestamp[ns]` không kèm timezone, còn snapshot Fabric là
  `timestamp[us, tz=UTC]`. Khi dùng công cụ khác, diễn giải cột này theo UTC.

### Chạy kiểm thử

```powershell
python -m unittest discover -s tests -p 'test_phase*.py' -v
. ./scripts/phase10_env.ps1
$env:EV_RUN_SPARK_TESTS = '1'
python -m unittest discover -s tests -p 'test_phase10_spark.py' -v
```

Nếu PowerShell chặn script, dùng `Set-ExecutionPolicy -Scope Process Bypass`
trong phiên chạy hiện tại rồi dot-source script. Cấu hình chỉ áp dụng cho phiên đó.

### Chạy lại và xử lý lỗi

Chọn run ID mới khi code/cấu hình thay đổi hoặc kiểm tra integrity báo lỗi.
Chỉ retry cùng ID khi đầu vào/cấu hình và các artifact đã hoàn thành còn nguyên.
Giữ thư mục run bị lỗi để chẩn đoán; không xóa marker nhằm bỏ qua quality gate.
Các run và ZIP chứa dữ liệu nằm trong output đã được Git ignore, cần giữ riêng
khi bàn giao. Backup Phase 9 vẫn là snapshot lịch sử; code Phase 10 mới nằm trong repo.

### Kết quả kiểm thử bản bổ sung

- Bộ kiểm thử toàn repo: 95 test được phát hiện, 88 đạt trên Windows; 7 test cần
  môi trường riêng được chạy tiếp như dưới đây. Lần chạy toàn repo dùng thư viện
  PyArrow trong backup đã kiểm checksum qua `PYTHONPATH`, với `python -B` để giữ
  nguyên gói backup. Khi chuẩn bị môi trường mới, cài `requirements/requirements_export.txt`
  cùng `requirements/requirements_phase10.txt` để có các thư viện kiểm thử tương ứng.
- 6/6 test Spark trên Parquet thật đạt: dữ liệu hợp lệ; KPI sai; segment trùng;
  khóa fact trùng; thuộc tính dimension bị sửa; schema bị đổi.
- 1/1 test trong Airflow Linux đạt: render `dag_run.conf.run_id` có shell
  substitution, chạy Bash và xác nhận giá trị bị từ chối, không thực thi payload.
- PySpark end-to-end: `review_fix_20261003_03`, exit code 0, đọc raw từ backup
  Phase 9. Tám bảng Gold đạt schema, aggregate và tái dựng chính xác từ Silver;
  KPI 668665 / 116779 / 551886, orphan 0, 35 segment.
- Log và kết quả chi tiết nằm trong `output/review_phase9_10_20261003/`;
  báo cáo PySpark tại `output/phase10/runs/review_fix_20261003_03/run_report.json`.
- Azure CI được bổ sung dependency Phase 10 và hai bộ test Phase 9/orchestration;
  kiểm tra cú pháp bao gồm cả `src` và `dags`. Chưa kích hoạt pipeline Azure từ
  phiên làm việc này. Test Spark và renderer Airflow được kiểm chứng cục bộ như trên.
- Airflow end-to-end mới: `airflow_test_8e01817f68574b0d81984bce18d48ff9`,
  DagRun `success`, sáu stage đều đạt, container exit code 0 theo Docker daemon.
  Container chạy với `--network none`,
  code và raw CSV từ backup được mount chỉ đọc; chỉ output được ghi.
- Quality kết thúc lúc `2026-10-03T13:30:39.877989Z`; publish bắt đầu lúc
  `2026-10-03T13:31:31.415992Z`. Đã kiểm lại checksum của toàn bộ marker/artifact
  sau khi chạy. Retry Bronze trên dữ liệu thật trả `already_passed` sau kiểm checksum.
- Báo cáo tổng hợp: `output/review_phase9_10_20261003/fix_verification.json`.

**Kết luận sau bổ sung:** giai đoạn 10 đạt phạm vi PySpark độc lập và Airflow DAG
đã nêu. Các lỗi quality gate, retry và run ID trong review đã được xử lý và kiểm thử.
