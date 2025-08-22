from transformers import pipeline
from . import narrative_generator
import re
import numpy as np
import os
import pdfplumber
import spacy

# --- MODELLERİ YÜKLEME ---
try:
    print("AI Modelleri yükleniyor... Bu işlem birkaç dakika sürebilir.")
    SENTIMENT_ANALYZER = pipeline("sentiment-analysis", model="ssenos/lantern_fine-tuning-v3") # En son eğittiğin versiyonu kullan
    print("SpaCy Transformer (TRF) modeli yükleniyor...")
    NLP = spacy.load("tr_core_news_trf")
    print("Tüm modeller başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Modeller yüklenemedi. Hata: {e}")
    SENTIMENT_ANALYZER = None
    NLP = None

# --- YARDIMCI ANALİZ FONKSİYONLARI ---

def load_corpus_from_local_pdfs() -> list[str]:
    # ... (Bu fonksiyon doğru ve tam, değişiklik yok) ...
    corpus = []
    corpus_folder = "corpus_pdfs"
    if not os.path.isdir(corpus_folder): return []
    for filename in os.listdir(corpus_folder):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(corpus_folder, filename)
            try:
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text: text += page_text + "\n"
                corpus.append(text)
            except Exception as e:
                print(f"UYARI: '{filename}' okunamadı: {e}")
    return corpus

def extract_definitive_keywords(text: str, top_n: int = 7) -> list[str]:
    """
    Sadece bizim tanımladığımız teknik terimler ve SpaCy'ın bulduğu
    kesin varlıklar üzerinden anahtar kelime çıkarır. (Düzeltilmiş ve Temizlenmiş)
    """
    if not NLP: return []
    try:
        keywords = set()
        text_lower = text.lower()

        known_techs = [
            "docker", "docker-compose", "postgresql", "spring boot", "spring security", "java", 
            "python", "fastapi", "vue.js", "react", "axios", "ci/cd", "pipeline", "kubernetes", 
            "sql", "jwt", "api", "rest", "spacy", "network security group", "sanal makine", 
            "veritabanı", "entity", "repository", "controller", "endpoint", "dependency", 
            "dbeaver", "junit", "mockito", "refactor", "@preauthorize", "scoped styles", 
            "connection refused", "403 forbidden", "network error", "nullpointerexception", "git", "github",
            "kabul kriterleri", "acceptance criteria", "explain analyze", "join", "sorgu planı"
        ]
        keywords.update({tech for tech in known_techs if tech in text_lower})

        doc = NLP(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"] and len(ent.text.strip()) > 2:
                if ent.text.lower() not in ["zeynep", "ayşe", "can", "ahmet"]:
                    keywords.add(ent.text.lower())
        
        return list(keywords)[:top_n]
    except Exception as e:
        print(f"Anahtar kelime çıkarımı hatası: {e}")
        return []

def analyze_process_satisfaction(answer: str) -> dict:
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    label = sentiment['label']
    status_map = {"Olumlu Gelişim": "Yüksek Motivasyon", "Proaktif / Fikir": "Yüksek Motivasyon", "Olumsuz Duygu / Demotive": "Düşük Motivasyon", "Engellenmiş / Yardım İhtiyacı": "Düşük Motivasyon", "İşbirliği / İletişim": "Orta", "Nötr Raporlama": "Orta"}
    status = status_map.get(label, "Orta")
    return {"status": status}

def analyze_proactiveness(answer: str) -> dict:
    action_words = ["hedefliyorum", "planliyorum", "yapacagim", "istiyorum", "cozecegim", "onerim", "fikrim", "eklersek", "iyilestirebiliriz", "olmali", "olabilir", "kabul kriterleri", "daha iyi yapabilirim"]
    if any(word in answer.lower() for word in action_words): return {"status": "Çözüm Odaklı"}
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    return {"status": "Çözüm Odaklı"} if sentiment['label'] == "Proaktif / Fikir" else {"status": "Pasif"}

def analyze_collaboration(answer: str) -> dict:
    help_words = ["yardım istedim", "danıştım", "yardımcı oldu", "birlikte çözdük", "yardımcı olmaya çalıştım", "birlikte kafa yorduk", "beyin fırtınası", "yardımım dokundu"]
    if any(word in answer.lower() for word in help_words): return {"status": "Aktif İletişim"}
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    return {"status": "Aktif İletişim"} if sentiment['label'] == "İşbirliği / İletişim" else {"status": "Nötr İletişim"}

# --- ANA ANALİZ FONKSİYONU (BAŞTAN SONA TUTARLI HALE GETİRİLDİ) ---

def run_full_analysis(report_data: dict) -> dict:
    if not SENTIMENT_ANALYZER or not NLP:
        return {"error": "AI modelleri yüklenemediği için analiz yapılamıyor."}

    # Adım 1: Veriyi Hazırla
    full_text = report_data['report_text'] + " " + " ".join([item['answer'] for item in report_data['answers']])
    
    # Adım 2: Kategori Bazlı Analizler
    category_results = {}
    for item in report_data['answers']:
        category, answer = item['category'], item['answer']
        if category == "Süreç Memnuniyeti": category_results['satisfaction'] = analyze_process_satisfaction(answer)
        elif category == "Proaktiflik": category_results['proactive'] = analyze_proactiveness(answer)
        elif category == "İşbirliği / İletişim": category_results['collaboration'] = analyze_collaboration(answer)

    # Adım 3: Bütünsel Analizler (Sinyaller ve Anahtar Kelimeler)
    text_lower = full_text.lower()
    positive_signals = {"başarı": ["başardım", "çözdüm", "tamamladım", "çalıştı"]}
    negative_signals = {"engel": ["hata aldım", "çözemedim", "ilerleyemedim"], "demotivasyon": ["motivasyonum düşüktü", "moralim bozuldu"]}
    found_pos_signals = {stype for stype, words in positive_signals.items() if any(w in text_lower for w in words)}
    found_neg_signals = {stype for stype, words in negative_signals.items() if any(w in text_lower for w in words)}
    key_topics = extract_definitive_keywords(full_text, top_n=7)
    
    # Adım 4: Hibrit Puanlama (AI Yorumu + Gerçeklik Kontrolü)
    satisfaction_status = category_results.get('satisfaction', {}).get('status', 'Orta')
    proactive_status = category_results.get('proactive', {}).get('status', 'Pasif')
    
    if "demotivasyon" in found_neg_signals:
        satisfaction_status = "Düşük Motivasyon"
    
    dev_score, mot_score = 5, 5
    if "başarı" in found_pos_signals: dev_score += 3
    if "engel" in found_neg_signals: dev_score -= 3
    if proactive_status == "Çözüm Odaklı": dev_score += 2
    
    status_puan_map = {"Yüksek Motivasyon": 9, "Orta": 6, "Düşük Motivasyon": 3}
    mot_score = status_puan_map.get(satisfaction_status, 5)
    
    development_score = max(1, min(10, dev_score))
    motivation_score = max(1, min(10, mot_score))
    
    # Adım 5: Risk, Durum ve Özet
    risk_level = "Düşük"
    if "engel" in found_neg_signals and "başarı" not in found_pos_signals: risk_level = "Yüksek"
    elif "demotivasyon" in found_neg_signals or "engel" in found_neg_signals: risk_level = "Orta"
        
    motivation_status = "Orta"
    if motivation_score >= 8: motivation_status = "Yüksek Motivasyon"
    elif motivation_score <= 4: motivation_status = "Düşük Motivasyon"
    
    narrative_data = {
        "overall_analysis": {"risk_level": risk_level, "motivation_status": motivation_status, "key_topics": {"challenges": key_topics}},
        "category_details": {**category_results, "found_pos_signals": list(found_pos_signals), "found_neg_signals": list(found_neg_signals)}
    }
    summary = narrative_generator.create_narrative_summary(narrative_data)
    
    # Adım 6: Nihai Çıktıyı Oluştur
    cleaned_category_details = {}
    for cat, res in category_results.items():
        cleaned_category_details[cat] = {"status": res.get("status")}

    final_result = {
        "overall_analysis": {
            "development_score": development_score, "motivation_score": motivation_score,
            "motivation_status": motivation_status, "risk_level": risk_level,
            "summary": summary, "key_topics": {"challenges": key_topics}
        },
        "category_details": cleaned_category_details
    }
    return final_result