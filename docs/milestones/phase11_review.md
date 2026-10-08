# Kiểm tra giai đoạn 11 — 2026-10-05

## Cập nhật khắc phục — 2026-10-06

**Hai phát hiện bên dưới đã được xử lý và xác minh trên Databricks.** Phần review ngày 2026-10-05 được giữ lại như lịch sử, không còn là trạng thái hiện tại.

- `scripts/phase11_package.py` đóng gói project sạch, tự đưa bốn module serverless vào `src/` và tạo manifest checksum. Notebook nhận `project_root`, kiểm tra manifest/checksum rồi import đúng package.
- `scripts/phase11_reconcile.py` và `requirements/requirements_phase11.txt` đưa công cụ đối chiếu ra khỏi `output/`; trả mã lỗi khi thiếu bảng, sai schema hoặc dữ liệu khác. Hướng dẫn: [Phase 11 Databricks](../pipelines/phase11_databricks.md).
- 4 tests mới và 12 tests điều phối Phase 10 đều đạt.
- Dùng cấu hình Databricks mặc định có sẵn trên máy, không đăng nhập lại. CLI ngoài sandbox đọc được run cũ `23656547233351` với trạng thái SUCCESS. Lỗi cached credentials trước đó là giới hạn truy cập của môi trường sandbox.
- Upload package vào release riêng và chạy notebook mới: job run `1020983582944630`, task run `744366088607539`, pipeline run `phase11_20261006T013808Z`, trạng thái **SUCCESS**, tổng thời gian `241376 ms`.
- Tải lại đầy đủ artifact: **116 file** khớp inventory/checksum của publish marker; checksum code trong run context khớp package đã tạo. Quality đạt, gồm dựng lại Gold từ Silver chính xác, 668665 respondents, 116779 Yes, 551886 No, orphan bằng 0, 35 nhóm segment.
- Công cụ mới đối chiếu **8/8 bảng Gold của run mới** với `review_fix_20261003_03`: schema, số dòng và `EXCEPT ALL` hai chiều đều đạt.

Bằng chứng: `metadata/phase11/clean_package_job_run.json`, `clean_package_manifest.json`, `clean_package_run_report.json`, `clean_package_verification.json`, `clean_package_reconciliation.json`. Notebook xác minh ở `/Shared/ev_phase11/phase11_runner_review_20261006`; project ở `/Volumes/workspace/ev_phase11/ev_phase11/releases/review_20261006/project`. Job cũ và dữ liệu nghiệm thu cũ được giữ lại.

Kết luận hiện tại: hai thiếu sót về tái triển khai và công cụ đối chiếu đã đóng. Giai đoạn 11 đạt trong phạm vi pipeline dữ liệu đã triển khai. Số liệu chi phí thực tế vẫn chưa được cập nhật trong lần khắc phục này.

## Kết luận

Kết quả dữ liệu của run `phase11_20261005T041811Z` đạt đối chiếu độc lập với Phase 10 `review_fix_20261003_03`. Tuy nhiên, chưa nên xác nhận hoàn tất toàn bộ khả năng triển khai lại từ repo: còn thiếu bước nối runtime serverless vào package thực thi. Trạng thái dịch vụ hiện tại chưa được xác minh do CLI không có cached credentials.

## Kết quả kiểm tra thực tế

- Đọc lại Parquet của cả 8 bảng Gold bằng DuckDB: tên/kiểu cột, số dòng và `EXCEPT ALL` hai chiều đều khớp. Chỉ loại giá trị của `processed_at_utc`, `silver_run_id`, `gold_run_id` khi so sánh dữ liệu; vẫn so sánh tên/kiểu của các cột này.
- Kiểm tra đủ tập 48 file Gold tải về, kích thước và SHA-256 với inventory trong `published.json`: đạt.
- Tính lại fact: 668665 dòng, 668665 ID phân biệt, 668665 record key phân biệt, 116779 Yes và 551886 No.
- Kiểm tra 5 dimension: khóa duy nhất, không null; orphan ở cả 5 quan hệ bằng 0.
- Cả 4 CSV nguồn hiện có khớp checksum trong báo cáo Bronze của run đã nghiệm thu.
- Chạy `python -m unittest discover -s tests -p test_phase10_orchestration.py`: 12 tests đạt. Đây là kiểm tra logic dùng chung của Phase 10, không thay thế chạy end-to-end trên serverless.
- So sánh 4 module runtime với `src`: chỉ đổi writer mode và bỏ cache/unpersist, không thấy thay đổi logic nghiệp vụ.

Bằng chứng mới nằm tại `output/phase11_review/reconciliation.json` và `output/phase11_review/integrity_quality.json`. Không ghi đè bằng chứng nghiệm thu cũ.

## Phát hiện cần xử lý

### 1. Thiếu bước đóng gói/triển khai runtime serverless

`databricks/notebooks/phase11_runner.py:8-15` thêm project root vào Python path và import `src.*`. Các module đã sửa cho serverless lại nằm tại `databricks/runtime_src/`. Không tìm thấy script hoặc hướng dẫn trong repo đưa các file này vào `project/src` trên Volume.

Nếu sao chép nguyên cây repo lên Volume rồi chạy notebook, Python sẽ chọn bản Phase 10 trong `src`, vẫn chứa `errorifexists` và `cache()`. Theo closeout, chính các thao tác này đã gây lỗi trên môi trường serverless đã dùng. Run cũ có thể đã được triển khai bằng cách chép đè thủ công; lần kiểm tra này không truy cập được Volume để xác nhận.

Cần lưu bước đóng gói runtime overlay có thể tái hiện, hoặc sửa cấu trúc package/import và đường dẫn phụ thuộc phù hợp, rồi xác minh trên một deployment sạch.

### 2. Công cụ tái đối chiếu chưa được lưu trong phần code được Git quản lý

Hai script đối chiếu hiện nằm trong `output/phase11_reconciliation/` và không xuất hiện trong `git ls-files`. Repo có JSON kết quả nhưng thiếu lệnh/script được quản lý phiên bản để người khác chạy lại cùng kiểm tra. Cần đưa công cụ đối chiếu vào `scripts/`, cho phép truyền đường dẫn và lưu hướng dẫn.

## Giới hạn xác minh

- Lệnh đọc `databricks jobs get-run 23656547233351 --profile ev-phase11 --output json` không thành công: `no cached credentials`. Chưa kiểm tra trực tiếp job, notebook, Volume hoặc quyền đang có trên dịch vụ; không chạy job mới.
- Bản tải về được kiểm tra có Gold, run report và publish marker; không chạy lại phép dựng Gold từ Silver của Phase 11 trong lần review này. Kết quả `silver_reconstruction: exact` là bằng chứng của run cũ.
- Checksum khớp publish marker chứng minh tính nhất quán của các artifact cục bộ, không tự xác thực nguồn tải từ dịch vụ.
- Billing probe đã lưu trả về danh sách rỗng, không chứng minh chi phí bằng 0. Chưa có số liệu chi phí thực tế mới.

Đánh giá: phần dữ liệu của giai đoạn 11 đạt; khả năng tái triển khai và xác minh dịch vụ hiện tại còn chưa chốt.
