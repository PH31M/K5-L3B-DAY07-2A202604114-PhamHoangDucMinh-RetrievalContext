"""
Dense Retriever Module for Day 7.
Tương thích với giao thức Retriever của starter/agentic.py.
Kết nối trực tiếp mô hình embedding thật (OpenRouter / OpenAI) và kho lưu trữ vector.
Tuyệt đối không dùng vector mock / ngẫu nhiên.
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def load_env_file(dotenv_path: Union[Path, str] = ".env") -> None:
    """Đọc file .env vào os.environ (không phụ thuộc vào thư viện bên ngoài)."""
    p = Path(dotenv_path)
    if not p.exists():
        return
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


class DenseRetriever:
    """Dense Retriever sử dụng embedding vector thật 1536 chiều."""

    def __init__(
        self,
        chunks_path: Union[Path, str] = "data/chunks.json",
        cache_path: Optional[Union[Path, str]] = None,
        model_name: Optional[str] = None,
        dimensions: Optional[int] = None,
        vector_store_type: Optional[str] = None,
    ) -> None:
        load_env_file()

        self.chunks_path = Path(chunks_path)
        self.cache_path = Path(cache_path or os.getenv("EMBEDDINGS_CACHE_PATH", "data/embeddings_cache.json"))
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
        self.dimensions = dimensions or int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        self.vector_store_type = vector_store_type or os.getenv("VECTOR_STORE_TYPE", "local")

        # Đọc API key từ môi trường
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        # Kiểm tra file chunks
        if not self.chunks_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file chunks tại: {self.chunks_path.resolve()}. "
                f"Hãy chạy 'python3 scripts/export_chunks.py' trước."
            )

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks: List[Dict[str, Any]] = json.load(f)

        self.chunk_map = {c["id"]: c for c in self.chunks}
        self.chunk_vectors: Dict[str, List[float]] = {}

        # Nạp hoặc sinh vector cho toàn bộ corpus nếu dùng local store
        if self.vector_store_type == "local":
            self._load_or_build_embeddings()

    def _get_api_config(self) -> Tuple[str, str]:
        """Xác định endpoint URL và API key phù hợp."""
        if self.openrouter_key:
            return "https://openrouter.ai/api/v1/embeddings", self.openrouter_key
        elif self.openai_key:
            return "https://api.openai.com/v1/embeddings", self.openai_key
        else:
            raise ValueError(
                "Chưa cấu hình API Key trong file .env! "
                "Vui lòng mở file .env và điền OPENROUTER_API_KEY hoặc OPENAI_API_KEY."
            )

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Gọi API embedding thật để lấy danh sách vector."""
        url, api_key = self._get_api_config()
        all_embeddings: List[List[float]] = []

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter" in url:
            headers["HTTP-Referer"] = "https://github.com/VinUni-AI20k/K5-L3-Day07"
            headers["X-Title"] = "Day07-Agentic-RAG"

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            cleaned_batch = [t if t.strip() else " " for t in batch]

            payload = {
                "model": self.model_name,
                "input": cleaned_batch,
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            last_error = None
            success = False
            for attempt in range(1, 4):
                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        resp_data = json.loads(resp.read().decode("utf-8"))

                    data_items = sorted(resp_data.get("data", []), key=lambda x: x.get("index", 0))
                    for item in data_items:
                        vec = item["embedding"]
                        if len(vec) != self.dimensions:
                            raise ValueError(
                                f"Sai lệch số chiều vector: kỳ vọng {self.dimensions}, nhận được {len(vec)}"
                            )
                        all_embeddings.append(vec)
                    success = True
                    break

                except urllib.error.HTTPError as e:
                    err_body = e.read().decode("utf-8") if e.fp else ""
                    last_error = RuntimeError(
                        f"Lỗi API Embedding (HTTP {e.code}): {e.reason}\nChi tiết: {err_body}"
                    )
                    if 400 <= e.code < 500 and e.code != 429:
                        raise last_error from e
                except Exception as e:
                    last_error = e

                if attempt < 3:
                    time.sleep(attempt * 2)

            if not success:
                raise RuntimeError(f"Lỗi kết nối khi gọi embedding sau 3 lần thử: {last_error}") from last_error

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Tạo vector cho 1 câu truy vấn."""
        if not query or not query.strip():
            raise ValueError("Query không được để trống")
        vectors = self.embed_texts([query])
        return vectors[0]

    def _load_or_build_embeddings(self) -> None:
        """Nạp vector từ file cache hoặc gọi API sinh vector cho 108 chunks nếu chưa có cache."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.chunk_vectors = json.load(f)
                if len(self.chunk_vectors) == len(self.chunks):
                    # Cache hợp lệ
                    return
            except Exception:
                pass

        # Chưa có cache hoặc cache thiếu: Cần API key để sinh vector
        if not self.openrouter_key and not self.openai_key:
            # Chưa có key trong .env
            raise ValueError(
                "Chưa tìm thấy OPENROUTER_API_KEY hoặc OPENAI_API_KEY trong file .env. "
                "Vui lòng điền API key vào .env để sinh vector embedding cho 108 chunks."
            )

        print(f"[*] Đang sinh vector embedding cho {len(self.chunks)} chunks bằng {self.model_name}...")
        texts = [c["text"] for c in self.chunks]
        vectors = self.embed_texts(texts)

        self.chunk_vectors = {c["id"]: vec for c, vec in zip(self.chunks, vectors)}

        # Lưu cache ra file
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.chunk_vectors, f)
        print(f"[+] Đã lưu vector cache thành công tại: {self.cache_path}")

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Tính Cosine Similarity giữa 2 vector."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1e-9
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1e-9
        return dot / (norm_a * norm_b)

    def search(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Thực hiện tìm kiếm ngữ nghĩa theo giao thức Retriever của starter/agentic.py.
        Trả về top_k chunks có điểm tương đồng Cosine cao nhất.
        """
        if not query or not query.strip():
            return []

        # Sinh query vector thật
        query_vec = self.embed_query(query)

        scored_results: List[Dict[str, Any]] = []

        for chunk in self.chunks:
            c_id = chunk["id"]
            if c_id not in self.chunk_vectors:
                continue

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

            # Tính điểm Cosine
            score = self._cosine_similarity(query_vec, self.chunk_vectors[c_id])
            scored_results.append({
                **chunk,
                "score": round(score, 6),
                "strategy": "dense",
            })

        # Sắp xếp theo score giảm dần, id tăng dần (ổn định thứ hạng)
        scored_results.sort(key=lambda x: (-x["score"], x["id"]))
        return scored_results[:top_k]


if __name__ == "__main__":
    print("=== KIỂM TRA MODULE DENSE RETRIEVER ===")
    try:
        retriever = DenseRetriever()
        print("✅ Retriever khởi tạo thành công với cấu hình:")
        print(f"  - Model: {retriever.model_name}")
        print(f"  - Dimensions: {retriever.dimensions}")
        print(f"  - Total chunks: {len(retriever.chunks)}")
        print(f"  - Cached vectors: {len(retriever.chunk_vectors)}")
    except ValueError as e:
        print(f"⚠️  Thông báo: {e}")
        print("👉 Hãy mở file .env và điền API key trước khi chạy truy vấn thật.")
