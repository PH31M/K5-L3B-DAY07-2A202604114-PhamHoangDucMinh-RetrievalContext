#!/usr/bin/env python3
"""
Đánh giá độc lập trên tập Test (Held-out Evaluation - Stage 6).
Chạy cả 2 cấu hình trên 10 câu tập Test (test_01 đến test_10):
1. Cấu hình Baseline: budget = 1200, top_k = 3
2. Cấu hình Đã chọn (Frozen Config): budget = 2400, top_k = 3

Đầu ra:
- results/agent/test_cases.json
- results/agent/test_baseline_traces.json
- results/agent/test_baseline_reviews.json
- results/agent/test_baseline_summary.json
- results/agent/test_frozen_traces.json
- results/agent/test_frozen_reviews.json
- results/agent/test_frozen_summary.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent_system import AgenticRAGSystem


def evaluate_test_config(
    system: AgenticRAGSystem,
    test_questions: List[Dict[str, Any]],
    chunks_map: Dict[str, Any],
    budget: int,
    top_k: int,
    config_name: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    print(f"\n---> Bắt đầu chạy cấu hình: {config_name} (budget={budget}, top_k={top_k})")
    traces: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []

    for idx, q in enumerate(test_questions, 1):
        qid = q["id"]
        q_text = q["question"]
        is_ans = q["answerable"]
        filters = q.get("filter")

        print(f"[{idx:02d}/{len(test_questions):02d}] {qid} ({'Ans' if is_ans else 'Abs'})...", end=" ", flush=True)

        q_start = time.perf_counter()
        res = system.answer_query(q_text, filters=filters, top_k=top_k, budget=budget)
        q_elapsed_ms = (time.perf_counter() - q_start) * 1000

        status = res["status"]
        answer = res["answer"]
        citations = res["citations"]
        events = res["events"]

        print(f"Status: {status} | Elapsed: {q_elapsed_ms:.0f}ms | Citations: {citations}")

        cases.append({
            "id": qid,
            "split": "test",
            "question": q_text,
            "answerable": is_ans,
            "expected_behavior": q.get("expected_behavior", "search_and_answer" if is_ans else "search_and_abstain"),
        })

        traces.append({
            "query_id": qid,
            "split": "test",
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

    return cases, traces, reviews


def main():
    print("=" * 80)
    print("       ĐÁNH GIÁ ĐỘC LẬP TRÊN TẬP KIỂM THỬ (HELD-OUT TEST SET - STAGE 6)       ")
    print("=" * 80)

    questions_file = ROOT / "data" / "questions.json"
    chunks_file = ROOT / "data" / "chunks.json"

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_list = json.load(f)
    chunks_map = {c["id"]: c for c in chunks_list}

    test_questions = [q for q in all_questions if q.get("split") == "test"]
    print(f"[*] Tổng số câu hỏi tập Test: {len(test_questions)} (Có đáp án: {sum(1 for q in test_questions if q['answerable'])}, Không có đáp án: {sum(1 for q in test_questions if not q['answerable'])})")

    system = AgenticRAGSystem()
    results_dir = ROOT / "results" / "agent"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Chạy Cấu hình Baseline (budget=1200, top_k=3)
    base_cases, base_traces, base_reviews = evaluate_test_config(
        system=system,
        test_questions=test_questions,
        chunks_map=chunks_map,
        budget=1200,
        top_k=3,
        config_name="Baseline (budget=1200, top_k=3)",
    )

    cases_path = results_dir / "test_cases.json"
    base_traces_path = results_dir / "test_baseline_traces.json"
    base_reviews_path = results_dir / "test_baseline_reviews.json"
    base_summary_path = results_dir / "test_baseline_summary.json"

    with open(cases_path, "w", encoding="utf-8") as f:
        json.dump(base_cases, f, ensure_ascii=False, indent=2)
    with open(base_traces_path, "w", encoding="utf-8") as f:
        json.dump(base_traces, f, ensure_ascii=False, indent=2)
    with open(base_reviews_path, "w", encoding="utf-8") as f:
        json.dump(base_reviews, f, ensure_ascii=False, indent=2)

    subprocess.run([
        sys.executable,
        str(ROOT / "starter" / "agent_metrics.py"),
        "--cases", str(cases_path),
        "--traces", str(base_traces_path),
        "--reviews", str(base_reviews_path),
        "--split", "test",
        "--output", str(base_summary_path),
    ], check=True)

    # 2. Chạy Cấu hình Đã chọn / Frozen (budget=2400, top_k=3)
    frozen_cases, frozen_traces, frozen_reviews = evaluate_test_config(
        system=system,
        test_questions=test_questions,
        chunks_map=chunks_map,
        budget=2400,
        top_k=3,
        config_name="Frozen Chosen Config (budget=2400, top_k=3)",
    )

    frozen_traces_path = results_dir / "test_frozen_traces.json"
    frozen_reviews_path = results_dir / "test_frozen_reviews.json"
    frozen_summary_path = results_dir / "test_frozen_summary.json"

    with open(frozen_traces_path, "w", encoding="utf-8") as f:
        json.dump(frozen_traces, f, ensure_ascii=False, indent=2)
    with open(frozen_reviews_path, "w", encoding="utf-8") as f:
        json.dump(frozen_reviews, f, ensure_ascii=False, indent=2)

    subprocess.run([
        sys.executable,
        str(ROOT / "starter" / "agent_metrics.py"),
        "--cases", str(cases_path),
        "--traces", str(frozen_traces_path),
        "--reviews", str(frozen_reviews_path),
        "--split", "test",
        "--output", str(frozen_summary_path),
    ], check=True)

    print("\n" + "=" * 80)
    print("       HOÀN TẤT ĐÁNH GIÁ TẬP TEST CHO CẢ 2 CẤU HÌNH       ")
    print("=" * 80)
    print(f"[+] Baseline summary: {base_summary_path}")
    print(f"[+] Frozen summary:   {frozen_summary_path}")


if __name__ == "__main__":
    main()
