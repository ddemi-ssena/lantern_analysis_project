# app/services/data_parser.py
from typing import Dict, List, Tuple
import re

def parse_report_file(file_path: str) -> Dict:
    """
    Verilen txt dosyasını okur ve yapısal bir dictionary'ye dönüştürür.
    
    Args:
        file_path: Okunacak .txt dosyasının yolu.

    Returns:
        {'report_text': '...', 'answers': [...] } formatında bir dictionary.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- AYRAÇLARA GÖRE METNİ BÖL ---
    pdf_section_match = re.search(r'--- PDF METNİ ---\n(.*?)\n--- SORU-CEVAPLAR ---', content, re.DOTALL)
    qa_section_raw = re.search(r'--- SORU-CEVAPLAR ---\n(.*)', content, re.DOTALL)

    if not pdf_section_match or not qa_section_raw:
        raise ValueError("Dosya formatı bozuk. Gerekli ayraçlar bulunamadı.")

    report_text = pdf_section_match.group(1).strip()
    
    # --- SORU-CEVAP BÖLÜMLERİNİ AYIR ---
    answers_list = []
    # Her bir soru-cevap bloğunu "---" ayraçlarına göre böl
    qa_blocks = qa_section_raw.group(1).strip().split('---')

    for block in qa_blocks:
        if not block.strip():
            continue

        question_match = re.search(r'question: (.*?)\n', block)
        category_match = re.search(r'category: (.*?)\n', block)
        answer_match = re.search(r'answer: (.*)', block, re.DOTALL)

        if question_match and category_match and answer_match:
            answers_list.append({
                "question": question_match.group(1).strip(),
                "category": category_match.group(1).strip(),
                "answer": answer_match.group(1).strip()
            })

    return {
        "report_text": report_text,
        "answers": answers_list
    }