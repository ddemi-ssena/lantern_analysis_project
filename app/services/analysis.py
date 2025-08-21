from transformers import pipeline
from . import narrative_generator
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# --- MODELLERİ YÜKLEME ---
try:
    print("AI Modelleri yükleniyor... Bu işlem birkaç dakika sürebilir.")
    
    # Kendi eğittiğimiz, halka açık fine-tuning modelimiz
    SENTIMENT_ANALYZER = pipeline(
        "sentiment-analysis",
        model="ssenos/lantern_fine-tuning-v2" # veya v1, hangisini kullanıyorsan
    )
    
    # Özetleme modeli
    SUMMARIZER = pipeline(
        task="summarization",
        model="google/mt5-small"
    )
    
    print("AI Modelleri başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Modeller yüklenemedi. Hata: {e}")
    SENTIMENT_ANALYZER = None
    SUMMARIZER = None

# --- YARDIMCI ANALİZ FONKSİYONLARI ---

def extract_keywords_tfidf(documents: list[str], target_document_index: int, top_n: int = 7) -> list[str]:
    """
    Bir metin koleksiyonu (corpus) içindeki belirli bir metnin
    en önemli anahtar kelimelerini TF-IDF kullanarak çıkarır.
    """
    if not documents or not (0 <= target_document_index < len(documents)):
        return []
        
    try:
        stop_words_list = [
            "ve", "bir", "ama", "için", "ile", "bu", "o", "çok", "daha", "gibi", 
            "ben", "sen", "biz", "siz", "onlar", "benim", "senin", "onun",
            "olarak", "sonra", "önce", "tüm", "her", "şey", "yok", "var", "evet", "hayır",
            "dedi", "oldu", "günü", "gün", "kadar", "şey", "bana", "sadece", "artık",
            "diye", "birlikte", "gibi", "ama", "ancak", "çünkü", "de", "da"
        ]
        
        tfidf_vectorizer = TfidfVectorizer(
            stop_words=stop_words_list, 
            # max_features'ı kaldırarak modelin tüm kelimeleri değerlendirmesini sağlıyoruz.
            # min_df=1, en az 1 dokümanda geçen kelimeleri dahil et (varsayılan)
            # max_df=0.8, dokümanların %80'inden fazlasında geçen kelimeleri (örn: "proje") ele.
            max_df=0.8,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        feature_names = np.array(tfidf_vectorizer.get_feature_names_out())
        target_scores = tfidf_matrix[target_document_index].toarray().flatten()
        
        # En yüksek skora sahip N kelimenin indekslerini bul
        # argsort küçükten büyüğe sıralar, bu yüzden sondan N tanesini alıyoruz
        # Eğer kelime sayısı N'den azsa, hepsini al
        num_keywords_to_get = min(top_n, len(feature_names))
        top_indices = np.argsort(target_scores)[-num_keywords_to_get:]
        top_indices_sorted = top_indices[::-1]
        
        top_keywords = feature_names[top_indices_sorted]

        final_keywords = []
        # Özel isimleri veya teknik olmayan kelimeleri elemek için bir kara liste
        blacklist = ["ayşe", "zeynep", "ahmet", "mehmet", "saatlerce", "günün", "bunun"]
        
        for kw in top_keywords:
            # TF-IDF skorunun çok düşük olmamasını sağla
            kw_index = np.where(feature_names == kw)[0][0]
            if target_scores[kw_index] < 0.05: # Çok düşük skorluları atla
                continue
            # Kara listede olmamasını sağla
            if kw in blacklist:
                continue
            
            if len(kw.strip()) < 3 and ' ' not in kw: 
                continue
                
            final_keywords.append(kw)

        # Sonuçta istediğimiz kadar kelime döndürelim (en fazla 5)
        return final_keywords[:5]

    except Exception as e:
        print(f"TF-IDF hatası: {e}")
        return []

def analyze_process_satisfaction(answer: str) -> dict:
    """ 'Süreç Memnuniyeti' kategorisindeki bir cevabı analiz eder. """
    # Bu fonksiyon artık fine-tuning modelimizi kullanıyor, bu yüzden daha akıllı.
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    # Dönen etikete göre bir durum belirleyelim
    label = sentiment['label']
    status_map = {
        "Olumlu Gelişim": "Yüksek Motivasyon",
        "Proaktif / Fikir": "Yüksek Motivasyon",
        "Olumsuz Duygu / Demotive": "Düşük Motivasyon",
        "Engellenmiş / Yardım İhtiyacı": "Düşük Motivasyon",
        "İşbirliği / İletişim": "Orta",
        "Nötr Raporlama": "Orta"
    }
    status = status_map.get(label, "Orta") # Etiket haritada yoksa varsayılan 'Orta'
        
    return {
        "status": status,
        "sentiment_label": label, # Kendi etiketimizi döndürüyoruz
        "sentiment_score": sentiment['score']
    }

def analyze_proactiveness(answer: str) -> dict:
    """ 'Proaktiflik' kategorisindeki bir cevabı analiz eder. """
    sentiment = SENTIMENT_ANALYZER(answer, truncation=True)[0]
    
    status = "Pasif"
    if sentiment['label'] == "Proaktif / Fikir":
        status = "Çözüm Odaklı"
        
    return {"status": status}

# --- ANA ANALİZ FONKSİYONU ---

def run_full_analysis(report_data: dict) -> dict:
    """
    Tüm rapor verisini alır, kategori bazlı analizleri çalıştırır ve
    bütünsel bir sonuç üretir.
    """
    if not SENTIMENT_ANALYZER: # SUMMARIZER'ı kontrol etmiyoruz, çünkü B planımız var
        return {"error": "AI duygu analizi modeli yüklenemediği için analiz yapılamıyor."}

    # --- Adım 1: Veriyi Hazırlama ---
    category_results = {}
    full_text_for_analysis = report_data['report_text']
    
    # TF-IDF için metin koleksiyonunu (corpus) oluştur
    corpus = [
        "Bugün Java ve Spring Boot ile bir API geliştirdim. Veritabanı işlemleri yaptım.",
        "React kullanarak frontend tarafında bir bileşen yazdım. CSS ve HTML ile uğraştım.",
        "Docker ve CI/CD pipeline üzerine çalıştım. SQL sorguları yazdım.",
        # Ve şimdi bugünün gerçek rapor metni ve cevapları:
        report_data['report_text'] + " " + " ".join([item['answer'] for item in report_data['answers']])
    ]
    target_index = len(corpus) - 1

    # --- Adım 2: Kategori Bazlı Analizler ---
    for item in report_data['answers']:
        category = item['category']
        answer = item['answer']
        full_text_for_analysis += f"\nSoru: {item['question']}\nCevap: {answer}"
        
        if category == "Süreç Memnuniyeti":
            category_results['satisfaction'] = analyze_process_satisfaction(answer)
        elif category == "Proaktiflik":
            category_results['proactive'] = analyze_proactiveness(answer)
        # Not: Teknik analiz artık kategori bazlı yapılmıyor.

    # --- Adım 3: Bütünsel Analizler ---
    key_topics = extract_keywords_tfidf(corpus, target_index, top_n=7)
    
    # Bütünsel duygu analizi yapalım (tüm metne bakarak)
    overall_sentiment = SENTIMENT_ANALYZER(full_text_for_analysis, truncation=True)[0]
    
    # --- Adım 4: Puanlama ---
    tech_score = 5 # Varsayılan
    if "Engellenmiş / Yardım İhtiyacı" in overall_sentiment['label']:
        tech_score = 3
    elif "Olumlu Gelişim" in overall_sentiment['label']:
        tech_score = 8
    elif key_topics: # Eğer anahtar kelime varsa, en azından ortalama bir gündür
        tech_score = 6

    proactive_score = 5 # Varsayılan
    if 'proactive' in category_results and category_results['proactive']['status'] == "Çözüm Odaklı":
        proactive_score = 9

    satisfaction_score = 5 # Varsayılan
    if 'satisfaction' in category_results:
        # Puanı doğrudan sentiment skorundan değil, durumdan alalım
        status_puan_map = {"Yüksek Motivasyon": 9, "Orta": 6, "Düşük Motivasyon": 3}
        satisfaction_score = status_puan_map.get(category_results['satisfaction']['status'], 5)

    development_score = int((tech_score * 0.6) + (proactive_score * 0.4))
    motivation_score = int(satisfaction_score)
    
    risk_level = "Düşük"
    if motivation_score <= 4 or tech_score <= 4:
        risk_level = "Yüksek"
    elif motivation_score <= 6 or tech_score <= 6:
        risk_level = "Orta"

    # --- Adım 5: Özetleme ve Sonuçlandırma ---
    summary = narrative_generator.create_narrative_summary({
        "overall_analysis": {"risk_level": risk_level, "motivation_status": category_results.get('satisfaction', {}).get('status', 'Değerlendirilemedi')},
        "category_details": {"technical": {"topics": key_topics, "status": "Değerlendirilemedi"}, "proactive": category_results.get('proactive')}
    })
    
    cleaned_category_details = {}
    if 'satisfaction' in category_results:
        cleaned_category_details['satisfaction'] = {"status": category_results['satisfaction'].get('status')}
    if 'proactive' in category_results:
        cleaned_category_details['proactive'] = {"status": category_results['proactive'].get('status')}

    final_result = {
        "overall_analysis": {
            "development_score": development_score,
            "motivation_score": motivation_score,
            "motivation_status": category_results.get('satisfaction', {}).get('status', 'Değerlendirilemedi'),
            "risk_level": risk_level,
            "summary": summary,
            "key_topics": {
                "challenges": key_topics # Anahtar kelimeleri buraya ekliyoruz
            }
        },
        "category_details": cleaned_category_details
    }
def run_full_analysis(report_data: dict) -> dict:

    """
    Tüm rapor verisini alır, kategori bazlı analizleri çalıştırır ve
    bütünsel bir sonuç üretir.
    """
    if not SENTIMENT_ANALYZER:
        return {"error": "AI duygu analizi modeli yüklenemediği için analiz yapılamıyor."}

    # --- Adım 1: Veriyi Hazırlama ---
    category_results = {}
    
    # Tüm metinleri birleştirelim (Hem TF-IDF hem de özet için kullanılacak)
    full_text_for_analysis = report_data['report_text'] + " " + " ".join([item['answer'] for item in report_data['answers']])
    
    # TF-IDF için metin koleksiyonunu (corpus) oluştur
    corpus = [
        "Bugün Java ve Spring Boot ile bir API geliştirdim. Veritabanı işlemleri yaptım.",
        "React kullanarak frontend tarafında bir bileşen yazdım. CSS ve HTML ile uğraştım.",
        "Docker ve CI/CD pipeline üzerine çalıştım. SQL sorguları yazdım.",
        full_text_for_analysis # Bugünün birleştirilmiş tam metni
    ]
    target_index = len(corpus) - 1

    # --- Adım 2: Bütünsel Anahtar Kelime Çıkarımı ---
    # !! ÖNEMLİ: Anahtar kelimeleri en başta, tüm metin üzerinden çıkarıyoruz !!
    key_topics = extract_keywords_tfidf(corpus, target_index, top_n=7)
    
    # --- Adım 3: Kategori Bazlı Analizler ---
    for item in report_data['answers']:
        category = item['category']
        answer = item['answer']
        
        if category == "Süreç Memnuniyeti":
            category_results['satisfaction'] = analyze_process_satisfaction(answer)
        elif category == "Proaktiflik":
            category_results['proactive'] = analyze_proactiveness(answer)
        # Not: Teknik analiz artık burada yapılmıyor.

    # --- Adım 4: Puanlama ---
    tech_score = 5 # Varsayılan
    # Fine-tuning modelinden bütünsel bir duygu alalım
    overall_sentiment = SENTIMENT_ANALYZER(full_text_for_analysis, truncation=True)[0]['label']
    if overall_sentiment == "Engellenmiş / Yardım İhtiyacı":
        tech_score = 3
    elif overall_sentiment == "Olumlu Gelişim":
        tech_score = 8
    elif key_topics: # Eğer anahtar kelime varsa, en azından ortalama bir gündür
        tech_score = 6

    proactive_score = 5 # Varsayılan
    if 'proactive' in category_results and category_results['proactive']['status'] == "Çözüm Odaklı":
        proactive_score = 9

    satisfaction_score = 5 # Varsayılan
    if 'satisfaction' in category_results:
        status_puan_map = {"Yüksek Motivasyon": 9, "Orta": 6, "Düşük Motivasyon": 3}
        satisfaction_score = status_puan_map.get(category_results['satisfaction']['status'], 5)

    development_score = int((tech_score * 0.6) + (proactive_score * 0.4))
    motivation_score = int(satisfaction_score)
    
    risk_level = "Düşük"
    if motivation_score <= 4 or tech_score <= 4:
        risk_level = "Yüksek"
    elif motivation_score <= 6 or tech_score <= 6:
        risk_level = "Orta"

    # --- Adım 5: Özetleme ve Sonuçlandırma ---
    narrative_data = {
        "overall_analysis": {
            "risk_level": risk_level,
            "motivation_status": category_results.get('satisfaction', {}).get('status', 'Değerlendirilemedi'),
            "key_topics": {"challenges": key_topics} # !! ÖNEMLİ: Anahtar kelimeleri hikayeleştiriciye gönderiyoruz
        },
        "category_details": category_results
    }
    summary = narrative_generator.create_narrative_summary(narrative_data)
    
    cleaned_category_details = {}
    if 'satisfaction' in category_results:
        cleaned_category_details['satisfaction'] = {"status": category_results['satisfaction'].get('status')}
    if 'proactive' in category_results:
        cleaned_category_details['proactive'] = {"status": category_results['proactive'].get('status')}
    # Not: Çıktıda 'technical' kategorisi olmayacak, çünkü bu bilgi artık 'key_topics' içinde.

    final_result = {
        "overall_analysis": {
            "development_score": development_score,
            "motivation_score": motivation_score,
            "motivation_status": category_results.get('satisfaction', {}).get('status', 'Değerlendirilemedi'),
            "risk_level": risk_level,
            "summary": summary,
            "key_topics": {
                "challenges": key_topics # !! ÖNEMLİ: Anahtar kelimeleri nihai sonuca ekliyoruz
            }
        },
        "category_details": cleaned_category_details
    }
    
    return final_result
    