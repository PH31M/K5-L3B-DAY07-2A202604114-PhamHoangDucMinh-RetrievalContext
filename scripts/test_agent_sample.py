#!/usr/bin/env python3
"""
Kiểm thử mẫu nghiệm thu Agentic System (Stage 4 DoD):
1. Ca 1 (Answerable): Câu hỏi có bằng chứng -> Trả lời kèm trích dẫn chính xác [chunk-id].
2. Ca 2 (Unanswerable): Câu hỏi thiếu bằng chứng -> Tự động từ chối (Abstain).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Thêm đường dẫn gốc để import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent_system import AgenticRAGSystem


def main():
    print("=" * 70)
    print("       KIỂM THỬ MẪU AGENTIC SYSTEM (STAGE 4 DoD)       ")
    print("=" * 70)

    system = AgenticRAGSystem(max_searches=3, top_k=3, budget=1200)

    # -------------------------------------------------------------
    # CA 1: CÂU HỎI CÓ ĐÁP ÁN (dev_01)
    # -------------------------------------------------------------
    q_ans = "What was documented in the International Debt Report 2025 regarding external debt burdens?"
    print(f"\n[CA 1 - ANSWERABLE] Câu hỏi: \"{q_ans}\"")
    print("-> Đang chạy Agent loop...")
    res_ans = system.answer_query(q_ans, filters={"section": "transmission_shocks"})

    print(f"Status: {res_ans['status']}")
    print(f"Answer: {res_ans['answer']}")
    print(f"Citations: {res_ans['citations']}")
    print(f"Số lượng events: {len(res_ans['events'])}")
    for e in res_ans["events"]:
        print(f"   - Event: {e.get('event')} | Query: {e.get('query')}")

    assert res_ans["status"] == "answered", f"Kỳ vọng status 'answered', nhận được {res_ans['status']}"
    assert len(res_ans["citations"]) > 0, "Kỳ vọng có ít nhất 1 citation hợp lệ"
    assert "bookdata_01_p75_b001" in res_ans["citations"], "Kỳ vọng citation chứa chunk bookdata_01_p75_b001"
    print("✅ CA 1 ĐẠT: Agent đã tìm kiếm và trả lời chính xác kèm citation!")

    # -------------------------------------------------------------
    # CA 2: CÂU HỎI THIẾU BẰNG CHỨNG (dev_16)
    # -------------------------------------------------------------
    q_abs = "What was the exact central bank policy interest rate of the Bank of Ghana in December 2025?"
    print(f"\n[CA 2 - ABSTAIN] Câu hỏi: \"{q_abs}\"")
    print("-> Đang chạy Agent loop...")
    res_abs = system.answer_query(q_abs)

    print(f"Status: {res_abs['status']}")
    print(f"Answer: {res_abs['answer']}")
    print(f"Citations: {res_abs['citations']}")
    print(f"Số lượng events: {len(res_abs['events'])}")
    for e in res_abs["events"]:
        print(f"   - Event: {e.get('event')} | Query: {e.get('query')}")

    assert res_abs["status"] == "abstain", f"Kỳ vọng status 'abstain', nhận được {res_abs['status']}"
    assert len(res_abs["citations"]) == 0, f"Kỳ vọng không có citations nào, nhận được {res_abs['citations']}"
    print("✅ CA 2 ĐẠT: Agent nhận diện không đủ bằng chứng và tự động từ chối (Abstain) chuẩn xác!")

    print("\n" + "=" * 70)
    print("🎉 TẤT CẢ CÁC CA KIỂM THỬ MẪU CỦA GIAI ĐOẠN 4 ĐÃ ĐẠT CHUẨN!")
    print("=" * 70)


if __name__ == "__main__":
    main()
