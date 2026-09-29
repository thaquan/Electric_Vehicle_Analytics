# RPT_EV_Analytics — giai đoạn 6

## Trạng thái ngày 2026-09-27

- Đã tạo `RPT_EV_Analytics.pbip` và thư mục `RPT_EV_Analytics.Report`.
- Báo cáo kết nối đến semantic model hiện có `SM_EV_Analytics`
  (`8e7e37b7-7bab-4122-84fb-3ae7b2121cd7`) trong `WS_EV_Analytics`.
- Không chạy lại pipeline, refresh hay sửa semantic model.
- Bỏ qua chạy SQL analytics endpoint theo yêu cầu người dùng. Không coi bước này là đã đạt.
- CLI kiểm tra PBIR: **0 lỗi, 0 cảnh báo**; kết quả tại
  `metadata/report_validation.json`.
- Đã mở báo cáo trong Power BI Desktop, kiểm tra dữ liệu thật và ảnh chụp cả ba trang.
  KPI Overview khớp 668.665 / 116.779 / 551.886 / 17,46%; tám KPI còn lại
  khớp bằng chứng DAX sau làm tròn. Ảnh lưu tại `docs/screenshots/`.
- Toàn bộ nội dung report bằng tiếng Anh theo yêu cầu mới nhất, dùng thuật ngữ
  **EV purchase intent**. Đã nạp lại và kiểm tra không có visual lỗi hoặc cắt chữ.
- Đã xuất bản lên `WS_EV_Analytics`; Fabric catalog xác nhận report ID
  `ae4d7c59-759e-4462-afed-1717475ae012` ngày 2026-09-27.
  [Mở báo cáo](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/reports/ae4d7c59-759e-4462-afed-1717475ae012).
- Đã thử slicer City type = Urban bằng Windows UI Automation: 289.305 người,
  46.595 có ý định mua, 242.710 không có ý định mua, tỷ lệ 16,11%; khớp đối chiếu.
  Xóa lựa chọn trong slicer khôi phục tổng 668.665. Ảnh: `docs/screenshots/Overview-Urban-filter.png`.
- Kiểm thử navigation/reset, lọc chéo từ biểu đồ và giao diện Service: **bỏ qua theo yêu cầu**.
  Không đánh dấu các kiểm thử này đã đạt. Không dùng Playwright.
- Giai đoạn 7 đã tạo bản export Parquet và manifest local có kiểm tra; xem
  [bằng chứng export](gold_export.md). Chưa thực hiện khôi phục môi trường riêng.

## Nội dung

| Trang | KPI | Biểu đồ và slicer |
| --- | --- | --- |
| Executive Overview | Người khảo sát; có/không có ý định mua EV; tỷ lệ ý định mua EV | Phân bố nơi sống; tỷ lệ theo tuổi và thu nhập. Lọc nơi sống, giới tính, tuổi, thu nhập. |
| Charging & Incentives | Tỷ lệ có thể sạc tại nhà; tỷ lệ có trợ cấp; trạm sạc trung bình gần nhà/nơi làm | Tỷ lệ ý định mua EV theo sạc tại nhà, trợ cấp, lo ngại quãng đường. Lọc sạc tại nhà, trợ cấp, lo ngại quãng đường, nơi sống. |
| Customer Profile | Thu nhập năm USD, tuổi, quãng đường đi làm km, số xe trung bình | Phân bố thu nhập và tuổi; tỷ lệ ý định mua EV theo quãng đường đi làm. Lọc thu nhập, tuổi, nơi sống, quãng đường. |

Mỗi trang có 1 thẻ chứa 4 KPI, 3 biểu đồ, 4 slicer, 7 hộp văn bản và 4 nút.
Tổng cộng 57 visual. Slicer hoạt động riêng trên từng trang, cho phép chọn nhiều giá trị.
Thiết kế automotive dark 1600 × 900 (16:9), nền navy `#0B1220`, thẻ `#131E2F`,
xanh mint `#34D399` cho tỷ lệ và xanh blue `#38BDF8` cho số lượng.
Thanh bên có 3 nút chuyển trang và **Reset slicers** (xóa slicer trên trang hiện tại,
không xóa mọi loại filter hoặc lựa chọn biểu đồ). Trong Desktop edit mode, dùng
Ctrl+click để chạy hành động nút. Chưa nghiệm thu thao tác nút/lọc chéo trực tiếp.
Nhãn **Survey snapshot** là ngày Gold đã xác minh, không phải thời điểm refresh trực tiếp.
Các tương tác từ slicer/biểu đồ đến KPI và các biểu đồ khác được cấu hình `DataFilter`.
Nhóm tuổi, thu nhập và quãng đường dùng thứ tự đã định nghĩa trong semantic model.
Tất cả chỉ số dùng explicit measure; không cộng hai bảng aggregate Gold.

Dashboard dùng thuật ngữ **EV purchase intent**. Dữ liệu tổng hợp không đại diện cho
doanh số, tỷ lệ chuyển đổi thực tế hay quan hệ nhân quả.

## Mở và xuất bản

1. Mở `RPT_EV_Analytics.pbip` bằng Power BI Desktop có hỗ trợ PBIP/PBIR.
2. Đăng nhập tài khoản có quyền truy cập `SM_EV_Analytics` trong `WS_EV_Analytics`.
3. Kiểm tra cả ba trang bằng dữ liệu thật theo danh sách bên dưới.
4. Publish vào `WS_EV_Analytics` với tên `RPT_EV_Analytics`.
5. Lưu URL/ID báo cáo và ảnh chụp vào hồ sơ nghiệm thu.

Đã chuẩn bị `metadata/report_create_payload.json` bằng CLI `pack --mode create`.
Tệp có envelope: phần body gửi Fabric API là `data.body`, không phải toàn bộ tệp.
Đây là gói triển khai, không phải bằng chứng báo cáo đã được tạo trên Service.

## Kiểm tra khi có Power BI

Các giá trị dưới đây lấy từ bằng chứng DAX đã lưu và đã đối chiếu với
12 KPI hiển thị trên ảnh chụp report trong Desktop, sau làm tròn.

| KPI khi xóa mọi bộ lọc | Giá trị mong đợi |
| --- | ---: |
| Người khảo sát | 668.665 |
| Có ý định mua EV | 116.779 |
| Không có ý định mua EV | 551.886 |
| Tỷ lệ ý định mua EV | 17,46% |
| Có thể sạc tại nhà | 69,19% |
| Có trợ cấp | 62,80% |
| Tuổi trung bình | 47,0 |
| Thu nhập năm USD trung bình | 84.769,27 |
| Quãng đường đi làm km trung bình | 32,2 |
| Số xe trung bình | 1,71 |
| Trạm sạc gần nhà trung bình | 4,96 |
| Trạm sạc gần nơi làm trung bình | 7,18 |

- Đối chiếu KPI và nhóm với `metadata/semantic_model_live_dax.json`,
  `metadata/semantic_model_profile_dax.json`, `metadata/star_expected_metrics.json`.
- Chọn một nhóm tuổi/thu nhập: KPI và biểu đồ phải cùng đổi; tỷ lệ bằng
  số có ý định mua EV chia số người khảo sát trong bộ lọc hiện tại.
- Kết hợp nơi sống + khả năng sạc tại nhà + trợ cấp trong Filter pane;
  đối chiếu các nhóm đã kiểm tra trong bằng chứng DAX.
- Chọn một thanh biểu đồ: các visual đích phải được lọc. Xóa lựa chọn
  và bộ lọc phải khôi phục tổng ban đầu.
- Kiểm tra chọn nhiều giá trị, xóa bộ lọc và tập kết quả rỗng (tỷ lệ để trống).
- Kiểm tra tiêu đề, nhãn KPI, phần trăm, thứ tự nhóm và không có visual lỗi/cắt chữ.
- Chụp ba trang ở trạng thái không lọc và ít nhất một trạng thái có lọc.

## Tái tạo và kiểm tra cấu trúc

```powershell
node scripts/build_report.cjs
node scripts/style_report.cjs
.tools/node_modules/.bin/powerbi-report-author.cmd validate RPT_EV_Analytics.Report --out metadata/report_validation.json
.tools/node_modules/.bin/powerbi-report-author.cmd pack RPT_EV_Analytics.Report --mode create --display-name RPT_EV_Analytics --out metadata/report_create_payload.json
```

Script sử dụng bộ khung report hiện có và tạo nội dung xác định theo ID ổn định.
Chạy lại sẽ ghi đè các visual do script quản lý; lưu các chỉnh sửa thủ công trước khi chạy.
Sau mọi sửa đổi, kiểm tra lại cấu trúc và hiển thị. Kiểm tra PBIR không thay thế
việc mở report, truy vấn dữ liệu và thử tương tác trong Power BI.
