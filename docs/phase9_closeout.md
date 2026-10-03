# Giai đoạn 9 — Kết quả backup độc lập

Ngày thực hiện: 2026-10-03. Trạng thái: **hoàn tất — nghiệm thu đạt**.

## Gói bàn giao đã nghiệm thu

- ZIP: `output/phase9/release-02/ev-analytics-backup.zip` (101214218 bytes).
- SHA-256 ZIP: `3fd0eac65a2c0c3c645dd8be5de9e23805dd9b1c14ec582f145ec5c5cc70520b`.
- SHA-256 manifest: `25cbb10637d209147b3aac7584605c9c714c50c688b6d2048e3fb2a5364e285d`.
- SHA-256 restore report: `7124c2187d1e2046e269678d142541b0009e1fbbc1a3d2e32de51275dcbe6962`.
- Inventory: 4223 file; 15 bảng dữ liệu được khôi phục.
- Silver run: `20260925T152449241452Z`.
- Gold run: `20260925T152721965637Z`.
- Lần khôi phục nghiệm thu chạy từ chính bản ZIP đã đóng gói, giải nén vào clean room mới.

Gói nằm trên ổ D, ngoài Fabric. Bản Gold nguồn được giữ nguyên. ZIP và dữ liệu không được đưa vào Git; clone repo không thay thế việc giữ gói backup này.

## Dữ liệu đã giữ

| Thành phần | Nội dung |
| --- | --- |
| Raw | 4 CSV nguyên bản, nguồn gốc và SHA-256 |
| Bronze | 4 CSV khớp nguồn và 4 bản Parquet với các cột dạng chuỗi |
| Silver | Train 668665 dòng; test 286571 dòng; original reference 10000 dòng |
| Gold | 1 fact, 5 dimensions, 2 bảng tổng hợp kiểm toán |
| Code | Scripts, notebooks, SQL, tests, dependency files và YAML CI/CD |
| Fabric | Định nghĩa notebook, pipeline và lakehouse hiện có trong repo |
| Power BI | TMDL, PBIP, PBIR, measures, relationships, partitions và report binding |
| Cấu hình | Mapping môi trường và tên biến cần cấp lại; khôi phục không cần credential |

Silver được tải bổ sung trực tiếp từ run `20260925T152449241452Z`, cùng nguồn gốc với Gold `20260925T152721965637Z` và pipeline `78f9cdfe-1e19-4624-bede-042310ec9bb9`. Marker Silver cũ trong repo trỏ tới run `20260924T031507399976Z`; marker lịch sử được giữ nguyên và không dùng để chọn dữ liệu cho backup mới. Có 14 file dữ liệu Silver nguồn và ba Delta v0 log.

Đây là backup snapshot Parquet, không phải backup toàn bộ lịch sử Delta.

## Thử khôi phục độc lập

1. Đóng ZIP từ gói đã kiểm checksum.
2. Giải nén vào `output/phase9/release-02/clean-room/ev-analytics-backup` mới.
3. Kiểm tra inventory của bản giải nén, rồi chạy script nằm bên trong chính bản backup.
4. Chạy Python với `-I -S -B`, chỉ dùng thư viện trong backup và thư viện chuẩn. Tiến trình không nhận credential; `USERPROFILE` trỏ tới runtime-home mới.
5. Python audit hook chặn socket, tiến trình con và đọc file ngoài phạm vi cho phép. Self-test xác nhận mạng và đường dẫn ngoài backup bị chặn.
6. Kiểm chứng raw/Bronze/Silver, tái dựng Silver train từ Gold, kiểm tra Gold; dựng lại 15 bảng Parquet và SQLite; tính lại KPI, orphan và 35 nhóm segment bằng SQL.

Đường dẫn đầu vào được ghi trong `input_paths.json`. Cơ chế cách ly nằm ở tiến trình Python cho script đã kiểm tra; không phải firewall của hệ điều hành. Parquet giữ schema chính xác; SQLite dùng cho đối chiếu SQL.

## Kết quả nghiệm thu

| Chỉ tiêu | Kỳ vọng | Kết quả |
| --- | ---: | ---: |
| Respondents | 668665 | 668665 |
| Yes | 116779 | 116779 |
| No | 551886 | 551886 |
| Orphan keys | 0 | 0 |
| Nhóm segment | 35 | 35 |
| Bảng khôi phục | 15 | 15 |

Trạng thái restore: `passed`.

- `independent_restore`: `true`.
- `fabric_access_during_restore`: `false`.
- `fabric_credentials_used`: `false`.
- `unexpected_blocked_operations`: `0`.
- Self-test chặn 1 thao tác mạng và 1 lần đọc file ngoài phạm vi như dự kiến.
- Trong bước khởi tạo thư viện có thêm 1 kết nối mạng bị audit hook chặn; đây là thao tác setup đã được ghi riêng và không phát sinh trong phần restore dữ liệu. Sau bước setup, không có thao tác bị chặn ngoài dự kiến.

Chín kiểm thử Phase 9 đã đạt, gồm inventory hợp lệ, dữ liệu bị sửa/thiếu/thừa, manifest bị sửa, đường dẫn vượt phạm vi, mục inventory trùng, chặn mạng/file ngoài/tiến trình con và kiểm thử hồi quy cho đối chiếu segment theo GROUP BY.

## Ghi chú về release-01

`release-01` được giữ làm bằng chứng chẩn đoán và **không** được tính là bản nghiệm thu. Dữ liệu, Gold validation, KPI, orphan và 35 nhóm đều đã đúng, nhưng tiến trình bị đánh failed ở kiểm tra trạng thái audit hook sau khi thư viện khởi tạo có một lần thử kết nối mạng bị chặn. Đồng thời cách đối chiếu cũ chạy một truy vấn join cho từng giá trị segment nên chậm.

Ở `release-02`, kiểm tra audit được tách thành self-test/setup/restore để vẫn chặn truy cập ngoài phạm vi nhưng không coi một thao tác setup đã bị chặn thành lỗi dữ liệu. Đối chiếu segment được đổi sang một truy vấn GROUP BY cho mỗi thuộc tính, có test hồi quy phát hiện sai lệch.

## Giới hạn và bước tiếp theo

- Runtime đi kèm dành cho Windows x64, CPython 3.13; interpreter được cài riêng.
- Backup hiện là snapshot Parquet, không giữ toàn bộ Delta history.
- Định nghĩa model/report được giữ lại; chưa chứng minh render hoặc DAX ngoài Fabric.
- Định nghĩa ứng dụng lấy từ repo hiện tại, không phải lần đồng bộ mới mọi chỉnh sửa trên Service.
- Chạy lại đầy đủ Bronze → Silver → Gold bằng PySpark/Airflow thuộc **giai đoạn 10**.

Xem [hướng dẫn khôi phục](phase9_backup.md) và [lộ trình](roadmap_phase9_12.md).
