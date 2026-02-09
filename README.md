🚀 LanternAnalytics API

LanternAnalytics API is an AI-powered FastAPI service designed to analyze internship reports and provide data-driven feedback to mentors.
It processes PDF reports, extracts technical insights, evaluates motivation levels, and generates natural-language summaries to support internship evaluation workflows.

This service is designed to integrate with an intern management web platform via API endpoints.

✨ Key Features
📄 Automated PDF Report Analysis

Extracts text from uploaded internship reports (PDF)

Cleans and preprocesses textual data for NLP analysis

😊 Sentiment & Motivation Analysis

Uses a fine-tuned Transformer model (ssenos/lantern_fine-tuning-v3)

Detects motivation trends and emotional tone in reports

🧠 NLP & Technical Entity Recognition

Powered by SpaCy Turkish Transformer model

Identifies technical skills and keywords such as:

Docker

FastAPI

PostgreSQL

Other domain-specific technologies

📊 Hybrid Performance Scoring

Combines multiple signals:

Technical competency indicators

Motivation signals

Proactiveness indicators

➡️ Produces a structured development score.

📝 Narrative Insight Generation

Converts analytical results into mentor-friendly summaries

Generates concise natural-language feedback

🏗️ System Architecture

LanternAnalytics works as a backend AI analysis service:

Connected to an internship web platform via API endpoints

Receives PDF reports and structured answers from the platform

Processes data asynchronously

Returns analytical insights and summaries

This design allows seamless integration into existing internship management systems.

🛠️ Tech Stack
Category	Technology
Backend Framework	FastAPI
NLP / AI	Hugging Face Transformers, SpaCy
Data Validation	Pydantic
PDF Processing	pdfplumber
Server	Uvicorn
Language	Python
📋 Requirements

Python 3.8+

FastAPI

Pydantic

Transformers & PyTorch

SpaCy (tr_core_news_trf)

pdfplumber

Install all dependencies via:

pip install -r requirements.txt

⚙️ Installation
Clone the repository
git clone https://github.com/ddemi-ssena/lantern_analysis_project.git
cd lantern_analysis_project

Install dependencies
pip install -r requirements.txt

Run the API server
uvicorn app.main:app --reload


API will be available at:

http://127.0.0.1:8000


Swagger documentation:

http://127.0.0.1:8000/docs

🔌 API Usage
Analyze Internship Report

POST /analyze

Used to analyze internship reports submitted from the web platform.

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

GitHub: https://github.com/ddemi-ssena

📜 License

This project is licensed under the MIT License.
See the LICENSE file for details.
