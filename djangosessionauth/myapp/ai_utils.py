import os
import re
from google import genai
import json
import markdown
from google.genai import types

# -----------------------------
# Flexible score extraction
# -----------------------------
def extract_score_flexible(category_name: str, text: str) -> float:
    """
    Extracts a numeric score out of 100 from AI analysis text for a given category.
    Flexible enough to handle:
    - colon or dash
    - extra spaces
    - decimal numbers
    - optional subcategories/notes after number
    """
    pattern = rf"{re.escape(category_name)}\s*[:\-]\s*(\d+\.?\d*)\s*/100"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    else:
        # fallback: try to find any number in the first line containing category_name
        lines = text.splitlines()
        for line in lines:
            if category_name.lower() in line.lower():
                nums = re.findall(r"\d+\.?\d*", line)
                if nums:
                    return float(nums[0])
    return 0.0


# -----------------------------------
# 3️⃣ Analyze Resume (Gemini AI)
# -----------------------------------
def analyze_resume(resume_text: str, target_role: str, experience_level: str, company_type: str) -> dict:
    """
    Sends resume to Gemini AI for ATS evaluation.
    Extracts numeric scores via robust regex (supports decimals and colons/dashes).
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
    # 1️⃣ Prompt (kept as-is)
    # ----------------------------
    prompt = f"""
        You are a professional ATS evaluator and resume coach.
        Evaluate this resume for:
        - Role: {target_role}
        - Level: {experience_level}
        - Company Type: {company_type}

        Provide a **final ATS score out of 100** and individual category scores **out of 100**:

        Hard Skills & Keywords
        Job Title & Level Matching
        Education & Certifications
        Formatting & Parseability

        ⚠️ Format Requirements:
        - Output in plain human-readable text
        - Include all scores first
        - Then show:
            - Matched Skills
            - Missing Skills
            - Weak Alignment Areas
            - Improvement Recommendations
        Resume Text:
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
    # 3️⃣ Robust Score Extraction
    # ----------------------------
    def extract_score(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0

    # Find the main scores block
    # Take only the part after the final ATS score appears
    if "Final ATS Score:" in raw_output:
        main_block = raw_output.split("Final ATS Score:")[1]  # everything after
    else:
        main_block = raw_output

    hard = extract_score_flexible("Hard Skills & Keywords", main_block)
    title = extract_score_flexible("Job Title & Level Matching", main_block)
    education = extract_score_flexible("Education & Certifications", main_block)
    formatting = extract_score_flexible("Formatting & Parseability", main_block)
    # ----------------------------
    # 4️⃣ Prepare Breakdown for visuals (int, out of 100)
    # ----------------------------
    breakdown = {
        "Hard Skills & Keywords": int(round(hard)),
        "Job Title & Level Matching": int(round(title)),
        "Education & Certifications": int(round(education)),
        "Formatting & Parseability": int(round(formatting)),
    }

    # ----------------------------
    # 5️⃣ Compute Weighted Score (Backend controlled)
    # ----------------------------
    weighted_score = (
        0.4 * hard +
        0.3 * title +
        0.2 * education +
        0.1 * formatting
    )
    weighted_score = round(weighted_score, 2)

    # ----------------------------
    # 6️⃣ Return full result
    # ----------------------------
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
