# Lộ trình EV Analytics từ giai đoạn 9

Cập nhật ngày 2026-10-03 theo lộ trình người dùng cung cấp.

## Điểm xuất phát

- Giai đoạn 7 đã có backup Gold và khôi phục trong Fabric. Kết quả này chưa chứng minh hệ thống chạy được khi không còn Fabric; xem [biên bản giai đoạn 7](phase7_closeout.md).
- Giai đoạn 8 giải quyết CI/CD và vận hành trên Fabric. Lộ trình này tiếp nhận thông tin người dùng cung cấp rằng các bước còn lại đã hoàn tất. Bằng chứng CI/CD hiện lưu trong repo được mô tả tại [triển khai Test tự động](test_cd.md); tài liệu này không phải một lần kiểm tra lại dịch vụ.
- Giai đoạn 9: **đã nghiệm thu khôi phục độc lập**. ZIP release-02 và lần kiểm tra lại ngày 2026-10-03 đều đạt; xem [biên bản giai đoạn 9](phase9_closeout.md).
- Giai đoạn 10: **đã nghiệm thu PySpark và Airflow DAG**, gồm các bổ sung quality gate, kiểm checksum khi retry và run ID an toàn; xem [biên bản giai đoạn 10](phase10_closeout.md). Bước tiếp theo là giai đoạn 11.

| Giai đoạn | Mục tiêu | Kết quả cần đạt |
| --- | --- | --- |
| 9. Backup độc lập khỏi Fabric | Đưa đủ dữ liệu, code và cấu hình ra ngoài Fabric | Khôi phục được từ bản backup mà không đọc lại OneLake |
| 10. Chạy bằng PySpark và Airflow | Tách xử lý dữ liệu khỏi notebook và pipeline Fabric | Chạy được Bronze → Silver → Gold trên môi trường độc lập |
| 11. Tích hợp Snowflake hoặc Databricks | Đưa cùng bài toán lên nền tảng khác | Có kết quả đối chiếu với bản chuẩn |
| 12. Nghiệm thu và bàn giao | Chốt tính đúng, quyền, hiệu năng và vận hành | Có hướng dẫn chạy, khôi phục và tiếp tục phát triển |

## Giai đoạn 9 — Backup độc lập khỏi Fabric

### 9.1. Kiểm kê những gì cần giữ

| Thành phần | Cần lưu |
| --- | --- |
| Dữ liệu nguồn | Các file đầu vào, nguồn gốc và checksum; giữ riêng nguồn tham chiếu với train/test |
| Bronze, Silver, Gold | Dữ liệu, schema, tên bảng và run ID; quan hệ giữa các run của cùng snapshot |
| Notebook | Mã xử lý, module phụ thuộc, thư viện và phiên bản runtime cần thiết |
| Pipeline | Định nghĩa, thứ tự chạy, tham số và điều kiện phụ thuộc |
| Semantic model | TMDL, measures, relationships và partition |
| Report | Định nghĩa report, trang, visual và liên kết model |
| Cấu hình | Mapping workspace/lakehouse/item và tên biến môi trường cần cung cấp lại |
| Bằng chứng | Số dòng, schema, kiểm tra chất lượng, checksum, run ID và KPI chuẩn |

Không đưa token, mật khẩu hoặc client secret vào gói backup. Với thông tin xác thực, chỉ ghi tên cấu hình cần cung cấp lại; kiểm tra cả notebook, file cấu hình và nhật ký trước khi đóng gói.

Các tài nguyên sẵn có để bắt đầu kiểm kê:

- Nguồn và schema: `metadata/source_manifest.json`, `metadata/schema_contract.yaml`, [Bronze/Silver](bronze_silver.md).
- Gold: [hướng dẫn export](gold_export.md), `metadata/gold_export_manifest.json` và `metadata/e2e_star_verified_run.json`.
- Code và định nghĩa: `scripts/`, `notebooks/`, các thư mục `.Notebook`, `PL_EV_E2E.DataPipeline/`, `sql/`, các file `requirements*.txt`.
- Power BI: `models/`, `SM_EV_Analytics.SemanticModel/`, `RPT_EV_Analytics.Report/` và `RPT_EV_Analytics.pbip`.
- Cấu hình và bằng chứng: `config/`, `metadata/`, [runbook khôi phục](recovery_runbook.md), [vận hành](operations_runbook.md).

Sự tồn tại của file trong repo chưa xác nhận gói backup đầy đủ. Danh mục phải ghi đường dẫn trong backup, nguồn, phiên bản/run ID, trạng thái đã sao chép và kết quả kiểm chứng của từng thành phần. Dữ liệu và ZIP đang bị loại khỏi Git, nên clone repo không đủ để khôi phục.

### 9.2. Xuất dữ liệu ra nơi nằm ngoài Fabric

Lưu backup trên ổ đĩa hoặc kho lưu trữ độc lập do người dùng kiểm soát. Một bản chỉ nằm trong OneLake chưa đáp ứng yêu cầu này.

- Dùng Parquet cho snapshot dữ liệu có thể đọc bằng nhiều công cụ; giữ nguyên file nguồn trong `data/raw/`.
- Nếu cần lịch sử Delta, sao lưu đầy đủ `_delta_log` và các file dữ liệu cần cho những phiên bản được giữ. Bản xuất Parquet chỉ giữ dữ liệu tại thời điểm xuất.
- Giữ nguyên bản backup Gold đã có. Bổ sung nguồn, Bronze, Silver, code và cấu hình còn thiếu để có đủ đầu vào chạy lại toàn bộ Bronze → Silver → Gold ở giai đoạn 10.
- Liên kết các tầng bằng run ID; không trộn dữ liệu thuộc các lần chạy khác nhau mà không có giải thích và đối chiếu.

Cấu trúc đích:

```text
ev-analytics-backup/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── code/
├── fabric-definitions/
├── powerbi/
├── config/
├── manifests/
└── verification/
```

Lưu phiên bản thư viện và hướng dẫn chuẩn bị môi trường trong `code/`. Nếu môi trường khôi phục không có Internet, chuẩn bị thêm các gói cài đặt cần thiết. Code khôi phục phải đọc đường dẫn backup cục bộ hoặc kho độc lập, không yêu cầu đăng nhập Fabric.

### 9.3. Kiểm chứng bản backup

Mỗi bảng cần có:

- Tên bảng, tầng dữ liệu, run ID và nguồn snapshot tương ứng.
- Số dòng, schema, kiểu dữ liệu, nullability và thông tin partition nếu có.
- Danh sách file, kích thước và checksum SHA-256.
- Kiểm tra khóa trùng, khóa thiếu/null và orphan theo hợp đồng dữ liệu. Nếu một kiểm tra không áp dụng, ghi rõ lý do.
- Kết quả kỳ vọng, kết quả thực tế và trạng thái đạt/không đạt.

Manifest toàn gói phải bao phủ cả dữ liệu, code, định nghĩa và cấu hình. Giữ checksum manifest để phát hiện thay đổi; checksum không thay thế chữ ký xác thực nguồn.

Bộ chuẩn cho Gold snapshot `20260925T152721965637Z`:

| Chỉ tiêu | Giá trị |
| --- | ---: |
| Respondents | 668665 |
| Yes | 116779 |
| No | 551886 |
| Orphan keys | 0 |

Đối chiếu thêm tám bảng Gold, năm quan hệ fact–dimension và 35 nhóm segment đã có trong bằng chứng export. Không thay giá trị chuẩn để làm cho một lần khôi phục sai vượt qua kiểm tra.

### 9.4. Thử khôi phục độc lập

Tạo thư mục hoặc môi trường sạch, chỉ cấp bản backup và runtime cần thiết:

1. Kiểm tra manifest và checksum toàn gói trước khi đọc dữ liệu.
2. Đọc lại dữ liệu nguồn và các snapshot Bronze, Silver, Gold từ backup.
3. Kiểm tra schema, số dòng và dựng lại các bảng cần thiết bằng công cụ độc lập.
4. Kiểm tra khóa, orphan; tính lại KPI và các nhóm segment từ dữ liệu đã khôi phục.
5. Ghi báo cáo đối chiếu trong `verification/`, gồm backup ID, run ID, phiên bản runtime, lệnh chạy, kết quả kỳ vọng/thực tế, lỗi và kết luận.

Chạy thử mà không có thông tin đăng nhập Fabric; chặn truy cập Fabric/OneLake khi môi trường hỗ trợ và lưu bằng chứng cấu hình đó. Không sử dụng cache dữ liệu từ lần chạy cũ hoặc đọc bổ sung từ thư mục dự án gốc. Lưu nhật ký đường dẫn đầu vào để kiểm tra mọi dữ liệu đều đến từ backup.

Giai đoạn 9 kiểm chứng khả năng khôi phục dữ liệu và giữ đủ tài sản để tiếp tục phát triển. Việc chuyển toàn bộ xử lý sang PySpark/Airflow thuộc giai đoạn 10. TMDL và định nghĩa report cần được lưu đầy đủ; việc lưu các định nghĩa đó chưa chứng minh report hoặc Direct Lake model chạy trên nền tảng khác.

### Điều kiện nghiệm thu giai đoạn 9

- [x] Kiểm kê đủ các thành phần ở mục 9.1 và xử lý các phần thiếu.
- [x] Backup nằm ngoài Fabric; chứa dữ liệu nguồn và cả ba tầng Bronze, Silver, Gold.
- [x] Manifest, checksum, schema, số dòng, khóa và run ID được kiểm chứng.
- [x] Không có token, mật khẩu hoặc client secret trong gói.
- [x] Khôi phục trong môi trường sạch thành công mà không đọc lại OneLake/Fabric.
- [x] KPI, orphan và các đối chiếu chuẩn đều đạt; lưu báo cáo và lệnh tái hiện.

**Giai đoạn 9 chỉ hoàn thành khi lần khôi phục độc lập đạt. Có file ZIP hoặc tải được dữ liệu xuống chưa đủ.**

## Giai đoạn 10 — Chạy bằng PySpark và Airflow

Tách logic xử lý khỏi API/notebook Fabric, đưa đường dẫn và tham số môi trường ra cấu hình. Tạo các tác vụ PySpark cho Bronze → Silver → Gold và DAG Airflow thể hiện thứ tự chạy, điều kiện phụ thuộc, xử lý lỗi và run ID.

Nghiệm thu bằng một lần chạy toàn bộ từ nguồn trong backup trên môi trường độc lập; so sánh schema, số dòng, chất lượng, KPI và segment với bản chuẩn. Lưu code, phiên bản môi trường, DAG và nhật ký chạy để tái hiện.

## Giai đoạn 11 — Tích hợp Snowflake hoặc Databricks

**Trạng thái: Hoàn tất bằng Databricks serverless.**

Ngày 2026-10-06 đã bổ sung đóng gói runtime và công cụ đối chiếu có thể tái hiện; chạy package sạch trên Databricks với run `phase11_20261006T013808Z` đạt SUCCESS, kiểm tra checksum 116 artifact và đối chiếu cả 8 bảng Gold đều đạt. Xem [hướng dẫn tái triển khai](phase11_databricks.md) và [kết quả khắc phục review](phase11_review.md).

Đã triển khai cùng pipeline/hợp đồng dữ liệu của giai đoạn 10 trên Databricks, tạo đủ Bronze → Silver → Gold → Quality → Publish. Run nghiệm thu `phase11_20261005T041811Z` đạt quality checks và đối chiếu trực tiếp cả 8 bảng Gold với Phase 10 `review_fix_20261003_03` đều khớp hoàn toàn về schema và dữ liệu nghiệp vụ; chỉ các giá trị lineage theo từng lần chạy (`processed_at_utc`, `silver_run_id`, `gold_run_id`) được phép khác.

Workspace chỉ hỗ trợ serverless nên runtime thực tế là Spark 4.2.0/Python 3.12.3 thay vì classic DBR pin trước đó. Các điều chỉnh tương thích Spark Connect/serverless và kết quả runtime, quyền, billing probe được ghi tại `docs/phase11_closeout.md`. Billing system table chưa có record tại thời điểm probe nên không suy diễn chi phí bằng 0.

## Giai đoạn 12 — Nghiệm thu và bàn giao

Chốt tính đúng, quyền, hiệu năng và vận hành trên phạm vi nền tảng đã triển khai. Bàn giao hướng dẫn cài đặt, chạy, kiểm tra, xử lý lỗi, backup, khôi phục và tiếp tục phát triển; chỉ rõ người phụ trách và nơi lưu bằng chứng.

Nghiệm thu khi người tiếp nhận thực hiện được quy trình chạy và khôi phục theo tài liệu, đối chiếu đạt bộ chuẩn và biết các giới hạn còn lại của hệ thống.
