#!/usr/bin/env python3
"""
Thử nghiệm Cải thiện 1 (Stage 5 - Exp 1): Context Budget Expansion.
- Giả thuyết: Nâng context budget từ 1200 lên 2400 ký tự sẽ giải quyết nút thắt cổ chai
  loại bỏ chunk rank 2/3 trong pack_context, giúp giải quyết triệt để lỗi của dev_04 và dev_10.
- Đầu ra:
  + results/agent/exp1_traces.json
  + results/agent/exp1_cases.json
  + results/agent/exp1_reviews.json
  + results/agent/exp1_summary.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent_system import AgenticRAGSystem


def main():
    print("=" * 80)
    print("   THỬ NGHIỆM CẢI THIỆN 1 (EXP 1): CONTEXT BUDGET EXPANSION (BUDGET = 2400)   ")
    print("=" * 80)

    questions_file = ROOT / "data" / "questions.json"
    chunks_file = ROOT / "data" / "chunks.json"

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_list = json.load(f)
    chunks_map = {c["id"]: c for c in chunks_list}

    dev_questions = [q for q in all_questions if q.get("split") == "dev"]

    # Khởi tạo Agent với budget = 2400
    system = AgenticRAGSystem(max_searches=3, top_k=3, budget=2400)

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

        print(f"[{idx:02d}/{len(dev_questions):02d}] Câu {qid} ({'Ans' if is_ans else 'Abs'})...", end=" ", flush=True)

        q_start = time.perf_counter()
        res = system.answer_query(q_text, filters=filters, budget=2400)
        q_elapsed_ms = (time.perf_counter() - q_start) * 1000

        status = res["status"]
        answer = res["answer"]
        citations = res["citations"]
        events = res["events"]

        print(f"Status: {status} | Elapsed: {q_elapsed_ms:.0f}ms | Citations: {citations}")

        cases.append({
            "id": qid,
            "split": "dev",
            "question": q_text,
            "answerable": is_ans,
            "expected_behavior": q.get("expected_behavior", "search_and_answer" if is_ans else "search_and_abstain"),
        })

        traces.append({
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
        })

        # Đánh giá Audit Review
        citation_support = [c_id in chunks_map for c_id in citations]
        review_item: Dict[str, Any] = {
            "query_id": qid,
            "citation_support": citation_support,
        }

        if is_ans:
            if status == "abstain":
                review_item["answer_grade"] = 0
                review_item["notes"] = "False abstention trên câu có đáp án"
            else:
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
            if status == "abstain":
                review_item["abstention_correct"] = True
                review_item["notes"] = "Từ chối đúng do tài liệu không chứa bằng chứng."
            else:
                review_item["abstention_correct"] = False
                review_item["notes"] = "Lỗi ảo giác: Đã trả lời khi tài liệu không có thông tin."

        reviews.append(review_item)

    total_elapsed = time.perf_counter() - total_start
    print(f"\n[*] Hoàn thành 20 câu trong {total_elapsed:.2f} giây.")

    cases_path = results_dir / "exp1_cases.json"
    traces_path = results_dir / "exp1_traces.json"
    reviews_path = results_dir / "exp1_reviews.json"
    summary_path = results_dir / "exp1_summary.json"

    with open(cases_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, ensure_ascii=False, indent=2)
    with open(reviews_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    # Tổng hợp qua starter/agent_metrics.py
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
