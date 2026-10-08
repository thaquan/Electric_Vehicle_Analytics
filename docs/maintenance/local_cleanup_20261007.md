# Rà soát và dọn local — 2026-10-07

Phạm vi: toàn bộ `D:/electric_vehical_sales`, gồm thư mục ẩn, Git-ignored, runtime và tất cả nhánh output. Đã kiểm kê **34,386 file / 5,485 thư mục** (tính cả thư mục gốc); lỗi truy cập sau khi quét bổ sung: **0**.

Phương pháp: kiểm kê đệ quy từng đường dẫn; đối chiếu Git, tham chiếu trong code/tests/config/runbook/metadata; kiểm tra manifest, ZIP, checksum với các ứng viên xóa. Thư viện bên thứ ba và dữ liệu nhị phân được phân loại theo package/manifest; không tuyên bố đọc từng dòng trong mọi file. Không dùng riêng tiêu chí “không được Git quản lý” để kết luận file rác.

Đã xóa **1,550 file**, tổng dung lượng nội dung **989,592,093 byte (943.75 MiB)**. Đây là dung lượng logic, không phải phép đo dung lượng trống ổ đĩa. Không xóa hoặc sửa file đã được Git quản lý.

## Từng mục đã xóa và lý do

| Đường dẫn | File | MiB | Lý do |
| --- | ---: | ---: | --- |
| `.playwright-cli` | 4 | 0.00 | Log và snapshot trình duyệt từ các phiên kiểm tra cũ; không được pipeline, tests hoặc tài liệu dùng làm bằng chứng nghiệm thu. |
| `.playwright-mcp` | 4 | 0.00 | Log và snapshot trình duyệt tạm của các phiên cũ; ảnh bằng chứng chính thức được giữ trong docs/screenshots. |
| `.tools/hadoop-3.3.4` | 0 | 0.00 | Chỉ có thư mục bin rỗng; scripts/phase10_env.ps1 sử dụng helper hadoop-3.3.5 vẫn được giữ. |
| `output/phase12/r3` | 562 | 352.88 | Gói đóng dở: ZIP không hợp lệ. Payload đã có trong final; bản final bổ sung/sửa tài liệu và kết quả quét. Không phải gói nghiệm thu. |
| `output/phase12/r4` | 564 | 407.87 | Bản đóng gói trung gian được thay thế bởi final. Manifest cho thấy payload giống bản cuối, chỉ hai tài liệu thay đổi đường dẫn r4/r3 sang final; không có bằng chứng nghiệm thu riêng. |
| `output/phase12/release-01` | 303 | 169.37 | Thư mục đóng gói dở: chỉ baseline/project/snapshots, thiếu manifest, runtime, reference và ZIP hoàn chỉnh. Bản r2 đã nghiệm thu và final vẫn được giữ. |
| `output/phase10/_spark_write_smoke` | 6 | 0.00 | Dữ liệu rất nhỏ của phép thử ghi Spark; không phải run nghiệp vụ, không có tham chiếu từ mã nguồn/tài liệu nghiệm thu. |
| `dags/__pycache__` | 2 | 0.01 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `databricks/notebooks/__pycache__` | 2 | 0.01 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `databricks/runtime_src/__pycache__` | 4 | 0.03 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `scripts/__pycache__` | 39 | 0.33 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `src/__pycache__` | 15 | 0.10 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `tests/__pycache__` | 16 | 0.14 | Bytecode Python tự sinh; mã nguồn .py được giữ, Python sẽ tạo lại khi chạy. |
| `metadata/report_create_payload.json` | 1 | 0.49 | Request triển khai được sinh từ PBIR bằng lệnh pack trong docs/architecture/powerbi_report.md; không phải nguồn report, có thể tạo lại. |
| `metadata/star_model_binding_request.json` | 1 | 0.00 | Request cập nhật binding đã sinh bởi scripts/prepare_star_binding.py; model TMDL và bằng chứng triển khai vẫn được giữ. |
| `output/gold_export_remote_readback` | 23 | 11.31 | Bản tải lại để kiểm chứng truyền OneLake: 23/23 file đã so SHA-256 và giống hoàn toàn output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z. Bản export gốc và metadata/gold_export_transfer_verification.json được giữ. |
| `output/phase12/airflow_e2e/phase10/runs/airflow_test_57a67695d9a94ddb90f97bab5ec768e2/bronze/parquet/test.parquet/_temporary` | 4 | 1.22 | File ghi Spark chưa commit còn lại từ lần chạy Airflow bị ngắt. Không có tiến trình Spark/Java đang chạy; run nghiệm thu khác có published marker được giữ nguyên. |

Mọi thư mục con bên trong mục xóa kế thừa lý do của thư mục cha; danh sách đầy đủ từng thư mục nằm trong `directory_review.csv`.

## Rà soát toàn bộ thư mục cấp gốc

| Thư mục | File trước dọn | Kết luận |
| --- | ---: | --- |
| `.git` | 2452 | Giữ lịch sử và cấu hình Git. |
| `.playwright-cli` | 4 | Đã xóa: Log và snapshot trình duyệt từ các phiên kiểm tra cũ; không được pipeline, tests hoặc tài liệu dùng làm bằng chứng nghiệm thu. |
| `.playwright-mcp` | 4 | Đã xóa: Log và snapshot trình duyệt tạm của các phiên cũ; ảnh bằng chứng chính thức được giữ trong docs/screenshots. |
| `.tools` | 2858 | Giữ thư viện Python/Power BI và helper Hadoop 3.3.5 phục vụ export, backup và Spark. |
| `LH_EV_Bronze.Lakehouse` | 4 | Định nghĩa Lakehouse cần cho Fabric Git/CI-CD. |
| `LH_EV_Gold.Lakehouse` | 4 | Định nghĩa Lakehouse cần cho Fabric Git/CI-CD. |
| `LH_EV_Silver.Lakehouse` | 4 | Định nghĩa Lakehouse cần cho Fabric Git/CI-CD. |
| `NB_EV_Bronze_To_Silver.Notebook` | 2 | Notebook định dạng Fabric Git; bản ipynb dùng import thủ công được giữ riêng. |
| `NB_EV_Silver_To_Gold.Notebook` | 2 | Notebook định dạng Fabric Git; bản ipynb dùng import thủ công được giữ riêng. |
| `PL_EV_E2E.DataPipeline` | 2 | Định nghĩa pipeline Fabric. |
| `RPT_EV_Analytics.Report` | 66 | Định nghĩa report PBIR và theme. |
| `SM_EV_Analytics.SemanticModel` | 12 | Semantic model TMDL gắn PBIP. |
| `config` | 5 | Cấu hình môi trường và mẫu recovery. |
| `dags` | 3 | DAG điều phối Airflow. |
| `data` | 8 | CSV gốc và Bronze có lineage/hash; không coi là file rác. |
| `databricks` | 18 | Job, notebook và runtime serverless Phase 11/12. |
| `docker` | 1 | Dockerfile Airflow phục vụ tái dựng môi trường. |
| `docs` | 29 | Runbook, thiết kế và ảnh bằng chứng nghiệm thu. |
| `metadata` | 70 | Contract, manifest, kết quả kiểm chứng và snapshot lịch sử. |
| `models` | 10 | Snapshot model đã triển khai, tách với semantic model của PBIP. |
| `notebooks` | 3 | Notebook import thủ công và recovery, khác mục đích với Fabric Git. |
| `output` | 28604 | Giữ dữ liệu/bằng chứng, backup và bản giải nén phục vụ phục hồi; chỉ xóa các mục đã xác minh. |
| `scripts` | 84 | Công cụ build, triển khai, xác minh, backup và recovery. |
| `sql` | 2 | SQL mẫu và truy vấn đối chiếu. |
| `src` | 23 | Mã pipeline PySpark. |
| `tests` | 33 | Tests và DAX kiểm chứng. |
| `references/upstream_notebook_source` | 66 | Nguồn tham khảo lấy dữ liệu; có mã nghiên cứu và notebook riêng, không xóa chỉ vì bị Git ignore. |

Các file tại thư mục gốc (README, requirements, pipeline YAML, PBIP, cấu hình Git/editor) được giữ. `references/predicting_electric_vehicle_full_eda.ipynb` khác checksum với notebook trong clone tham khảo, nên không xóa như bản trùng.

## Những mục đáng chú ý được giữ

- `output/phase9/release-01`: docs/milestones/phase9_closeout.md yêu cầu giữ làm bằng chứng chẩn đoán; việc chạy thất bại không đồng nghĩa file rác.
- `output/phase9/release-02`, `output/phase12/r2`, `output/phase12/final`, `output/phase12/restore02` và các run đã publish: backup, nghiệm thu và nguồn cho quy trình phục hồi.
- Các bản backup nháp Phase 9, bản giải nén và run cũ còn lại: chưa đủ bằng chứng rằng mọi nội dung đều dư thừa hoặc không cần lưu; giữ lại. Không suy luận rằng một file không có import/tham chiếu trực tiếp là không dùng.
- `.tools/cd-runtime`, `.tools/parquet-runtime`, `.tools/node_modules`: môi trường phụ thuộc, không phải cache rác; scripts và runbook còn dùng.
- Các `.pbi/localSettings.json` nằm trong bản lưu trước đồng bộ/recovery: giữ trạng thái lịch sử. Bytecode bên trong các gói recovery/backup cũng được giữ để không thay đổi cây artifact đã đóng gói.
- Snapshot model ở `models/` và model trong PBIP, notebook Fabric Git và notebook import: phục vụ các đường triển khai khác nhau, không xóa vì trông giống nhau.

## Kiểm tra sau dọn

- 307 file Git-tracked: SHA-256 không đổi.
- 4/4 CSV raw: SHA-256 khớp metadata/source_manifest.json.
- ZIP Phase 9 release-02 và Phase 12 final: SHA-256 khớp hồ sơ nghiệm thu.
- ZIP final đã kiểm CRC thành công trước dọn; SHA-256 sau dọn vẫn khớp.
- Không còn mục nào trong danh sách xóa tồn tại; mọi thao tác xóa thành công.
- Không chạy lại pipeline/cloud hay unit tests vì không đổi mã nguồn; kiểm tra tập trung vào toàn vẹn file và artifact.

## Hồ sơ chi tiết

- [Danh sách từng thư mục và quyết định](../../output/local_cleanup_20261007/directory_review.csv)
- [Kiểm kê trước dọn](../../output/local_cleanup_20261007/inventory_before.json)
- [Danh sách và lý do xóa](../../output/local_cleanup_20261007/deletion_results.json)
- [Kết quả kiểm chứng](../../output/local_cleanup_20261007/verification.json)

Hồ sơ chi tiết đặt trong output (Git-ignored); các liên kết trên chỉ mở được trong bản local có hồ sơ này. Báo cáo Markdown được đồng bộ lên GitHub và Azure DevOps. Các file đã xóa đều không được Git quản lý, nên việc dọn local không tạo thay đổi xóa file trên hai remote.
