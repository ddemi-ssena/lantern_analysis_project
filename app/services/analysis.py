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
    SENTIMENT_ANALYZER = pipeline("sentiment-analysis", model="ssenos/lantern_fine-tuning-v3")
    print("SpaCy Transformer (TRF) modeli yükleniyor...")
    NLP = spacy.load("tr_core_news_trf")
    print("Tüm modeller başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Modeller yüklenemedi. Hata: {e}")
    SENTIMENT_ANALYZER = None
    NLP = None



def load_corpus_from_local_pdfs() -> list[str]:
    corpus = []
    corpus_folder = "corpus_pdfs"
    if not os.path.isdir(corpus_folder):
        return []
        
    for filename in os.listdir(corpus_folder):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(corpus_folder, filename)
            try:
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                corpus.append(text)
            except Exception as e:
                print(f"UYARI: Corpus PDF dosyası '{filename}' okunamadı: {e}")
    return corpus

def extract_definitive_keywords(text: str, top_n: int = 7) -> list[str]:
    """
    Sadece bizim tanımladığımız teknik terimler ve SpaCy'ın bulduğu
    kesin varlıklar üzerinden anahtar kelime çıkarır.
    """
    if not NLP:
        return []
    try:
        keywords = set()
        text_lower = text.lower()

        # Önceden tanımlanmış teknik terimler listesi
        known_techs = [
            "docker", "docker-compose", "postgresql", "spring boot", "spring security", "java", 
            "python", "fastapi", "vue.js", "react", "axios", "ci/cd", "pipeline", "kubernetes", 
            "sql", "jwt", "api", "rest", "spacy", "network security group", "sanal makine", 
            "veritabanı", "entity", "repository", "controller", "endpoint", "dependency", 
            "dbeaver", "junit", "mockito", "refactor", "@preauthorize", "scoped styles", 
            "connection refused", "403 forbidden", "network error", "nullpointerexception", "git", "github",
            "kabul kriterleri", "acceptance criteria", "explain analyze", "join", "sorgu planı"
        ]
        # Metin içinde geçen teknik terimleri sete ekle
        keywords.update({tech for tech in known_techs if tech in text_lower})

        # SpaCy ile metindeki varlıkları (Entity) bul
        doc = NLP(text)
        for ent in doc.ents:
            # Sadece organizasyon ve ürün isimlerini al, genel isimleri (insan adı vb.) hariç tut
            if ent.label_ in ["ORG", "PRODUCT"] and len(ent.text.strip()) > 2:
                if ent.text.lower() not in ["zeynep", "ayşe", "can", "ahmet"]:
                    keywords.add(ent.text.lower())
        
        # Bulunan anahtar kelimelerden en fazla 'top_n' tanesini döndür
        return list(keywords)[:top_n]
    except Exception as e:
        print(f"Anahtar kelime çıkarımı sırasında hata: {e}")
        return []
def analyze_process_satisfaction(answer: str) -> dict:
    # Gelen cevabı duygu analizi modeline gönder
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    # Modelin döndürdüğü etiketi (label) al
    label = sentiment['label']
    
    # Etiketleri, bizim istediğimiz motivasyon durumlarına çevir
    status_map = {
        "Olumlu Gelişim": "Yüksek Motivasyon", 
        "Proaktif / Fikir": "Yüksek Motivasyon", 
        "Olumsuz Duygu / Demotive": "Düşük Motivasyon", 
        "Engellenmiş / Yardım İhtiyacı": "Düşük Motivasyon", 
        "İşbirliği / İletişim": "Orta", 
        "Nötr Raporlama": "Orta"
    }
    
    # Haritadan doğru durumu bul, bulamazsan varsayılan olarak "Orta" kullan
    status = status_map.get(label, "Orta")
    
    # Sonucu bir dictionary olarak döndür
    return {"status": status}

def analyze_proactiveness(answer: str) -> dict:
    # 1. Önce, anahtar kelimeleri kontrol et.
    action_words = ["hedefliyorum", "planliyorum", "yapacagim", "istiyorum", "cozecegim", "onerim", "fikrim", "eklersek", "iyilestirebiliriz", "olmali", "olabilir", "kabul kriterleri", "daha iyi yapabilirim"]
    if any(word in answer.lower() for word in action_words):
        # Eğer proaktif kelime varsa, hiç analiz yapmadan doğrudan sonucu dön.
        return {"status": "Çözüm Odaklı"}

    # 2. Eğer proaktif kelime YOKSA, o zaman duygu analizi yap.
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    # 3. Analiz sonucuna göre karar ver.
    if sentiment['label'] == "Proaktif / Fikir":
        return {"status": "Çözüm Odaklı"}
    else:
        return {"status": "Pasif"}

def analyze_collaboration(answer: str) -> dict:
    # 1. Önce, işbirliği ile ilgili anahtar kelimeleri kontrol et.
    help_words = ["yardım istedim", "danıştım", "yardımcı oldu", "birlikte çözdük", 
                  "yardımcı olmaya çalıştım", "birlikte kafa yorduk", "beyin fırtınası", 
                  "yardımım dokundu"]
    if any(word in answer.lower() for word in help_words):
        # Eğer işbirliği kelimesi varsa, hiç analiz yapmadan doğrudan sonucu dön.
        return {"status": "Aktif İletişim"}

    # 2. Eğer işbirliği kelimesi YOKSA, o zaman duygu analizi yap.
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    # 3. Analiz sonucuna göre karar ver.
    if sentiment['label'] == "İşbirliği / İletişim":
        return {"status": "Aktif İletişim"}
    else:
        return {"status": "Nötr İletişim"}

# app/services/analysis.py

def run_full_analysis(report_data: dict) -> dict:
    if not SENTIMENT_ANALYZER or not NLP:
        return {"error": "AI modelleri yüklenemediği için analiz yapılamıyor."}

    # Adım 1: Veriyi Hazırla
    answers = report_data.get('answers', [])
    full_text = report_data.get('report_text', '') + " " + " ".join([item.get('answer', '') for item in answers])
    
    # Adım 2: Kategori Bazlı Analizler
    category_results = {}
    for item in answers:
        category, answer = item.get('category'), item.get('answer')
        if not category or not answer: continue
        if category == "Süreç Memnuniyeti": category_results['satisfaction'] = analyze_process_satisfaction(answer)
        elif category == "Proaktiflik": category_results['proactive'] = analyze_proactiveness(answer)
        elif category == "İşbirliği / İletişim": category_results['collaboration'] = analyze_collaboration(answer)

    # Adım 3: Bütünsel Analizler
    text_lower = full_text.lower()
    positive_signals = {"başarı": ["başardım", "çözdüm", "tamamladım", "çalıştı"]}
    negative_signals = {"engel": ["hata aldım", "çözemedim", "ilerleyemedim"], "demotivasyon": ["motivasyonum düşüktü", "moralim bozuldu"]}
    found_pos_signals = {stype for stype, words in positive_signals.items() if any(w in text_lower for w in words)}
    found_neg_signals = {stype for stype, words in negative_signals.items() if any(w in text_lower for w in words)}
    keyTopicsList = extract_definitive_keywords(full_text, top_n=7)
    
    # Adım 4: Hibrit Puanlama (TÜM DEĞİŞKENLER camelCase YAPILDI)
    satisfactionStatus = category_results.get('satisfaction', {}).get('status', 'Orta')
    proactiveStatus = category_results.get('proactive', {}).get('status', 'Pasif')
    
    if "demotivasyon" in found_neg_signals:
        satisfactionStatus = "Düşük Motivasyon"
    
    dev_score, mot_score = 5, 5
    if "başarı" in found_pos_signals: dev_score += 3
    if "engel" in found_neg_signals: dev_score -= 3
    if proactiveStatus == "Çözüm Odaklı": dev_score += 2
    
    status_puan_map = {"Yüksek Motivasyon": 9, "Orta": 6, "Düşük Motivasyon": 3}
    mot_score = status_puan_map.get(satisfactionStatus, 5)
    
    developmentScore = max(1, min(10, dev_score))
    motivationScore = max(1, min(10, mot_score))
    
    # Adım 5: Risk, Durum ve Özet (TÜM DEĞİŞKENLER camelCase YAPILDI)
    riskLevel = "Düşük"
    if "engel" in found_neg_signals and "başarı" not in found_pos_signals: riskLevel = "Yüksek"
    elif "demotivasyon" in found_neg_signals or "engel" in found_neg_signals: riskLevel = "Orta"
        
    motivationStatus = "Orta"
    if motivationScore >= 8: motivationStatus = "Yüksek Motivasyon"
    elif motivationScore <= 4: motivationStatus = "Düşük Motivasyon"
    
    narrativeData = {
        "overallAnalysis": {"riskLevel": riskLevel, "motivationStatus": motivationStatus, "keyTopics": {"challenges": keyTopicsList}},
        "categoryDetails": {**category_results, "foundPosSignals": list(found_pos_signals), "foundNegSignals": list(found_neg_signals)}
    }
    summary = narrative_generator.create_narrative_summary(narrativeData)
    
    # Adım 6: Nihai Çıktıyı Oluştur (category_results'ı temizle)
    categoryDetails = {}
    for cat, res in category_results.items():
        categoryDetails[cat] = {"status": res.get("status")}

    # Adım 7: Düz bir sonuç sözlüğü döndür (TÜM ANAHTARLAR camelCase)
    flat_result = {
        "internId": report_data.get("intern_id"),
        "developmentScore": developmentScore, 
        "motivationScore": motivationScore,
        "motivationStatus": motivationStatus, 
        "riskLevel": riskLevel,
        "summary": summary, 
        "keyTopics": {"challenges": keyTopicsList},
        "categoryDetails": categoryDetails
    }
    
    return flat_result