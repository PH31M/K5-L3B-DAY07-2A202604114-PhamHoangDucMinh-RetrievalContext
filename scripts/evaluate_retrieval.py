#!/usr/bin/env python3
"""
Đánh giá so sánh 3 phương pháp Retrieval trên tập Dev:
1. Dense Retrieval (openai/text-embedding-3-small, 1536 dims)
2. Lexical Retrieval (BM25, k1=1.5, b=0.75)
3. Hybrid Retrieval (Dense + BM25 qua Reciprocal Rank Fusion - RRF)

Xuất bảng số liệu và lưu traces/summary tại: results/retrieval/
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Thêm đường dẫn gốc để import src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dense_retriever import DenseRetriever
from src.hybrid_retriever import HybridRetriever
from src.lexical_retriever import LexicalRetriever
from starter.baseline import hit, pack_context


def evaluate_method(
    retriever: Any,
    strategy_name: str,
    questions: List[Dict[str, Any]],
    top_k: int = 3,
    budget: int = 1200,
    cost_per_query: float = 0.0,
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Chạy đánh giá cho 1 retriever trên danh sách câu hỏi."""
    traces: List[Dict[str, Any]] = []

    for q in questions:
        start = time.perf_counter()
        results = retriever.search(q["question"], filters=q.get("filter"), top_k=top_k)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Đánh dấu hit cho từng chunk kết quả
        marked_results = [{**c, "hit": hit(c, q["gold"])} for c in results]
        context, ids = pack_context(marked_results, budget=budget)

        hit1 = bool(marked_results and marked_results[0]["hit"])
        hit3 = any(c["hit"] for c in marked_results)
        context_hit = any(c["hit"] and c["id"] in ids for c in marked_results)

        traces.append({
            "query_id": q["id"],
            "split": q.get("split", "dev"),
            "question": q["question"],
            "strategy": strategy_name,
            "top_k": top_k,
            "budget_chars": budget,
            "filter": q.get("filter"),
            "gold": q["gold"],
            "results": marked_results,
            "context": context,
            "context_ids": ids,
            "context_chars": len(context),
            "elapsed_ms": round(elapsed_ms, 3),
            "hit1": hit1,
            "hit3": hit3,
            "context_hit": context_hit,
        })

    n = len(traces)
    n_hit1 = sum(t["hit1"] for t in traces)
    n_hit3 = sum(t["hit3"] for t in traces)
    n_context_hit = sum(t["context_hit"] for t in traces)

    summary = {
        "strategy": strategy_name,
        "n": n,
        "hit1_count": n_hit1,
        "hit1_rate": round(n_hit1 / max(1, n) * 100, 2),
        "hit3_count": n_hit3,
        "hit3_rate": round(n_hit3 / max(1, n) * 100, 2),
        "context_hit_count": n_context_hit,
        "context_hit_rate": round(n_context_hit / max(1, n) * 100, 2),
        "avg_context_chars": round(statistics.mean(t["context_chars"] for t in traces), 1),
        "median_ms": round(statistics.median(t["elapsed_ms"] for t in traces), 3),
        "avg_ms": round(statistics.mean(t["elapsed_ms"] for t in traces), 3),
        "total_cost_usd": round(n * cost_per_query, 6),
    }

    return summary, traces


def generate_markdown_report(summaries: List[Dict[str, Any]], split: str, output_path: Path):
    """Tạo báo cáo markdown tổng hợp."""
    lines = [
        f"# Bảng So sánh Hiệu năng Retrieval trên tập {split.upper()}",
        "",
        "Đánh giá trên cùng một corpus (`data/chunks.json`, 108 chunks) và cùng ngân sách context (`budget = 1200`).",
        "",
        "| Phương pháp (Strategy) | Hit@1 (n/N, %) | Evidence Hit@3 (n/N, %) | Context Evidence Rate (n/N, %) | Latency trung vị (ms) | Chi phí ước tính |",
        "|---|:---:|:---:|:---:|:---:|:---:|",
    ]

    for s in summaries:
        name = s["strategy"]
        h1 = f"{s['hit1_count']}/{s['n']} ({s['hit1_rate']}%)"
        h3 = f"{s['hit3_count']}/{s['n']} ({s['hit3_rate']}%)"
        ch = f"{s['context_hit_count']}/{s['n']} ({s['context_hit_rate']}%)"
        lat = f"{s['median_ms']} ms"
        cost = f"${s['total_cost_usd']:.6f}" if s["total_cost_usd"] > 0 else "$0.00 (offline)"
        lines.append(f"| **{name}** | {h1} | {h3} | {ch} | {lat} | {cost} |")

    lines.extend([
        "",
        "### Nhận xét & Đánh giá Kỹ thuật:",
        "- **Dense Retrieval:** Rất mạnh về tương đồng ý niệm, ngữ nghĩa ngữ cảnh rộng, nhưng độ trễ phụ thuộc vào mạng khi gọi API embedding.",
        "- **Lexical Retrieval (BM25):** Tốc độ cực nhanh (< 1ms), khớp chính xác các thực thể số, tên riêng và từ khóa chuyên ngành, hoàn toàn miễn phí không tốn API.",
        "- **Hybrid Retrieval (RRF):** Kết hợp sức mạnh của cả hai, bù đắp trường hợp một phương pháp bị trượt, cho độ phủ context và thứ hạng ổn định nhất.",
    ])

    report_text = "\n".join(lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    return report_text


def main():
    parser = argparse.ArgumentParser(description="Đánh giá và so sánh 3 phương pháp Retrieval trên tập Dev/Test")
    parser.add_argument("--chunks", default="data/chunks.json", type=Path)
    parser.add_argument("--questions", default="data/questions.json", type=Path)
    parser.add_argument("--split", default="dev", choices=("dev", "test"))
    parser.add_argument("--output-dir", default="results/retrieval", type=Path)
    parser.add_argument("--budget", default=1200, type=int)

    args = parser.parse_args()

    # 1. Nạp dữ liệu
    all_questions = json.loads(args.questions.read_text(encoding="utf-8"))
    # Chỉ đánh giá trên các câu có đáp án (có gold evidence) của split được chọn
    selected_questions = [
        q for q in all_questions
        if q.get("split") == args.split and q.get("answerable") is not False
    ]
    print(f"\n[*] Đang chạy benchmark Retrieval trên tập {args.split.upper()} ({len(selected_questions)} câu có đáp án)...")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Khởi tạo 3 Retriever
    print("[1/3] Khởi tạo Dense Retriever (openai/text-embedding-3-small)...")
    dense_retriever = DenseRetriever(chunks_path=args.chunks)

    print("[2/3] Khởi tạo Lexical Retriever (BM25)...")
    lexical_retriever = LexicalRetriever(chunks_path=args.chunks)

    print("[3/3] Khởi tạo Hybrid Retriever (RRF)...")
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        lexical_retriever=lexical_retriever,
    )

    # 3. Đánh giá từng phương pháp
    methods = [
        ("Dense (Embedding 3 Small)", dense_retriever, 0.0000002),
        ("Lexical (BM25)", lexical_retriever, 0.0),
        ("Hybrid (Dense + BM25 RRF)", hybrid_retriever, 0.0000002),
    ]

    summaries = []
    for name, ret, cost_per_q in methods:
        print(f"  -> Đang đánh giá: {name}...")
        summary, traces = evaluate_method(
            ret,
            name,
            selected_questions,
            top_k=3,
            budget=args.budget,
            cost_per_query=cost_per_q,
        )
        summaries.append(summary)

        # Lưu traces và summary
        prefix = name.split()[0].lower()
        (args.output_dir / f"{prefix}_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / f"{prefix}_traces.json").write_text(
            json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # 4. Xuất báo cáo tổng hợp
    report_file = args.output_dir / f"benchmark_comparison_{args.split}.md"
    report_text = generate_markdown_report(summaries, args.split, report_file)

    print("\n" + "=" * 80)
    print(report_text)
    print("=" * 80)
    print(f"✅ Hoàn tất! Các file traces và báo cáo đã được lưu tại: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
