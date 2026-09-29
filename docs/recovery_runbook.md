# Quy trình khôi phục EV Analytics

> Cập nhật 2026-09-29: lần thử khôi phục đã hoàn tất; xem
> [kết quả bàn giao](phase7_closeout.md). Các mô tả "chưa thực hiện" bên dưới
> ghi lại trạng thái tại thời điểm phát hành ZIP gốc. Khi thực hiện lần khôi phục mới,
> cần kiểm tra lại từng bước; không sử dụng kết quả lịch sử làm bằng chứng mới.

## 1. Phạm vi và trạng thái

Tài liệu này hướng dẫn khôi phục bản Gold v2 đã xuất, không chạy lại pipeline.
Phần 3–4 gồm chuẩn bị gói bàn giao, notebook/script và quy trình này.
Các thao tác tạo workspace, nạp bảng, deploy model, refresh và publish report bên dưới
thuộc **phần 5**, chưa được thực hiện khi phát hành gói.

| Thành phần | Giá trị chuẩn |
| --- | --- |
| Gold run ID | `20260925T152721965637Z` |
| Export ID | `20260927T130004568586Z` |
| SHA-256 manifest snapshot | `0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f` |
| Fact | 668665 dòng |
| Dimensions | 45 / 4 / 16 / 2 / 30 dòng |
| Audit aggregates | 1 / 35 dòng |
| KPI | 668665 / 116779 / 551886 |
| Purchase intent rate | 0.17464500160768098 |
| Semantic model | 6 bảng, 5 quan hệ, 12 measures |
| Report | 3 trang, 57 visual |

KPI đo ý định mua EV trong dữ liệu tổng hợp. Hai bảng aggregate chỉ phục vụ audit.
Kiểm thử navigation/reset, chart cross-filter và giao diện dashboard còn lại
vẫn là **bỏ qua theo yêu cầu**, không đánh dấu đạt. Việc xác minh KPI trên bản sao
recovery ở cuối tài liệu là bằng chứng riêng của phần 5.

## 2. Chuẩn bị máy và quyền truy cập

- Python 3.11 trở lên; bản bàn giao được kiểm tra bằng Python 3.13.
- Nếu kiểm tra nội dung Parquet local: cài `project/requirements-export.txt`
  (PyArrow 25.0.1, pandas và numpy).
- Workspace đích có Fabric capacity hoạt động, quyền tạo lakehouse/notebook/model/report.
- Tài khoản đọc được toàn bộ bảng Delta của lakehouse mới; quyền Build trên model
  khi kiểm tra DAX/report. Nếu dùng danh tính cố định cho model, cấp quyền đọc cho danh tính đó.
- Power BI Desktop có hỗ trợ PBIP, TMDL và Direct Lake để kiểm tra bản report/model.
- Azure CLI để chạy helper tạo item; đăng nhập bằng user có quyền Contributor trở lên.
- Node.js 20+ để chạy validator PBIR khi đổi kết nối report.

Notebook recovery dùng PySpark, PyArrow và pandas của Fabric runtime. Nếu runtime
thiếu thư viện hoặc không đọc được schema Parquet, dừng ở preflight và cấu hình
environment trước; không bỏ kiểm tra checksum/schema.

## 3. Kiểm tra gói trước khi sử dụng

Ví dụ tên ZIP: `EV_Analytics_Recovery_20260925T152721965637Z.zip`.
Trong PowerShell, trước khi giải nén:

```powershell
$recoveryZip = '.\EV_Analytics_Recovery_20260925T152721965637Z.zip'
$expectedHash = ((Get-Content -LiteralPath ($recoveryZip + '.sha256') -Raw).Trim() -split '\s+')[0]
$actualHash = (Get-FileHash -LiteralPath $recoveryZip -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw 'ZIP checksum mismatch' }
Expand-Archive -LiteralPath $recoveryZip -DestinationPath '.\recovery_work'
Set-Location '.\recovery_work\EV_Analytics_Recovery'
python verify_package.py .
```

Kết quả cần có `status: passed` và `parquet_tables: 8`.
Verifier kiểm tra chính xác inventory, nên chạy trước khi thêm file local.
Giữ ZIP và checksum nguyên bản để có thể kiểm tra lại bằng `verify_package.py <zip>`.
Checksum phát hiện thay đổi file; không thay thế chữ ký số.

Nếu muốn tính lại toàn bộ KPI/PK/FK trên máy, tạo môi trường riêng rồi chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r project/requirements-export.txt
.\.venv\Scripts\python.exe project/scripts/export_gold_snapshot.py verify --output snapshot
```

Kết quả phải có KPI chuẩn, `orphan_keys: 0` và `segment_groups: 35`.

## 4. Tạo workspace và lakehouse mới

Trong Fabric:

1. Tạo `WS_EV_Analytics_Recovery`, gán capacity phù hợp.
2. Tạo `LH_EV_Gold_Recovery`. Nếu lakehouse bật schema, dùng `dbo`.
3. Ghi workspace ID và lakehouse ID từ URL/properties.
4. Không tạo shortcut về lakehouse nguồn: bản thử cần có dữ liệu vật lý độc lập.

Tại thư mục gốc của gói:

```powershell
Copy-Item recovery.example.json recovery.config.json
```

Điền file cấu hình:

| Trường | Cách điền |
| --- | --- |
| `workspace_id` | GUID workspace mới |
| `workspace_name` | Tên workspace mới, mặc định `WS_EV_Analytics_Recovery` |
| `lakehouse_id` | GUID lakehouse mới |
| `lakehouse_name` | Tên lakehouse mới |
| `lakehouse_schema` | `dbo` nếu bật schema; chuỗi rỗng nếu lakehouse không có schema |
| `semantic_model_name` | `SM_EV_Analytics_Recovery` |
| `semantic_model_id` | Để `null` tới khi tạo model thành công |
| `report_name` | `RPT_EV_Analytics_Recovery` |
| `gold_run_id`, `snapshot_manifest_sha256` | Giữ nguyên |
| `snapshot_relative_path` | Giữ `Files/recovery/snapshot` |

Các tên trong helper dùng chữ cái, số và dấu gạch dưới. Script từ chối ID nguồn
và yêu cầu workspace khác nguồn. Cấu hình không chứa token hoặc mật khẩu.

## 5. Upload snapshot và mã phục hồi

Upload các file vào lakehouse mới bằng Lakehouse explorer hoặc OneLake File Explorer,
giữ đúng cấu trúc sau:

```text
LH_EV_Gold_Recovery/Files/recovery/
├── recovery.config.json
├── snapshot/
│   ├── manifest.json
│   ├── manifest.sha256
│   ├── parquet/                  # 8 file .parquet
│   └── evidence/                 # giữ đủ bằng chứng export
└── scripts/
    ├── recovery_common.py
    ├── fabric_restore_gold.py
    ├── export_gold_snapshot.py
    └── star_schema.py
```

Lấy scripts từ `project/scripts/` của gói. Không upload cả thư mục cha thành
`snapshot/snapshot/`; manifest phải nằm trực tiếp trong `Files/recovery/snapshot`.

Import `project/notebooks/NB_EV_Restore_Gold.ipynb` thành notebook mới trong workspace
recovery. Gắn **lakehouse mới làm default**, mở session mới sau khi đổi lakehouse.
Notebook không chứa binding tới lakehouse nguồn. Nó kiểm tra
`currentWorkspaceId`, `defaultLakehouseWorkspaceId` và `defaultLakehouseId` trước khi ghi.
[Tài liệu runtime context](https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-runtime)

## 6. Nạp Parquet thành Delta

1. Giữ `MODE = "preflight"`, chạy notebook.
2. Yêu cầu `preflight_passed_no_tables_written`. Bước này kiểm tra checksum,
   KPI/PK/FK của Parquet, schema Spark và tên bảng đích chưa tồn tại.
3. Đổi thành `MODE = "restore"`, chạy lại.
4. Yêu cầu `data_restored_and_verified`, đủ tám `verified_tables`.

Notebook giữ nguyên tên bảng có hậu tố snapshot và lineage Gold/Silver gốc.
Nó ghi Parquet thành Delta, đọc lại từng bảng qua catalog và so sánh dữ liệu
hai chiều bằng `exceptAll`. Cách nạp file bằng Spark và `saveAsTable` được Fabric hỗ trợ.
[Hướng dẫn nạp dữ liệu](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data)

Bằng chứng được lưu tại:

```text
Files/recovery/results/restore_data_<recovery_run_id>.json
```

Tải file này về `results/` local. Trạng thái đạt ở đây chỉ áp dụng cho dữ liệu;
model refresh, publish report và recovery tổng thể vẫn chưa được đánh dấu đạt.

## 7. Chuẩn bị và tạo semantic model

Chạy tại thư mục gốc của gói:

```powershell
python project/scripts/prepare_recovery.py model --config recovery.config.json --snapshot snapshot --output generated/model
```

Script tạo:

- `generated/model/SM_EV_Analytics_Recovery.SemanticModel/`.
- `create_semantic_model.json`: request body có các file TMDL mã hóa Base64.
- `recovery_gold_checks.sql`: SQL chỉ dùng Gold trong lakehouse recovery.
- `prepared.json`: endpoint và trạng thái **prepared_not_deployed**.

Bản mới có URL OneLake đích, `schemaName` phù hợp, logical ID mới và bỏ database ID
của model nguồn. Sáu entityName vẫn trỏ tới snapshot được khôi phục. Measures,
relationships, format và sort columns được giữ nguyên.

Để tạo model qua API khi thực hiện phần 5:

```powershell
az login --tenant <TENANT_ID> --allow-no-subscriptions
python project/scripts/create_recovery_item.py model --config recovery.config.json --prepared generated/model --result results/model_created.json
```

Helper dùng token của phiên Azure CLI trong bộ nhớ, gọi `POST /semanticModels`,
theo dõi operation nếu trả 202, rồi ghi ID vào `results/model_created.json`.
TMDL là định dạng được API semantic model hỗ trợ. Caller cần quyền phù hợp và
scope `SemanticModel.ReadWrite.All` hoặc `Item.ReadWrite.All`.
[Create semantic model](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model),
[TMDL definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition)

Điền `item.id` nhận được vào `semantic_model_id` trong `recovery.config.json`.
Helper chỉ tạo item mới, không update/delete item hiện có. Nếu tên đã tồn tại
hoặc network timeout, kiểm tra kết quả và workspace trước khi thử lại.

## 8. Cấu hình connection và refresh

Trong workspace recovery:

1. Mở settings của `SM_EV_Analytics_Recovery`.
2. Cấu hình gateway/cloud connection hoặc danh tính đọc OneLake theo tùy chọn tenant.
3. Kiểm tra kết nối trỏ tới workspace/lakehouse mới; cấp quyền đọc cho danh tính thực thi.
4. Chạy **Refresh now**, chờ kết quả thành công và lưu refresh history.
5. Kiểm tra model có 6 bảng, 5 quan hệ active many-to-one, lọc dimension → fact,
   12 measures; không đưa hai bảng aggregate vào model.

Direct Lake dùng bảng Delta và model tồn tại trên Fabric. Mở PBIP report gốc
không tự tạo bản model độc lập. Có thể live edit model recovery bằng Power BI Desktop
để kiểm tra expression và partitions.
[Direct Lake trong Desktop](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-power-bi-desktop)

Chạy truy vấn sau trên **model recovery**, trong DAX query view của công cụ kết nối model:

```dax
EVALUATE
ROW(
    "respondent_count", [Respondents],
    "yes_count", [Intending to Buy EV],
    "no_count", [Not Intending to Buy EV],
    "purchase_intent_rate", [Purchase Intent Rate]
)
```

Đối chiếu 668665 / 116779 / 551886 và tỷ lệ 0.17464500160768098.
Lưu kết quả DAX mới. Có thể chạy thêm các truy vấn trong
`project/tests/semantic_model_validation.dax` để đối chiếu 35 nhóm và bộ lọc kết hợp.

`generated/model/recovery_gold_checks.sql` là kiểm tra SQL endpoint tùy chọn;
việc SQL endpoint đã bỏ qua trước đây vẫn giữ nguyên trạng thái. Không chạy phần
so sánh với `LH_EV_Silver` trong SQL nguồn khi môi trường recovery chỉ chứa Gold.

## 9. Chuẩn bị report và publish

Sau khi model refresh thành công và ID mới đã có trong config:

```powershell
python project/scripts/prepare_recovery.py report --config recovery.config.json --output generated/report
npx --yes @microsoft/powerbi-report-authoring-cli@0.4.0 validate generated/report/RPT_EV_Analytics_Recovery.Report --out results/report_validation.json
```

Script đổi `definition.pbir` sang model mới, tạo logical ID mới, giữ nguyên
giao diện và resources. CLI validation không xác nhận truy cập model hoặc dữ liệu live.
PBIR dùng `byConnection` để tham chiếu semantic model trên Service.
[Cấu trúc PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)

Chọn một cách publish:

**Qua Power BI Desktop:** mở `generated/report/RPT_EV_Analytics_Recovery.pbip`, đăng nhập,
kiểm tra đúng model recovery và publish vào `WS_EV_Analytics_Recovery`.

**Qua API:**

```powershell
python project/scripts/create_recovery_item.py report --config recovery.config.json --prepared generated/report --result results/report_created.json
```

Request tạo report đã gồm PBIR và tài nguyên. API cần quyền tạo report và scope
`Report.ReadWrite.All` hoặc `Item.ReadWrite.All`.
[Create report](https://learn.microsoft.com/en-us/rest/api/fabric/report/items/create-report)

Mở report mới, xóa bộ lọc, đối chiếu KPI **668.665 / 116.779 / 551.886**, lưu URL
và ảnh KPI. Không dùng ảnh/DAX của workspace nguồn làm bằng chứng cho recovery.

## 10. Ghi nhận kết quả phần 5

Sao chép `project/config/recovery_verification.example.json` thành
`results/recovery_verification.json`, điền các ID thực tế và liên kết bằng chứng.
Chỉ đổi trạng thái tổng thể thành `passed` khi đủ:

- Checksum gói/snapshot đúng; tám bảng Delta có schema/số dòng đúng, PK/FK hợp lệ.
- Dữ liệu Delta khớp Parquet; các bảng nằm vật lý trong lakehouse mới.
- Model dùng lakehouse mới, refresh thành công, DAX trả ba KPI đúng.
- Report dùng model mới, đã publish và KPI trên report khớp.
- Workspace, lakehouse, semantic model và report ID đều ghi rõ.

Các kiểm thử dashboard đã bỏ qua vẫn ghi `skipped_by_user_request`.
Một lần chuẩn bị payload, pass unit test hoặc pass checksum không đủ để ghi recovery đạt.

## 11. Xử lý lỗi và chạy lại

| Tình huống | Cách xử lý |
| --- | --- |
| Hash không khớp, thiếu file | Tải lại đúng ZIP/snapshot, kiểm tra trước khi nạp |
| Context notebook sai | Gắn lakehouse recovery làm default và mở session mới |
| Bảng đích đã tồn tại | Script dừng trước khi ghi; kiểm tra chúng và log lần trước. Dùng lakehouse recovery mới, hoặc dọn riêng các bảng thử sau khi xác minh đúng đích |
| Ghi được một phần rồi lỗi | Xem `written_tables`/`verified_tables` trong log; không append hay overwrite để che lỗi; sửa nguyên nhân và thử lại trên đích sạch |
| Lỗi schema/decimal/timestamp | Kiểm tra runtime, `lakehouse_schema`, timezone UTC; giữ nguyên schema trong manifest |
| API 401/403 | Đăng nhập lại đúng tenant, kiểm tra license, workspace role và API scope |
| API 202 còn chạy/timeout | Dùng `operation_url` đã lưu để xem tiến độ và `/result`; không gửi POST tạo mới lần nữa khi chưa biết kết quả |
| Model refresh lỗi quyền | Kiểm tra danh tính connection và quyền đọc OneLake đích |
| Report vẫn dùng nguồn | Kiểm tra `generated/report/.../definition.pbir` và model ID; chuẩn bị lại vào thư mục mới |
| KPI sai | Dừng nghiệm thu; kiểm tra toàn bộ filter, snapshot, sáu partition và relationships |

Các thao tác ghi tập trung ở workspace recovery. Bản nguồn không bị thay đổi.
Khi dừng một lần thử, giữ lại log và gói ZIP; việc xóa workspace thử là thao tác riêng,
không có trong script đóng gói hoặc notebook này.

## 12. Kiểm tra đã thực hiện ở phần 3–4

- Kiểm tra offline các cấu hình đích, TMDL/PBIP tạo từ ID thử và tính toàn vẹn của gói.
- So sánh giữ nguyên 57 visual khi đổi kết nối report.
- PBIR: **0 lỗi, 1 cảnh báo** do schema Microsoft `visualContainer/2.12.0` không tải được.
  Không thay schema version để né cảnh báo. Bằng chứng: `project/metadata/recovery_report_preflight.json`.
- Notebook được kiểm tra cú pháp; chưa chạy Spark trong workspace recovery.
- API helper, refresh và publish report chưa được chạy live.

Nguồn bổ sung: [Fabric API authentication](https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/fabric-api-quickstart),
[Long-running operations](https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation).
