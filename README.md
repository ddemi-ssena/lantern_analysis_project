# 🚀 LanternAnalytics API

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-AI%20Backend-green)
![Transformers](https://img.shields.io/badge/HuggingFace-NLP-yellow)
![SpaCy](https://img.shields.io/badge/SpaCy-Turkish%20NLP-orange)
![License](https://img.shields.io/badge/License-MIT-purple)

**LanternAnalytics API** is an AI-powered FastAPI backend service designed to analyze internship reports and generate data-driven feedback for mentors.

The system processes PDF internship reports, extracts technical insights, evaluates motivation levels, and produces natural-language summaries to support internship evaluation workflows.

It is designed to integrate seamlessly into internship management platforms via API endpoints.

---

## ✨ Key Features

### 📄 Automated PDF Report Analysis
- Extracts text from uploaded internship report PDFs  
- Cleans and preprocesses textual data for NLP tasks  
- Identifies relevant technical content  

### 😊 Sentiment & Motivation Analysis
- Uses a fine-tuned Transformer model:  
  **ssenos/lantern_fine-tuning-v3**
- Detects emotional tone and motivation trends  
- Provides structured motivation insights  

### 🧠 NLP & Technical Entity Recognition
Powered by SpaCy Turkish Transformer model:

Detects technologies and technical skills such as:

- Docker  
- FastAPI  
- PostgreSQL  
- Other domain-specific technologies  

### 📊 Hybrid Performance Scoring
Combines multiple analytical signals:

- Technical competency indicators  
- Motivation analysis  
- Proactiveness signals  

➡️ Produces a structured development/performance score.

### 📝 Narrative Insight Generation
- Converts analytical results into natural-language summaries  
- Generates concise mentor-friendly feedback  
- Helps streamline evaluation processes  

---

## 🏗️ System Architecture

LanternAnalytics functions as a backend AI analysis service:

- Connected to internship platforms via API endpoints  
- Receives PDF reports and structured Q&A data  
- Processes analysis asynchronously  
- Returns structured insights and summaries  

This modular architecture allows easy integration into existing systems.

---

## 🛠️ Tech Stack

### Backend
- FastAPI  
- Python  

### AI / NLP
- Hugging Face Transformers  
- SpaCy Turkish Transformer (`tr_core_news_trf`)  
- PyTorch  

### Data Processing
- Pydantic  
- pdfplumber  

### Server
- Uvicorn  

---

## 📋 Requirements

Minimum requirements:

- Python 3.8+
- FastAPI
- Pydantic
- Transformers & PyTorch
- SpaCy (`tr_core_news_trf`)
- pdfplumber

Install dependencies:

```bash
pip install -r requirements.txt
⚙️ Installation
1️⃣ Clone Repository
git clone https://github.com/ddemi-ssena/lantern_analysis_project.git
cd lantern_analysis_project
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Run API Server
uvicorn app.main:app --reload
🌐 API Access
Base URL
http://127.0.0.1:8000
Swagger Documentation
http://127.0.0.1:8000/docs
🔌 API Usage
Analyze Internship Report
Endpoint:

POST /analyze
Parameters
Parameter	Type	Description
pdf_report	File	Internship report PDF
answers_json	Form Data	Structured Q&A responses
intern_id	Integer	Intern identifier
📂 Project Structure
lantern_analysis_project/
│
├── app/
│   ├── main.py
│   ├── models.py
│   └── services/
│       ├── analysis.py
│       └── narrative_generator.py
│
├── corpus_pdfs/
├── requirements.txt
└── README.md
🎯 Use Cases
Internship performance evaluation

AI-powered educational analytics

Mentor feedback automation

Corporate internship tracking systems

👩‍💻 Author
Sena Özişçi
AI Developer Candidate

GitHub:
👉 https://github.com/ddemi-ssena

📜 License
This project is licensed under the MIT License.

See the LICENSE file for details.
