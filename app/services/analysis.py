# app/services/analysis.py
import pdfplumber
from fastapi import UploadFile
import io
from transformers import pipeline # <-- YENİ IMPORT

# --- Faz 1'den kalan fonksiyonlar (değişiklik yok) ---
def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise ValueError("Yüklenen dosya bir PDF olmalıdır.")
    pdf_bytes = io.BytesIO(pdf_file.file.read())
    full_text = ""
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        return full_text
    except Exception as e:
        print(f"PDF okuma hatası: {e}")
        raise IOError("PDF dosyası okunamadı veya bozuk.")

def combine_texts_for_analysis(report_text: str, answer1: str, answer2: str, answer3: str) -> str:
    combined_text = f"""
--- GÜNLÜK RAPOR METNİ ---
{report_text}
--- STRATEJİK SORULAR VE CEVAPLAR ---
Soru 1: Bugün teknik olarak en çok ne öğrendin veya hangi konuda zorlandın?
Cevap: {answer1}

Soru 2: Karşılaştığın bir problemi nasıl çözdün veya çözmek için kimden yardım aldın?
Cevap: {answer2}

Soru 3: Bugünkü genel motivasyonunu ve memnuniyetini 1-10 arasında nasıl puanlarsın?
Cevap: {answer3}
"""
    return combined_text

# --- YENİ GERÇEK ANALİZ FONKSİYONLARI ---

# app/services/analysis.py - YENİ HALİ

# ...
def analyze_sentiment(text_to_analyze: str) -> dict:
    """
    Verilen metnin duygu analizini yapar (pozitif/negatif).
    Metin çok uzunsa, pipeline'ın truncate özelliği ile otomatik olarak
    modelin maksimum limiti olan 512 token'a kısaltılır.
    """
    print("Duygu analizi modeli yükleniyor/çalıştırılıyor...")
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="savasy/bert-base-turkish-sentiment-cased"
    )
    
    # --- DEĞİŞİKLİK BURADA ---
    # `truncation=True` parametresi, metin uzunsa modelin limitine göre
    # otomatik olarak kısaltma yapmasını sağlar. Karakter sayma işini tamamen ortadan kaldırıyoruz.
    result = sentiment_analyzer(text_to_analyze, truncation=True)
    # --- DEĞİŞİKLİK SONU ---
    
    return result[0]
def summarize_text(text_to_summarize: str) -> str:
    """
    Verilen uzun metni özetler.
    Not: Bu model de ilk çağrıldığında indirilecektir.
    """
    print("Metin özetleme modeli yükleniyor/çalıştırılıyor...")
    # Sorunlu model yerine, tamamen halka açık ve popüler bir
    # alternatif olan "facebook/bart-large-cnn" modelini kullanıyoruz.
    # Bu model aslında İngilizce için eğitilmiş olsa da, `pipeline`
    # çoğu zaman basit özetlemeler için makul sonuçlar üretebilir.
    # Daha iyi bir alternatif: `semanur/t5-base-turkish-news-summary`
    summarizer = pipeline(
        "summarization", 
        model="google/mt5-small"
    )
    # Modelin çok kısa veya çok uzun özetler yapmasını engelliyoruz.
    summary = summarizer(text_to_summarize, max_length=150, min_length=30, do_sample=False)
    # Çıktı [{'summary_text': '...'}] formatındadır.
    return summary[0]['summary_text']

def extract_keywords_simple(text_to_analyze: str) -> list[str]:
    """
    Metin içinde geçen önceden tanımlı teknik anahtar kelimeleri bulan basit bir fonksiyon.
    Not: Bu, AI tabanlı değildir ancak başlangıç için çok etkilidir.
    """
    print("Anahtar kelimeler çıkarılıyor...")
    # Bu listeyi projenizin ihtiyaçlarına göre genişletebilirsiniz.
    TECHNICAL_KEYWORDS = [
        "java", "spring", "spring boot", "python", "fastapi", "react", "vue",
        "javascript", "html", "css", "sql", "postgresql", "mysql", "docker",
        "kubernetes", "aws", "azure", "git", "github", "api", "rest", "jwt",
        "microservices", "veritabanı", "database", "algoritma", "data structure"
    ]
    
    found_keywords = set() # Aynı kelimeyi tekrar eklememek için set kullanıyoruz.
    text_lower = text_to_analyze.lower() # Metni küçük harfe çevirerek aramayı kolaylaştırıyoruz.
    
    for keyword in TECHNICAL_KEYWORDS:
        if keyword in text_lower:
            found_keywords.add(keyword.title()) # Kelimeleri daha güzel göstermek için baş harflerini büyütüyoruz.
            
    return list(found_keywords)