# Giai đoạn 12 — Nghiệm thu và bàn giao

Cập nhật ngày 2026-10-06. **Trạng thái: các kiểm chứng kỹ thuật đã đạt; chưa ký nghiệm thu bàn giao cho người tiếp nhận.** Xem [biên bản kỹ thuật](../project_summary.md) và [runbook bàn giao](phase12_operations.md). Các mục yêu cầu người tiếp nhận vẫn để trống cho đến khi có xác nhận thực tế.

Mục tiêu là để người tiếp nhận tự vận hành, kiểm tra và khôi phục hệ thống theo tài liệu. Kết quả kỹ thuật của các giai đoạn trước là bằng chứng đầu vào; chưa thay thế việc bàn giao cho người tiếp nhận.

## 1. Chốt phạm vi và người chịu trách nhiệm

- [ ] Ghi rõ người bàn giao, người tiếp nhận, người vận hành chính và người dự phòng.
- [ ] Chốt môi trường được bàn giao: Fabric/Power BI, PySpark/Airflow độc lập và Databricks serverless; ghi môi trường nào cần tiếp tục vận hành.
- [x] Ghi repo, base commit, release, workspace, job, Volume và nơi giữ backup cục bộ trong runbook/manifest; nơi giữ bản sao ngoài máy vẫn cần chỉ định.
- [ ] Chốt các kiểm tra được miễn hoặc hoãn, lý do và người chấp thuận.

Phase 11 hiện xác minh pipeline dữ liệu trên Databricks. Chưa có bằng chứng chuyển semantic model hoặc report Power BI sang nguồn Databricks; không coi việc này là đã hoàn tất. Chỉ bổ sung chuyển nguồn report nếu phạm vi bàn giao yêu cầu.

## 2. Hoàn thiện bộ tài liệu vận hành

- [ ] Người tiếp nhận kiểm tra hướng dẫn cài đặt và phiên bản runtime cần dùng.
- [ ] Xác nhận cách dùng danh tính đã cấu hình và quyền tối thiểu trên repo, workspace, job, dữ liệu và backup bằng tài khoản của người tiếp nhận.
- [x] Chuẩn bị hướng dẫn chạy, xem log, xử lý lỗi, retry, publish và chọn lại release tốt gần nhất; bổ sung lỗi thực tế từ diễn tập vào runbook.
- [ ] Ghi đường dẫn backup thực tế, người giữ, thời hạn lưu và cách lấy bản sao khi máy hiện tại không còn sử dụng được.

| Nội dung | Tài liệu hiện có |
| --- | --- |
| Fabric Bronze/Silver/Gold | [Bronze/Silver](../pipelines/bronze_silver.md), [Gold](../pipelines/gold_runbook.md), [pipeline](../pipelines/pipeline_runbook.md) |
| Power BI | [Semantic model](../architecture/semantic_model.md), [report](../architecture/powerbi_report.md) |
| CI/CD và xử lý sự cố Fabric Test | [Test CD](../deployment/test_cd.md), [operations](operations_runbook.md) |
| Backup độc lập | [Phase 9 backup](../recovery/phase9_backup.md), [kết quả khôi phục](../project_summary.md) |
| PySpark/Airflow | [PySpark/Airflow](../pipelines/standalone_pipeline.md) |
| Databricks và đối chiếu | [Đóng gói, chạy và đối chiếu](../pipelines/phase11_databricks.md), [kết quả nghiệm thu](../project_summary.md) |

Các file Markdown dùng UTF-8. Với Windows PowerShell, đọc bằng `Get-Content -Encoding utf8 <file.md>`. Trong editor, chọn mở lại bằng UTF-8 trước khi lưu nếu chữ hiển thị sai.

## 3. Chạy thử bàn giao từ đầu đến cuối

- [ ] Người tiếp nhận tự lấy đúng release và nguồn dữ liệu, kiểm tra checksum rồi chuẩn bị môi trường theo tài liệu.
- [x] Agent chạy pipeline Airflow từ code/CSV trong ZIP đã giải nén vào output mới; tiếp tục an toàn khi run bị ngắt. Databricks đã có run package sạch được xác minh ở Phase 11.
- [x] Kiểm tra trạng thái job/container, quality, publish marker, schema, khóa, lineage và integrity của sáu stage.
- [x] Đối chiếu đủ tám bảng Gold của Airflow với bản chuẩn từ ZIP; lưu log và báo cáo thực tế.
- [x] Fabric Test: xác minh refresh gần nhất, liên kết report/model và KPI trực tiếp bằng API JSON. Không kích hoạt refresh mới; thao tác report/UI và SQL endpoint vẫn giữ trạng thái hoãn đã ghi trong hồ sơ.

Bộ chuẩn: **668665 respondents, 116779 Yes, 551886 No, orphan bằng 0, tám bảng Gold và 35 nhóm segment**. Không chỉ đối chiếu KPI tổng; schema và dữ liệu từng bảng cũng phải đạt. Các giá trị lineage thay đổi theo run được xử lý theo hướng dẫn đối chiếu.

## 4. Diễn tập khôi phục và xử lý lỗi

- [ ] Kiểm tra backup bàn giao có code/config/runtime của release mới nhất; backup Phase 9 tạo trước các bổ sung Phase 10–11 nên không mặc nhiên là gói bàn giao cuối cùng.
- [ ] Người tiếp nhận lấy backup từ nơi lưu đã chỉ định và khôi phục vào môi trường/thư mục mới.
- [x] Agent đã khôi phục baseline 15 bảng và đối chiếu đủ tám bảng snapshot Databricks từ ZIP thử r2; lưu bằng chứng. Kiểm chứng archive bàn giao cuối được ghi riêng trong acceptance.
- [x] Kiểm thử dữ liệu lỗi, quality/publish gate, checksum sai, file thừa và ZIP traversal; không dùng dữ liệu lỗi làm kết quả nghiệm thu.
- [ ] Xác minh cách chọn release tốt trước đó và đường dẫn dữ liệu tương ứng khi cần rollback.

Code và JSON trong GitHub/Azure DevOps không thay thế backup dữ liệu. `data/raw/`, các kết quả lớn và ZIP trong `output/` không được Git quản lý.

## 5. Chốt hiệu năng, chi phí và các giới hạn

- [ ] Ghi thời gian chạy, quy mô dữ liệu, runtime và điều kiện đo; thống nhất mức chấp nhận cho vận hành.
- [x] Truy vấn lại billing Databricks: đã có usage DBU; ghi rõ chưa xác minh số tiền thực trả và chưa chỉ định người theo dõi chi phí.
- [ ] Ghi lịch chạy/kiểm tra phù hợp, người nhận thông báo lỗi và cách xử lý; không tự coi snapshot cố định cần lịch chạy hằng ngày.
- [ ] Ghi các bước kiểm tra còn hoãn ở Fabric SQL endpoint, report Service và các giới hạn runtime/serverless theo phạm vi nghiệm thu.

Run package sạch Phase 11 `phase11_20261006T013808Z` đã đạt SUCCESS trong **241376 ms**, 116 artifact khớp checksum và tám bảng Gold khớp Phase 10. Đây là một phép đo đã có, chưa phải cam kết hiệu năng/SLA. Billing probe cũ rỗng không chứng minh chi phí bằng 0.

## 6. Lập biên bản nghiệm thu cuối

- [x] Tổng hợp kết quả theo từng tiêu chí, liên kết bằng chứng và danh sách tồn đọng trong biên bản kỹ thuật.
- [ ] Ghi ngày bàn giao, release/commit, người tiếp nhận và xác nhận họ đã chạy/khôi phục được theo tài liệu.
- [ ] Ghi các ngoại lệ được chấp thuận, người chịu trách nhiệm và thời hạn xử lý.
- [ ] Cập nhật README và tổng kết nghiệm thu sau khi đáp ứng đủ điều kiện.

Chỉ đánh dấu giai đoạn 12 hoàn tất khi người tiếp nhận thực hiện được quy trình đã thống nhất và xác nhận kết quả. Đã có diễn tập kỹ thuật do agent thực hiện; chưa có xác nhận bàn giao của người tiếp nhận.
