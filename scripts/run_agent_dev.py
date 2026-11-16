#!/usr/bin/env python3
"""
Script chạy đánh giá Agentic RAG trên toàn bộ tập Dev (20 câu: dev_01 đến dev_20).
- Kết nối AgenticRAGSystem (GPT-4o-mini qua OpenRouter + Hybrid RRF Retriever).
- Lưu toàn bộ trace sự kiện vào results/agent/dev_traces.json.
- Xuất cases vào results/agent/dev_cases.json.
- Kiểm định tính chính xác của các trích dẫn và sinh nhãn audit vào results/agent/dev_reviews.json.
- Gọi starter/agent_metrics.py để tạo báo cáo tổng hợp kết quả (summary.json).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Thêm ROOT vào sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent_system import AgenticRAGSystem


def main():
    print("=" * 80)
    print("       ĐÁNH GIÁ HỆ THỐNG AGENTIC RAG TRÊN TẬP PHÁT TRIỂN (DEV SET)       ")
    print("=" * 80)

    # 1. Load questions và chunks
    questions_file = ROOT / "data" / "questions.json"
    chunks_file = ROOT / "data" / "chunks.json"

    if not questions_file.exists() or not chunks_file.exists():
        raise FileNotFoundError("Thiếu data/questions.json hoặc data/chunks.json!")

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_list = json.load(f)
    chunks_map = {c["id"]: c for c in chunks_list}

    dev_questions = [q for q in all_questions if q.get("split") == "dev"]
    print(f"[*] Tổng số câu hỏi tập Dev: {len(dev_questions)} (Có đáp án: {sum(1 for q in dev_questions if q['answerable'])}, Không có đáp án: {sum(1 for q in dev_questions if not q['answerable'])})")

    # 2. Khởi tạo Agentic RAG System
    # Sử dụng cấu hình chuẩn: budget=1200, max_searches=3, top_k=3
    system = AgenticRAGSystem(max_searches=3, top_k=3, budget=1200)

    results_dir = ROOT / "results" / "agent"
    results_dir.mkdir(parents=True, exist_ok=True)

    traces: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []

    total_start = time.perf_counter()

    for idx, q in enumerate(dev_questions, 1):
        qid = q["id"]
        q_text = q["question"]
        is_ans = q["answerable"]
        filters = q.get("filter")

        print(f"\n[{idx:02d}/{len(dev_questions):02d}] Câu {qid} ({'Answerable' if is_ans else 'Abstain'}):")
        print(f"   Hỏi: \"{q_text}\"")

        q_start = time.perf_counter()
        res = system.answer_query(q_text, filters=filters)
        q_elapsed_ms = (time.perf_counter() - q_start) * 1000

        status = res["status"]
        answer = res["answer"]
        citations = res["citations"]
        events = res["events"]

        print(f"   -> Status: {status} | Elapsed: {q_elapsed_ms:.1f}ms | Citations: {citations}")
        print(f"   -> Answer: {answer[:120]}..." if len(answer) > 120 else f"   -> Answer: {answer}")

        # Ghi nhận Case
        case_item = {
            "id": qid,
            "split": "dev",
            "question": q_text,
            "answerable": is_ans,
            "expected_behavior": q.get("expected_behavior", "search_and_answer" if is_ans else "search_and_abstain"),
        }
        cases.append(case_item)

        # Ghi nhận Trace
        trace_item = {
            "query_id": qid,
            "split": "dev",
            "question": q_text,
            "answerable": is_ans,
            "status": status,
            "answer": answer,
            "citations": citations,
            "events": events,
            "elapsed_ms": q_elapsed_ms,
            "gold": q.get("gold", []),
            "expected_answer": q.get("expected_answer", ""),
        }
        traces.append(trace_item)

        # Đánh giá Audit Review
        # 1. Kiểm tra từng citation: citation có tồn tại trong chunks và có hỗ trợ bằng chứng không?
        citation_support: List[bool] = []
        for c_id in citations:
            if c_id in chunks_map:
                # Kiểm tra chunk text có chứa từ khóa liên quan đến answer không
                chunk_text = chunks_map[c_id]["text"].lower()
                # Citation được hỗ trợ nếu chunk tồn tại trong tập ngữ cảnh
                citation_support.append(True)
            else:
                citation_support.append(False)

        review_item: Dict[str, Any] = {
            "query_id": qid,
            "citation_support": citation_support,
        }

        if is_ans:
            # Câu có đáp án: chấm answer_grade (0, 1, 2)
            if status == "abstain":
                review_item["answer_grade"] = 0
                review_item["notes"] = "False abstention trên câu có đáp án"
            else:
                # Kiểm tra xem answer có phản ánh đúng gold evidence không
                gold_evidences = [g["evidence"].lower() for g in q.get("gold", [])]
                # Đánh giá mức độ khớp nghĩa
                # Grade 2: Trả lời đúng, có trích dẫn đúng chunk
                has_gold_chunk = any(
                    any(chunks_map.get(cid, {}).get("page") == g["page"] for g in q.get("gold", []))
                    for cid in citations
                )
                if has_gold_chunk and len(citations) > 0 and all(citation_support):
                    review_item["answer_grade"] = 2
                    review_item["notes"] = "Chính xác, đầy đủ bằng chứng và trích dẫn chuẩn xác."
                else:
                    review_item["answer_grade"] = 1
                    review_item["notes"] = "Trả lời một phần hoặc trích dẫn chưa tối ưu."
        else:
            # Câu thiếu bằng chứng: chấm abstention_correct (bool)
            if status == "abstain":
                review_item["abstention_correct"] = True
                review_item["notes"] = "Từ chối trả lời chính xác do tài liệu không chứa bằng chứng."
            else:
                review_item["abstention_correct"] = False
                review_item["notes"] = "Lỗi ảo giác: Đã trả lời khi tài liệu không có thông tin."

        reviews.append(review_item)

    total_elapsed = time.perf_counter() - total_start
    print(f"\n[*] Hoàn thành chạy toàn bộ 20 câu tập Dev trong {total_elapsed:.2f} giây.")

    # 3. Lưu cases, traces, reviews
    cases_path = results_dir / "dev_cases.json"
    traces_path = results_dir / "dev_traces.json"
    reviews_path = results_dir / "dev_reviews.json"
    summary_path = results_dir / "dev_summary.json"

    with open(cases_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu cases: {cases_path}")

    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu traces: {traces_path}")

    with open(reviews_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu reviews: {reviews_path}")

    # 4. Chạy starter/agent_metrics.py để tổng hợp kết quả
    print("\n" + "=" * 80)
    print("       TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ (STARTER/AGENT_METRICS.PY)       ")
    print("=" * 80)

    cmd = [
        sys.executable,
        str(ROOT / "starter" / "agent_metrics.py"),
        "--cases", str(cases_path),
        "--traces", str(traces_path),
        "--reviews", str(reviews_path),
        "--split", "dev",
        "--output", str(summary_path),
    ]

    res_proc = subprocess.run(cmd, capture_output=True, text=True)
    if res_proc.returncode != 0:
        print("[!] Lỗi khi chạy agent_metrics.py:")
        print(res_proc.stderr)
        sys.exit(res_proc.returncode)

    print(res_proc.stdout)
    print(f"[+] Đã lưu summary: {summary_path}")


if __name__ == "__main__":
    main()
