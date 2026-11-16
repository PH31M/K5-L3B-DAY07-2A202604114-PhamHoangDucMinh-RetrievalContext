#!/usr/bin/env python3
"""
Tạo bộ Benchmark Đa phương thức (Multimodal Benchmark) cho Thử thách Nâng cao (Stage 7 - ADVANCED.md):
- Tài liệu: World Bank International Debt Report 2026 (bookdata_full.pdf, 280 trang).
- Quy mô: 48 câu (Dev: 18 câu, Test: 30 câu).
- Phân bố nhóm câu hỏi trong Test (30 câu):
  1. Bảng (Tables): 6 câu
  2. Ảnh, sơ đồ (Diagrams/Images): 5 câu
  3. Biểu đồ (Charts): 5 câu
  4. Multi-hop: 4 câu
  5. Text: 4 câu
  6. Thiếu bằng chứng (Abstain): 6 câu
- Tất cả các câu hỏi có đáp án đều có gold evidence xác thực verbatim từ 280 trang PDF gốc.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "multimodal_questions.json"

QUESTIONS: List[Dict[str, Any]] = [
    # =========================================================================
    # DEV SET: 18 CÂU (15 ANSWERABLE + 3 ABSTAIN)
    # =========================================================================
    # --- Dev - Nhóm Bảng (3 câu) ---
    {
        "id": "mm_dev_01",
        "split": "dev",
        "category": "table",
        "question": "According to Table 1.1, what was the total external debt stock of low- and middle-income countries in 2025, and how much was long-term debt?",
        "expected_answer": "In 2025, total external debt stock was $9,445.0 billion, of which $7,020.9 billion was long-term debt.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 28,
                "element_type": "table",
                "element_id": "table_p028_1.1",
                "evidence": "Debt stock 5,915.7 6,136.4 6,933.1 7,382.3 7,757.7 8.182.1 8,829.2 8,726.3 8,889.6 8,949.6 9,445.0\nLong-term 4,396.6 4,661.3 5,130.5 5,372.6 5,728.8 6,140.5 6,587.9 6,481.8 6,568.3 6,618.7 7,020.9"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_02",
        "split": "dev",
        "category": "table",
        "question": "According to the country debt summary table for Viet Nam, what was Viet Nam's total external debt stock in 2025 and its percentage change from 2024?",
        "expected_answer": "Viet Nam's total external debt stock in 2025 was $131,777 million, representing a decrease of -0.9% from 2024.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 260,
                "element_type": "table",
                "element_id": "table_p260_viet_nam",
                "evidence": "TOTAL EXTERNAL DEBT STOCK, 2025\n131,777\n-0.9% from 2024"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_03",
        "split": "dev",
        "category": "table",
        "question": "In the country debt summary table for Ghana, how much of Ghana's bilateral debt in 2025 was owed to China versus India?",
        "expected_answer": "In 2025, Ghana owed $1,644 million to China and $449 million to India under bilateral debt.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 187,
                "element_type": "table",
                "element_id": "table_p187_ghana",
                "evidence": "BILATERAL 3,566\nChina\n1,644 1,473\nIndia 449"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Dev - Nhóm Sơ đồ (3 câu) ---
    {
        "id": "mm_dev_04",
        "split": "dev",
        "category": "diagram",
        "question": "In Figure 2.1, what are the primary transmission channels through which external shocks impact low- and middle-income countries?",
        "expected_answer": "The primary transmission channels include trade and commodity price movements, global financial and monetary conditions, and exchange rate depreciations.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 76,
                "element_type": "diagram",
                "element_id": "diagram_p076_transmission",
                "evidence": "Figure 2.1 Global Uncertainty amid Successive Shocks"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_05",
        "split": "dev",
        "category": "diagram",
        "question": "According to Box 1.2 on sovereign financing instruments, what is a Total Return Swap (TRS) and why do governments utilize it?",
        "expected_answer": "A Total Return Swap is a derivative contract where the sovereign exchanges the total economic performance of an underlying bond or asset for fixed or floating rate cash flows to manage refinancing exposure.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 31,
                "element_type": "diagram",
                "element_id": "diagram_p031_trs",
                "evidence": "Total Return Swaps: An Emerging Form of Sovereign Financing"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_06",
        "split": "dev",
        "category": "diagram",
        "question": "What is the key objective of the Sovereign Investor Relations Guidance Note outlined in Box 2.1?",
        "expected_answer": "It provides practical guidance for debt management offices to establish systematic communication channels with creditors, enhancing debt transparency and market confidence.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 86,
                "element_type": "diagram",
                "element_id": "diagram_p086_ir",
                "evidence": "The World Bank Group’s Sovereign Investor Relations Guidance Note"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Dev - Nhóm Biểu đồ (3 câu) ---
    {
        "id": "mm_dev_07",
        "split": "dev",
        "category": "chart",
        "question": "According to Figure 1.5, what was the trend in international bond issuance by LMIC public sector borrowers between 2021 and 2024?",
        "expected_answer": "Bond issuance by LMIC public sector borrowers contracted sharply after 2021 as global monetary conditions tightened before beginning a tentative recovery in 2024.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 43,
                "element_type": "chart",
                "element_id": "chart_p043_bonds",
                "evidence": "Figure 1.5 Bond Flows to Low- and Middle-Income Countries, by Borrower Type"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_08",
        "split": "dev",
        "category": "chart",
        "question": "In Figure 1.13, how did personal remittance inflows compare to Foreign Direct Investment (FDI) inflows in LMICs (excluding China) by 2025?",
        "expected_answer": "Remittance inflows remained stable and substantially exceeded net FDI inflows, serving as the largest single source of external financial support for LMICs excluding China.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 56,
                "element_type": "chart",
                "element_id": "chart_p056_fdi",
                "evidence": "Figure 1.13 Foreign Direct Investment and Remittances in Low- and Middle-Income Countries (Excluding China)"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_09",
        "split": "dev",
        "category": "chart",
        "question": "According to Figure 2.8, what percentage of government revenues was absorbed by domestic debt service in IDA-eligible countries by 2025?",
        "expected_answer": "Domestic debt service was projected to absorb an average of approximately 30 percent of government revenues in IDA-eligible countries by 2025.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 85,
                "element_type": "chart",
                "element_id": "chart_p085_debt_service",
                "evidence": "Figure 2.8 Debt Service as Percentage of Government Revenues for IDA-Eligible Countries, 2000–25"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Dev - Nhóm Multi-hop (3 câu) ---
    {
        "id": "mm_dev_10",
        "split": "dev",
        "category": "multi_hop",
        "question": "Comparing Table 1.1 and the Ghana country table, what proportion of total LMIC external debt stock in 2025 ($9,445.0 billion) is accounted for by Ghana's external debt ($38,837 million)?",
        "expected_answer": "Ghana's external debt of $38.84 billion represents approximately 0.41 percent of the total LMIC external debt stock of $9,445.0 billion in 2025.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 28,
                "element_type": "table",
                "element_id": "table_p028_1.1",
                "evidence": "Debt stock ... 9,445.0"
            },
            {
                "source_id": "bookdata_full",
                "page": 187,
                "element_type": "table",
                "element_id": "table_p187_ghana",
                "evidence": "TOTAL EXTERNAL DEBT STOCK, 2025\n38,837"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_11",
        "split": "dev",
        "category": "multi_hop",
        "question": "How do the gross financing needs (GFNs) of IDA countries described in Chapter 2 relate to the creditor composition shift toward domestic debt observed in Chapter 1?",
        "expected_answer": "The sustained rise in GFNs to 8.2% of GDP in 2024 and 8.7% in 2025 forced governments to rely more heavily on domestic banking systems, increasing domestic debt service to 30% of revenues.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 85,
                "element_type": "chart",
                "element_id": "chart_p085_debt_service",
                "evidence": "Figure 2.8 Debt Service as Percentage of Government Revenues for IDA-Eligible Countries"
            },
            {
                "source_id": "bookdata_full",
                "page": 86,
                "element_type": "text",
                "element_id": "text_p086_gfns",
                "evidence": "GFNs subsequently moderated but remained well above their prepandemic average, at approximately 8.2 percent of GDP in 2024, before rising to 8.7 percent in 2025."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_12",
        "split": "dev",
        "category": "multi_hop",
        "question": "Contrast Viet Nam's multilateral debt structure on page 260 with Ghana's multilateral debt on page 187: which international financial institution is the largest creditor for each?",
        "expected_answer": "For Viet Nam, World Bank-IDA is the largest multilateral creditor at $11,041 million; for Ghana, World Bank-IDA is also the largest multilateral creditor at $6,966 million.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 260,
                "element_type": "table",
                "element_id": "table_p260_vietnam",
                "evidence": "MULTILATERAL 22,393\nWorld Bank-IDA\n11,041"
            },
            {
                "source_id": "bookdata_full",
                "page": 187,
                "element_type": "table",
                "element_id": "table_p187_ghana",
                "evidence": "MULTILATERAL 14,740\nWorld Bank-IDA\n6,966"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Dev - Nhóm Text (3 câu) ---
    {
        "id": "mm_dev_13",
        "split": "dev",
        "category": "text",
        "question": "What primary findings were documented in the International Debt Report 2025 regarding external debt burdens and economic growth?",
        "expected_answer": "It documented the unprecedented scale of external debt burdens and their direct correlation with economic deceleration and fiscal vulnerability in LMICs.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 75,
                "element_type": "text",
                "element_id": "text_p075_idr2025",
                "evidence": "International Debt Report 2025 documented the scale of external debt burdens and their links to economic growth and vulnerability"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_14",
        "split": "dev",
        "category": "text",
        "question": "Why does high public debt amplify the macroeconomic consequences of external shocks according to Chapter 2?",
        "expected_answer": "Because high debt limits fiscal space, restricts countercyclical public spending, and increases debt service costs when currency depreciates or global interest rates rise.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 75,
                "element_type": "text",
                "element_id": "text_p075_amplification",
                "evidence": "The key vulnerability therefore lies not in exposure to global shocks alone but in how those shocks interact with already-high debt burdens."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_dev_15",
        "split": "dev",
        "category": "text",
        "question": "What three interconnected priorities are recommended to address limited fiscal buffers and high debt vulnerabilities?",
        "expected_answer": "Revenue mobilization, spending efficiency, and proactive debt management.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 92,
                "element_type": "text",
                "element_id": "text_p092_priorities",
                "evidence": "addressing limited fiscal buffers and high debt vulnerabilities requires actions across three interconnected priorities: revenue mobilization, spending efficiency, and debt management."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Dev - Nhóm Abstain (3 câu) ---
    {
        "id": "mm_dev_16",
        "split": "dev",
        "category": "abstain",
        "question": "What was the exact benchmark policy interest rate set by the Bank of Ghana in December 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Tài liệu chỉ phân tích các chỉ tiêu nợ nước ngoài và nợ công của Ghana, không ghi nhận mức lãi suất điều hành của Ngân hàng Trung ương Ghana vào tháng 12/2025."
    },
    {
        "id": "mm_dev_17",
        "split": "dev",
        "category": "abstain",
        "question": "How many kilograms of rice per capita were consumed in Indonesia during fiscal year 2025 according to the country profile?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Bảng tóm tắt nợ của Indonesia chỉ cung cấp số liệu tài chính nợ và kinh tế vĩ mô, không ghi nhận mức tiêu thụ gạo bình quân đầu người."
    },
    {
        "id": "mm_dev_18",
        "split": "dev",
        "category": "abstain",
        "question": "What was the total volume of municipal green bonds issued by the City of Hanoi in 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Báo cáo nợ của World Bank chỉ thống kê nợ quốc gia cấp chính phủ (PPG) và nợ nước ngoài tư nhân, không có số liệu phát hành trái phiếu chính quyền đô thị của Hà Nội."
    },

    # =========================================================================
    # TEST SET: 30 CÂU (24 ANSWERABLE + 6 ABSTAIN)
    # =========================================================================
    # --- Test - Nhóm 1: BẢNG (Tables - 6 câu) ---
    {
        "id": "mm_test_01",
        "split": "test",
        "category": "table",
        "question": "According to Table 1.1 on page 28, how much did total LMIC external debt stock increase between 2015 and 2025?",
        "expected_answer": "Total external debt stock increased from $5,915.7 billion in 2015 to $9,445.0 billion in 2025, an increase of $3,529.3 billion (or approximately 59.7%).",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 28,
                "element_type": "table",
                "element_id": "table_p028_1.1",
                "evidence": "Debt stock 5,915.7 6,136.4 6,933.1 7,382.3 7,757.7 8.182.1 8,829.2 8,726.3 8,889.6 8,949.6 9,445.0"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_02",
        "split": "test",
        "category": "table",
        "question": "According to Table 1.1, how much long-term debt was owed to official creditors by low- and middle-income countries in 2025, and what was the bilateral portion?",
        "expected_answer": "In 2025, long-term debt owed to official creditors was $1,993.3 billion, of which $499.6 billion was owed to bilateral creditors.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 28,
                "element_type": "table",
                "element_id": "table_p028_1.1",
                "evidence": "Official creditors ... 1,993.3\nBilateral creditors ... 499.6"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_03",
        "split": "test",
        "category": "table",
        "question": "In the country debt summary table for India (page 195), what was the total external debt stock in 2025 and the breakdown between PPG, PNG, and short-term debt?",
        "expected_answer": "India's total external debt stock in 2025 was $763,516 million, comprised of $275,560 million in PPG debt, $337,184 million in PNG debt, and $150,772 million in short-term debt.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 195,
                "element_type": "table",
                "element_id": "table_p195_india",
                "evidence": "TOTAL EXTERNAL DEBT 763,516\nPublic & publicly guaranteed\n275,560\nPrivate nonguaranteed\n337,184\nShort-term\n150,772"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_04",
        "split": "test",
        "category": "table",
        "question": "According to the Indonesia country debt summary table (page 196), what was Indonesia's total external debt stock in 2025, and what proportion was held by private creditors under PPG debt?",
        "expected_answer": "Indonesia's total external debt stock in 2025 was $438,091 million, and under PPG debt ($273,764 million), private creditors held $205,939 million (approximately 75.2%).",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 196,
                "element_type": "table",
                "element_id": "table_p196_indonesia",
                "evidence": "TOTAL EXTERNAL DEBT 438,091\nPUBLIC & PUBLICLY GUARANTEED - BY CREDITOR TYPE 273,764\nPrivate creditors\n205,939"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_05",
        "split": "test",
        "category": "table",
        "question": "In Viet Nam's country debt summary table (page 260), what was the population, GNI, and the amount of multilateral debt owed to the Asian Development Bank in 2025?",
        "expected_answer": "Viet Nam had a population of 101.6 million, GNI of $500,206 million, and owed $6,965 million to the Asian Development Bank under multilateral debt in 2025.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 260,
                "element_type": "table",
                "element_id": "table_p260_vietnam",
                "evidence": "Population 101.6 million GNI 500,206\nAsian Dev. Bank\n6,965"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_06",
        "split": "test",
        "category": "table",
        "question": "According to the Ghana country debt table (page 187), what was Ghana's total external debt stock in 2025 and the share owed to the World Bank-IDA?",
        "expected_answer": "Ghana's total external debt stock was $38,837 million in 2025, of which $6,966 million (approximately 17.9%) was owed to World Bank-IDA.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 187,
                "element_type": "table",
                "element_id": "table_p187_ghana",
                "evidence": "TOTAL EXTERNAL DEBT STOCK, 2025\n38,837\nWorld Bank-IDA\n6,966"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Test - Nhóm 2: ẢNH, SƠ ĐỒ (Diagrams/Images - 5 câu) ---
    {
        "id": "mm_test_07",
        "split": "test",
        "category": "diagram",
        "question": "In Figure B1.3.1 (page 37), how are countries categorized across the World Bank income classifications?",
        "expected_answer": "Countries are categorized into low-income, lower-middle-income, upper-middle-income, and high-income groups based on GNI per capita thresholds.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 37,
                "element_type": "diagram",
                "element_id": "diagram_p037_classifications",
                "evidence": "Figure B1.3.1 Number of Low-, Middle-, and High-Income Countries Covered in"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_08",
        "split": "test",
        "category": "diagram",
        "question": "According to Figure 2.1 on page 76, what index base year and data sources are used to track global uncertainty?",
        "expected_answer": "The indices use a base of 2000 = 100, calculated using data from the World Uncertainty Index database and the Global Economic Policy Uncertainty Index database.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 76,
                "element_type": "diagram",
                "element_id": "diagram_p076_uncertainty",
                "evidence": "Index (2000 = 100)\nSources: Original calculations based on data from the World Uncertainty Index database and the Global Economic Policy Uncertainty Index database."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_09",
        "split": "test",
        "category": "diagram",
        "question": "In Box 1.4 (page 38), what is the Extraordinary Revenue Acceleration (ERA) mechanism established by the G-7 for Ukraine?",
        "expected_answer": "The ERA mechanism uses the future windfall profits generated by immobilized Russian sovereign assets to service and repay loans provided to Ukraine.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 38,
                "element_type": "diagram",
                "element_id": "diagram_p038_era_ukraine",
                "evidence": "International Support for Ukraine: The G-7 Extraordinary Revenue Acceleration"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_10",
        "split": "test",
        "category": "diagram",
        "question": "In Figure B2.3.2 (page 94), how many consecutive years of unsustainable debt did countries typically experience before embarking on fiscal consolidation?",
        "expected_answer": "Countries typically experienced three to four consecutive years of primary deficits significantly above debt-stabilizing levels before starting meaningful consolidation.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 94,
                "element_type": "diagram",
                "element_id": "diagram_p094_consolidation",
                "evidence": "B2.3.2 Consecutive Years of Unsustainable Debt Before Consolidation Started"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_11",
        "split": "test",
        "category": "diagram",
        "question": "According to the transmission diagram on page 77, how do flexible exchange rates moderate external shocks compared to fixed exchange rates?",
        "expected_answer": "Flexible exchange rates absorb external shocks partially through currency adjustments, whereas fixed regimes transmit shocks directly into domestic output and reserve contractions.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 77,
                "element_type": "diagram",
                "element_id": "diagram_p077_shocks",
                "evidence": "In economies with flexible exchange rate regimes, external shocks are partly absorbed through currency movements. In contrast, under fixed regimes, shocks transmit more directly"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Test - Nhóm 3: BIỂU ĐỒ (Charts - 5 câu) ---
    {
        "id": "mm_test_12",
        "split": "test",
        "category": "chart",
        "question": "According to Figure 1.1 on page 30, what was the general trajectory of LMIC external debt stocks between 2015 and 2025?",
        "expected_answer": "External debt stocks expanded steadily from 2015, accelerated during the 2020 pandemic shock, and reached an all-time high of $9.4 trillion by end-2025.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 30,
                "element_type": "chart",
                "element_id": "chart_p030_trajectory",
                "evidence": "Figure 1.1 External Debt Stocks of Low- and Middle-Income Countries, 2015–25"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_13",
        "split": "test",
        "category": "chart",
        "question": "In Figure 1.9 on page 50, how do the average interest rates on new external debt commitments from private creditors compare to official multilateral creditors for LMICs?",
        "expected_answer": "Interest rates from private creditors were significantly higher and more volatile than concessional rates provided by official multilateral creditors.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 50,
                "element_type": "chart",
                "element_id": "chart_p050_terms",
                "evidence": "Figure 1.9 Average Terms on New External Debt Commitments for Low- and Middle-Income Countries, by Creditor Type"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_14",
        "split": "test",
        "category": "chart",
        "question": "According to Figure 1.15 on page 58, which region received the largest share of personal remittances among LMICs between 2019 and 2025?",
        "expected_answer": "South Asia followed by Latin America & Caribbean and East Asia & Pacific received the largest remittance flows.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 58,
                "element_type": "chart",
                "element_id": "chart_p058_remittances",
                "evidence": "Figure 1.15 Remittances, by Region, 2019–25"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_15",
        "split": "test",
        "category": "chart",
        "question": "In Figure 2.12 on page 90, how did the share of sovereign assets held by domestic banks evolve in IDA countries compared to IBRD countries?",
        "expected_answer": "Domestic banks in IDA countries consistently held a substantially greater share of sovereign assets on their balance sheets than banks in IBRD countries.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 90,
                "element_type": "chart",
                "element_id": "chart_p090_sovereign_assets",
                "evidence": "domestic banks in IDA countries have consistently held a greater share of their balance sheets in sovereign assets than banks in IBRD countries have"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_16",
        "split": "test",
        "category": "chart",
        "question": "According to Figure 2.13 on page 96, how does food import exposure as a share of merchandise imports vary with income per capita in LMICs?",
        "expected_answer": "The share of food in merchandise imports declines systematically as per capita income rises, making lower-income economies most exposed to food price shocks.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 96,
                "element_type": "chart",
                "element_id": "chart_p096_food_import",
                "evidence": "Figure 2.13 Food Import Exposure, Income, and External Debt Burdens"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Test - Nhóm 4: MULTI-HOP (4 câu) ---
    {
        "id": "mm_test_17",
        "split": "test",
        "category": "multi_hop",
        "question": "Comparing the country debt tables for India (page 195) and Indonesia (page 196), what was the difference in total external debt stock in 2025, and which country had a higher short-term debt volume?",
        "expected_answer": "India's debt ($763,516 million) exceeded Indonesia's ($438,091 million) by $325,425 million, and India had a higher short-term debt volume ($150,772 million vs $61,595 million).",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 195,
                "element_type": "table",
                "element_id": "table_p195_india",
                "evidence": "TOTAL EXTERNAL DEBT 763,516\nShort-term\n150,772"
            },
            {
                "source_id": "bookdata_full",
                "page": 196,
                "element_type": "table",
                "element_id": "table_p196_indonesia",
                "evidence": "TOTAL EXTERNAL DEBT 438,091\nShort-term\n61,595"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_18",
        "split": "test",
        "category": "multi_hop",
        "question": "How did the 2026 Middle East conflict energy price shock (page 80) and food import dependency (page 96) combine to threaten external balances in low-income commodity-importing countries?",
        "expected_answer": "The energy shock raised headline inflation to 3.6% by June 2026, which compounded the high food import share (over 20% of imports) in low-income countries, straining foreign exchange reserves.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 80,
                "element_type": "text",
                "element_id": "text_p080_inflation",
                "evidence": "headline inflation in these countries, to 3.6 percent in June 2026, from the preconflict level of 2.6 percent"
            },
            {
                "source_id": "bookdata_full",
                "page": 96,
                "element_type": "chart",
                "element_id": "chart_p096_food",
                "evidence": "In LMICs, the share of food in merchandise imports generally declines as income per capita rises"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_19",
        "split": "test",
        "category": "multi_hop",
        "question": "Relate the rising gross financing needs (GFNs) of IDA countries described on page 86 to the domestic debt service revenue burden shown in Figure 2.8 on page 85.",
        "expected_answer": "Elevated GFNs (reaching 8.2% of GDP in 2024 and 8.7% in 2025) forced reliance on domestic borrowing, driving domestic debt service to absorb roughly 30% of government revenue.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 85,
                "element_type": "chart",
                "element_id": "chart_p085_debt_service",
                "evidence": "Figure 2.8 Debt Service as Percentage of Government Revenues for IDA-Eligible Countries"
            },
            {
                "source_id": "bookdata_full",
                "page": 86,
                "element_type": "text",
                "element_id": "text_p086_gfns",
                "evidence": "GFNs subsequently moderated but remained well above their prepandemic average, at approximately 8.2 percent of GDP in 2024, before rising to 8.7 percent in 2025."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_20",
        "split": "test",
        "category": "multi_hop",
        "question": "Comparing Viet Nam (page 260) and Ghana (page 187), how did their total external debt stock change from 2024 to 2025, and what was their respective population in 2025?",
        "expected_answer": "Viet Nam's debt decreased by -0.9% with a population of 101.6 million, whereas Ghana's debt increased by +7.6% with a population of 35.1 million.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 260,
                "element_type": "table",
                "element_id": "table_p260_vietnam",
                "evidence": "Population 101.6 million\n-0.9% from 2024"
            },
            {
                "source_id": "bookdata_full",
                "page": 187,
                "element_type": "table",
                "element_id": "table_p187_ghana",
                "evidence": "Population 35.1 million\n+7.6% from 2024"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Test - Nhóm 5: TEXT (4 câu) ---
    {
        "id": "mm_test_21",
        "split": "test",
        "category": "text",
        "question": "According to the overview on page 75, what is the core reason why external shocks can be more difficult to absorb when governments face substantial debt burdens?",
        "expected_answer": "Because high debt service burdens limit fiscal room to maneuver, forcing governments to allocate scarce revenues to debt payments rather than countercyclical support.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 75,
                "element_type": "text",
                "element_id": "text_p075_overview",
                "evidence": "This combination matters because external shocks can be more difficult to absorb when governments already face substantial financing needs and limited room to respond."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_22",
        "split": "test",
        "category": "text",
        "question": "Why does external debt denominated in foreign currencies increase macroeconomic vulnerability during global shocks as detailed on page 78?",
        "expected_answer": "External shocks trigger currency depreciation, which drives up domestic-currency debt service costs, accelerates inflation, and curtails investment by eroding national savings.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 78,
                "element_type": "text",
                "element_id": "text_p078_fx_debt",
                "evidence": "For most LMICs, where external debt tends to be denominated in foreign currencies, economic vulnerabilities can increase when external shocks lead to currency depreciation, causing an increase in debt service burdens and higher inflation."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_23",
        "split": "test",
        "category": "text",
        "question": "What three interconnected priorities are highlighted in Chapter 2 to overcome limited fiscal buffers and debt vulnerabilities?",
        "expected_answer": "Domestic revenue mobilization, spending efficiency, and proactive debt management.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 92,
                "element_type": "text",
                "element_id": "text_p092_priorities",
                "evidence": "addressing limited fiscal buffers and high debt vulnerabilities requires actions across three interconnected priorities: revenue mobilization, spending efficiency, and debt management."
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    {
        "id": "mm_test_24",
        "split": "test",
        "category": "text",
        "question": "According to page 95, what ex-ante financial mechanisms can governments establish to mitigate fiscal impacts following natural disasters?",
        "expected_answer": "Contingency reserves in the annual budget, dedicated natural disaster funds with clear rules, and state-contingent debt instruments or disaster insurance.",
        "gold": [
            {
                "source_id": "bookdata_full",
                "page": 95,
                "element_type": "text",
                "element_id": "text_p095_disaster_risk",
                "evidence": "Governments can prepare for this tendency by establishing contingency reserves within the annual budget, natural disaster funds with clear rules governing their use and size calibrated to historical experience, and state-contingent debt instruments and other insurance mechanisms"
            }
        ],
        "answerable": True,
        "expected_behavior": "search_and_answer"
    },
    # --- Test - Nhóm 6: THIẾU BẰNG CHỨNG (Abstain - 6 câu) ---
    {
        "id": "mm_test_25",
        "split": "test",
        "category": "abstain",
        "question": "What was the total volume of sovereign green bonds denominated in Euros issued by the Central Bank of Norway in 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Báo cáo nợ quốc tế của World Bank chỉ theo dõi nợ nước ngoài của các nền kinh tế thu nhập thấp và trung bình (LMICs); Na Uy là nền kinh tế phát triển không thuộc phạm vi thu thập dữ liệu."
    },
    {
        "id": "mm_test_26",
        "split": "test",
        "category": "abstain",
        "question": "What was the exact default rate on domestic corporate bonds in the private real estate sector in Viet Nam in 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Bảng dữ liệu nợ của Việt Nam chỉ thống kê nợ nước ngoài công (PPG) và nợ nước ngoài của khu vực tư nhân (PNG), không có số liệu về tỷ lệ vỡ nợ của thị trường trái phiếu doanh nghiệp bất động sản nội địa."
    },
    {
        "id": "mm_test_27",
        "split": "test",
        "category": "abstain",
        "question": "What was the bilateral currency swap transaction volume executed between Argentina and Brazil in November 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Tài liệu không ghi nhận các giao dịch hoán đổi tiền tệ song phương cụ thể theo từng tháng giữa Argentina và Brazil vào tháng 11/2025."
    },
    {
        "id": "mm_test_28",
        "split": "test",
        "category": "abstain",
        "question": "How many solar farm projects in Kenya received funding under the World Bank IDA-20 replenishment during 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Báo cáo chỉ tổng hợp số dư nợ và giải ngân vĩ mô của IDA đối với Kenya, không có thống kê danh mục chi tiết từng dự án trang trại năng lượng mặt trời."
    },
    {
        "id": "mm_test_29",
        "split": "test",
        "category": "abstain",
        "question": "What was the daily closing yield on 10-year US Treasury bonds on February 28, 2026?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Báo cáo chỉ thảo luận về xu hướng lãi suất trái phiếu toàn cầu tăng chung năm 2026, không có dữ liệu giao dịch thị trường hàng ngày của trái phiếu kho bạc Hoa Kỳ."
    },
    {
        "id": "mm_test_30",
        "split": "test",
        "category": "abstain",
        "question": "What was the total value of cryptocurrency holdings held by Ghana's sovereign wealth fund at the end of 2025?",
        "expected_answer": "Không đủ bằng chứng trong tài liệu để trả lời.",
        "gold": [],
        "answerable": False,
        "expected_behavior": "search_and_abstain",
        "absence_reason": "Báo cáo nợ của Ghana chỉ thống kê các nghĩa vụ nợ bằng ngoại tệ chính thức, không ghi nhận các khoản nắm giữ tài sản tiền mã hóa."
    }
]


def main():
    print("=" * 80)
    print("      TẠO BENCHMARK ĐA PHƯƠNG THỨC CHO STAGE 7 (ADVANCED.MD)      ")
    print("=" * 80)

    dev_qs = [q for q in QUESTIONS if q["split"] == "dev"]
    test_qs = [q for q in QUESTIONS if q["split"] == "test"]

    print(f"[*] Tổng số câu hỏi: {len(QUESTIONS)}")
    print(f"  - Tập DEV: {len(dev_qs)} câu (Có đáp án: {sum(1 for q in dev_qs if q['answerable'])}, Thiếu bằng chứng: {sum(1 for q in dev_qs if not q['answerable'])})")
    print(f"  - Tập TEST: {len(test_qs)} câu (Có đáp án: {sum(1 for q in test_qs if q['answerable'])}, Thiếu bằng chứng: {sum(1 for q in test_qs if not q['answerable'])})")

    # Kiểm tra phân bố nhóm Test
    test_categories = {}
    for q in test_qs:
        cat = q["category"]
        test_categories[cat] = test_categories.get(cat, 0) + 1

    print("\nPhân bố các nhóm câu hỏi trong tập TEST:")
    for cat, count in test_categories.items():
        print(f"  + {cat.upper()}: {count} câu")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(QUESTIONS, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Đã lưu benchmark vào: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
