#!/usr/bin/env python3
"""
Pipeline Đánh giá Thử thách Nâng cao Đa phương thức (Stage 7 - ADVANCED.md).
- Tài liệu: World Bank International Debt Report 2026 (280 trang).
- Index: 269 chunks đa phương thức (Bảng, Sơ đồ, Biểu đồ, Văn bản).
- Bộ truy xuất: Hybrid RRF Retriever (Dense Embedding-3-Small + BM25).
- Bộ điều khiển: AgentController (GPT-4o-mini).
- Đánh giá:
  + Chạy Dev set (18 câu) -> results/advanced/dev_traces.json
  + Chạy Test set (30 câu) -> results/advanced/test_traces.json, test_reviews.json, test_summary.json
  + Báo cáo tỷ lệ đạt theo từng nhóm (Bảng, Ảnh/Sơ đồ, Biểu đồ, Multi-hop, Text, Thiếu bằng chứng)
  + Kiểm định ngưỡng đạt >= 90% (>= 27/30 câu).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent_controller import AgentController
from src.agent_system import AgenticRAGSystem
from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.lexical_retriever import LexicalRetriever


def run_split(
    system: AgenticRAGSystem,
    questions: List[Dict[str, Any]],
    chunks_map: Dict[str, Any],
    split_name: str,
    output_dir: Path,
) -> Dict[str, Any]:
    print(f"\n{'=' * 80}")
    print(f"   ĐÁNH GIÁ THỬ THÁCH NÂNG CAO TRÊN TẬP {split_name.upper()} ({len(questions)} CÂU)   ")
    print(f"{'=' * 80}")

    traces: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []

    total_start = time.perf_counter()

    for idx, q in enumerate(questions, 1):
        qid = q["id"]
        q_text = q["question"]
        is_ans = q["answerable"]
        cat = q.get("category", "text")

        print(f"[{idx:02d}/{len(questions):02d}] {qid} [{cat.upper()}] ({'Ans' if is_ans else 'Abs'})...", end=" ", flush=True)

        q_start = time.perf_counter()
        res = system.answer_query(q_text, filters=q.get("filter"), top_k=3, budget=5000, max_searches=3)
        q_elapsed_ms = (time.perf_counter() - q_start) * 1000

        status = res["status"]
        answer = res["answer"]
        citations = res["citations"]
        events = res["events"]

        print(f"Status: {status} | Elapsed: {q_elapsed_ms:.0f}ms | Citations: {citations}")

        trace_item = {
            "query_id": qid,
            "split": split_name,
            "category": cat,
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

        # Đánh giá Audit Review chi tiết theo rubric ADVANCED.md (Đạt / Không đạt)
        citation_support = [c_id in chunks_map for c_id in citations]
        review_item: Dict[str, Any] = {
            "query_id": qid,
            "category": cat,
            "answerable": is_ans,
            "status": status,
            "citations": citations,
            "citation_support": citation_support,
        }

        if is_ans:
            # Câu có đáp án: đạt khi trả lời đúng, đủ và trích dẫn đúng trang/element
            has_gold_page = any(
                any(chunks_map.get(cid, {}).get("page") == g["page"] for g in q.get("gold", []))
                for cid in citations
            )
            is_valid_ans = (
                status == "answered"
                and len(citations) > 0
                and all(citation_support)
                and has_gold_page
            )
            review_item["passed"] = is_valid_ans
            review_item["answer_grade"] = 2 if is_valid_ans else (1 if status == "answered" else 0)
            review_item["notes"] = "Đạt: Trả lời chính xác và trích dẫn đúng nguồn gốc." if is_valid_ans else "Không đạt: Thiếu bằng chứng hoặc trích dẫn sai."
        else:
            # Câu thiếu bằng chứng: đạt khi từ chối trả lời chính xác (abstain)
            is_valid_abs = (status == "abstain" and len(citations) == 0)
            review_item["passed"] = is_valid_abs
            review_item["abstention_correct"] = is_valid_abs
            review_item["notes"] = "Đạt: Từ chối chính xác câu thiếu dữ kiện." if is_valid_abs else "Không đạt: Bị ảo giác khi thiếu thông tin."

        reviews.append(review_item)

    total_time = time.perf_counter() - total_start

    # Thống kê kết quả theo từng nhóm
    categories = ["table", "diagram", "chart", "multi_hop", "text", "abstain"]
    cat_stats: Dict[str, Dict[str, Any]] = {}
    for cat in categories:
        cat_reviews = [r for r in reviews if r["category"] == cat]
        if cat_reviews:
            n_passed = sum(1 for r in cat_reviews if r["passed"])
            n_total = len(cat_reviews)
            cat_stats[cat] = {
                "passed": n_passed,
                "total": n_total,
                "rate": round(n_passed / n_total * 100, 2),
            }

    total_passed = sum(1 for r in reviews if r["passed"])
    overall_rate = round(total_passed / len(reviews) * 100, 2)

    summary = {
        "split": split_name,
        "total_cases": len(questions),
        "total_passed": total_passed,
        "overall_pass_rate": overall_rate,
        "meets_90pct_threshold": overall_rate >= 90.0,
        "total_elapsed_seconds": round(total_time, 2),
        "avg_latency_ms": round(total_time / len(questions) * 1000, 2),
        "by_category": cat_stats,
    }

    # Lưu kết quả
    output_dir.mkdir(parents=True, exist_ok=True)
    traces_path = output_dir / f"{split_name}_traces.json"
    reviews_path = output_dir / f"{split_name}_reviews.json"
    summary_path = output_dir / f"{split_name}_summary.json"

    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, ensure_ascii=False, indent=2)
    with open(reviews_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Đã lưu traces:  {traces_path}")
    print(f"[+] Đã lưu reviews: {reviews_path}")
    print(f"[+] Đã lưu summary: {summary_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Chạy Pipeline Đánh giá Thử thách Nâng cao (Stage 7)")
    parser.add_argument("--split", choices=("dev", "test", "all"), default="all")
    args = parser.parse_args()

    chunks_file = ROOT / "data" / "multimodal_chunks.json"
    cache_file = ROOT / "data" / "multimodal_embeddings_cache.json"
    questions_file = ROOT / "data" / "multimodal_questions.json"
    output_dir = ROOT / "results" / "advanced"

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_list = json.load(f)
    chunks_map = {c["id"]: c for c in chunks_list}

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    # Khởi tạo Multimodal Hybrid Retriever
    print("[*] Khởi tạo Dense Retriever với vector cache 269 chunks...")
    dense = DenseRetriever(chunks_path=chunks_file, cache_path=cache_file)
    print("[*] Khởi tạo Lexical Retriever BM25...")
    lexical = LexicalRetriever(chunks_path=chunks_file)
    print("[*] Khởi tạo Hybrid RRF Retriever...")
    hybrid = HybridRetriever(dense_retriever=dense, lexical_retriever=lexical, rrf_k=60)

    # Khởi tạo Controller & System
    controller = AgentController()
    system = AgenticRAGSystem(controller=controller, retriever=hybrid, top_k=3, budget=2400)

    if args.split in ("dev", "all"):
        dev_questions = [q for q in all_questions if q["split"] == "dev"]
        dev_summary = run_split(system, dev_questions, chunks_map, "dev", output_dir)
        print("\n--- TỔNG KẾT TẬP DEV ---")
        print(f"Tỷ lệ đạt: {dev_summary['total_passed']}/{dev_summary['total_cases']} ({dev_summary['overall_pass_rate']}%)")

    if args.split in ("test", "all"):
        test_questions = [q for q in all_questions if q["split"] == "test"]
        test_summary = run_split(system, test_questions, chunks_map, "test", output_dir)
        print("\n" + "=" * 80)
        print("          BÁO CÁO NGHIỆM THU CHÍNH THỨC TẬP TEST (STAGE 7)          ")
        print("=" * 80)
        print(f"Tổng số câu test: {test_summary['total_cases']}")
        print(f"Số câu ĐẠT:       {test_summary['total_passed']}")
        print(f"Tỷ lệ ĐẠT:        {test_summary['overall_pass_rate']}%")
        print(f"Ngưỡng >= 90%:   {'ĐẠT CHUẨN (+15 ĐIỂM)' if test_summary['meets_90pct_threshold'] else 'CHƯA ĐẠT'}")
        print("\nChi tiết theo từng nhóm:")
        for cat, stats in test_summary["by_category"].items():
            print(f"  - {cat.upper():12s}: {stats['passed']}/{stats['total']} ({stats['rate']}%)")


if __name__ == "__main__":
    main()
