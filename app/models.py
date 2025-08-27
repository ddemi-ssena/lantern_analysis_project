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
    developmentScore: int
    motivationScore: int
    motivationStatus: str
    riskLevel: str
    summary: str
    keyTopics: Dict[str, List[str]]

class AnalysisResult(BaseModel):
    """
    Analiz sonrası API'den dönecek olan nihai sonucu temsil eden model.
    """
    internId: int = Field(..., description="Analizi yapılan stajyerin ID'si.")
    overallAnalysis: OverallAnalysis
    categoryDetails: Dict[str, Any] # Daha esnek olması için Any kullanıyoruz