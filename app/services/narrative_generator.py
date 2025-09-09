# app/services/narrative_generator.py

def create_narrative_summary(analysis_result: dict) -> str:
    """
    Ham analiz sonucunu alır ve mentorun okuyabileceği,
    akıcı bir metin özeti (hikaye) oluşturur.
    """
    # Adım 1: Veriyi güvenli bir şekilde camelCase anahtarlarla oku
    overall = analysis_result.get("overallAnalysis", {})
    details = analysis_result.get("categoryDetails", {})
    
    keyTopics = overall.get("keyTopics", {}).get("challenges", [])
    
    riskLevel = overall.get("riskLevel", "Bilinmiyor").lower()
    motivationStatus = overall.get("motivationStatus", "Bilinmiyor")
    
    summary_parts = []
    
    # Adım 2: Genel durumu özetleyen giriş cümlesini oluştur
    if riskLevel == "yüksek":
        summary_parts.append(f"Bugün stajyer için dikkat gerektiren bir gün olmuş. Motivasyon durumu '{motivationStatus}' olarak tespit edildi.")
    elif riskLevel == "orta":
        summary_parts.append(f"Bugün stajyer için bazı zorluklar içeren bir gün olmuş. Genel motivasyon durumu '{motivationStatus}'.")
    else: # Düşük risk
        summary_parts.append(f"Stajyer bugün genel olarak verimli bir gün geçirmiş görünüyor. Motivasyon durumu '{motivationStatus}'.")

    # Adım 3: Teknik konular ve zorluklar hakkında yorum yap
    if keyTopics:
        tech_topics_str = ", ".join(keyTopics)
        # Zorluk sinyali, 'details' içindeki negatif sinyallerden gelir.
        found_neg_signals = details.get("foundNegSignals", [])
        
        if "engel" in found_neg_signals:
             summary_parts.append(f"Teknik olarak '{tech_topics_str}' konularında bir zorluk yaşanmış görünüyor.")
        else:
             summary_parts.append(f"Teknik tarafta '{tech_topics_str}' konuları üzerinde durulmuş.")

    # Adım 4: Proaktiflik hakkında yorum yap
    proactive = details.get("proactive", {})
    if proactive:
        proactive_status = proactive.get("status")
        if proactive_status == "Çözüm Odaklı":
            summary_parts.append("Karşılaştığı sorunlara karşı çözüm odaklı bir yaklaşım sergiliyor ve bir sonraki adıma dair plan belirtmiş olabilir.")
        else: # Pasif
            summary_parts.append("Ancak, karşılaştığı zorluklar karşısında proaktif bir plan belirtmemiş.")
            
    # Adım 5: İşbirliği hakkında yorum yap
    collaboration = details.get("collaboration", {})
    if collaboration.get("status") == "Aktif İletişim":
        summary_parts.append("Ayrıca, gün içinde takım arkadaşları veya mentoruyla verimli bir etkileşim kurmuş.")
        
    # Adım 6: Cümleleri birleştir ve sonucu döndür
    final_summary = " ".join(summary_parts)
    return final_summary