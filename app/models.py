# app/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- Kategori Detayları için Alt Modeller ---

class TechnicalAnalysisDetail(BaseModel):
    status: str
    topics: List[str]
    

class SatisfactionAnalysisDetail(BaseModel):
    status: str
  

class ProactiveAnalysisDetail(BaseModel):
    status: str

# --- Ana Sonuç Modeli ---

class OverallAnalysis(BaseModel):
    development_score: int
    motivation_score: int
    motivation_status: str
    risk_level: str
    summary: str
    key_topics: Dict[str, List[str]]

class AnalysisResult(BaseModel):
    """
    Analiz sonrası API'den dönecek olan nihai sonucu temsil eden model.
    """
    intern_id: int = Field(..., description="Analizi yapılan stajyerin ID'si.")
    overall_analysis: OverallAnalysis
    category_details: Dict[str, Any] # Daha esnek olması için Any kullanıyoruz