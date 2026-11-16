"""
Hybrid Retriever Module for Day 7.
Kết hợp Dense Retrieval (openai/text-embedding-3-small) và Lexical Retrieval (BM25)
bằng thuật toán Reciprocal Rank Fusion (RRF).
Tương thích với giao thức Retriever của starter/agentic.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .dense_retriever import DenseRetriever
from .lexical_retriever import LexicalRetriever


class HybridRetriever:
    """Hybrid Retriever kết hợp Dense (Semantic) và Lexical (BM25) qua RRF."""

    def __init__(
        self,
        chunks_path: Union[Path, str] = "data/chunks.json",
        cache_path: Optional[Union[Path, str]] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        lexical_retriever: Optional[LexicalRetriever] = None,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        lexical_weight: float = 1.0,
    ) -> None:
        self.dense = dense_retriever or DenseRetriever(chunks_path=chunks_path, cache_path=cache_path)
        self.lexical = lexical_retriever or LexicalRetriever(chunks_path=chunks_path)
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight
        self.chunk_map = self.dense.chunk_map

    def search(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
        candidate_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Thực hiện tìm kiếm Hybrid bằng thuật toán Reciprocal Rank Fusion (RRF):
        RRF_Score(d) = sum_m [ weight_m / (k + rank_m(d)) ]
        """
        if not query or not query.strip():
            return []

        # 1. Thu thập top ứng viên từ Dense và Lexical
        dense_results = self.dense.search(query, filters=filters, top_k=candidate_k)
        lexical_results = self.lexical.search(query, filters=filters, top_k=candidate_k)

        # 2. Tính điểm RRF
        rrf_scores: Dict[str, float] = {}
        dense_ranks: Dict[str, int] = {}
        lexical_ranks: Dict[str, int] = {}

        for rank, item in enumerate(dense_results, start=1):
            c_id = item["id"]
            dense_ranks[c_id] = rank
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + self.dense_weight / (self.rrf_k + rank)

        for rank, item in enumerate(lexical_results, start=1):
            c_id = item["id"]
            lexical_ranks[c_id] = rank
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + self.lexical_weight / (self.rrf_k + rank)

        # 3. Chuẩn bị kết quả đầu ra
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: (-x[1], x[0]))

        final_results: List[Dict[str, Any]] = []
        for c_id, score in sorted_candidates[:top_k]:
            chunk = self.chunk_map[c_id]
            final_results.append({
                "id": chunk["id"],
                "source_id": chunk["source_id"],
                "source": chunk["source"],
                "page": chunk["page"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
                "score": round(score, 6),
                "strategy": "hybrid_rrf",
                "dense_rank": dense_ranks.get(c_id),
                "lexical_rank": lexical_ranks.get(c_id),
            })

        return final_results


if __name__ == "__main__":
    hybrid = HybridRetriever()
    test_q = "What percentage of GDP did trade openness reach across low- and middle-income countries in 2025?"
    results = hybrid.search(test_q, top_k=3)
    print(f"Hybrid RRF Search Top-{len(results)}:")
    for r in results:
        print(f"  [{r['id']} | Page {r['page']}] Score: {r['score']} (Dense Rank: {r.get('dense_rank')}, Lexical Rank: {r.get('lexical_rank')})")
