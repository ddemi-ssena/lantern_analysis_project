from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from app.models import AnalysisResult, OverallAnalysis # OverallAnalysis'i de import et
from app.services import analysis
import json
import io
import pdfplumber
from typing import Optional

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
    pdf_report: Optional[UploadFile] = File(None),
    answers_json: str = Form(...),
    intern_id: int = Form(...),
    analysis_service: analysis = Depends(get_analysis_service)
):
    try:
        # ==========================================================
        # ==     EKSİK OLAN PDF OKUMA KISMI DOLDURULDU            ==
        # ==========================================================
        report_text = ""
        if pdf_report and pdf_report.filename:
            print("[DEBUG] PDF okunuyor...")
            try:
                # Gelen dosyayı byte olarak oku
                pdf_bytes = io.BytesIO(await pdf_report.read())
                # pdfplumber ile byte verisini aç
                with pdfplumber.open(pdf_bytes) as pdf:
                    # Tüm sayfaları gez ve metni birleştir
                    for page in pdf.pages:
                        text = page.extract_text() or ""
                        report_text += text + "\n"
                print("[DEBUG] PDF okuma tamamlandı.")
            except Exception as e:
                print(f"[UYARI] PDF okunamadı ama analiz devam ediyor. Hata: {e}")
                report_text = "" # Hata olursa metni güvenli olması için boşalt
        else:
            print("[DEBUG] PDF gönderilmedi, bu adım atlandı.")
        # ==========================================================

        # Adım 2: JSON Okuma
        print("[DEBUG] JSON ayrıştırılıyor...")
        answers_list = json.loads(answers_json)
        
        # Adım 3: Analiz için veriyi hazırla ve Analiz Servisini Çağır
        report_data = {
            "report_text": report_text,
            "answers": answers_list,
            "intern_id": intern_id
        }

        # final_analysis_dict artık "düz" bir sözlük
        final_analysis_dict = analysis_service.run_full_analysis(report_data)
        print("[DEBUG] Analiz tamamlandı.")

        if "error" in final_analysis_dict:
             raise HTTPException(status_code=500, detail=final_analysis_dict["error"])
        
        # Adım 4: Sonucu Pydantic Modeline Göre İnşa Et
        try:
            overall_data = OverallAnalysis(
                developmentScore=final_analysis_dict.get("developmentScore"),
                motivationScore=final_analysis_dict.get("motivationScore"),
                motivationStatus=final_analysis_dict.get("motivationStatus"),
                riskLevel=final_analysis_dict.get("riskLevel"),
                summary=final_analysis_dict.get("summary"),
                keyTopics=final_analysis_dict.get("keyTopics")
            )

            final_result_model = AnalysisResult(
                internId=final_analysis_dict.get("internId"),
                overallAnalysis=overall_data,
                categoryDetails=final_analysis_dict.get("categoryDetails")
            )

            return final_result_model
        except Exception as e:
            print("Pydantic modeli oluşturulurken hata oluştu!")
            print(f"Gelen Ham Veri: {final_analysis_dict}") 
            raise e

    except Exception as e:
        print("!!!!!!!!!!!!!!!!! ENDPOINT'TE BEKLENMEDİK BİR HATA YAKALANDI !!!!!!!!!!!!!!!!!")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sunucuda beklenmedik bir hata oluştu: {e}")