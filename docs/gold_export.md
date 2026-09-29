# Giai đoạn 7 — Export Parquet và manifest

## Phạm vi

Phần 1–2 xuất snapshot Gold v2 `20260925T152721965637Z` đã được xác minh.
Không chạy lại pipeline, notebook biến đổi, refresh model hoặc thay đổi bảng nguồn.
Gói project và hướng dẫn khôi phục thuộc phần 3–4; xem [recovery runbook](recovery_runbook.md)
và `metadata/gold_recovery_package_status.json`. Khôi phục workspace riêng (phần 5) chưa thực hiện.
Kiểm thử dashboard còn lại giữ trạng thái **bỏ qua theo yêu cầu**, không đánh dấu đạt.

## Bản export

- Export ID: `20260927T130004568586Z`.
- Workspace nguồn: `5fe78794-25c3-41ee-b35e-bc56542d2cea`.
- Lakehouse nguồn: `32e99e91-38e9-4428-8fd2-6bcff6573088` (`LH_EV_Gold`).
- Local: `output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z/`.
- Đích OneLake: `Files/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z/`.
- Trạng thái truyền và bằng chứng hoàn tất: `metadata/gold_export_status.json`.
- Nguồn xác minh: `metadata/e2e_star_verified_run.json`; không dùng marker Gold v1 cũ.

| Bảng | Số dòng |
| --- | ---: |
| fact_ev_purchase_intent | 668665 |
| dim_demographics | 45 |
| dim_income | 4 |
| dim_mobility | 16 |
| dim_charging | 2 |
| dim_attitude_incentive | 30 |
| agg_ev_kpi | 1 |
| agg_ev_segments | 35 |

## Cách tạo

1. Tải Delta log version 0 của đúng tám bảng bằng Fabric OneLake connector.
2. Đọc danh sách `add` trong từng log. Chỉ lấy file dữ liệu thuộc version này;
   không quét toàn thư mục và không lấy các file thống kê trong `_delta_log/_stats`.
3. Kiểm tra protocol reader v1, không partition, không column mapping,
   không deletion vector hoặc remove action. Script dừng nếu các điều kiện này thay đổi.
4. Tải 49 file nguồn (14.311.522 byte), lưu ETag, dung lượng, request ID và checksum.
5. PyArrow đọc và ghi lại thành tám file Parquet Snappy, tổng 11.721.983 byte.
   Decimal giữ `decimal(18,4)`; timestamp được lưu microsecond UTC.
6. So sánh chính xác dữ liệu trước/sau ghi; kiểm tra schema, số dòng, lineage,
   PK/FK, khóa SHA-256 của dimensions, thứ tự band, KPI và 35 nhóm audit.
7. Chỉ tạo manifest hoàn chỉnh khi các kiểm tra đều đạt. Tải lại bản OneLake và
   đối chiếu SHA-256 với bản local trước khi ghi trạng thái truyền đã xác minh.

Đây là export dữ liệu snapshot có kiểm tra, không phải bản sao toàn bộ lịch sử Delta.
Khi khôi phục Direct Lake, nạp Parquet thành bảng Delta trong lakehouse mới.

## Nội dung manifest

`manifest.json` ghi Gold/Silver/pipeline run ID; định danh nguồn; Delta version;
schema từng cột; số dòng; SHA-256 từng file; checksum và ETag file nguồn;
primary keys; năm quan hệ many-to-one, chiều lọc dimension → fact;
kết quả kiểm tra dữ liệu; và checksum các file bằng chứng.

`manifest.sha256` kiểm tra tính toàn vẹn của manifest. Hash này không phải chữ ký số.
Bằng chứng nguồn và cấu hình đối chiếu được giữ trong `evidence/`.
Hai bảng aggregate chỉ phục vụ audit, không thêm vào semantic model.

## Kiểm tra tại máy khác

Giữ nguyên thư mục export và các script `export_gold_snapshot.py`, `star_schema.py`.
Từ thư mục project:

```powershell
python -m pip install -r requirements-export.txt
python scripts/export_gold_snapshot.py verify --output <thu-muc-export>
```

Verifier đọc manifest, kiểm tra checksum và schema, sau đó tính lại KPI và khóa
từ Parquet. Không cần truy cập Fabric để kiểm tra bản export đã tải.

Quy trình lấy nguồn và tạo lại export bằng connector:

```powershell
python scripts/export_gold_snapshot.py plan --staging output/gold_export_staging
# Connector tải đúng các file trong download_plan.json và lưu transfer receipts.
python scripts/export_gold_snapshot.py build --staging output/gold_export_staging --output <thu-muc-export-moi>
```

Lệnh `build` từ chối ghi đè thư mục export có sẵn. Runtime PyArrow cục bộ của lần
thực hiện này nằm trong `.tools/parquet-runtime`, ngoài dữ liệu export.

## Giới hạn nghiệm thu

KPI của Parquet: **668665 / 116779 / 551886**, tỷ lệ `0.17464500160768098`.
Không có khóa ngoại mồ côi; 35 nhóm audit khớp dữ liệu fact sau khi nối dimensions.
Kiểm tra này xác minh export và việc truyền file, chưa chứng minh đã khôi phục
semantic model hoặc report vào môi trường riêng.

Tham khảo: [Delta protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md),
[Apache Arrow Parquet](https://arrow.apache.org/docs/python/parquet.html).
