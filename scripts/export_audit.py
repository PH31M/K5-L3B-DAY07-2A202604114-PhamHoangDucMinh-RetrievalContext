"""Xuất từng câu test thành bản đối chiếu: câu hỏi, gold, câu trả lời agent, nội dung chunk được trích.

Dùng để audit thủ công (đối chiếu câu trả lời với evidence), không chấm tự động.

  python3 scripts/export_audit.py --kind basic    --split test --traces results/agent/test_frozen_traces.json
  python3 scripts/export_audit.py --kind advanced --split test --traces results/advanced/test_traces.json
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("basic", "advanced"), required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--traces", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-chunk-chars", type=int, default=1800)
    a = ap.parse_args()

    qfile = "data/questions.json" if a.kind == "basic" else "data/multimodal_questions.json"
    cfile = "data/chunks.json" if a.kind == "basic" else "data/multimodal_chunks.json"
    questions = {q["id"]: q for q in load(ROOT / qfile) if q.get("split") == a.split}
    chunks = {c["id"]: c for c in load(ROOT / cfile)}
    traces = {t["query_id"]: t for t in load(ROOT / a.traces)}

    out = []
    for qid, q in questions.items():
        t = traces[qid]
        out.append(f"\n## {qid} [{q.get('category', '-')}] answerable={q['answerable']} status={t['status']}")
        out.append(f"Q: {q['question']}")
        out.append(f"GOLD ANSWER: {q.get('expected_answer') or q.get('answer') or '(abstain)'}")
        for g in q.get("gold", []) or []:
            out.append(f"GOLD EVIDENCE (p{g.get('page')}, {g.get('element_type', '')}): {str(g.get('evidence'))[:600]}")
        out.append(f"AGENT ANSWER: {t['answer']}")
        out.append(f"CITATIONS: {t['citations']}")
        for cid in t["citations"]:
            c = chunks.get(cid)
            if c is None:
                out.append(f"--- {cid}: KHÔNG TỒN TẠI")
                continue
            out.append(f"--- {cid} (p{c.get('page')}):\n{c['text'][:a.max_chunk_chars]}")
    Path(a.output).write_text("\n".join(out), encoding="utf-8")
    print(f"Đã ghi {len(questions)} câu -> {a.output}")


if __name__ == "__main__":
    main()
