# app/models.py
from pydantic import BaseModel, Field
from typing import List

class AnalysisInput(BaseModel):
    """
    API'ye gelen veriyi temsil eden model.
    Not: PDF dosyası form verisi olarak ayrı geldiği için burada tanımlanmıyor.
    """
    answer1: str = Field(..., description="1. stratejik soruya verilen cevap.")
    answer2: str = Field(..., description="2. stratejik soruya verilen cevap.")
    answer3: str = Field(..., description="3. stratejik soruya verilen cevap.")
    intern_id: int = Field(..., description="Analizi yapılan stajyerin ID'si.")

class AnalysisResult(BaseModel):
    """
    Analiz sonrası API'den dönecek olan sonucu temsil eden model.
    """
    satisfaction_status: str = Field(..., description="Memnuniyet Durumu (Memnun / Gelişime Açık / Endişeli)")
    development_score: int = Field(..., ge=1, le=10, description="Gelişim Puanı (1-10 arası)")
    ai_summary: str = Field(..., description="Yapay zeka tarafından oluşturulan günün özeti.")
    extracted_keywords: List[str] = Field(..., description="Metinden çıkarılan anahtar kelimeler.")
    intern_id: int = Field(..., description="Analizi yapılan stajyerin ID'si.")