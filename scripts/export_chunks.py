#!/usr/bin/env python3
"""
Script trích xuất 108 chunks từ tài liệu Day 6 (World Bank International Debt Report 2026)
và lưu vào data/chunks.json theo đúng hợp đồng dữ liệu chuẩn của Day 7.
"""

import argparse
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

# Đảm bảo có thể import pypdf từ venv Day 6 nếu môi trường hiện tại chưa cài
day6_site_packages = Path(__file__).resolve().parent.parent.parent / "K5-L3B-DAY06-PhamHoangDucMinh-2A202604114-DataIngestion/starter/.venv/lib/python3.11/site-packages"
if day6_site_packages.exists():
    sys.path.insert(0, str(day6_site_packages))

try:
    import pypdf
except ImportError:
    print("Lỗi: Không tìm thấy thư viện 'pypdf'. Hãy cài đặt bằng 'pip install pypdf' hoặc chạy với venv của Day 6.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_section_metadata(phys_page: int) -> str:
    """Xác định section trong Chương 2 theo số trang vật lý."""
    if 75 <= phys_page <= 84:
        return "transmission_shocks"
    elif 85 <= phys_page <= 95:
        return "fiscal_pressures"
    elif 96 <= phys_page <= 102:
        return "food_import"
    else:
        return "notes_references"


def normalize_text(text: str) -> str:
    """Chuẩn hóa Unicode NFKC, khoảng trắng và xử lý ngắt dòng gạch nối theo chuẩn Day 6."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()


def by_paragraph(page_num: int, doc_id: str, source: str, text: str, page_meta: dict, max_size: int = 800) -> list[dict]:
    """Cắt đoạn văn tự nhiên, gom cụm tối đa max_size ký tự (Strategy B tối ưu từ Day 6)."""
    if not text or not text.strip():
        return []

    raw_blocks = [b.strip() for b in re.split(r'\n+', text) if b.strip()]
    units: list[str] = []
    for block in raw_blocks:
        if len(block) <= max_size:
            units.append(block)
        else:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', block) if s.strip()]
            for s in sentences:
                if len(s) <= max_size:
                    units.append(s)
                else:
                    for i in range(0, len(s), max_size):
                        units.append(s[i:i + max_size].strip())

    chunks: list[dict] = []
    current_unit: list[str] = []
    current_len = 0
    c_idx = 0

    for unit in units:
        unit_len = len(unit)
        add_len = unit_len if not current_unit else unit_len + 2  # tính thêm ký tự "\n\n"
        if current_len + add_len <= max_size:
            current_unit.append(unit)
            current_len += add_len
        else:
            if current_unit:
                chunk_text = "\n\n".join(current_unit).strip()
                meta = dict(page_meta)
                meta.update({
                    "chunk_index": c_idx,
                    "strategy": "by_paragraph",
                    "char_count": len(chunk_text),
                })
                chunks.append({
                    "id": f"{doc_id}_p{page_num}_b{c_idx:03d}",
                    "source_id": doc_id,
                    "source": source,
                    "page": page_num,
                    "text": chunk_text,
                    "metadata": meta,
                })
                c_idx += 1
            current_unit = [unit]
            current_len = unit_len

    if current_unit:
        chunk_text = "\n\n".join(current_unit).strip()
        meta = dict(page_meta)
        meta.update({
            "chunk_index": c_idx,
            "strategy": "by_paragraph",
            "char_count": len(chunk_text),
        })
        chunks.append({
            "id": f"{doc_id}_p{page_num}_b{c_idx:03d}",
            "source_id": doc_id,
            "source": source,
            "page": page_num,
            "text": chunk_text,
            "metadata": meta,
        })

    return chunks


def extract_chunks(pdf_path: Path, output_path: Path, max_size: int = 800) -> list[dict]:
    """Đọc 32 trang thuộc Chương 2, trích xuất và lưu ra file JSON."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file PDF tại: {pdf_path}")

    reader = pypdf.PdfReader(str(pdf_path))
    doc_id = "bookdata_01"
    source = "World Bank International Debt Report 2026"

    # Chương 2: trang vật lý từ 75 đến 106 (0-indexed: 74 đến 105)
    start_idx = 74
    end_idx = 106

    all_chunks: list[dict] = []

    for idx in range(start_idx, end_idx):
        phys_page = idx + 1
        raw_text = reader.pages[idx].extract_text() or ""
        clean_text = normalize_text(raw_text)

        is_empty = len(clean_text) < 50
        page_meta = {
            "section": get_section_metadata(phys_page),
            "year": 2026,
            "chapter": 2,
            "char_count": len(clean_text),
            "is_empty": is_empty,
        }

        chunks = by_paragraph(
            page_num=phys_page,
            doc_id=doc_id,
            source=source,
            text=clean_text,
            page_meta=page_meta,
            max_size=max_size,
        )
        all_chunks.extend(chunks)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    return all_chunks


def validate_chunks(chunks: list[dict]):
    """Kiểm tra tính hợp lệ dữ liệu theo schema Day 7."""
    assert len(chunks) == 108, f"Kỳ vọng đúng 108 chunks, thực tế nhận được {len(chunks)}"
    ids = set()
    for c in chunks:
        for k in ("id", "source_id", "source", "page", "text", "metadata"):
            assert k in c and c[k] is not None, f"Chunk {c.get('id')} thiếu trường {k}"
        assert c["id"] not in ids, f"Trùng ID: {c['id']}"
        ids.add(c["id"])
        assert 75 <= c["page"] <= 106, f"Trang {c['page']} ngoài phạm vi 75-106"
        assert len(c["text"].strip()) > 0, f"Chunk {c['id']} có text rỗng"


def main():
    parser = argparse.ArgumentParser(description="Trích xuất 108 chunks Day 6 sang định dạng data/chunks.json Day 7")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("../K5-L3B-DAY06-PhamHoangDucMinh-2A202604114-DataIngestion/data/bookdata_01.pdf"),
        help="Đường dẫn tới file bookdata_01.pdf",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/chunks.json"),
        help="Đường dẫn file JSON đầu ra",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=800,
        help="Kích thước tối đa của mỗi chunk (mặc định 800 ký tự)",
    )

    args = parser.parse_args()

    # Kiểm tra đường dẫn PDF thay thế nếu đường dẫn mặc định không thấy
    if not args.pdf.exists():
        fallback_pdf = Path("data/bookdata_01.pdf")
        if fallback_pdf.exists():
            args.pdf = fallback_pdf

    logging.info(f"Đang trích xuất chunks từ: {args.pdf}")
    chunks = extract_chunks(args.pdf, args.output, max_size=args.max_size)
    validate_chunks(chunks)

    logging.info(f"✅ THÀNH CÔNG: Đã trích xuất và kiểm tra đúng {len(chunks)} chunks!")
    logging.info(f"File kết quả đã được lưu tại: {args.output.resolve()}")


if __name__ == "__main__":
    main()
