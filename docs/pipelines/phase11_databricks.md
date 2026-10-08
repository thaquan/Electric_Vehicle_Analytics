# Đóng gói, chạy và đối chiếu Phase 11

Các lệnh dưới đây chạy từ thư mục gốc repo. CLI dùng cấu hình Databricks mặc định trên máy; chỉ thêm `--profile` khi cần chọn workspace khác. Không cần cung cấp lại tài khoản nếu CLI đã đăng nhập. Môi trường sandbox có thể không đọc được cache đăng nhập; khi đó chạy CLI trong terminal có quyền truy cập cache hiện có.

## 1. Tạo project serverless sạch

```powershell
python scripts/phase11_package.py --output output/phase11_release_20261006/project
```

Thư mục đích phải chưa tồn tại; mỗi release dùng một tên mới. Có thể truyền `--raw <thu-muc-csv>` nếu nguồn không nằm tại `data/raw/kaggle`. Công cụ kiểm tra kích thước/SHA-256 nguồn theo manifest trước khi tạo package.

Package chỉ chứa 16 file cần chạy: bốn CSV nguồn, bốn JSON metadata, hai module dùng chung trong `scripts`, `src/__init__.py`, `src/run_contract.py` và bốn module serverless. Các file `databricks/runtime_src/{bronze,silver,gold,quality_checks}.py` được đặt vào `project/src/` để các import `src.*` trong notebook và giữa các module chọn đúng bản serverless. Không thay đổi `src/` Phase 10 trong repo. `package_manifest.json` lưu checksum từng file và mapping overlay.

Notebook kiểm tra package manifest và checksum trước khi xử lý. Không upload nguyên repo thay cho package. Không sửa file trong release đã đóng gói; tạo release mới khi thay đổi code hoặc metadata.

## 2. Upload và chạy trên Databricks

Catalog/schema/Volume `workspace.ev_phase11.ev_phase11` đã có từ lần triển khai đầu. Dùng thư mục release và notebook riêng để giữ lại run cũ:

```powershell
databricks fs cp output/phase11_release_20261006/project dbfs:/Volumes/workspace/ev_phase11/ev_phase11/releases/review_20261006/project --recursive
databricks workspace import /Shared/ev_phase11/phase11_runner_review_20261006 --file databricks/notebooks/phase11_runner.py --format SOURCE --language PYTHON
databricks jobs submit --json @databricks/jobs/phase11_review_submit.json --no-wait
```

`phase11_review_submit.json` là mẫu chạy một lần bằng serverless, có tham số `project_root` trỏ tới release trên. Khi tạo release mới, đổi cả đường dẫn Volume, notebook và tham số trong JSON. Không dùng `phase11_job.json` classic cluster cho workspace serverless này. `phase11_job_serverless.json` là định nghĩa job cũ; muốn chuyển job đó sang release mới phải cập nhật notebook path/base parameters tương ứng.

Lấy `run_id` trả về rồi đọc trạng thái:

```powershell
databricks jobs get-run <run_id> --output json
```

Chỉ chốt chạy thành công khi `state.result_state` là `SUCCESS`. `tasks[].run_id` dùng với `databricks jobs get-run-output <task_run_id>` để xem lỗi nếu cần. Run dữ liệu `phase11_<UTC timestamp>` và các artifact nằm dưới `<project_root>/output/phase11/runs/`. Kiểm tra `run_report.json` có `status: passed` và `published.json` có `status: published`.

## 3. Tải dữ liệu và đối chiếu

```powershell
python -m pip install -r requirements/requirements_phase11.txt
databricks fs cp dbfs:/Volumes/workspace/ev_phase11/ev_phase11/releases/review_20261006/project/output/phase11/runs/<pipeline_run_id> output/phase11_reconciliation/<pipeline_run_id> --recursive
python scripts/phase11_reconcile.py --reference-gold output/phase10/runs/review_fix_20261003_03/gold --candidate-gold output/phase11_reconciliation/<pipeline_run_id>/gold --output output/phase11_review/reconciliation_new_run.json
```

Script nhận thư mục Gold bất kỳ, hỗ trợ cả bảng Parquet dạng thư mục và file đơn. Bắt buộc có đúng tám bảng, so sánh tên/kiểu/thứ tự cột và số dòng, rồi chạy `EXCEPT ALL` hai chiều để giữ đúng số lần xuất hiện của bản ghi trùng. Chỉ bỏ ba giá trị lineage theo run khi so sánh dữ liệu; kiểu/tên các cột đó vẫn được kiểm tra. Nullability không được coi là hợp đồng vật lý của Parquet reader. Thiếu bảng, sai schema, lỗi đọc hoặc dữ liệu khác đều trả `status: failed` và exit code 1; đạt trả exit code 0.

Đối chiếu lại run cũ, không cần truy cập dịch vụ:

```powershell
python scripts/phase11_reconcile.py --reference-gold output/phase10/runs/review_fix_20261003_03/gold --candidate-gold output/phase11_reconciliation/phase11_20261005T041811Z/gold --output output/phase11_review/reconciliation_20261006.json
python -m unittest discover -s tests -p test_phase11.py
```

Dữ liệu lớn trong `output/` không được Git quản lý; cần giữ bản backup riêng. Code đóng gói, đối chiếu, notebook, tests và tài liệu nằm ngoài `output/` để có thể đưa vào cùng commit.
