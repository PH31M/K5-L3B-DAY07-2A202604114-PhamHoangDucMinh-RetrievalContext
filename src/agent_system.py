"""
Agent System Orchestrator for Day 7.
Kết nối AgentController và HybridRetriever thành hệ thống Agentic RAG hoàn chỉnh.
Tuân thủ hợp đồng sự kiện và đánh giá của starter/agentic.py.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "starter") not in sys.path:
    sys.path.insert(0, str(ROOT / "starter"))

from .agent_controller import AgentController
from .hybrid_retriever import HybridRetriever
from starter.agentic import run_agent


class AgenticRAGSystem:
    """Hệ thống Agentic RAG điều phối vòng lặp Controller - Tool."""

    def __init__(
        self,
        controller: Optional[AgentController] = None,
        retriever: Optional[HybridRetriever] = None,
        max_searches: int = 3,
        top_k: int = 3,
        budget: int = 2400,
    ) -> None:
        self.controller = controller or AgentController()
        self.retriever = retriever or HybridRetriever()
        self.max_searches = max_searches
        self.top_k = top_k
        self.budget = budget

    def answer_query(
        self,
        question: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        max_searches: Optional[int] = None,
        top_k: Optional[int] = None,
        budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Thực thi vòng lặp Agentic RAG trên 1 câu hỏi người dùng.
        Trả về kết quả có status ('answered' | 'abstain'), answer, citations và events.
        """
        return run_agent(
            question=question,
            controller=self.controller,
            retriever=self.retriever,
            filters=filters,
            max_searches=max_searches or self.max_searches,
            top_k=top_k or self.top_k,
            budget=budget or self.budget,
        )


if __name__ == "__main__":
    system = AgenticRAGSystem()
    q = "What was documented in the International Debt Report 2025 regarding external debt burdens?"
    print(f"[*] Đang chạy thử Agent với câu hỏi: \"{q}\"...")
    res = system.answer_query(q, filters={"section": "transmission_shocks"})
    print("\nKết quả:")
    print("Status:", res["status"])
    print("Answer:", res["answer"])
    print("Citations:", res["citations"])
    print(f"Tổng số events: {len(res['events'])}")
    for e in res["events"]:
        print("  Event:", e.get("event"), "Query:", e.get("query"))
