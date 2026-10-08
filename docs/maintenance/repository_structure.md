# Quy ước thư mục và tên file

Áp dụng từ 2026-10-08. File/thư mục do dự án đặt tên dùng `snake_case`: chữ thường, dấu `_`, không dùng dấu `-` hoặc khoảng trắng. Giữ phần mở rộng đúng loại file.

| Vị trí | Chức năng |
| --- | --- |
| `src/` | Mã xử lý dữ liệu dùng chung |
| `scripts/` | Công cụ build, triển khai, kiểm chứng, backup và recovery; giữ các module cạnh nhau để tương thích import hiện tại |
| `tests/`, `sql/` | Kiểm thử và truy vấn đối chiếu |
| `dags/`, `docker/phase10_airflow/` | Điều phối Airflow và container |
| `databricks/` | Job, notebook và runtime Databricks |
| `notebooks/` | Notebook phục vụ import và recovery Fabric |
| `ci/` | YAML cho Azure Pipelines |
| `requirements/` | Dependencies Python theo môi trường; `requirements.txt` ở gốc là entry point trỏ đến `requirements/base.txt` |
| `config/` | Cấu hình môi trường và mẫu recovery |
| `metadata/` | Contract, manifest và bằng chứng kiểm chứng; giữ nguyên hồ sơ lịch sử |
| `docs/architecture/` | Mô hình dữ liệu và thiết kế báo cáo |
| `docs/pipelines/` | Hướng dẫn pipeline và xuất dữ liệu |
| `docs/deployment/` | CI/CD và triển khai Test |
| `docs/recovery/` | Backup và khôi phục |
| `docs/operations/` | Vận hành và bàn giao |
| `docs/milestones/` | Kết quả, đánh giá và roadmap các giai đoạn |
| `docs/maintenance/` | Quy ước cấu trúc và hồ sơ dọn dẹp |
| `docs/screenshots/` | Ảnh báo cáo, tên dùng `_` |
| `references/` | Repository và notebook tham khảo, không đưa lên Git |
| `data/` | Dữ liệu nguồn và các lớp dữ liệu local |
| `output/` | Kết quả chạy, bằng chứng và gói backup đã tạo |
| `.tools/` | Thư viện và runtime bên thứ ba |

## Ngoại lệ để bảo toàn khả năng chạy và lịch sử

- Giữ tên tiêu chuẩn `README.md`, `Dockerfile`, các file cấu hình ẩn và tên do định dạng Fabric/Power BI yêu cầu.
- Các item `*.Lakehouse`, `*.Notebook`, `*.DataPipeline`, `*.Report`, `*.SemanticModel` và PBIP vẫn ở gốc, giữ topology Git/deployment và liên kết hiện có. `notebook-content.py`, `pipeline-content.json`, resource theme và tên bảng TMDL không đổi.
- Không sửa tên bên trong thư viện bên thứ ba, clone tham khảo, snapshot dữ liệu hoặc gói backup đã đóng dấu checksum. Đây không phải file rác. Quy ước mới áp dụng cho file dự án mới và các mục đã chuyển, không viết lại bằng chứng lịch sử.
- Không xóa dữ liệu, log nghiệm thu hoặc backup chỉ dựa vào tuổi file hay trạng thái Git-ignored. Chỉ xóa cache/file tạm xác định được; kiểm tra phạm vi đường dẫn trước khi xóa.

## Azure Pipelines

Đường dẫn cấu hình cho `EV-Analytics-CI` (ID 1) là `ci/azure_pipelines.yml`; cho `EV-Analytics-Test-CD` (ID 2) là `ci/azure_pipelines_test_cd.yml`. Cả hai dùng nhánh mặc định `refs/heads/main`. YAML path được lưu trong Azure DevOps ngoài repository: mỗi lần chuyển YAML cần cập nhật cả định nghĩa pipeline. Thay đổi vào `main` đi qua PR và build policy hiện có, sau đó đồng bộ cùng commit sang GitHub.

Release Test và rollback mới đặt dependencies tại `requirements/requirements_cd.txt`. Các bản release/backup cũ vẫn giữ nguyên cấu trúc và công cụ đi kèm.

Danh sách di chuyển local: `output/reorganization_20261008/moves.json`.
