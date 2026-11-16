#!/usr/bin/env python3
"""
Script nghiệm thu Giai đoạn 1:
1. Kiểm tra data/chunks.json (đủ 108 chunks, đúng schema).
2. Kiểm tra kết nối API Key và khởi tạo DenseRetriever.
3. Thực hiện 1 truy vấn kiểm thử với mô hình embedding thật và in top-3 chunks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Thêm đường dẫn gốc để import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dense_retriever import DenseRetriever


def verify():
    print("=" * 60)
    print("      KIỂM TRA & NGHIỆM THU GIAI ĐOẠN 1 (STAGE 1 DoD)      ")
    print("=" * 60)

    # 1. Kiểm tra file chunks
    chunks_path = Path("data/chunks.json")
    print("\n[Bước 1/3] Kiểm tra file data/chunks.json...")
    if not chunks_path.exists():
        print("❌ THẤT BẠI: Không tìm thấy file data/chunks.json")
        sys.exit(1)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    if len(chunks) != 108:
        print(f"❌ THẤT BẠI: Số lượng chunks là {len(chunks)}, kỳ vọng đúng 108.")
        sys.exit(1)

    required_keys = ("id", "source_id", "source", "page", "text", "metadata")
    for c in chunks:
        for k in required_keys:
            if k not in c or c[k] is None:
                print(f"❌ THẤT BẠI: Chunk {c.get('id')} thiếu trường {k}")
                sys.exit(1)

    print(f"✅ ĐẠT: 108 chunks hợp lệ đầy đủ schema Day 7 (từ {chunks[0]['id']} đến {chunks[-1]['id']}).")

    # 2. Khởi tạo DenseRetriever
    print("\n[Bước 2/3] Khởi tạo DenseRetriever & kiểm tra API Key...")
    try:
        retriever = DenseRetriever(chunks_path=chunks_path)
    except ValueError as e:
        print(f"❌ CHƯA CẤU HÌNH API KEY: {e}")
        print("👉 Vui lòng mở file .env và điền OPENROUTER_API_KEY hoặc OPENAI_API_KEY.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ LỖI KHỞI TẠO: {e}")
        sys.exit(1)

    print(f"✅ ĐẠT: Kết nối thành công mô hình {retriever.model_name} ({retriever.dimensions} dims).")

    # 3. Chạy truy vấn thực tế
    print("\n[Bước 3/3] Thực hiện truy vấn kiểm thử với embedding thật...")
    test_query = "What was documented in the International Debt Report 2025 regarding external debt burdens?"
    print(f"Query: \"{test_query}\"")

    try:
        results = retriever.search(test_query, top_k=3)
    except Exception as e:
        print(f"❌ LỖI TRUY VẤN: {e}")
        sys.exit(1)

    print(f"\nTop-{len(results)} kết quả tìm kiếm:")
    for idx, r in enumerate(results, start=1):
        print(f"  [{idx}] ID: {r['id']} | Page: {r['page']} | Score: {r['score']}")
        print(f"      Trích đoạn: {r['text'][:120]}...\n")

    assert len(results) > 0, "Không trả về kết quả nào"
    assert results[0]["page"] == 75, f"Kỳ vọng kết quả top 1 ở trang 75, nhận được trang {results[0]['page']}"

    print("=" * 60)
    print("BẠN ĐÃ HOÀN THÀNH TOÀN BỘ NGHIỆM THU GIAI ĐOẠN 1!")
    print("=" * 60)


if __name__ == "__main__":
    verify()
