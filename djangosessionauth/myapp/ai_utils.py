import PyPDF2
import re
from google import genai
import os
import requests


# -----------------------------------
# 1️⃣ Extract PDF text normally
# -----------------------------------
def extract_pdf_text(file_path):
    text = ""

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

    return text.strip()


# -----------------------------------
# 2️⃣ OCR.space fallback
# -----------------------------------
def extract_text_with_ocr_space(file_path):
    api_key = os.getenv("OCR_SPACE_API_KEY")
    url = "https://api.ocr.space/parse/image"

    with open(file_path, "rb") as file:
        response = requests.post(
            url,
            headers={
                "apikey": api_key
            },
            files={
                "file": file
            },
            data={
                "language": "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "isTable": True,
                "OCREngine": 2,          # Engine 2 is more accurate
                "scale": True,           # Improves small text
                "isCreateSearchablePdf": False
            }

        )

    if response.status_code != 200:
        print("OCR API HTTP Error:", response.status_code)
        return ""

    result = response.json()

    if result.get("IsErroredOnProcessing"):
        print("OCR Processing Error:", result)
        return ""

    parsed_results = result.get("ParsedResults")

    if not parsed_results:
        return ""

    extracted_text = parsed_results[0].get("ParsedText")

    if not extracted_text:
        return ""

    return extracted_text.strip()


# -----------------------------------
# 3️⃣ Main Resume Analysis Function
# -----------------------------------
def analyze_resume(file_path, target_role, experience_level, company_type):

    # Step 1: Try normal PDF extraction
    resume_text = extract_pdf_text(file_path)

    # Step 2: If empty → use OCR.space
    if not resume_text:
        resume_text = extract_text_with_ocr_space(file_path)

    # Step 3: If still empty → stop
    if not resume_text:
        return {
            "final_score": 0,
            "raw_analysis": "No readable text found in resume.",
            "weighted_score": 0,
            "breakdown": {}
        }

    # -----------------------------------
    # Gemini Client (Correct Key)
    # -----------------------------------
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = f"""
You are an Applicant Tracking System (ATS) used by leading technology companies.

Candidate Target Role: {target_role}
Experience Level: {experience_level}
Target Company Type: {company_type}

Use widely accepted industry expectations for professional in this role within the {target_role} and {experience_level} in {company_type}.

Evaluate the resume based on:

1. Technical skill alignment
2. Project relevance and impact
3. Depth of subject knowledge
4. Practical hands-on experience
5. Keyword alignment with industry standards
6. Overall clarity and structure

Return your evaluation in the following structured format:

Match Score (0–100):
Breakdown of score by category:
- Technical Skills:
- Projects:
- Experience Depth:
- Keywords:
- Presentation:

Be objective and critical. Avoid generic praise.
Provide measurable feedback 

 Matched skills:
 Missing skills:
 Weak alignment areas:
 Improvement recommendations:

Resume:
{resume_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    analysis_text = response.candidates[0].content.parts[0].text

    # -----------------------------------
    # Extract & Reweight Scores
    # -----------------------------------
    def extract_score(category):
        match = re.search(rf"{category}:\s*(\d+)", analysis_text)
        if match:
            score = int(match.group(1))
            return min(round((score / 100) * 5, 2), 5)
        return 0

    technical = extract_score("Technical Skills")
    projects = extract_score("Projects")
    experience = extract_score("Experience Depth")
    keywords = extract_score("Keywords")
    presentation = extract_score("Presentation")

    breakdown = {
        "technical_skills": round((technical / 5) * 20, 2),
        "projects": round((projects / 5) * 20, 2),
        "experience_depth": round((experience / 5) * 20, 2),
        "keywords": round((keywords / 5) * 20, 2),
        "presentation": round((presentation / 5) * 20, 2),
    }

    weighted_total = round(sum(breakdown.values()), 2)

    return {
        "final_score": weighted_total,
        "raw_analysis": analysis_text,
        "weighted_score": weighted_total,
        "breakdown": breakdown
    }
