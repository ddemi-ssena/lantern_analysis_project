# app/main.py - SON VE TAM VERSİYON (Hata ayıklama logları ile)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from app.models import AnalysisResult
from app.services import analysis
import json
import io
import pdfplumber

app = FastAPI(
    title="LanternAnalytics API",
    description="Stajyer raporlarını analiz eden yapay zeka servisi.",
    version="1.0.0"
)

# --- GÜVENLİK MEKANİZMASI ---
def get_analysis_service():
    if not analysis.SENTIMENT_ANALYZER:
        raise HTTPException(
            status_code=503, 
            detail="AI modelleri yüklenemediği için servis kullanılamıyor."
        )
    return analysis
# ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "LanternAnalytics API'sine hoş geldiniz!"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_intern_report(
    pdf_report: UploadFile = File(...),
    answers_json: str = Form(...),
    intern_id: int = Form(...),
    analysis_service: analysis = Depends(get_analysis_service)
):
    try:
        # --- Adım 1 & 2: PDF ve JSON okuma ---
        print("[DEBUG] Adım 1: PDF okuma başlıyor...")
        pdf_bytes = io.BytesIO(await pdf_report.read())
        report_text = ""
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                report_text += text + "\n"
        print("[DEBUG] Adım 1 Tamamlandı: PDF okundu.")

        print("[DEBUG] Adım 2: JSON ayrıştırma başlıyor...")
        answers_list = json.loads(answers_json)
        print("[DEBUG] Adım 2 Tamamlandı: JSON ayrıştırıldı.")
        
        # --- Adım 3: Analiz için veriyi hazırla ve çağır ---
        report_data = {
            "report_text": report_text,
            "answers": answers_list
        }

        print("[DEBUG] Adım 3: Tam analiz fonksiyonu (run_full_analysis) çağrılıyor...")
        final_analysis = analysis_service.run_full_analysis(report_data)
        print("[DEBUG] Adım 3 Tamamlandı: Analiz bitti.")

        if "error" in final_analysis:
             raise HTTPException(status_code=500, detail=final_analysis["error"])
        
        # --- Adım 4: Sonucu döndür ---
        return AnalysisResult(
            intern_id=intern_id,
            **final_analysis
        )
    except Exception as e:
        # Bu blok, analysis_service.run_full_analysis içindeki herhangi bir hatayı yakalayacak
        print("!!!!!!!!!!!!!!!!! ANALİZ SIRASINDA BEKLENMEDİK BİR HATA YAKALANDI !!!!!!!!!!!!!!!!!")
        import traceback
        traceback.print_exc() # Hatanın tüm detaylarını terminale yazdır
        raise HTTPException(status_code=500, detail=f"Sunucuda beklenmedik bir hata oluştu: {e}")