import os
import re
from google import genai
import json
import markdown


# -----------------------------------
# 3️⃣ Analyze Resume (Gemini AI)
# -----------------------------------
def analyze_resume(resume_text: str, target_role: str, experience_level: str, company_type: str) -> dict:
    """
    Sends resume to Gemini AI for ATS evaluation, parses numeric scores dynamically.

    Returns a dict with:
    - final_score: overall match score (0-100)
    - weighted_score: same as final_score
    - breakdown: dictionary of all numeric parameters returned by AI
    - raw_analysis: full Gemini AI output
    """

    # ----------------------------
    # 0️⃣ Early validation
    # ----------------------------
    if not resume_text or not resume_text.strip():
        return {
            "final_score": 0,
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": "No readable text found in resume."
        }

    # 1️⃣ Initialize Gemini client
    # ----------------------------
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "<p>AI configuration error.</p>"  # simplified new line

    client = genai.Client(api_key=api_key)  # new line

    # ----------------------------
    # 2️⃣ Build Gemini prompt
    # ----------------------------
    prompt = f"""
    You are a professional ATS system evaluating a candidate's resume for {target_role}, {experience_level} level, at {company_type}. 
    Your goal is to produce a structured evaluation with numeric scoring and detailed recommendations.

    ⚠️ STRICT FORMAT REQUIRED ⚠️
    Return ONLY in the format below. Do not include explanations outside this format.

    Score Distribution Guidance:
    1. Hard Skills & Keywords (40%) — Primary filter
    - Evaluate both exact and semantic matches of technical skills.
    - Missing required skills can heavily reduce score.
    - Consider recency and frequency of skill usage, penalize keyword stuffing.

    2. Job Title & Level Matching (30%) — Contextual filter
    - Compare candidate's past/current titles with the target role.
    - Boost score for exact matches or relevant seniority indicators.

    3. Education & Certifications (20%) — Binary filter
    - Pass/Fail check for required degrees and certifications.
    - Missing mandatory qualifications can lower score significantly.

    4. Formatting & Parseability (10%) — Technical filter
    - Penalize if resume sections cannot be parsed (e.g., inside graphics or tables).
    - Ensure standard headers are recognized for accurate scoring.

    ⚡ NEW INSTRUCTIONS ⚡
    - You may generate any number of scoring parameters and subdivisions. Be creative.
    - Provide numeric scores for each parameter and for the overall Match Score.
    - Ensure the output is readable by humans and structured clearly.
    - Show how the final Match Score was obtained, but you can choose the format.
    - Keep it consistent and easy to map to a breakdown UI.
    STRICT FORMAT OUTPUT:

    Match Score: <number out of 100>

    Hard Skills & Keywords (40%)
    Job Title & Level Matching (30%) 
    Education & Certifications (20%) 
    Formatting & Parseability (10%)

    Also provide points for each below parameters -
    Matched Skills:
    Missing Skills:
    Weak Alignment Areas:
    Improvement Recommendations:

    Resume:
    {resume_text}
    Return ONLY JSON in this format:
{{
  "weighted_score": 0-100,
  "breakdown": {{
      "Hard Skills & Keywords": 0-100,
      "Job Title & Level Matching": 0-100,
      "Education & Certifications": 0-100,
      "Formatting & Parseability": 0-100
  }},
  "raw_analysis": "full text explanation"
}}
    """ # new line

    # ----------------------------
    # 3️⃣ Call Gemini AI
    # ----------------------------
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        raw_output = response.candidates[0].content.parts[0].text

    except Exception:
        raw_output = '{"error": "AI analysis failed."}'
    # Remove markdown wrapper if present
    cleaned_output = re.sub(r"```json|```", "", raw_output).strip()

    try:
        data = json.loads(cleaned_output)

        # HARD SCHEMA ENFORCEMENT
        required_keys = {"weighted_score", "breakdown", "raw_analysis"}
        if not required_keys.issubset(set(data.keys())):
            data = {
                "weighted_score": 0,
                "breakdown": {},
                "raw_analysis": cleaned_output
            }
    except Exception:
        print("JSON parsing failed. Raw response:\n", cleaned_output)
        data = {
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": cleaned_output
        }
        # ----------------------------
# 4️⃣ Enforce Required Schema
# ----------------------------
    if isinstance(data, dict):

        # Case 1: Gemini returned detailed section instead of required wrapper
        if "weighted_score" not in data and "breakdown" not in data:
            data = {
                "weighted_score": 0,
                "breakdown": {},
                "raw_analysis": json.dumps(data, indent=2)
            }

        # Case 2: weighted_score missing
        if "weighted_score" not in data:
            data["weighted_score"] = 0

        # Case 3: breakdown missing
        if "breakdown" not in data:
            data["breakdown"] = {}

        # Case 4: raw_analysis missing
        if "raw_analysis" not in data:
            data["raw_analysis"] = json.dumps(data, indent=2)

    return normalize_analysis(data)

def normalize_analysis(data: dict) -> dict:
    """
    Ensures stable structure even if Gemini output changes slightly.
    """

    if not isinstance(data, dict):
        return {
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": str(data)
        }

    normalized = {
        "weighted_score": data.get("weighted_score", 0),
        "breakdown": data.get("breakdown", {}),
        "raw_analysis": data.get("raw_analysis", "")
    }

    # Ensure required breakdown keys exist
    required_sections = [
        "Hard Skills & Keywords",
        "Job Title & Level Matching",
        "Education & Certifications",
        "Formatting & Parseability"
    ]

    for section in required_sections:
        if section not in normalized["breakdown"]:
            normalized["breakdown"][section] = 0

    return normalized
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
{resume_text}
"""  # new line

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.candidates[0].content.parts[0].text
    except Exception:
        return "<p>Resume generation failed. Please try again.</p>"  # new line

def render_analysis_html(result):
    explanation = result.get("raw_analysis", "")
    html_body = markdown.markdown(explanation)
    return html_body
