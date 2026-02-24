import os
import re
from google import genai
import json
import markdown
from google.genai import types



# -----------------------------------
# 3️⃣ Analyze Resume (Gemini AI)
# -----------------------------------
def analyze_resume(resume_text: str, target_role: str, experience_level: str, company_type: str) -> dict:
    """
    Sends resume to Gemini AI for ATS evaluation.
    Extracts numeric scores using regex (no JSON parsing).
    Computes weighted score in backend for stability.
    Returns:
        {
            "weighted_score": float,
            "breakdown": dict,
            "raw_analysis": full_text
        }
    """

    # ----------------------------
    # 0️⃣ Early validation
    # ----------------------------
    if not resume_text or not resume_text.strip():
        return {
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": "No readable text found in resume."
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": "AI configuration error."
        }

    client = genai.Client(api_key=api_key)

    # ----------------------------
    # 1️⃣ Strict Human-Readable Prompt
    # ----------------------------
    prompt = f"""
You are a professional ATS evaluator.

Evaluate this resume for:
Role: {target_role}
Level: {experience_level}
Company Type: {company_type}

⚠️ STRICT OUTPUT FORMAT ⚠️
Follow this EXACT structure:


Hard Skills & Keywords: <number>
Job Title & Level Matching: <number>
Education & Certifications: <number>
Formatting & Parseability: <number>

Matched Skills:
<bullet points>

Missing Skills:
<bullet points>

Weak Alignment Areas:
<bullet points>

Improvement Recommendations:
<bullet points>

Resume:
{resume_text}
"""

    # ----------------------------
    # 2️⃣ Call Gemini (deterministic)
    # ----------------------------
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        raw_output = response.candidates[0].content.parts[0].text.strip()

    except Exception as e:
        print("GEMINI ERROR:", str(e))
        return {
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": "AI analysis failed."
        }

    # ----------------------------
    # 3️⃣ Extract Scores via Regex
    # ----------------------------
    def extract_score(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0

    hard = extract_score(r"Hard Skills\s*&\s*Keywords:\s*(\d+)", raw_output)
    title = extract_score(r"Job Title\s*&\s*Level Matching:\s*(\d+)", raw_output)
    education = extract_score(r"Education\s*&\s*Certifications:\s*(\d+)", raw_output)
    formatting = extract_score(r"Formatting\s*&\s*Parseability:\s*(\d+)", raw_output)

    breakdown = {
    "Hard Skills & Keywords": int(round(hard * 10)),
    "Job Title & Level Matching": int(round(title * 10)),
    "Education & Certifications": int(round(education * 10)),
    "Formatting & Parseability": int(round(formatting * 10)),
}

    # ----------------------------
    # 4️⃣ Compute Weighted Score (Backend Controlled)
    # ----------------------------
    weighted_score = (
        0.4 * hard +
        0.3 * title +
        0.2 * education +
        0.1 * formatting
    )

    weighted_score = round(weighted_score * 10, 2)

    return {
        "weighted_score": weighted_score,
        "breakdown": breakdown,
        "raw_analysis": raw_output
    }

# -----------------------------------
# 4️⃣ Generate Optimized Resume HTML
# -----------------------------------
def generate_resume_content(resume_text: str, survey_data: str, analysis_text: str) -> str:
    """
    Uses Gemini AI to rewrite the resume into optimized HTML.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "<p>AI configuration error.</p>"  # simplified new line

    client = genai.Client(api_key=api_key)  # new line

    prompt = f"""
You are a professional resume writer.

Rewrite and optimize this resume for a candidate applying to software roles, using:

- Survey Data: {survey_data}
- ATS Feedback: {analysis_text}

Requirements:
1. Generate a single-page resume (~150-200 words max)
2. Use standard structure: Contact, Summary, Skills, Work, Projects, Education, Awards (optional)
3. Clear formatting and bullet points for humans and ATS
4. Use action verbs, quantify achievements, highlight technical skills
5. Return ONLY clean HTML content
Resume to rewrite:
Return ONLY clean HTML content.
{resume_text}
"""  # new line

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        return response.candidates[0].content.parts[0].text
    except Exception:
        return "<p>Resume generation failed. Please try again.</p>"  # new line

def render_analysis_html(result):
    explanation = result.get("raw_analysis", "")

    # Ensure explanation is always a string
    if not isinstance(explanation, str):
        explanation = json.dumps(explanation, indent=2)

    return markdown.markdown(explanation)
