#!/usr/bin/env python3
"""
Bộ trích xuất và lập chỉ mục đa phương thức (Multimodal Indexing) cho tài liệu 280 trang:
World Bank International Debt Report 2026 (bookdata_full.pdf).
Trích xuất:
1. Văn bản (Text)
2. Bảng biểu thống kê (Tables - bao gồm các bảng nợ quốc gia chi tiết trang 138-240)
3. Biểu đồ (Charts - dữ liệu trục, chú giải, xu hướng)
4. Sơ đồ (Diagrams - sơ đồ lây truyền, cơ chế thể chế)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pypdf

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data" / "bookdata_full.pdf"
OUTPUT_CHUNKS = ROOT / "data" / "multimodal_chunks.json"


def clean_text(text: str) -> str:
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_multimodal_chunks(pdf_path: Path) -> List[Dict[str, Any]]:
    print(f"[*] Đang đọc toàn bộ 280 trang từ file: {pdf_path.name}...")
    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    print(f"[*] Tổng số trang phát hiện: {total_pages}")

    chunks: List[Dict[str, Any]] = []

    for page_idx in range(total_pages):
        page_num = page_idx + 1  # 1-indexed
        raw_text = reader.pages[page_idx].extract_text() or ""
        text = clean_text(raw_text)

        if not text:
            continue

        # 1. Nhận diện Table 1.1 hoặc Table 1.2 trong Chapter 1
        if "Table 1.1" in text or "Table 1.2" in text:
            if "Table 1.1" in text and "Box 1.1" in text:
                # Tách Table 1.1 và Box 1.1 thành 2 chunks riêng biệt
                parts = text.split("Box 1.1", 1)
                t_text = parts[0].strip()
                b_text = ("Box 1.1 " + parts[1]).strip()

                tbl_id = f"table_p{page_num:03d}_1_1"
                t_header = f"[{tbl_id} | World Bank International Debt Report 2026 | page {page_num} | TABLE: Table 1.1 External Debt Stock of Low- and Middle-Income Countries, 2015–25]\n"
                chunks.append({
                    "id": tbl_id,
                    "source_id": "bookdata_full",
                    "source": "World Bank International Debt Report 2026",
                    "page": page_num,
                    "element_type": "table",
                    "title": "Table 1.1 External Debt Stock of Low- and Middle-Income Countries, 2015–25",
                    "text": t_header + t_text,
                    "metadata": {
                        "page": page_num,
                        "element_type": "table",
                        "category": "chapter_table",
                        "char_count": len(t_text),
                    }
                })

                box_id = f"diagram_p{page_num:03d}_box1_1"
                b_header = f"[{box_id} | World Bank International Debt Report 2026 | page {page_num} | DIAGRAM / BOX: Box 1.1 External Debt Data Concepts]\n"
                chunks.append({
                    "id": box_id,
                    "source_id": "bookdata_full",
                    "source": "World Bank International Debt Report 2026",
                    "page": page_num,
                    "element_type": "diagram",
                    "title": "Box 1.1 External Debt Data: Concepts, Sources, and Coverage",
                    "text": b_header + b_text,
                    "metadata": {
                        "page": page_num,
                        "element_type": "diagram",
                        "char_count": len(b_text),
                    }
                })
                continue
            else:
                tbl_title = "Table 1.1 External Debt Stock of Low- and Middle-Income Countries, 2015–25" if "Table 1.1" in text else "Table 1.2 Net Debt Inflows to IDA-Eligible Countries, 2015–25"
                tbl_id = f"table_p{page_num:03d}_{'1_1' if 'Table 1.1' in text else '1_2'}"
                header = f"[{tbl_id} | World Bank International Debt Report 2026 | page {page_num} | TABLE: {tbl_title}]\n"
                chunks.append({
                    "id": tbl_id,
                    "source_id": "bookdata_full",
                    "source": "World Bank International Debt Report 2026",
                    "page": page_num,
                    "element_type": "table",
                    "title": tbl_title,
                    "text": header + text,
                    "metadata": {
                        "page": page_num,
                        "element_type": "table",
                        "category": "chapter_table",
                        "char_count": len(text),
                    }
                })
                continue

        # 2. Nhận diện Country Debt Summary Table (Trang 138-240)
        if "TOTAL EXTERNAL DEBT STOCK" in text and ("Figure 1 Total external debt" in text or "PUBLIC & PUBLICLY GUARANTEED" in text or "Data as reported" in text):
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            country_name = "Unknown"
            for line in lines[:6]:
                if line.isupper() and len(line) > 2 and "INTERNATIONAL" not in line and "DEBT" not in line and "REPORT" not in line and "PAGE" not in line and "SOURCE" not in line and "TOTAL" not in line:
                    country_name = line
                    break

            chunk_id = f"table_p{page_num:03d}_{country_name.lower().replace(' ', '_').replace(',', '')}"
            header = f"[{chunk_id} | World Bank International Debt Report 2026 | page {page_num} | Country: {country_name} | TABLE: Summary External Debt Data]\n"
            chunks.append({
                "id": chunk_id,
                "source_id": "bookdata_full",
                "source": "World Bank International Debt Report 2026",
                "page": page_num,
                "element_type": "table",
                "title": f"Summary External Debt Data - {country_name}",
                "country": country_name,
                "text": header + text,
                "metadata": {
                    "page": page_num,
                    "element_type": "table",
                    "category": "country_table",
                    "country": country_name,
                    "char_count": len(text),
                }
            })
            continue

        # 3. Nhận diện Sơ đồ / Khung phân tích (Diagrams / Boxes)
        is_diagram = (
            ("Transmission channels" in text and "external shocks" in text) or
            ("Figure 2.1" in text and "Uncertainty" in text) or
            ("Box 1.2" in text or "Total Return Swaps" in text) or
            ("Box 1.4" in text or "Extraordinary Revenue Acceleration" in text) or
            ("Box 2.1" in text or "Investor Relations" in text) or
            ("Figure B" in text)
        )
        if is_diagram:
            diag_id = f"diagram_p{page_num:03d}"
            header = f"[{diag_id} | World Bank International Debt Report 2026 | page {page_num} | DIAGRAM / BOX]\n"
            chunks.append({
                "id": diag_id,
                "source_id": "bookdata_full",
                "source": "World Bank International Debt Report 2026",
                "page": page_num,
                "element_type": "diagram",
                "title": f"Analytical Diagram / Box on Page {page_num}",
                "text": header + text,
                "metadata": {
                    "page": page_num,
                    "element_type": "diagram",
                    "char_count": len(text),
                }
            })
            continue

        # 4. Nhận diện Biểu đồ (Charts)
        has_chart = bool(re.search(r"Figure\s+\d+\.\d+", text))
        if has_chart:
            fig_match = re.search(r"Figure\s+[\d\.]+[^\n\r]+", text)
            fig_title = fig_match.group(0).strip() if fig_match else "Chart"
            chart_id = f"chart_p{page_num:03d}"
            header = f"[{chart_id} | World Bank International Debt Report 2026 | page {page_num} | CHART: {fig_title}]\n"
            chunks.append({
                "id": chart_id,
                "source_id": "bookdata_full",
                "source": "World Bank International Debt Report 2026",
                "page": page_num,
                "element_type": "chart",
                "title": f"{fig_title} on Page {page_num}",
                "text": header + text,
                "metadata": {
                    "page": page_num,
                    "element_type": "chart",
                    "char_count": len(text),
                }
            })
            continue

        # 5. Text Chunks (Chia theo đoạn ~800 ký tự)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        curr_text = ""
        b_idx = 0
        for para in paragraphs:
            if len(curr_text) + len(para) + 2 > 800 and curr_text:
                t_id = f"text_p{page_num:03d}_b{b_idx:03d}"
                header = f"[{t_id} | World Bank International Debt Report 2026 | page {page_num} | TEXT]\n"
                chunks.append({
                    "id": t_id,
                    "source_id": "bookdata_full",
                    "source": "World Bank International Debt Report 2026",
                    "page": page_num,
                    "element_type": "text",
                    "title": f"Report Content Page {page_num} Part {b_idx}",
                    "text": header + curr_text.strip(),
                    "metadata": {
                        "page": page_num,
                        "element_type": "text",
                        "char_count": len(curr_text.strip()),
                    }
                })
                curr_text = para
                b_idx += 1
            else:
                curr_text = (curr_text + "\n\n" + para).strip() if curr_text else para

        if curr_text:
            t_id = f"text_p{page_num:03d}_b{b_idx:03d}"
            header = f"[{t_id} | World Bank International Debt Report 2026 | page {page_num} | TEXT]\n"
            chunks.append({
                "id": t_id,
                "source_id": "bookdata_full",
                "source": "World Bank International Debt Report 2026",
                "page": page_num,
                "element_type": "text",
                "title": f"Report Content Page {page_num} Part {b_idx}",
                "text": header + curr_text.strip(),
                "metadata": {
                    "page": page_num,
                    "element_type": "text",
                    "char_count": len(curr_text.strip()),
                }
            })

    return chunks


def main():
    print("=" * 80)
    print("     TRÍCH XUẤT CHỈ MỤC ĐA PHƯƠNG THỨC (STAGE 7 - MULTIMODAL INDEXING)     ")
    print("=" * 80)

    chunks = extract_multimodal_chunks(PDF_PATH)
    print(f"\n[+] Tổng số chunks/elements đa phương thức được lập chỉ mục: {len(chunks)}")

    type_counts = {}
    for c in chunks:
        t = c["element_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\nThống kê phân bố các phần tử đa phương thức:")
    for t, cnt in type_counts.items():
        print(f"  - {t.upper()}: {cnt} chunks")

    OUTPUT_CHUNKS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CHUNKS, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Đã lưu chỉ mục vào: {OUTPUT_CHUNKS} (Kích thước: {OUTPUT_CHUNKS.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
