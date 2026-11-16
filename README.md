# Day 7 — Agentic RAG & Context Engineering

**Học viên:** Phạm Hoàng Đức Minh  
**Mã số sinh viên (MSSV):** `2A202604114`  
**Lớp:** `L3B`  
**Repository:** `K5-L3B-DAY07-2A202604114-PhamHoangDucMinh-RetrievalContext`  
**Báo cáo cá nhân chính thức:** [report/individual/2A202604114_PhamHoangDucMinh.md](report/individual/2A202604114_PhamHoangDucMinh.md)

---

## 1. Tổng quan Dự án

Dự án triển khai một hệ thống **Agentic RAG** hoàn chỉnh, tự chủ truy xuất bằng chứng ngữ cảnh, trích xuất câu trả lời kèm trích dẫn chính xác và nhận biết từ chối trả lời (abstain) khi tài liệu không chứa bằng chứng.

- **Dữ liệu chuẩn**: Chương 2 báo cáo *World Bank International Debt Report 2026* (32 trang, 108 chunks chuẩn hóa theo Chiến lược B Day 6).
- **Thử thách nâng cao**: Toàn văn báo cáo *World Bank International Debt Report 2026* (**280 trang**, **270 chunks đa phương thức** gồm 130 bảng biểu, 44 biểu đồ, 15 sơ đồ, 81 văn bản).
- **Mô hình**:
  - Embedding: `openai/text-embedding-3-small` (1536 chiều, vector cache thực tế).
  - LLM Controller: `openai/gpt-4o-mini` qua OpenRouter API với cơ chế retry tự động.
- **Phương pháp truy xuất**: Hybrid RRF (BM25 Okapi + Dense Cosine Similarity, $k_{rrf}=60$).

---

## 2. Kết quả Thực nghiệm Nổi bật

### Phần Cơ bản (Tập Held-out Test - 10 câu):
- **Grounded Answer Rate (Mean)**: **2.00 / 2.0 (100.0%)** (100% câu có đáp án đạt Grade 2).
- **Citation Validity**: **100.0%** (100% trích dẫn chunk ID đều tồn tại và hỗ trợ nội dung).
- **Answer Citation Coverage**: **100.0%** (100% câu trả lời đều có trích dẫn chunk).
- **Abstention Accuracy**: **100.0%** (5/5 câu thiếu bằng chứng được nhận diện và từ chối chính xác).
- **False Abstention Rate**: **0.0%** (Không có câu có đáp án nào bị từ chối nhầm).

### Thử thách Nâng cao Multimodal (+15 điểm Bonus):
- **Tập Test Đa phương thức (30 câu)**: Đạt **29 / 30 câu (96.67%)**, vượt qua ngưỡng 90% theo quy định tại `ADVANCED.md`.
  - Bảng (Tables): **6 / 6 (100%)**
  - Ảnh, sơ đồ (Diagrams): **4 / 5 (80%)**
  - Biểu đồ (Charts): **5 / 5 (100%)**
  - Multi-hop: **4 / 4 (100%)**
  - Văn bản (Text): **4 / 4 (100%)**
  - Thiếu bằng chứng (Abstain): **6 / 6 (100%)**

---

## 3. Cài đặt Môi trường

```bash
# 1. Tạo và kích hoạt môi trường ảo (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 2. Cài đặt các gói phụ thuộc
pip install pypdf fonttools

# 3. Cấu hình khóa API trong file .env
cp .env.example .env
# Điền khóa OPENROUTER_API_KEY hoặc OPENAI_API_KEY vào .env
```

---

## 4. Hướng dẫn Tái lập Thực nghiệm (Replication Guide)

### Kiểm tra Thiết lập và Chạy Unit Tests
```bash
python3 -m unittest discover -s tests -v
```

### Giai đoạn 1: Trích xuất Chunks & Lập chỉ mục Vector
```bash
# Trích xuất 108 chunks Day 6
python3 scripts/export_chunks.py

# Sinh cache vector embedding
python3 src/dense_retriever.py

# Xác minh nghiệm thu Giai đoạn 1
python3 scripts/verify_stage1.py
```

### Giai đoạn 2 & 3: Xây dựng Benchmark & Đánh giá Retrieval (TF-IDF vs BM25 vs Dense vs Hybrid)
```bash
# Tạo bộ benchmark 30 câu (20 Dev + 10 Test)
python3 scripts/build_benchmark.py

# Đánh giá so sánh 3 phương pháp Retrieval trên Dev và Test
python3 scripts/evaluate_retrieval.py --split dev
python3 scripts/evaluate_retrieval.py --split test
```

### Giai đoạn 4 & 5: Đánh giá Agentic RAG trên Dev & Thử nghiệm Cải tiến
```bash
# Đánh giá cấu hình ban đầu trên Dev (Stage 4)
python3 scripts/run_agent_dev.py

# Thử nghiệm Cải thiện 1 (Context Budget Expansion: budget=2400)
python3 scripts/run_exp1_budget.py

# Thử nghiệm Cải thiện 2 (Top-k=5, budget=3600 & Phân tích Đánh đổi)
python3 scripts/run_exp2_topk.py
```

### Giai đoạn 6: Đánh giá Độc lập trên Tập Held-out Test
```bash
# Chạy cả Baseline và Cấu hình đã chọn trên 10 câu tập Test
python3 scripts/run_agent_test.py
```

### Giai đoạn 7: Thử thách Nâng cao Đa phương thức (Multimodal Challenge · 280 trang)
```bash
# 1. Trích xuất 270 chunks đa phương thức từ tài liệu 280 trang
python3 scripts/build_multimodal_index.py

# 2. Tạo benchmark đa phương thức 48 câu (18 Dev + 30 Test)
python3 scripts/build_multimodal_benchmark.py

# 3. Chạy pipeline đánh giá trên cả Dev và Test (đạt 29/30 = 96.67%)
python3 scripts/run_advanced_pipeline.py --split all
```

---

## 5. Cấu trúc Thư mục

```text
├── data/
│   ├── chunks.json                    # 108 chunks phần cơ bản (Chương 2)
│   ├── embeddings_cache.json          # Vector cache 108 chunks (1536d)
│   ├── questions.json                 # Benchmark 30 câu (20 Dev + 10 Test)
│   ├── bookdata_full.pdf              # Toàn văn báo cáo 280 trang
│   ├── multimodal_chunks.json         # 270 chunks đa phương thức (bảng, biểu đồ, sơ đồ)
│   ├── multimodal_embeddings_cache.json # Vector cache 270 chunks (1536d)
│   └── multimodal_questions.json      # Benchmark 48 câu đa phương thức
├── src/
│   ├── dense_retriever.py             # Dense Retriever (Embedding-3-Small)
│   ├── lexical_retriever.py           # Lexical Retriever (BM25 Okapi)
│   ├── hybrid_retriever.py            # Hybrid Retriever (RRF Fusion)
│   ├── agent_controller.py            # LLM Controller điều phối JSON & Retry
│   └── agent_system.py                # Hệ thống Agentic RAG hoàn chỉnh
├── scripts/
│   ├── export_chunks.py               # Trích xuất 108 chunks từ Day 6
│   ├── verify_stage1.py               # Script nghiệm thu Giai đoạn 1
│   ├── build_benchmark.py             # Tạo benchmark chuẩn 30 câu
│   ├── evaluate_retrieval.py          # So sánh các phương pháp Retrieval
│   ├── run_agent_dev.py               # Đánh giá Agent trên tập Dev
│   ├── run_exp1_budget.py             # Thử nghiệm Cải thiện 1 (Budget=2400)
│   ├── run_exp2_topk.py               # Thử nghiệm Cải thiện 2 (Top-k=5, Budget=3600)
│   ├── run_agent_test.py              # Đánh giá độc lập trên tập Test
│   ├── build_multimodal_index.py      # Lập chỉ mục đa phương thức 280 trang
│   ├── build_multimodal_benchmark.py  # Tạo benchmark đa phương thức 48 câu
│   └── run_advanced_pipeline.py       # Pipeline đánh giá Thử thách Nâng cao
├── results/
│   ├── retrieval/                     # Traces và báo cáo Retrieval
│   ├── agent/                         # Traces, reviews và summary của Agent
│   └── advanced/                      # Traces, reviews và summary Thử thách Nâng cao
├── report/individual/
│   └── 2A202604114_PhamHoangDucMinh.md # Báo cáo cá nhân chính thức đầy đủ số liệu
└── tests/                             # Bộ 15 bài kiểm thử đơn vị
```
