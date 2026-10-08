# Tổng kết và phạm vi nghiệm thu

Cập nhật tài liệu: 2026-10-08. Phần chức năng chính đã hoàn thành trong phạm vi phân tích **ý định mua EV** trên dữ liệu tổng hợp. Các kết quả dưới đây là bằng chứng của những lần chạy đã ghi nhận, không phải xác nhận rằng dịch vụ cloud vừa được kiểm tra lại. Chưa ký bàn giao vận hành cuối cùng.

## Kết quả kỹ thuật

| Thành phần | Kết quả đã kiểm chứng | Bằng chứng |
| --- | --- | --- |
| Dữ liệu và mô hình | 668665 respondents, 116779 Yes, 551886 No; orphan 0; 35 nhóm segment; tám bảng Gold | [Số liệu chuẩn](../metadata/star_expected_metrics.json), [DAX](../metadata/semantic_model_live_dax.json) |
| Power BI | Ba trang, 12 measures; ảnh Desktop và bộ lọc Urban đã kiểm tra | [Phạm vi kiểm tra report](architecture/powerbi_report.md) |
| Khôi phục Fabric | Tám bảng Delta khớp snapshot Parquet; model/report phục hồi được | [Kết quả recovery](../metadata/recovery_verification.json), [runbook](recovery/recovery_runbook.md) |
| CI/CD Test | README ghi nhận CI #30 và CD #31 thành công ngày 2026-10-07; hồ sơ bootstrap được giữ riêng theo ngày | [CI #30](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=30), [CD #31](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=31), [hướng dẫn](deployment/test_cd.md) |
| PySpark/Airflow | Sáu stage đạt, chỉ publish sau quality/integrity; tám bảng Gold khớp bản chuẩn | [Airflow verification](../metadata/phase12/airflow_verification.json), [reconciliation](../metadata/phase12/airflow_reconciliation.json), [runbook](pipelines/standalone_pipeline.md) |
| Databricks | Package sạch chạy thành công; 116 artifact khớp checksum; tám bảng Gold khớp standalone | [Verification](../metadata/phase11/clean_package_verification.json), [reconciliation](../metadata/phase11/clean_package_reconciliation.json), [hướng dẫn](pipelines/phase11_databricks.md) |
| Kiểm thử | Hồ sơ ngày 2026-10-06 ghi nhận 103 test đạt qua các runtime phù hợp; đây không phải số test trong riêng Azure CI | [Phạm vi các suite](../metadata/phase12/tests.json) |
| Backup/handoff | Baseline 15 bảng khôi phục từ ZIP thử r2; bản cuối kiểm toàn bộ inventory và đối chiếu payload với bản đã khôi phục | [Restore](../metadata/phase12/restore_report.json), [archive verification](../metadata/phase12/final_archive_verification.json), [acceptance](../metadata/phase12/acceptance.json) |

Power BI vẫn dùng nguồn Fabric. Databricks là đường chạy thay thế cho pipeline dữ liệu. Run package sạch `phase11_20261006T013808Z` hoàn thành trong 241376 ms; đây là một phép đo, chưa phải SLA. Các lỗi đóng gói runtime serverless và thiếu công cụ đối chiếu đã được xử lý bằng `scripts/phase11_package.py` và `scripts/phase11_reconcile.py`.

## Backup được giữ riêng

- Baseline: `output/phase9/release-02/ev-analytics-backup.zip`; SHA-256 `3fd0eac65a2c0c3c645dd8be5de9e23805dd9b1c14ec582f145ec5c5cc70520b`.
- Handoff: `output/phase12/final/ev-analytics-handoff.zip`; checksum và inventory ở [package report](../metadata/phase12/package_report.json).
- Bản cuối được giải nén và kiểm inventory mới; không mô tả việc so payload với r2 thành một lần khôi phục baseline mới.
- ZIP là snapshot lịch sử có manifest riêng, không tự cập nhật theo HEAD. Giữ nguyên archive; clone Git không thay thế backup dữ liệu. Snapshot Parquet không chứa toàn bộ lịch sử Delta.

## Các giới hạn còn mở

1. Navigation/reset, chart cross-filter, Service rendering và SQL endpoint riêng đã hoãn theo yêu cầu trước đó; chưa tính là đạt.
2. Chưa xác minh bản backup ngoài máy/ổ D, nơi lưu và thời hạn giữ.
3. Chưa xác nhận người tiếp nhận, quyền của họ, diễn tập do họ thực hiện hoặc phương án nghiệm thu thay thế.
4. Chưa cấu hình kênh thông báo tự động hoặc chốt giới hạn thời gian/chi phí. [Billing](../metadata/phase12/runtime_billing.json) có usage DBU, chưa xác minh số tiền thực trả.
5. Nguồn CSV có provenance/checksum nhưng chưa đối chiếu trực tiếp với bản tải từ Kaggle. Dữ liệu synthetic không chứng minh nhu cầu thực tế hoặc quan hệ nhân quả.

Chi tiết vận hành ở [runbook bàn giao](operations/phase12_operations.md) và [checklist bàn giao](operations/phase12_handoff.md). Các mục cần xác nhận vẫn để mở.

## Chính sách hồ sơ

Repo giữ code, tests, cấu hình, contract, manifest, hướng dẫn sử dụng và bằng chứng nghiệm thu tiêu biểu. Roadmap, review theo giai đoạn, nhật ký dọn dẹp, phản hồi API trung gian và công cụ UI dùng trong phiên làm việc được lưu local tại `output/repository_cleanup_20261008/archive/`, kèm `manifest.json` ở thư mục cha để tra đường dẫn gốc và SHA-256. Các file đã chuyển còn có trong lịch sử Git trước đợt tinh gọn; không cần viết lại lịch sử.

Các JSON nghiệm thu còn giữ là hồ sơ bất biến: đường dẫn trong JSON có thể chỉ đến artifact local hoặc archive lịch sử. Chúng không phải hướng dẫn chạy hiện tại. Xem [chỉ mục bằng chứng](../metadata/README.md) trước khi sử dụng.
