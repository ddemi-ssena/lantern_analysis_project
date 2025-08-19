from transformers import pipeline
from . import narrative_generator

# --- MODELLERİ BİR KERE YÜKLEYİP HAFIZADA TUTALIM (PERFORMANS İÇİN) ---
try:
    print("AI Modelleri yükleniyor... Bu işlem birkaç dakika sürebilir.")
    
    # Duygu analizi modelini yüklüyoruz
    SENTIMENT_ANALYZER = pipeline(
        task="sentiment-analysis",
        model="savasy/bert-base-turkish-sentiment-cased"
    )
    
    # Metin özetleme modelini yüklüyoruz
    SUMMARIZER = pipeline(
        task="summarization",
        model="google/mt5-small"
    )
    
    print("AI Modelleri başarıyla yüklendi.")

except Exception as e:
    print(f"HATA: Modeller yüklenemedi. Hata: {e}")
    # Hata durumunda değişkenleri None olarak ayarlıyoruz
    SENTIMENT_ANALYZER = None
    SUMMARIZER = None
# --- ANALİZ FONKSİYONLARI ---

def analyze_technical_competence(answer: str) -> dict:
    """ 'Teknik Yetkinlik' kategorisindeki bir cevabı analiz eder. """
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    # Basit anahtar kelime çıkarma
    technical_keywords = [
        "java", "spring boot", "jwt", "403 hatası", "dependency", "veritabanı",
        "api", "rest", "docker", "python", "react", "konfigürasyon"
    ]
    found_keywords = [kw for kw in technical_keywords if kw in answer.lower()]

    # Başarı ve zorluk belirleme (basit anahtar kelimelerle)
    achievements = ["öğrendim", "başardım", "çözdüm", "tamamladım"]
    challenges = ["zorlandım", "hata aldım", "çözemedim", "bulamadım", "ilerleyemedim"]
    
    status = "Nötr"
    if any(word in answer.lower() for word in achievements):
        status = "Başarılı"
    elif any(word in answer.lower() for word in challenges):
        status = "Zorlanıyor"
        
    return {
        "status": status,
        "topics": list(set(found_keywords)),
        "sentiment_label": sentiment['label'],
        "sentiment_score": sentiment['score']
    }

def analyze_process_satisfaction(answer: str) -> dict:
    """ 'Süreç Memnuniyeti' kategorisindeki bir cevabı analiz eder. """
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    status = "Orta"
    if sentiment['label'] == 'positive' and sentiment['score'] > 0.8:
        status = "Yüksek Motivasyon"
    elif sentiment['label'] == 'negative' and sentiment['score'] > 0.7:
        status = "Düşük Motivasyon"
        
    return {
        "status": status,
        "sentiment_label": sentiment['label'],
        "sentiment_score": sentiment['score']
    }

def analyze_proactiveness(answer: str) -> dict:
    """ 'Proaktiflik' kategorisindeki bir cevabı analiz eder. """
    # Eylem ve çözüm odaklı kelimeleri arayalım
    action_words = ["hedefliyorum", "planlıyorum", "yapacağım", "istiyorum", "çözeceğim"]
    
    status = "Pasif"
    if any(word in answer.lower() for word in action_words):
        status = "Çözüm Odaklı"
        
    return {"status": status}
def run_full_analysis(report_data: dict) -> dict:
    """
    Tüm rapor verisini alır, kategori bazlı analizleri çalıştırır ve
    bütünsel bir sonuç üretir.
    """
    if not SENTIMENT_ANALYZER or not SUMMARIZER:
        return {"error": "AI modelleri yüklenemediği için analiz yapılamıyor."}

    # Adım 1: Tüm kategori bazlı analizleri yap ve sonuçları sakla
    category_results = {}
    full_text_for_summary = report_data['report_text']

    for item in report_data['answers']:
        category = item['category']
        answer = item['answer']
        full_text_for_summary += f"\nSoru: {item['question']}\nCevap: {answer}"
        
        if category == "Teknik Yetkinlik":
            category_results['technical'] = analyze_technical_competence(answer)
        elif category == "Süreç Memnuniyeti":
            category_results['satisfaction'] = analyze_process_satisfaction(answer)
        elif category == "Proaktiflik":
            category_results['proactive'] = analyze_proactiveness(answer)
    
    # Adım 2: Kategori sonuçlarına dayanarak bütünsel puanları hesapla
    tech_score = 5 # Varsayılan
    if 'technical' in category_results:
        if category_results['technical']['status'] == "Başarılı":
            tech_score = 8
        elif category_results['technical']['status'] == "Zorlanıyor":
            tech_score = 3

    proactive_score = 5 # Varsayılan
    if 'proactive' in category_results and category_results['proactive']['status'] == "Çözüm Odaklı":
        proactive_score = 9

    satisfaction_score = 5 # Varsayılan
    if 'satisfaction' in category_results:
        s_score = category_results['satisfaction']['sentiment_score']
        if category_results['satisfaction']['sentiment_label'] == 'positive':
            satisfaction_score = 5 + (s_score * 5)
        else:
            satisfaction_score = 5 - (s_score * 4)

    development_score = int((tech_score * 0.6) + (proactive_score * 0.4))
    motivation_score = int(satisfaction_score)

    # Adım 3: Puanlara dayanarak riski belirle
    risk_level = "Düşük"
    if motivation_score <= 4 and tech_score <= 4:
        risk_level = "Yüksek"
    elif motivation_score <= 6 or tech_score <= 6:
        risk_level = "Orta"

    # Adım 4: Anlatısal özeti oluştur
    # Hikayeleştiriciye göndermek için gerekli tüm veriyi bir araya topla
    narrative_data = {
        "overall_analysis": {
            "risk_level": risk_level,
            "motivation_status": category_results.get('satisfaction', {}).get('status', 'Bilinmiyor'),
        },
        "category_details": category_results
    }
    summary = narrative_generator.create_narrative_summary(narrative_data)
    
    # Adım 5: Tüm sonuçları nihai bir dictionary içinde birleştir
     # Kategori detaylarından teknik kısımları ayıklayalım
    cleaned_category_details = {
        "technical": {
            "status": category_results.get('technical', {}).get('status', 'Bilinmiyor'),
            "topics": category_results.get('technical', {}).get('topics', [])
        },
        "satisfaction": {
            "status": category_results.get('satisfaction', {}).get('status', 'Bilinmiyor')
        },
        "proactive": {
            "status": category_results.get('proactive', {}).get('status', 'Bilinmiyor')
        }
    }

    final_result = {
        "overall_analysis": {
            "development_score": development_score,
            "motivation_score": motivation_score,
            "motivation_status": category_results.get('satisfaction', {}).get('status', 'Bilinmiyor'),
            "risk_level": risk_level,
            "summary": summary,
            "key_topics": {
                "challenges": category_results.get('technical', {}).get('topics', [])
            }
        },
        "category_details": cleaned_category_details # <-- SADELEŞTİRİLMİŞ DETAYLARI GÖNDERİYORUZ
    }
    
    return final_result