"""
Lexical Retriever Module for Day 7 using BM25.
Triển khai thuật toán BM25 kinh điển (k1=1.5, b=0.75) hoàn toàn bằng Python standard library.
Tương thích với giao thức Retriever của starter/agentic.py.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def tokenize(text: str) -> List[str]:
    """Tách từ chuẩn hóa Unicode NFC và viết thường."""
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class LexicalRetriever:
    """Lexical Retriever sử dụng thuật toán BM25 chuẩn."""

    def __init__(
        self,
        chunks_path: Union[Path, str] = "data/chunks.json",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.chunks_path = Path(chunks_path)
        if not self.chunks_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file chunks tại: {self.chunks_path.resolve()}")

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks: List[Dict[str, Any]] = json.load(f)

        self.k1 = k1
        self.b = b
        self.n_docs = len(self.chunks)

        # 1. Tokenize toàn bộ chunks
        self.doc_tokens = [tokenize(c["text"]) for c in self.chunks]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.n_docs)

        # 2. Tính Term Frequency (TF) và Document Frequency (DF)
        self.doc_term_counts = [Counter(tokens) for tokens in self.doc_tokens]
        self.df: Counter[str] = Counter()
        for counts in self.doc_term_counts:
            for term in counts:
                self.df[term] += 1

        # 3. Tính IDF theo chuẩn Lucene / Okapi BM25:
        # IDF = ln(1 + (N - df + 0.5) / (df + 0.5))
        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1.0 + (self.n_docs - freq + 0.5) / (freq + 0.5))

    def search(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Thực hiện tìm kiếm BM25.
        Trả về top_k chunks có điểm BM25 cao nhất.
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []

        scored_results: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(self.chunks):
            # Áp dụng bộ lọc metadata nếu có
            if filters:
                meta = chunk.get("metadata", {})
                match = True
                for k, v in filters.items():
                    if meta.get(k) != v and chunk.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            # Tính điểm BM25 cho document
            doc_counts = self.doc_term_counts[idx]
            doc_len = self.doc_lengths[idx]
            len_norm = 1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len))

            score = 0.0
            for term in query_terms:
                if term not in doc_counts:
                    continue
                tf = doc_counts[term]
                idf = self.idf.get(term, 0.0)
                # BM25 TF formula
                tf_norm = (tf * (self.k1 + 1.0)) / (tf + self.k1 * len_norm)
                score += idf * tf_norm

            if score > 0.0:
                scored_results.append({
                    "id": chunk["id"],
                    "source_id": chunk["source_id"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "text": chunk["text"],
                    "metadata": chunk.get("metadata", {}),
                    "score": round(score, 6),
                    "strategy": "lexical_bm25",
                })

        # Sắp xếp theo score giảm dần, id tăng dần
        scored_results.sort(key=lambda x: (-x["score"], x["id"]))
        return scored_results[:top_k]


if __name__ == "__main__":
    retriever = LexicalRetriever()
    test_q = "What percentage of GDP did trade openness reach across low- and middle-income countries in 2025?"
    results = retriever.search(test_q, top_k=3)
    print(f"BM25 Search Top-{len(results)}:")
    for r in results:
        print(f"  [{r['id']} | Page {r['page']}] Score: {r['score']}")
