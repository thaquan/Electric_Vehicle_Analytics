# Giai đoạn 7 — Kết quả bàn giao

Ngày chốt: 2026-09-29. Giai đoạn 8 chưa bắt đầu.

## Kết quả

| Nội dung | Kết quả và bằng chứng |
| --- | --- |
| Export | 8 Parquet, Gold run `20260925T152721965637Z`; `metadata/gold_export_manifest.json` |
| Chuyển môi trường | 29/29 file tải lại khớp SHA-256; `metadata/recovery_upload_verification.json` |
| Khôi phục | 8/8 Delta khớp Parquet; `metadata/restore_data_20260929T012932575742Z.json` |
| Model | 6 partition Ready, 6 bảng, 5 quan hệ, 12 measures; `metadata/recovery_model_dax_verification.json` |
| KPI DAX | 668665 / 116779 / 551886; tỷ lệ 0.17464500160768098 |
| Report | Service API xác nhận report và model đích; `metadata/recovery_report_service_verification.json` |
| KPI trên report | Người dùng xác nhận đã kiểm tra xong; chưa cung cấp ảnh, không ghi nhận là kiểm tra hình ảnh tự động |

Workspace recovery: `d9e8b78a-5c35-4267-b558-1780029a951c`.
Lakehouse: `48ebc295-3cc7-4f2e-bdcd-c6e15260d9ac`.
Model: `a0835af9-0dde-42d8-ab16-8439d3a63f09`.

[Mở report recovery](https://app.powerbi.com/groups/d9e8b78a-5c35-4267-b558-1780029a951c/reports/61e38b4a-e9a1-4a0f-9411-112d86c18eb2).

Không chạy lại pipeline để thực hiện recovery. Workspace recovery không cần kết nối Git.
Các kiểm thử navigation/reset, chart cross-filter và Service rendering còn lại vẫn là
`skipped_by_user_request`, không chuyển thành đạt.

## Gói dữ liệu đã dùng trong lần thử

- ZIP: `output/releases/20260927T152509Z/EV_Analytics_Recovery_20260925T152721965637Z.zip`.
- ZIP SHA-256: `f0afddb74d18cc094419de05f8941ac1279a7aed3dda90f9c70fcabfbaa44070`.
- Manifest SHA-256: `0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f`.
- Snapshot trên OneLake nguồn: `Files/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z`.
- Bản sao trên lakehouse recovery: `Files/recovery/snapshot`.

Giữ nguyên ZIP đã dùng cho lần thử; các trạng thái `not_started` bên trong ZIP mô tả
thời điểm phát hành 2026-09-27. Trạng thái nghiệm thu hiện tại nằm trong repository.
Parquet/ZIP và dữ liệu nguồn không được đưa vào Git.

## Các vấn đề đã xử lý

1. API tạo model trả HTTP 202 với Location ở máy chủ vùng. Helper cũ chỉ chấp nhận
   `api.fabric.microsoft.com` nên dừng dù server đã nhận yêu cầu. Bản sửa dùng
   `x-ms-operation-id` để tạo URL polling ở public endpoint và lưu thông tin accepted
   trước khi kiểm tra URL. Không gửi lại POST khi kết quả tạo chưa rõ.
2. Định nghĩa database do Fabric Git xuất có thể không có tên hoặc ID. Helper chuẩn bị
   model hỗ trợ cả định dạng đó và định dạng export local có tên/ID.
3. Giao diện từng báo expression source bị đánh dấu xóa. Refresh trực tiếp qua MCP/XMLA
   thành công, sáu partition Ready và DAX đúng mà không sửa model. Chưa xác định nguyên
   nhân của lỗi phiên chỉnh sửa giao diện; không ghi nhận đã sửa lỗi sản phẩm Fabric.

## Bắt đầu từ repository trên máy mới

Repository không chứa snapshot dữ liệu. Muốn chạy toàn bộ kiểm thử recovery, tải gói
backup, kiểm tra checksum và giải nén snapshot về đường dẫn được mô tả trong runbook.
`tests/test_recovery_package.py` dùng snapshot đó hoặc `snapshot/` cạnh thư mục project
trong gói đã giải nén. Không coi lỗi thiếu snapshot trên một clone mới là lỗi khôi phục.

Xem [quy trình khôi phục](recovery_runbook.md) và [hướng dẫn export](gold_export.md).

## Gói bàn giao cập nhật

Gói `output/releases/20260929_phase7_closeout/EV_Analytics_Recovery_20260925T152721965637Z.zip`
chứa helper đã sửa và hồ sơ nghiệm thu. SHA-256:
`a595f3c0cfd3eff7c91c2ce7e2b61257a4fbd73e974879012912ef107d7b78b5`.
Đã kiểm tra inventory 230 file và 10 test recovery trong gói giải nén;
tổng bộ test project có 41 test đạt. Không chạy lại Spark recovery với gói sửa này.
Các trạng thái `not_started` trong release.json áp dụng cho một lần khôi phục mới;
kết quả lịch sử nằm ở recovery_verification.json.
