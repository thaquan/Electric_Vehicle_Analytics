# Phase 11 Closeout — Databricks

## Kết quả

Phase 11 đã được triển khai trên Databricks bằng serverless compute và đã chạy thành công end-to-end theo cùng hợp đồng dữ liệu của Phase 10.

- Databricks job: `149867914773886` (`EV Analytics Phase 11 Databricks`)
- Successful job run: `23656547233351`
- Task run: `922294573463102`
- Pipeline run id: `phase11_20261005T041811Z`
- Compute: Databricks serverless
- Spark runtime đo được: `4.2.0`
- Python runtime đo được: `3.12.3`
- Job runtime: `203005 ms` tổng thời gian; task execution `198000 ms`; setup `4000 ms`

## Data contract và kết quả quality

Nguồn dữ liệu giữ nguyên checksum so với Phase 10, gồm train SHA-256 `141B8AC4B171CEBCE17EA7F52CF5C26F1AC5B675C24850096A3CFACA60B036D4`.

Run thành công tạo đủ Bronze → Silver → Gold → Quality → Publish. Quality report trả về:

- respondents: `668665`
- yes: `116779`
- no: `551886`
- orphan_keys: `0`
- segment_groups: `35`
- Gold tables: `8`
- dimension rows: demographics `45`, income `4`, mobility `16`, charging `2`, attitude_incentive `30`
- schema checks: `passed`
- silver reconstruction: `exact`
- aggregate checks: `passed`

Published marker được tạo thành công và inventory được kiểm tra trước/sau quality checks.

## Reconciliation với Phase 10

Đối chiếu trực tiếp Gold của Phase 11 với reference run Phase 10 `review_fix_20261003_03` đã PASS cho cả 8 bảng:

`agg_ev_kpi`, `agg_ev_segments`, `dim_attitude_incentive`, `dim_charging`, `dim_demographics`, `dim_income`, `dim_mobility`, `fact_ev_purchase_intent`.

Với từng bảng: schema giống nhau, row count giống nhau và `EXCEPT ALL` hai chiều đều bằng `0` sau khi loại đúng ba giá trị lineage được phép khác theo từng lần chạy: `processed_at_utc`, `silver_run_id`, `gold_run_id`. Cấu trúc/cột lineage vẫn được kiểm tra schema và không bị bỏ khỏi contract.

Bằng chứng: `metadata/phase11/phase11_vs_phase10_reconciliation.json`.

## Điều chỉnh tương thích Databricks serverless

Workspace này chỉ hỗ trợ serverless compute, vì vậy không thể pin classic cluster DBR 16.4 LTS như kế hoạch ban đầu. Runtime thực tế được probe là Spark `4.2.0` và Python `3.12.3`.

Phase 10 local code không bị thay đổi. Phase 11 dùng adapter/runtime copies với ba điều chỉnh kỹ thuật, không đổi business logic:

1. Tái sử dụng active Spark Connect session của Databricks thay vì `SparkSession.builder.master('local[*]')`.
2. Đổi writer mode `errorifexists` thành alias được Spark Connect hỗ trợ là `error`.
3. Bỏ `cache()/persist()` và `unpersist()` trong runtime copies vì serverless trả lỗi `PERSIST TABLE is not supported`; các phép tính, quality rules và exact reconstruction vẫn giữ nguyên.

## Storage và quyền

Unity Catalog schema: `workspace.ev_phase11`.

Managed Volume: `workspace.ev_phase11.ev_phase11`.

Notebook chính: `/Shared/ev_phase11/phase11_runner`.

Người dùng xác thực có quyền tạo/chạy job và quyền truy cập catalog/schema/volume cần thiết cho pipeline. Không lưu token/secret trong repo.

## Billing / cost

Runtime probe truy vấn `system.billing.usage` cho job `149867914773886` trong cửa sổ 1 ngày và tại thời điểm `2026-10-05T04:35:39Z` chưa có bản ghi usage trả về. Vì system billing có thể cập nhật trễ, không được diễn giải kết quả rỗng thành chi phí bằng 0 và không bịa số cost.

Bằng chứng runtime/billing: `metadata/phase11/runtime_billing_probe.json`.

## Bằng chứng chính

- `metadata/phase11/phase11_vs_phase10_reconciliation.json`
- `metadata/phase11/runtime_billing_probe.json`
- `config/environments/databricks.json`
- `databricks/notebooks/phase11_runner.py`
- `databricks/notebooks/phase11_probe.py`
- `databricks/jobs/phase11_job_serverless.json`
- `databricks/jobs/phase11_probe_job.json`

Kết luận: Phase 11 đạt tiêu chí nghiệm thu về cùng bài toán/hợp đồng dữ liệu, đối chiếu với Phase 10, ghi nhận cấu hình/quyền/runtime và thực hiện best-effort đo billing. Sai khác nền tảng đã được giải thích và kiểm chứng không làm thay đổi dữ liệu nghiệp vụ.
