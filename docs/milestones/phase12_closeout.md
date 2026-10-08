# Phase 12 — Hồ sơ nghiệm thu kỹ thuật và bàn giao

Ngày thực hiện: 2026-10-06. **Các kiểm chứng kỹ thuật đã đạt; chưa ký nghiệm thu bàn giao cuối cùng.** Người tiếp nhận và nơi lưu bản sao ngoài máy hiện tại chưa được chủ dự án xác nhận. Các bước do agent thực hiện không được ghi thành thao tác của người tiếp nhận.

## Phạm vi đã xử lý

Giữ nguyên phạm vi hệ thống đã xây dựng: Fabric/Power BI hiện có, PySpark/Airflow và Databricks serverless. Không chuyển nguồn Power BI sang Databricks. Tài liệu thực thi: [phase12_operations.md](../operations/phase12_operations.md); checklist: [phase12_handoff.md](../operations/phase12_handoff.md).

Repo base commit là `a618597e515f55fe930df6c6ec2e8dd1a0483c9f`. Bản bàn giao chứa thêm thay đổi Phase 12 trong working tree; manifest của ZIP định danh chính xác từng file. Code và dữ liệu nguồn được giữ tách biệt; ZIP không được Git quản lý.

## Kiểm thử và dịch vụ

- 103 kiểm thử đạt: 92 test thông thường, 6 test Spark trên Parquet thật, 1 test renderer Airflow trong Linux và 4 test inventory/ZIP Phase 12. Bảy test bị skip ở lần discovery Windows đã được chạy bằng runtime phù hợp. Chi tiết: `metadata/phase12/tests.json`.
- Các trường hợp lỗi đã kiểm tra gồm dữ liệu/manifest không khớp, file thừa, ZIP path traversal, KPI sai, khóa trùng, schema sai, quality failure không publish và run ID Airflow không thực thi shell substitution.
- Fabric **Test**: report/model binding, trạng thái refresh gần nhất và live DAX KPI đều đạt. Dùng API JSON; API Arrow trả 401 trong lần thử đầu. Không kích hoạt refresh mới, không kiểm tra hình ảnh report và không mở lại các kiểm tra Service UI/SQL endpoint đã hoãn. Bằng chứng: `metadata/phase12/fabric_test_health_json.json`.
- Databricks: danh tính hiện có sở hữu job, schema và Volume; không sửa quyền. Không suy diễn đây là kiểm chứng quyền tối thiểu hoặc quyền của người tiếp nhận khác. Bằng chứng: `metadata/phase12/databricks_access.json`.
- CI được bổ sung dependency DuckDB và test Phase 11–12. Chưa push hoặc chạy Azure CI cho các sửa đổi Phase 12 này.

## Billing và hiệu năng

Probe Databricks ngày 2026-10-06 đạt SUCCESS, Spark 4.2.0. Billing đã có usage trong cửa sổ bảy ngày: job `149867914773886` ghi nhận `2.158577282142857143 DBU`, job xác minh package sạch `183474134559346` ghi nhận `1.058020875 DBU`. Đây là tổng net usage theo job/SKU trong cửa sổ truy vấn, không gán toàn bộ usage job cũ cho một run riêng lẻ. Chưa xác minh đơn giá/hợp đồng nên không kết luận số tiền thực trả. Bằng chứng: `metadata/phase12/runtime_billing.json` và `probe_job.json`.

Run Databricks package sạch trước đó đạt trong 241376 ms với 668665 respondents. Đây là phép đo cụ thể, chưa phải SLA hay kết quả tải đồng thời. Không tự đặt ngân sách hoặc mức thời gian chấp nhận thay chủ dự án.

## Khôi phục và chạy từ bản bàn giao

Kết quả cuối của diễn tập được ghi trong `metadata/phase12/acceptance.json` và các báo cáo restore/reconciliation đi kèm. Chỉ sử dụng bản archive có checksum trong `metadata/phase12/package_report.json`; không dùng thư mục thử thất bại làm bản bàn giao.

- Khôi phục offline từ ZIP thử r2 đạt: 15 bảng baseline; 668665 respondents, 116779 Yes, 551886 No, orphan 0, 35 nhóm segment. Snapshot Databricks có 116 artifact đúng checksum, tám bảng Gold khớp Phase 10. Không truyền credential cloud cho tiến trình khôi phục. Bằng chứng: `restore_report.json` và `restored_phase11_reconciliation.json`.
- Airflow dùng code và CSV từ bản ZIP đã giải nén, mount chỉ đọc và `--network none`. Run dữ liệu `airflow_test_116a0996dd984181bd9f7b9ab4ebbfe3` đạt cả sáu stage; Gold khớp tám bảng chuẩn. Lần chạy đầu bị ngắt sau quality; đã tiếp tục bằng DAG thật, kiểm lại integrity rồi bỏ qua các stage đã đạt, hoàn tất publish lúc `2026-10-06T12:49:21.366506+00:00`. Container tiếp tục kết thúc với exit code 0. Không dùng khoảng thời gian có gián đoạn để kết luận SLA. Bằng chứng: `airflow_verification.json`, `airflow_reconciliation.json` và log trong `output/phase12/`.
- Bản cuối trong `output/phase12/final/` bổ sung hồ sơ/runbook và cấu hình CI. Archive được giải nén vào clean room mới, kiểm toàn bộ inventory. Payload khôi phục, native runtime và mã kiểm chứng được so checksum với bản r2 đã khôi phục thành công; kết quả trong `final_archive_verification.json`. Không mô tả kiểm tra tương đương payload này thành một lần dựng lại baseline mới.

`package_report.json` và `final_archive_verification.json` được tạo sau khi đóng ZIP và giao kèm bên ngoài ZIP để tránh vòng lặp checksum. Trong ZIP có manifest và các bằng chứng kỹ thuật đã tạo trước khi đóng gói.

Các sự cố chuẩn bị được giữ trong log: đường dẫn Windows quá dài ở lần đóng gói đầu; thiếu mountpoint khi project được mount chỉ đọc; hostname không phân giải khi Docker `--network none`; run bị ngắt trước publish. Runbook đã có hướng dẫn dùng đường dẫn ngắn, tạo mountpoint rỗng, ánh xạ hostname về loopback và tiếp tục run qua integrity gate. Các lần thử lỗi không được tính là run nghiệm thu.

## Phần cần người tiếp nhận/chủ dự án xác nhận

1. Danh tính người tiếp nhận/vận hành chính và người dự phòng; phạm vi nền tảng sẽ tiếp tục vận hành.
2. Vị trí bản sao ZIP ngoài ổ D/máy hiện tại, người quản lý và thời hạn lưu; kiểm checksum bản sao sau khi chuyển.
3. Người tiếp nhận chạy và khôi phục được theo tài liệu hoặc ghi rõ hình thức nghiệm thu khác được chủ dự án chấp thuận.
4. Kênh nhận thông báo lỗi, mức thời gian/chi phí chấp nhận và các ngoại lệ còn giữ lại.

Chưa cấu hình gửi thông báo tự động, chưa cấp quyền cho danh tính mới và chưa đánh dấu người tiếp nhận đã thao tác. Snapshot backup không chứa toàn bộ lịch sử Delta. Python/Java/Spark/Airflow và việc provision dịch vụ cloud có yêu cầu môi trường riêng được ghi trong runbook.
