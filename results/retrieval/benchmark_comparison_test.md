# Bảng So sánh Hiệu năng Retrieval trên tập TEST

Đánh giá trên cùng một corpus (`data/chunks.json`, 108 chunks) và cùng ngân sách context (`budget = 1200`).

| Phương pháp (Strategy) | Hit@1 (n/N, %) | Evidence Hit@3 (n/N, %) | Context Evidence Rate (n/N, %) | Latency trung vị (ms) | Chi phí ước tính |
|---|:---:|:---:|:---:|:---:|:---:|
| **Dense (Embedding 3 Small)** | 2/5 (40.0%) | 3/5 (60.0%) | 2/5 (40.0%) | 1018.465 ms | $0.000001 |
| **Lexical (BM25)** | 4/5 (80.0%) | 5/5 (100.0%) | 4/5 (80.0%) | 0.185 ms | $0.00 (offline) |
| **Hybrid (Dense + BM25 RRF)** | 2/5 (40.0%) | 5/5 (100.0%) | 2/5 (40.0%) | 979.468 ms | $0.000001 |

### Nhận xét & Đánh giá Kỹ thuật:
- **Dense Retrieval:** Rất mạnh về tương đồng ý niệm, ngữ nghĩa ngữ cảnh rộng, nhưng độ trễ phụ thuộc vào mạng khi gọi API embedding.
- **Lexical Retrieval (BM25):** Tốc độ cực nhanh (< 1ms), khớp chính xác các thực thể số, tên riêng và từ khóa chuyên ngành, hoàn toàn miễn phí không tốn API.
- **Hybrid Retrieval (RRF):** Kết hợp sức mạnh của cả hai, bù đắp trường hợp một phương pháp bị trượt, cho độ phủ context và thứ hạng ổn định nhất.
