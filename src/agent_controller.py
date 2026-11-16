"""
Agent Controller Module for Day 7.
Gọi mô hình LLM thật (OpenRouter / OpenAI) qua HTTP request với cơ chế retry tự động.
Triển khai giao thức Controller.decide(question, history) của starter/agentic.py.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .dense_retriever import load_env_file


class AgentController:
    """LLM Controller điều phối vòng lặp Agentic RAG."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        timeout: int = 60,
    ) -> None:
        load_env_file()

        self.provider = provider or os.getenv("LLM_PROVIDER", "openrouter")
        self.model_name = model_name or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout

        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def _get_api_config(self) -> Tuple[str, str]:
        """Lấy endpoint URL và API key."""
        if self.openrouter_key:
            return "https://openrouter.ai/api/v1/chat/completions", self.openrouter_key
        elif self.openai_key:
            return "https://api.openai.com/v1/chat/completions", self.openai_key
        else:
            raise ValueError(
                "Chưa cấu hình API Key trong file .env! "
                "Vui lòng điền OPENROUTER_API_KEY hoặc OPENAI_API_KEY."
            )

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Gửi request tới Chat Completion API kèm cơ chế retry tự động."""
        url, api_key = self._get_api_config()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter" in url:
            headers["HTTP-Referer"] = "https://github.com/VinUni-AI20k/K5-L3-Day07"
            headers["X-Title"] = "Day07-Agentic-RAG"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                content = resp_data["choices"][0]["message"]["content"]
                return content
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8") if e.fp else ""
                last_error = RuntimeError(f"Lỗi API LLM (HTTP {e.code}): {e.reason} - {err_body}")
                # Nếu lỗi client (4xx ngoài 429), không cần retry
                if 400 <= e.code < 500 and e.code != 429:
                    raise last_error
            except Exception as e:
                last_error = e

            if attempt < self.max_retries:
                sleep_time = attempt * 2
                time.sleep(sleep_time)

        raise RuntimeError(f"Lỗi kết nối khi gọi LLM sau {self.max_retries} lần thử: {last_error}") from last_error

    def decide(self, question: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Quyết định hành động tiếp theo của Agent:
        - action: 'search' kèm 'query' nếu cần tìm thêm chứng cứ.
        - action: 'answer' kèm 'answer' và 'citations' nếu đã đủ bằng chứng hoặc không có bằng chứng (abstain).
        """
        system_prompt = (
            "You are an Agentic RAG Controller evaluating evidence from Chapter 2 of the World Bank International Debt Report 2026.\n"
            "Your job is to answer user questions using ONLY facts directly substantiated by the provided context chunks.\n\n"
            "Decision Rules:\n"
            "1. IF you have NOT performed any search yet, or if the current context is empty or missing key information to answer the question:\n"
            '   Return JSON: {"action": "search", "query": "<focused search keywords without punctuation>"}\n'
            "2. IF the context contains the necessary and sufficient evidence to answer:\n"
            "   Formulate a concise, factual answer.\n"
            "   You MUST cite the supporting chunk IDs in the text as [chunk-id] and in the citations array.\n"
            '   Return JSON: {"action": "answer", "answer": "<answer text with [chunk-id]>", "citations": ["<chunk-id>"]}\n'
            "   Every citation in the array MUST appear in your answer and MUST exist in the context.\n"
            "3. IF a search was already performed, but the retrieved context clearly DOES NOT contain the answer (e.g. facts about other countries, specific dates, or figures absent from the report):\n"
            '   Return JSON: {"action": "answer", "answer": "Không đủ bằng chứng trong tài liệu để trả lời.", "citations": []}\n'
            "   Do NOT invent or guess any facts.\n\n"
            "Output MUST be valid JSON only."
        )

        # Định dạng lịch sử tương tác
        if not history:
            user_content = f"Question: {question}\n\nNo search has been performed yet."
        else:
            last_item = history[-1]
            searches = last_item.get("queries", [])
            context = last_item.get("context", "")
            context_ids = last_item.get("context_ids", [])
            user_content = (
                f"Question: {question}\n\n"
                f"Searches performed: {searches}\n\n"
                f"Available Context Chunks (IDs: {context_ids}):\n"
                f"{context if context else '(Context is empty)'}"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        raw_output = self._call_llm(messages)

        # Parse JSON an toàn
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned).strip()

        try:
            parsed = json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                raise ValueError(f"Không thể parse JSON từ LLM output: {raw_output}")

        action = parsed.get("action")
        if action == "search":
            query = parsed.get("query", "").strip()
            if not query:
                query = question
            return {"action": "search", "query": query}

        elif action == "answer":
            answer = parsed.get("answer", "").strip()
            citations = parsed.get("citations", [])
            if not isinstance(citations, list):
                citations = []
            citations = [str(c).strip() for c in citations if str(c).strip()]
            return {"action": "answer", "answer": answer, "citations": citations}

        else:
            return {"action": "search", "query": question}
