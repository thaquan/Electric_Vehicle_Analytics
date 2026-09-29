# EV Analytics — Gói bàn giao và khôi phục

Snapshot Gold v2: **20260925T152721965637Z**. KPI chuẩn: **668665 / 116779 / 551886**.

Gói gồm 8 Parquet và manifest, notebook/script, SQL, semantic model TMDL,
report PBIP cùng tài nguyên giao diện và hướng dẫn cấu hình.
Phần 3–4 đã chuẩn bị; chưa chạy khôi phục trong workspace riêng (phần 5).
Kiểm thử dashboard còn lại: **bỏ qua theo yêu cầu**, không đánh dấu đạt.

## Bắt đầu

1. Đối chiếu SHA-256 của file ZIP với file `.zip.sha256` đi kèm rồi giải nén.
2. Mở terminal tại thư mục `EV_Analytics_Recovery` và chạy:

   ```powershell
   python verify_package.py .
   ```

   Chạy kiểm tra này trước khi tạo thêm config, môi trường Python hoặc file kết quả
   trong thư mục gói. Verifier yêu cầu danh sách file đúng như lúc bàn giao.
   Có thể kiểm tra lại ZIP nguyên bản bất kỳ lúc nào:

   ```powershell
   python verify_package.py <duong-dan-file.zip>
   ```

3. Đọc [quy trình khôi phục chi tiết](project/docs/recovery_runbook.md).
4. Khi thực hiện phần 5: tạo workspace/lakehouse mới, điền `recovery.config.json`,
   nạp snapshot, tạo model, refresh, rồi publish report theo đúng thứ tự trong runbook.

## Cấu trúc

| Đường dẫn | Nội dung |
| --- | --- |
| `snapshot/` | 8 Parquet, manifest và bằng chứng export |
| `project/` | Mã nguồn và artifacts gốc, có thể đối chiếu với project hiện tại |
| `project/notebooks/NB_EV_Restore_Gold.ipynb` | Notebook chạy trong lakehouse mới |
| `project/scripts/prepare_recovery.py` | Tạo bản model/report với kết nối đích |
| `project/scripts/create_recovery_item.py` | Gửi lệnh tạo item khi thực hiện recovery |
| `recovery.example.json` | Cấu hình mẫu; các ID đích chưa được điền |
| `package_manifest.json` | Danh sách file và SHA-256 toàn gói |
| `release.json` | Phạm vi, snapshot và phiên bản công cụ |

PBIP/TMDL trong `project/` là bản nguồn để lưu trữ; chúng vẫn có tham chiếu môi trường
gốc. Dùng script chuẩn bị để tạo bản recovery trong `generated/`, rồi mở PBIP ở đó.
Không cần chạy lại pipeline hay các notebook Bronze/Silver/Gold để khôi phục snapshot.

## Kiểm tra đã thực hiện

- Kiểm tra inventory, checksum file trong thư mục và bên trong ZIP.
- Kiểm tra cấu hình, chống chọn nhầm đích và tạo bản TMDL/PBIP bằng ID thử offline.
- PBIR của bản đổi kết nối: 0 lỗi, 1 cảnh báo tải schema Microsoft `visualContainer/2.12.0`.
  Các visual giữ nguyên từng byte; giới hạn này không được tính là schema đã đạt.
- Chưa chạy Spark restore, API tạo model/report, refresh hoặc kiểm tra dashboard recovery.

Ảnh và bằng chứng DAX có sẵn trong `project/` thuộc môi trường nguồn.
Khi thực hiện phần 5, lưu bằng chứng mới riêng theo mẫu trong runbook.
