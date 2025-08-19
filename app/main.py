# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from app.models import AnalysisResult
from app.services import analysis
from app.services.data_parser import parse_report_file # Bu fonksiyonu kullanmayacağız ama yapısal veri için önemli
import json
import io
import pdfplumber

app = FastAPI(
    title="LanternAnalytics API",
    description="Stajyer raporlarını analiz eden yapay zeka servisi.",
    version="1.0.0" # Sürümü güncelledik
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "LanternAnalytics API'sine hoş geldiniz!"}


# Hata yönetimi için bir yardımcı fonksiyon
def get_analysis_service():
    if not analysis.SENTIMENT_ANALYZER or not analysis.SUMMARIZER:
        raise HTTPException(
            status_code=503, 
            detail="AI modelleri yüklenemediği için servis kullanılamıyor."
        )
    return analysis


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_intern_report(
    # PDF dosyasını alıyoruz
    pdf_report: UploadFile = File(..., description="Stajyerin yüklediği günlük PDF raporu."),
    
    # Yapısal soru-cevap verisini JSON formatında bir string olarak alıyoruz
    answers_json: str = Form(..., description="Soru-cevap listesini içeren JSON formatında string. Örn: '[{\"question\": \"...\", \"category\": \"...\", \"answer\": \"...\"}]'"),
    
    # Stajyer ID'sini alıyoruz
    intern_id: int = Form(..., description="Analizi yapılan stajyerin ID'si."),
    
    # Modellerin yüklü olup olmadığını kontrol eden dependency
    analysis_service: analysis = Depends(get_analysis_service)
):
    """
    Bir stajyerin PDF raporunu ve yapısal soru-cevap JSON'unu alıp
    yapay zeka analizinden geçirir ve çok boyutlu sonuçları döndürür.
    """
    # Adım 1: PDF'ten metni çıkar
    try:
        # UploadFile'ı doğrudan okumak için bir IO sarmalayıcı kullanalım
        pdf_bytes = io.BytesIO(await pdf_report.read())
        report_text = ""
        # "analysis." ön ekini kaldırıyoruz, çünkü pdfplumber artık doğrudan bu dosyada tanınıyor.
        with pdfplumber.open(pdf_bytes) as pdf: # <-- DÜZELTİLMİŞ SATIR
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    report_text += text + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF dosyası okunamadı veya bozuk: {e}")

    # Adım 2: Gelen JSON string'ini Python listesine çevir
    try:
        answers_list = json.loads(answers_json)
        if not isinstance(answers_list, list):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=400, 
            detail="`answers_json` formatı bozuk. Geçerli bir JSON listesi olmalıdır."
        )

    # Adım 3: Analiz servisine göndereceğimiz veri yapısını oluştur
    report_data = {
        "report_text": report_text,
        "answers": answers_list
    }

    # Adım 4: Tam analizi çalıştır
    try:
        final_analysis = analysis_service.run_full_analysis(report_data)
        if "error" in final_analysis:
             raise HTTPException(status_code=500, detail=final_analysis["error"])
    except Exception as e:
        # Analiz sırasında beklenmedik bir hata olursa yakala
        raise HTTPException(status_code=500, detail=f"Analiz sırasında bir hata oluştu: {e}")

    # Adım 5: Nihai sonucu Pydantic modeliyle birleştirip döndür
    return AnalysisResult(
        intern_id=intern_id,
        **final_analysis # final_analysis içindeki tüm alanları buraya açar
    )