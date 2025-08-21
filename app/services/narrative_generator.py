def create_narrative_summary(analysis_result: dict) -> str:
    """
    Ham analiz sonucunu alır ve mentorun okuyabileceği,
    akıcı bir metin özeti (hikaye) oluşturur.
    
    Args:
        analysis_result: run_full_analysis fonksiyonundan dönen dictionary.

    Returns:
        Oluşturulan anlatısal özet.
    """
    # Analizin ana bileşenlerini değişkenlere atayalım
    overall = analysis_result.get("overall_analysis", {})
    details = analysis_result.get("category_details", {})
    
    key_topics = overall.get("key_topics", {}).get("challenges", [])

    tech = details.get("technical", {})
    satisfaction = details.get("satisfaction", {})
    proactive = details.get("proactive", {})
    
    # 1. Giriş cümlesi: Genel durumu özetle
    risk_level = overall.get("risk_level", "Bilinmiyor").lower()
    motivation_status = overall.get("motivation_status", "Bilinmiyor")
    
    summary_parts = []
    
    if risk_level == "yüksek":
        summary_parts.append(f"Bugün stajyer için dikkat gerektiren bir gün olmuş. Motivasyon durumu '{motivation_status}' olarak tespit edildi.")
    elif risk_level == "orta":
        summary_parts.append(f"Bugün stajyer için bazı zorluklar içeren bir gün olmuş. Genel motivasyon durumu '{motivation_status}'.")
    else: # Düşük risk
        summary_parts.append(f"Stajyer bugün genel olarak verimli bir gün geçirmiş görünüyor. Motivasyon durumu '{motivation_status}'.")

    if key_topics:
        # Artık elimizde temiz bir liste var, bunu doğrudan kullanabiliriz.
        tech_topics_str = ", ".join(key_topics)
        
        # Durum bilgisi için kategori detaylarına bakalım
        tech_status = details.get("technical", {}).get("status", "Bilinmiyor")

        if tech_status == "Zorlanıyor" or "Yardım İhtiyacı" in (details.get("satisfaction", {}).get("sentiment_label", "")):
             summary_parts.append(f"Teknik olarak '{tech_topics_str}' konularında bir zorluk yaşanmış görünüyor.")
        else:
             summary_parts.append(f"Teknik tarafta '{tech_topics_str}' konuları üzerinde durulmuş.")

    # 3. Proaktiflik analiz cümlesi
    if proactive:
        proactive_status = proactive.get("status")
        if proactive_status == "Çözüm Odaklı":
            summary_parts.append("Karşılaştığı sorunlara karşı çözüm odaklı bir yaklaşım sergiliyor ve bir sonraki adımı planlamış.")
        else: # Pasif
            summary_parts.append("Ancak, karşılaştığı zorluklar karşısında bir sonraki adıma dair proaktif bir plan belirtmemiş.")
            
    collaboration_label = details.get("satisfaction", {}).get("sentiment_label", "") # Fine-tuning modelimizden geliyor
    if collaboration_label == "İşbirliği / İletişim":
        summary_parts.append("Ayrıca, gün içinde takım arkadaşları veya mentoruyla verimli bir etkileşim kurmuş.")
        
    final_summary = " ".join(summary_parts)
    return final_summary