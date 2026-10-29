# Đánh giá portfolio — 28/10/2026

## Kết luận

**Có thể đưa vào portfolio ứng tuyển Junior Data Analyst / BI Analyst và Junior Data Engineer ngay, với phạm vi trình bày đúng.** Dự án thể hiện pipeline, mô hình BI, kiểm thử và triển khai thực chất. Tuy nhiên, chưa nên mô tả là hệ thống production hoàn chỉnh, ingestion tổng quát cho dữ liệu thay đổi, hoặc dự án đã tạo ra hiệu quả kinh doanh thực tế.

Điểm cần ưu tiên hoàn thiện là tính nhất quán giữa generator và Fabric artifact, khả năng xác minh KPI live bằng danh tính hiện tại, và tài liệu nghiệm thu. Không có cơ sở yêu cầu làm thêm ML hoặc thêm công nghệ chỉ để portfolio đủ điều kiện.

| Hướng ứng tuyển | Nhận xét |
| --- | --- |
| Junior DA / BI | Đạt: câu hỏi rõ, KPI đúng grain, star schema, DAX và dashboard có đối soát. Cần decision memo và phân tích có điều kiện để nổi bật hơn. |
| Junior DE / Analytics Engineer | Đạt cho dự án xử lý snapshot: có quality gate, integrity, orchestration, integration tests và CI/CD thực tế. Cần làm rõ quy trình rebuild/deploy Fabric. |
| Mid-level / production | Chưa đủ bằng chứng: thiếu vận hành dài hạn, đo hiệu năng/chi phí, xử lý snapshot mới và diễn tập phục hồi release hiện hành. |

Đây là nhận định dựa trên bằng chứng của repository, không phải bảo đảm tuyển dụng hoặc chứng nhận không còn lỗi.

## Phiên bản và phạm vi đã kiểm tra

- GitHub `main`: `f08edd5bee7c1c09d1b1c60c99619be3b9d74c85`.
- Azure DevOps `main` và local HEAD: `48fa1fe022f78b86dd9837a5a85bd8e9c74dd6c5`.
- Đã đọc HEAD trực tiếp từ cả hai remote bằng `git ls-remote`. Commit khác nhau nhưng tree đều là `15ab0a0b6cecc4ee5f5b2f85ac37b191cacd5d30`; `git diff origin/main github/main` không có khác biệt. Như vậy nội dung hai nhánh main đang đồng bộ.
- Kiểm kê 285 file được Git theo dõi. Parse 73 Python và các JSON, notebook, PBIP/PBIR/PBISM/platform; không phát hiện lỗi parse. Đây không thay thế việc thực thi TMDL hoặc validation toàn bộ schema PBIR.
- Đọc các luồng chính: Bronze/Silver/Gold, run contract, quality, orchestration, Fabric generators, release/deployment, API guard, semantic model, SQL/recovery và tests/CI. Xem ba ảnh dashboard được commit. Không khẳng định từng dòng code hay mọi tổ hợp tương tác đã được kiểm thử.
- Hai tài liệu review ngày 22/10 và kế hoạch 23/10 đã có trong workspace nhưng chưa được Git theo dõi. Chúng không thuộc nội dung đã công bố trên hai remote. Báo cáo này dùng kết quả kiểm chứng mới, không coi kế hoạch là thay đổi đã thực hiện.

## Bằng chứng kiểm chứng mới

| Kiểm tra | Kết quả |
| --- | --- |
| Azure CI #84, commit `48fa1fe` | Đã truy vấn trực tiếp và tải artifact: 118 unit + 8 Spark + 3 Airflow = **129 passed, 0 failed/error/skipped**. |
| Azure CD #85 | Đã tải evidence: `status=passed`, `preflight_only=false`, release từ CI #84, đúng commit `48fa1fe`. |
| Health sau CD #85, ngày 22/10 | Binding, refresh và KPI DAX đều passed; 668.665 respondents, 116.779 Yes, 551.886 No. |
| Branch policy Azure | Có Build policy enabled và blocking, áp dụng chính xác `refs/heads/main`, build definition 1. Chưa kiểm tra toàn bộ quyền bypass hoặc approval checks của environment. |
| Unit local ngày 28/10 | **118/118 passed**, không skip, sau khi bổ sung PyArrow 25.0.1 và pandas 2.3.3 vào venv riêng; `pip check` passed. |
| Runtime local ban đầu | 113 passed, 1 import error vì thiếu PyArrow. Đây là vấn đề dependency môi trường, không phải assertion failure. Venv dùng `--system-site-packages`, nên không được gọi là clean-room reproduction hoàn toàn. |
| Bốn CSV local | Đều khớp SHA-256/size trong source manifest. Không phải xác thực nguồn Kaggle độc lập. |
| Tính KPI độc lập bằng pandas | 668.665 dòng/ID duy nhất; 116.779 Yes; 551.886 No; tỷ lệ 17,464500%; **35/35 nhóm khớp**. Không gọi transformation production. |
| Rebuild trên bản sao | Bốn generator chạy được. Report JSON chỉ thay formatting; model không thay đổi. Hai notebook thêm metadata; pipeline thay workspace/notebook binding. |
| Live health ngày 28/10 | Report binding passed, refresh gần nhất Completed ngày 22/10. Truy vấn `executeDaxQueries` bằng danh tính Azure CLI hiện tại trả **HTTP 401**. Chưa xác nhận lại KPI live hôm nay. |
| Sàng lọc secret cơ bản | Không phát hiện private key/token GitHub/AWS key/SAS signature theo các mẫu đã quét trong tracked files. Không phải audit toàn bộ Git history hoặc dependency vulnerabilities. |

CI: [build #84](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=84). CD: [build #85](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=85). [GitHub](https://github.com/thaquan/Electric_Vehicle_Analytics).

Không chạy lại Spark/Airflow local trong đợt này: đã kiểm chứng artifact CI đúng commit; Docker daemon local không hoạt động. Không deploy, refresh, sửa quyền, gửi thông báo hoặc sửa mã ứng dụng trong đợt review.

## Các điểm cần sửa, theo ưu tiên

### P1 — Chưa có quy ước rebuild Fabric đủ rõ và được kiểm thử

`scripts/build_pipeline.py:14,32` lấy physical notebook/workspace ID từ `metadata/fabric_workspace.json`. Artifact `PL_EV_E2E.DataPipeline/pipeline-content.json` đang commit dùng notebook ID khác và workspace ID toàn số 0. Rebuild đổi cả năm activity sang physical ID của workspace cấu hình. Hai notebook Git cũng được thêm metadata Lakehouse khi rebuild.

**Ảnh hưởng:** người clone repo rồi rebuild có thể nhận một bộ định nghĩa khác bộ đang commit. Có thể liên quan tới biểu diễn logical/physical ID trong Git integration; chỉ diff local chưa đủ kết luận pipeline đang triển khai bị hỏng. CI/CD hiện tại chủ yếu chứng minh runtime tests và triển khai model/report, không chứng minh round trip Fabric pipeline vào workspace mới.

**Cần làm:** quy định nguồn chuẩn và mode Git/API, phân biệt logical/physical ID, validate từng mode; thêm regression kiểm tra generator và artifact sau chuẩn hóa. Thử round trip ở workspace riêng trước khi đổi GUID. `tests/test_pipeline.py:85` hiện kiểm tra wiring/parameter/dependency nhưng chưa khóa đầy đủ ánh xạ ID này.

**Hoàn thành khi:** clone → generate → kiểm tra khác biệt có giải thích → deploy vào workspace riêng → pipeline chạy thành công với binding đúng; có evidence theo commit.

### P1 — KPI live chưa xác minh lại được bằng danh tính hiện tại

`scripts/check_test_health.py` đọc binding/refresh thành công nhưng DAX Arrow API trả HTTP 401. CD #85 có KPI passed bằng danh tính của service connection ngày 22/10.

**Ảnh hưởng:** chưa thể cam kết đường kiểm tra live hiện tại hoạt động từ máy này. HTTP 401 chưa chứng minh DAX sai, model hỏng, hoặc pipeline service identity cũng mất quyền.

**Cần làm:** kiểm tra token audience/phiên đăng nhập và quyền truy vấn/Build của danh tính được chọn; chạy lại health rồi lưu kết quả mới. Không sửa permission hoặc bỏ kiểm tra để ép pass. Với portfolio, tiếp tục cung cấp ảnh và video demo để người tuyển dụng xem được khi không có quyền workspace.

### P2 — Tài liệu trạng thái chưa đồng bộ với bằng chứng mới

`docs/validation.md:19` còn ghi navigation/reset/cross-filter/Service acceptance chưa xác minh nói chung; acceptance và UAT ngày 17/10 đã có representative cases passed. README vẫn dẫn CI #67/CD #70 dù main đã có CI #84/CD #85 xanh.

**Cần làm:** viết rõ release, thời điểm và phạm vi; cập nhật evidence CI/CD mới. Phân biệt Service UAT ngày 17/10, API health ngày 22/10 và kết quả live ngày 28/10. SQL endpoint và mọi tổ hợp tương tác vẫn cần ghi riêng nếu chưa thử. Không xóa hoặc viết lại bằng chứng lịch sử để làm trạng thái trông tốt hơn.

### P2 — Contract và quy tắc schema còn nhiều nguồn khai báo

Không thấy Python/JavaScript/CI trực tiếp đọc `metadata/schema_contract.yaml`; runtime thực thi manifest/profile cùng các hằng số trong `scripts/bronze_silver.py:24`, `src/silver.py:9` và luồng Fabric. `src/run_contract.py:65` seal metadata JSON, không seal YAML.

**Ảnh hưởng:** sửa YAML không làm validator đổi theo; các runtime có nguy cơ lệch rule trong tương lai. Chưa phát hiện dữ liệu hiện tại bị xử lý sai vì điều này.

**Cần làm:** ghi rõ YAML là tài liệu hay executable contract. Nếu là executable contract, parse và validate nó, đưa vào integrity context; dùng chung schema/null/typing rules phù hợp giữa các runtime.

### P2 — Phân tích và dashboard còn dư địa hoàn thiện

- Các gap measure và `Executive Insight` ở `SM_EV_Analytics.SemanticModel/definition/tables/EV Respondents.tmdl:88,143` kiểm tra BLANK nhưng chưa có ngưỡng cỡ mẫu. Sau nhiều slicer, nhóm rất nhỏ vẫn có thể được xếp hạng gap. Thêm N cho hai phía, cảnh báo/ẩn xếp hạng khi thiếu mẫu; ngưỡng phải được giải thích.
- Chưa có decision memo riêng nối phát hiện → quyết định giả định → rủi ro → cách đo tiếp theo. Thêm phân tích phân tầng income/city/age để xem liên hệ subsidy/charging còn giữ như thế nào. Đây vẫn là mô tả trên synthetic data, không thành bằng chứng nhân quả.
- Ba ảnh cho thấy bố cục và màu nhất quán, nhưng nhiều SVG/matrix có scrollbar; bubble có điểm/nhãn sát nhau và biểu đồ hai trục cần đọc cẩn thận. Chỉnh khả năng đọc ở kích thước màn hình thông dụng, rồi kiểm tra Desktop/Service.

### P2 khi mở rộng sang production — Phạm vi hiện tại là snapshot có kiểm soát

Checksum, target distribution và Gold expected metrics pin một snapshot cố định; `scripts/recovery_common.py:8` và release guard cũng pin Gold run. Đây là lựa chọn hợp lý cho regression và portfolio. Chưa chứng minh tiếp nhận dữ liệu hợp lệ mới, schema evolution hoặc promotion tổng quát.

Airflow `failure_alert` tại `dags/ev_analytics_phase10.py:17` chỉ ghi log. Chưa có bằng chứng notification tới người nhận, diễn tập live rollback cho release hiện hành, backup độc lập ngoài máy, RTO/RPO đo được hoặc benchmark chi phí/hiệu năng.

Các mục này cần trước khi tuyên bố production readiness; không phải tất cả đều là điều kiện bắt buộc để đưa dự án junior vào portfolio.

### P3 — Nguồn dữ liệu và cách bàn giao

`docs/data_access.md:11` công khai rằng chưa đối chiếu fresh official Kaggle download. Hash local khớp chỉ xác nhận snapshot. Nên hoàn thành đối chiếu và ghi nguồn/version rõ hơn; tiếp tục không đưa raw data lên Git. Repo chưa có LICENSE cho mã nguồn; có thể bổ sung nếu muốn người khác tái sử dụng, sau khi chọn phạm vi phù hợp.

## Điểm mạnh cần giữ và cách ghi portfolio

- Respondent grain rõ; train có nhãn tách khỏi test/reference; không biến purchase intent thành sales/revenue.
- Một fact, năm dimensions, 29 measures; hai aggregate audit nằm ngoài model để tránh đếm lặp.
- Chặn publication khi quality chưa đạt; kiểm tra checksum/context trước retry; có kiểm tra corruption và reconstruction thay vì chỉ kiểm tra row count.
- Unit, Spark và Airflow là ba gate riêng, không coi skip là pass; release chỉ xuất sau khi cả ba đạt. Azure main có blocking build policy.
- Test CD có manifest, kiểm tra commit/build, rollback definitions, binding, refresh, KPI và report readback; evidence đúng commit hiện tại đã được xác minh.

Cách mô tả phù hợp:

> Built an EV purchase-intent analytics project over 668,665 synthetic records using Microsoft Fabric, PySpark and Power BI; implemented a star schema, data-quality gates and Azure DevOps CI/CD with 129 passing tests and verified Test deployment.

Không ghi đã tăng doanh thu/conversion, xử lý dữ liệu realtime, đạt SLA production, hoặc chứng minh nhu cầu thị trường thực tế khi chưa có evidence tương ứng.

Ưu tiên tiếp theo: đóng quy ước generator/binding → xác minh lại live health → đồng bộ tài liệu → bổ sung phân tích có điều kiện, decision memo và cỡ mẫu. Có thể ứng tuyển trong khi tiếp tục hoàn thiện các mục này.

## Artifact của đợt review

Thư mục local được Git ignore: `output/review-20261028/`.

- `static-review.json`, `rebuild-check.json`, `independent-kpi.json`, `security-screen.json`.
- `ci84/{unit,spark,airflow}/`: báo cáo JSON/JUnit tải từ Azure.
- `cd85/`: deployment/health/readback và rollback evidence tải từ Azure.
- `tests/`: lần chạy dependency chưa đủ; `tests-fixed/` và `unit-fixed.log`: 118 unit passed.
- `live-health.json`: lưu cả checks đã đạt và lỗi HTTP 401; không phải full pass.
- `rebuild-source/`: bản sao riêng dùng thử generator; `venv/`: môi trường review riêng.

Không commit artifact, venv, raw data hoặc bản sao rebuild. Báo cáo này không sửa hai tài liệu review cũ đang untracked.


## Theo dõi phần 2 — 29/10/2026

Đã xác minh lại KPI live lúc **07:57 ngày 29/10/2026 (Asia/Bangkok)** bằng danh tính
người dùng Azure CLI hiện tại và backend JSON `executeQueries`: binding, latest
refresh và KPI đều passed; 668.665 respondents, 116.779 Yes, 551.886 No. Refresh
gần nhất vẫn là ngày 22/10; lần kiểm tra này không deploy hay khởi tạo refresh.

Với cùng client/token, backend Arrow `executeDaxQueries` vẫn trả HTTP 401. Audience
đúng và token còn hạn tại thời điểm thử; nguyên nhân riêng của lỗi Arrow chưa xác
định. Không sửa quyền hay hạ gate, không tự động fallback. Đường kiểm tra KPI từ
máy này đã được xác minh qua JSON; không gọi Arrow hoặc service principal là đã
được xác minh lại. Quyền ACL/Build chưa được liệt kê độc lập.

Evidence mới: [live_health_20261029.json](evidence/live_health_20261029.json).
Cách chọn backend và phạm vi kiểm chứng: [operations runbook](operations/operations_runbook.md).
Bốn test health và năm test Arrow decoder đều passed, không skip. Các helper health
và config Test không đổi so với HEAD `48fa1fe`; working tree còn nhiều thay đổi khác,
nên kết quả này không nghiệm thu toàn bộ code/report đang chỉnh sửa.

Các quan sát ngày 28/10 ở trên được giữ nguyên như bằng chứng lịch sử.

## Theo dõi phần 3 — 29/10/2026

Đã đồng bộ [README](../README.md), [validation overview](validation.md),
[CI/CD history](cicd_evidence.md), [mục lục evidence](evidence/README.md) và
[hướng dẫn CD](deployment/test_cd.md) với các bằng chứng theo thời điểm:

- Service UAT đại diện thuộc release CI #67/CD #70 ngày 17/10, không được tự động mở rộng sang release sau.
- Artifact CI #84/CD #85 ngày 22/10 trên `48fa1fe` ghi nhận 129 test passed, không skip, cùng deployment/binding/refresh/KPI passed; hash của các báo cáo gốc đã được đối chiếu lại.
- Probe ngày 28/10 vẫn là lần Arrow lỗi 401. Ngày 29/10 JSON live passed, Arrow cùng token vẫn 401; không gọi đây là deploy, refresh mới hay xác minh lại service principal.
- SQL analytics endpoint, mọi tổ hợp tương tác và nghiệm thu các thay đổi code/report chưa commit vẫn chưa được xác minh.

Đã bỏ mô tả release 17/10 là release hiện hành trong hướng dẫn CD và sửa thứ tự
thời gian của release 14/10. Evidence JSON lịch sử được giữ nguyên. Lượt này chỉ
sửa tài liệu; không chạy lại pipeline, deploy hay tạo bằng chứng UAT mới. Không
khẳng định các build online mới nhất: truy vấn Azure CLI trong lượt này bị chặn
khi đọc cấu hình cục bộ. Các build và trạng thái được ghi theo evidence đã kiểm chứng.
