# Sắp xếp thư mục ngày 2026-10-08

Đã chuyển/đổi tên 39 mục theo [quy ước cấu trúc](repository_structure.md): tài liệu chia 7 nhóm chức năng, YAML vào `ci/`, dependencies vào `requirements/`, nguồn tham khảo vào `references/`, chuẩn hóa tên ảnh và thư mục Docker bằng `_`.

Đã cập nhật README, liên kết tài liệu, lệnh cài dependencies và công cụ tạo release/rollback/backup. `requirements.txt` ở gốc tiếp tục dùng được và nạp `requirements/base.txt`.

## Dọn dẹp và bảo toàn dữ liệu

- Không phát hiện file tạm/rác bổ sung có đủ bằng chứng để xóa trong các thư mục mã nguồn, cấu hình và tài liệu được rà soát. Đợt dọn trước đã xử lý các mục đó; không xóa thêm dữ liệu chỉ để tăng số lượng file dọn.
- Đã bỏ hai thư mục cũ rỗng còn lại sau khi chuyển clone tham khảo. Toàn bộ 40 file Git metadata của clone nằm ở vị trí mới; `git status` sạch và HEAD vẫn là `10d297ee2f52115c4b4121fbda35475475c9d841`.
- Giữ nguyên dữ liệu gốc, các gói backup/recovery, nội dung `metadata/`, thư viện bên thứ ba và cấu trúc item Fabric/Power BI. Một số thư mục thư viện hạn chế quyền đọc trong sandbox; không sửa quyền hay xóa các thư mục đó.
- Bổ sung ignore cho cache pytest, file `.tmp`, `.temp`, file editor kết thúc bằng `~`, `Thumbs.db` và `.DS_Store`.

## Kiểm chứng

- 39/39 đích di chuyển tồn tại, đường dẫn cũ không còn.
- 83 liên kết local trong README và tài liệu hợp lệ; không có liên kết local hỏng.
- Cú pháp Python trong `scripts`, `src`, `tests`, `dags`, `databricks` hợp lệ.
- 4/4 checksum CSV nguồn khớp manifest; 173 file tracked thuộc metadata/model/định nghĩa nền tảng không đổi.
- Các include `-r` trong requirements trỏ đúng file.
- Kiểm thử: 96 test đạt, 7 test bỏ qua theo điều kiện môi trường (Spark/Airflow). Lần discover đầu có một lỗi import do Python không nạp được `pyarrow`; chạy riêng 5 test DAX với runtime `.tools/parquet-runtime` đã đạt. Các test còn lại đã đạt trong lần discover đầu.
- Kết quả trên thuộc lần kiểm tra local đầu tiên. Đợt cập nhật tiếp theo đưa cấu trúc mới qua PR/CI, đồng bộ Azure DevOps và GitHub, và chuyển cấu hình pipeline sang hai đường dẫn trong `ci/`. Kết quả build/deployment remote được lưu trực tiếp trong Azure Pipelines; không dùng kết quả local để thay cho nghiệm thu cloud.

Hồ sơ local (Git-ignored): [danh sách di chuyển](../../output/reorganization_20261008/moves.json), [kiểm chứng](../../output/reorganization_20261008/verification.json), [log kiểm thử](../../output/reorganization_20261008/tests.log), [kiểm thử DAX](../../output/reorganization_20261008/test_dax_query.log).
