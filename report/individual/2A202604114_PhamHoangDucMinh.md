# Báo cáo Day 7 — Agentic RAG & Context Engineering

**Học viên:** Phạm Hoàng Đức Minh  
**Mã số sinh viên (MSSV):** 2A202604114  
**Lớp:** L3B  
**Repository:** `K5-L3B-DAY07-2A202604114-PhamHoangDucMinh-RetrievalContext`  

---

## Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:**
  - Tài liệu gốc: *World Bank International Debt Report 2026* (`bookdata_01.pdf` / `bookdata_full.pdf`), ấn bản công khai chính thức của World Bank Group, giấy phép Open Knowledge / CC BY 3.0 IGO.
  - Phần cơ bản (Giai đoạn 1–6): Kế thừa trực tiếp từ Day 6 (Chương 2 "Debt Dynamics: Policy Implications", số trang vật lý 75–106, tổng cộng 32 trang). Trích xuất chính xác **108 chunks** theo Chiến lược B Day 6 (`by_paragraph`, `max_size=800` ký tự, ghép câu khoảng trắng chuẩn xác). Lưu trữ tại `data/chunks.json`.
  - Thử thách nâng cao (Giai đoạn 7): Toàn văn tài liệu gồm **280 trang**, được trích xuất thành **270 chunks đa phương thức** (130 bảng biểu, 44 biểu đồ, 15 sơ đồ, 81 văn bản). Lưu trữ tại `data/multimodal_chunks.json`.
- **Vector store, embedding model, phiên bản và số chiều:**
  - Embedding model: `openai/text-embedding-3-small` phiên bản mới nhất, kết nối API qua OpenRouter/OpenAI.
  - Số chiều vector: **1536 chiều**. Tuyệt đối không sử dụng vector giả lập hoặc ngẫu nhiên.
  - Vector cache lưu trữ tại `data/embeddings_cache.json` (3.2 MB cho 108 chunks) và `data/multimodal_embeddings_cache.json` (3.3 MB cho 270 chunks).
- **Agent model, cách chạy và phân chia dev/test:**
  - LLM Controller: `openai/gpt-4o-mini` qua OpenRouter API với cấu hình `temperature=0.0`, định dạng đầu ra `response_format={"type": "json_object"}` và tích hợp cơ chế retry tự động chống ngắt kết nối.
  - Phân chia benchmark chuẩn (30 câu):
    - **Tập Dev (20 câu)**: 15 câu có đáp án (`dev_01` – `dev_15`) và 5 câu thiếu bằng chứng (`dev_16` – `dev_20`).
    - **Tập Test (10 câu)**: 5 câu có đáp án (`test_01` – `test_05`) và 5 câu thiếu bằng chứng (`test_06` – `test_10`).
- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:**
  - *Câu có đáp án (Answerable)*: Toàn bộ câu hỏi đều có bằng chứng trích dẫn thực tế (`gold evidence`) nằm trọn vẹn trong chunk tương ứng với đúng `source_id`, `page` và đoạn văn nguyên bản. Chấm điểm theo rubric 3 mức: Grade 2 (trả lời đúng và trích dẫn chuẩn xác chunk chứa bằng chứng), Grade 1 (trả lời đúng một phần hoặc trích dẫn chưa tối ưu), Grade 0 (trả lời sai, ảo giác hoặc từ chối nhầm - False Abstention).
  - *Câu thiếu bằng chứng (Unanswerable/Abstain)*: Các câu hỏi gần chủ đề kinh tế vĩ mô nhưng thông tin hoàn toàn không có trong tài liệu (lãi suất điều hành ngân hàng trung ương cụ thể, tỷ lệ vỡ nợ doanh nghiệp tư nhân, viện trợ song phương chi tiết từng tháng). Đạt chuẩn khi Agent tự động nhận diện và từ chối trả lời (`status: "abstain"`), không phát sinh ảo giác.

---

## Retrieval và thử nghiệm

### Bảng So sánh Hiệu năng Retrieval trên Dev và Test

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **Baseline** | TF-IDF, $k=3$, filter section, budget 1200 | Khớp từ khóa thô TF-IDF không có rerank | dev | 11/15 (73.3%) | 15/15 (100.0%) | 12/15 (80.0%) | 0.15 ms / $0.00 |
| **Phương pháp 2** | BM25 Okapi ($k_1=1.5, b=0.75$), $k=3$, budget 1200 | Trọng số hóa tần suất từ và chuẩn hóa độ dài chunk | dev | 13/15 (86.7%) | 15/15 (100.0%) | 13/15 (86.7%) | 0.22 ms / $0.00 |
| **Phương pháp 3** | Dense Embedding (text-embedding-3-small, 1536d), $k=3$, budget 1200 | Tìm kiếm tương đồng ngữ nghĩa bằng Cosine Similarity | dev | 12/15 (80.0%) | 15/15 (100.0%) | 12/15 (80.0%) | 1072 ms / $0.000003 |
| **Cải thiện 1** | Hybrid RRF ($k_{rrf}=60$), $k=3$, filter section, budget 1200 | Kết hợp Dense và BM25 bằng Reciprocal Rank Fusion | dev | 14/15 (93.3%) | 15/15 (100.0%) | 14/15 (93.3%) | 1035 ms / $0.000003 |
| **Cải thiện 2 (Chốt)** | Hybrid RRF ($k_{rrf}=60$), $k=3$, budget 2400 | Mở rộng context budget lên 2400 ký tự | dev | **14/15 (93.3%)** | **15/15 (100.0%)** | **15/15 (100.0%)** | 1040 ms / $0.000003 |
| **Cấu hình đã chọn** | Hybrid RRF ($k_{rrf}=60$), $k=3$, budget 2400 | Cấu hình chiến thắng đóng băng chạy trên Test | test | 2/5 (40.0%) | **5/5 (100.0%)** | **5/5 (100.0%)** | 980 ms / $0.000001 |
| **Baseline** | TF-IDF, $k=3$, budget 1200 | Chạy đối chiếu Baseline trên Test | test | 3/5 (60.0%) | 4/5 (80.0%) | 3/5 (60.0%) | 0.18 ms / $0.00 |

### Phân tích lỗi Dev, nguyên nhân và lý do chọn cấu hình:
1. **Lỗi 1 (`dev_10` - Câu hỏi về nhu cầu tài chính tổng thể GFNs 2024–2025)**:
   - *Hiện tượng*: Bộ truy xuất tìm được đúng chunk chứa số liệu (`bookdata_01_p86_b000`) ở vị trí rank 2. Tuy nhiên, hàm `pack_context` với `budget=1200` đã loại bỏ chunk rank 2 này do chunk rank 1 đã chiếm 876 ký tự ($876 + 824 = 1700 > 1200$). Agent nhận ngữ cảnh bị cắt cụt và từ chối nhầm (False Abstention).
   - *Cách khắc phục*: Mở rộng `budget` lên 2400 ký tự (Cải thiện 2) cho phép đóng gói đủ cả 3 chunks hàng đầu. Kết quả `dev_10` đạt điểm tối đa Grade 2 với trích dẫn chính xác.
2. **Lỗi 2 (`dev_04` - Cơ chế nợ ngoại tệ làm tăng tổn thương kinh tế)**:
   - *Hiện tượng*: Tương tự, chunk vàng chứa cơ chế phá giá tiền tệ (`bookdata_01_p78_b000`) nằm ở rank 2 bị cắt bỏ bởi `budget=1200`. LLM chỉ nhận chunk rank 1 ở trang 75 nên câu trả lời thiếu cơ chế cốt lõi và chỉ đạt Grade 1.
   - *Cách khắc phục*: Khi nâng budget lên 2400, chunk trang 78 được nạp trọn vẹn vào context, câu trả lời đạt điểm tối đa Grade 2.
3. **Lý do chọn cấu hình Hybrid RRF ($k=3, budget=2400$)**:
   - BM25 bắt chính xác các thực thể số và tên viết tắt (IDA, IBRD, 9.4 trillion), trong khi Dense bắt rất tốt các khái niệm trừu tượng (vulnerability, debt dynamics).
   - RRF kết hợp thứ hạng không bị lệch thang điểm số (calibration), đẩy Hit@3 lên 100% trên cả Dev và Test, đồng thời ngân sách 2400 ký tự giải quyết dứt điểm nút thắt cổ chai cắt xén ngữ cảnh.

---

## Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:**
  - Tool tra cứu: `search(query, top_k=3, filters)`. Agent tự động sinh query rút gọn, giữ lại các thực thể phân biệt.
  - Số lượt gọi tối đa: `max_searches = 3`.
  - Điều kiện dừng: Khi Agent tìm đủ bằng chứng để trả lời kèm citation `[chunk-id]`, hoặc đạt giới hạn lượt gọi (`search_limit`), hoặc xác định câu hỏi không có bằng chứng (`abstain`).
  - Chọn context: Ngữ cảnh lũy kế qua các lượt tìm kiếm được khử trùng lặp và đóng gói qua `pack_context(candidates, budget=2400)`.
  - Xử lý lỗi: Tích hợp retry tự động (3 lần, exponential backoff) chống ngắt kết nối HTTP 429/timeout; nghiêm cấm fallback sang dữ liệu giả lập.

### Bảng So sánh Hiệu năng Agent trên Dev và Test

| Cấu hình / split | Tool use | Số lượt gọi TB | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline Dev (b=1200)** | 20/20 (100%) | 1.05 | 0: 1 \| 1: 1 \| 2: 13 (Mean: **1.80**) | 14/14 (100%) | 14/14 (100%) | 5/5 (100%) | 1/15 (6.67%) |
| **Cải thiện 1 Dev (b=2400)** ★ | 20/20 (100%) | 1.00 | 0: 0 \| 1: 0 \| 2: 15 (Mean: **2.00**) | 15/15 (100%) | 15/15 (100%) | 5/5 (100%) | **0/15 (0.0%)** |
| **Cải thiện 2 Dev (k=5, b=3600)** | 20/20 (100%) | 1.00 | 0: 0 \| 1: 0 \| 2: 15 (Mean: **2.00**) | 16/16 (100%) | 15/15 (100%) | 5/5 (100%) | 0/15 (0.0%) |
| **Baseline Test (b=1200)** | 10/10 (100%) | 1.00 | 0: 0 \| 1: 3 \| 2: 2 (Mean: **1.40**) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 0/5 (0.0%) |
| **Cấu hình đã chọn Test** ★ | 10/10 (100%) | 1.00 | 0: 0 \| 1: 0 \| 2: 5 (Mean: **2.00**) | 6/6 (100%) | 5/5 (100%) | 5/5 (100%) | **0/5 (0.0%)** |

### Bảng Mẫu Traces Chi tiết theo Từng Query ID (Tập Test)

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| `test_01` | Conditional | `search(query="external disruptions import dependent economies")` $\to$ `['bookdata_01_p77_b000']` | Production shortfalls in major supplier countries, export restrictions, or supply chain disruptions make import-dependent economies vulnerable [bookdata_01_p77_b000]. | Grade 2: Khớp 100% gold evidence trang 77. |
| `test_02` | Direct | `search(query="drops global commodity prices LMICs")` $\to$ `['bookdata_01_p82_b000']` | Drops in global commodity prices reduce export earnings and profits, worsening fiscal positions and current account balances [bookdata_01_p82_b000]. | Grade 2: Khớp 100% gold evidence trang 82. |
| `test_03` | Direct | `search(query="events pandemic shock elevated financing needs IDA")` $\to$ `['bookdata_01_p86_b000']` | The commodity price and inflation surge following the Russian invasion of Ukraine, and sharp monetary tightening beginning in 2022 elevated financing needs [bookdata_01_p86_b000]. | Grade 2: Khớp 100% gold evidence trang 86. |
| `test_04` | Conditional | `search(query="fiscal consolidation delay primary deficit debt stabilizing")` $\to$ `['bookdata_01_p93_b001']` | Countries typically waited three to four years before embarking on meaningful fiscal consolidation [bookdata_01_p93_b001]. | Grade 2: Khớp 100% gold evidence trang 93. |
| `test_05` | Direct | `search(query="reserve mechanisms financial instruments post-disaster fiscal")` $\to$ `['bookdata_01_p95_b000', 'bookdata_01_p95_b001']` | Contingency reserves in annual budget, natural disaster funds with clear usage rules, and state-contingent debt instruments [bookdata_01_p95_b000] [bookdata_01_p95_b001]. | Grade 2: Trích dẫn kép chính xác cả 2 chunk bổ trợ trang 95. |
| `test_06` | Abstain | `search(query="local-currency green bonds government of Indonesia 2025")` $\to$ Không có bằng chứng | Không đủ bằng chứng để trả lời. | Abstention đúng: Báo cáo không có dữ liệu trái phiếu xanh Indonesia. |
| `test_07` | Abstain | `search(query="CPI headline inflation rate Argentina September 2026")` $\to$ Không có bằng chứng | Không đủ bằng chứng để trả lời. | Abstention đúng: Báo cáo chỉ có số liệu đến tháng 6/2026. |
| `test_08` | Abstain | `search(query="mathematical weighting formula IMF SDR interest rate 2026")` $\to$ Không có bằng chứng | Không đủ bằng chứng để trả lời. | Abstention đúng: Báo cáo không có công thức tính SDR. |
| `test_09` | Abstain | `search(query="metric tons milling wheat Egypt Romania August 2025")` $\to$ Không có bằng chứng | Không đủ bằng chứng để trả lời. | Abstention đúng: Không có số liệu giao dịch lúa mì cụ thể. |
| `test_10` | Abstain | `search(query="primary budget surplus Pakistan IMF 2025 EFF")` $\to$ Không có bằng chứng | Không đủ bằng chứng để trả lời. | Abstention đúng: Không có chỉ tiêu ngân sách cụ thể của Pakistan. |

- **Đường dẫn artifacts, thời gian và chi phí:**
  - Traces và Reviews: `results/agent/dev_traces.json`, `results/agent/exp1_traces.json`, `results/agent/test_frozen_traces.json`.
  - Tổng hợp chỉ số: `results/agent/test_frozen_summary.json`.
  - Thời gian xử lý: ~9.5s/câu trên Dev, ~8.8s/câu trên Test. Chi phí token: ~$0.00015/câu.
- **Đánh đổi và giới hạn:**
  - Tăng context budget từ 1200 lên 2400 giúp nâng Grounded Mean từ 1.80 lên 2.00 mà độ trễ chỉ tăng nhẹ từ 6.1s lên 9.5s.
  - Tuy nhiên, tiếp tục tăng lên 3600 (`top_k=5`) làm độ trễ vọt lên 20.6s mà không đem lại thêm điểm chất lượng nào do hiệu ứng bão hòa trần (*ceiling effect*).

---

## Thử thách nâng cao (+15 điểm bonus)

- **Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:**
  - Toàn văn báo cáo *World Bank International Debt Report 2026* (`data/bookdata_full.pdf`).
  - Nguồn gốc: World Bank Open Knowledge Repository, bản công bố chính thức tháng 12/2025, dung lượng 14.3 MB, bản quyền CC BY 3.0 IGO.
  - Quy mô tài liệu: **280 trang** (đạt và vượt xa điều kiện tối thiểu 100 trang của [ADVANCED.md](file:///Users/minh/GitHub-PMinh/K5-L3B-DAY07-2A202604114-PhamHoangDucMinh-RetrievalContext/ADVANCED.md)).
- **Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:**
  - Lập chỉ mục thành công **270 chunks đa phương thức** phủ kín toàn bộ 280 trang tại `data/multimodal_chunks.json`:
    - *Bảng biểu (130 chunks)*: Trích xuất có cấu trúc Table 1.1, Table 1.2 và 128 bảng tóm tắt nợ quốc gia (Country Summary Debt Tables) tại trang 138–265.
    - *Biểu đồ (44 chunks)*: Trích xuất caption, chú giải trục tọa độ và các chuỗi số liệu của Figure X.Y.
    - *Sơ đồ (15 chunks)*: Phân tích các hộp nghiên cứu chuyên sâu (Box 1.1 đến Box 2.3) và sơ đồ cơ chế lây truyền.
    - *Văn bản (81 chunks)*: Phân đoạn nội dung phân tích vĩ mô có cấu trúc.
  - Phần loại trừ: Các trang bìa trang trí và trang danh mục tên chuyên gia tham gia soạn thảo (trang 1–4).
- **Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:**
  - Bộ benchmark gồm **48 câu hỏi** tại `data/multimodal_questions.json`:
    - Dev: 18 câu (15 có đáp án, 3 thiếu bằng chứng).
    - Test: 30 câu (24 có đáp án, 6 thiếu bằng chứng) bao phủ trọn vẹn 6 nhóm bắt buộc.
  - Model: `openai/gpt-4o-mini` qua OpenRouter kết hợp Hybrid RRF Retriever với `budget = 5000` ký tự (phù hợp với các bảng dữ liệu nợ quốc gia lớn) và bộ chuẩn hóa trích dẫn đa phần tử `[id1] [id2]`.

### Bảng Kết quả Thử nghiệm Chính thức Tập Test 30 câu

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|:---:|:---:|---|
| **Bảng (Tables)** | **6 / 6** | **100.0%** | Đọc chính xác 100% số liệu nợ của Table 1.1, Ấn Độ, Indonesia, Việt Nam, Ghana |
| **Ảnh, sơ đồ** | **4 / 5** | **80.0%** | Nhận diện đúng sơ đồ phân loại thu nhập, cơ chế ERA Ukraine, bất ổn toàn cầu |
| **Biểu đồ** | **5 / 5** | **100.0%** | Đọc chuẩn xác quỹ đạo nợ, điều kiện lãi suất, kiều hối vùng, tài sản quốc gia |
| **Multi-hop** | **4 / 4** | **100.0%** | Kết hợp dữ kiện thành công giữa 2 quốc gia hoặc giữa bảng số liệu và văn bản |
| **Text** | **4 / 4** | **100.0%** | Tổng hợp chính xác các nguyên nhân vĩ mô, rủi ro nợ ngoại tệ, giải pháp tài khóa |
| **Thiếu bằng chứng** | **6 / 6** | **100.0%** | 100% từ chối đúng các câu hỏi ngoài phạm vi báo cáo, không bị ảo giác |
| **TOÀN BỘ (OVERALL)** | **29 / 30** | **96.67%** |  **VƯỢT NGƯỠNG $\ge 90.0\%$** |

- **Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:**
  - File traces chi tiết: `results/advanced/test_traces.json`.
  - File reviews kiểm định từng câu: `results/advanced/test_reviews.json`.
  - File summary chính thức: `results/advanced/test_summary.json`.
  - Thời gian trung bình: 6.8s/câu. Chi phí: ~$0.00018/câu. Số lỗi hệ thống / provider errors: **0**.
- **Giới hạn, cách tái lập và đường dẫn benchmark:**
  - Lệnh tái lập toàn bộ: `python3 scripts/run_advanced_pipeline.py --split test`.
  - Đường dẫn benchmark: `data/multimodal_questions.json`.
  - Giới hạn: Một số biểu đồ dạng đồ thị đường không có nhãn số trực tiếp trong PDF vector cần kết hợp vision rendering để đọc giá trị điểm cực tiểu/cực đại.
