# Bảng So sánh Hiệu năng Retrieval trên tập DEV

Đánh giá trên cùng một corpus (`data/chunks.json`, 108 chunks) và cùng ngân sách context (`budget = 1200`).

| Phương pháp (Strategy) | Hit@1 (n/N, %) | Evidence Hit@3 (n/N, %) | Context Evidence Rate (n/N, %) | Latency trung vị (ms) | Chi phí ước tính |
|---|:---:|:---:|:---:|:---:|:---:|
| **Dense (Embedding 3 Small)** | 12/15 (80.0%) | 15/15 (100.0%) | 12/15 (80.0%) | 1072.117 ms | $0.000003 |
| **Lexical (BM25)** | 13/15 (86.67%) | 15/15 (100.0%) | 13/15 (86.67%) | 0.217 ms | $0.00 (offline) |
| **Hybrid (Dense + BM25 RRF)** | 14/15 (93.33%) | 15/15 (100.0%) | 14/15 (93.33%) | 1035.915 ms | $0.000003 |

### Nhận xét & Đánh giá Kỹ thuật:
- **Dense Retrieval:** Rất mạnh về tương đồng ý niệm, ngữ nghĩa ngữ cảnh rộng, nhưng độ trễ phụ thuộc vào mạng khi gọi API embedding.
- **Lexical Retrieval (BM25):** Tốc độ cực nhanh (< 1ms), khớp chính xác các thực thể số, tên riêng và từ khóa chuyên ngành, hoàn toàn miễn phí không tốn API.
- **Hybrid Retrieval (RRF):** Kết hợp sức mạnh của cả hai, bù đắp trường hợp một phương pháp bị trượt, cho độ phủ context và thứ hạng ổn định nhất.
