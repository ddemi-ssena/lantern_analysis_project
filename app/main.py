# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from app.models import AnalysisResult
from app.services import analysis

app = FastAPI(
    title="LanternAnalytics API",
    description="Stajyer raporlarını analiz eden yapay zeka servisi.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "LanternAnalytics API'sine hoş geldiniz!"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_intern_report(
    pdf_report: UploadFile = File(..., description="Stajyerin yüklediği günlük PDF raporu."),
    intern_id: int = Form(..., description="Analizi yapılan stajyerin ID'si."),
    answer1: str = Form(..., description="1. stratejik soruya verilen cevap."),
    answer2: str = Form(..., description="2. stratejik soruya verilen cevap."),
    answer3: str = Form(..., description="3. stratejik soruya verilen cevap.")
):
    try:
        report_text = analysis.extract_text_from_pdf(pdf_report)
    except (ValueError, IOError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    full_text_for_analysis = analysis.combine_texts_for_analysis(
        report_text, answer1, answer2, answer3
    )

    # --- ARTIK BURASI GERÇEK ANALİZ YAPIYOR ---
    # 1. Gerçek AI fonksiyonlarını çağır
    sentiment = analysis.analyze_sentiment(full_text_for_analysis)
    summary = analysis.summarize_text(full_text_for_analysis)
    keywords = analysis.extract_keywords_simple(full_text_for_analysis)
    
    # 2. AI çıktısını iş metriklerine dönüştür (Business Logic)
    satisfaction_status = "Gelişime Açık" # Varsayılan değer
    development_score = 6 # Varsayılan değer

    # Duygu analizinin sonucuna ve skoruna göre durumu ve puanı belirliyoruz.
    # 'positive' ve 'negative' etiketleri kullandığımız modele göre değişebilir.
    # Modelin etiketlerini kontrol etmek için print(sentiment) yapabilirsin.
    if sentiment['label'] == 'positive':
        satisfaction_status = "Memnun"
        # Skor ne kadar yüksekse, puan o kadar yüksek olsun (örn: 7-10 arası)
        development_score = 7 + int(sentiment['score'] * 3) 
    elif sentiment['label'] == 'negative':
        satisfaction_status = "Endişeli"
        # Skor ne kadar yüksekse, puan o kadar düşük olsun (örn: 1-4 arası)
        development_score = 4 - int(sentiment['score'] * 3)

    # Puanın 1-10 aralığında kalmasını garantile
    development_score = max(1, min(10, development_score))

    # 3. Sonucu Pydantic modeliyle oluştur
    real_result = AnalysisResult(
        satisfaction_status=satisfaction_status,
        development_score=development_score,
        ai_summary=summary,
        extracted_keywords=keywords,
        intern_id=intern_id
    )
    # ----------------------------------------------------------------

    return real_result