import PyPDF2
import re
from google import genai
import os
import requests


# -----------------------------------
# 1️⃣ Extract PDF text
# -----------------------------------
def extract_pdf_text(file_path):
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
    except Exception:
        return ""
    return text.strip()


# -----------------------------------
# 2️⃣ OCR Fallback (for images)
# -----------------------------------
def extract_text_with_ocr_space(file_path):
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        return ""

    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": f},
                data={
                    "apikey": api_key,
                    "language": "eng",
                },
            )

        result = response.json()
        parsed = result.get("ParsedResults")
        if parsed and len(parsed) > 0:
            return parsed[0].get("ParsedText", "").strip()
    except Exception:
        return ""

    return ""


# -----------------------------------
# 3️⃣ Analyze Resume
# -----------------------------------
def analyze_resume(file_path, target_role, experience_level, company_type):

    # Extract text
    resume_text = ""
    if file_path.lower().endswith(".pdf"):
        resume_text = extract_pdf_text(file_path)

    if not resume_text:
        resume_text = extract_text_with_ocr_space(file_path)

    if not resume_text:
        return {
            "final_score": 0,
            "weighted_score": 0,
            "breakdown": {},
            "raw_analysis": "No readable text found in resume."
        }

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
    You are an ATS evaluating a resume for {target_role}, {experience_level} level, at {company_type}.

    STRICT FORMAT:

    Match Score: <number>

    Technical Skills: <number>
    Projects: <number>
    Experience Depth: <number>
    Keywords: <number>
    Presentation: <number>

    Matched Skills:
    Missing Skills:
    Weak Alignment Areas:
    Improvement Recommendations:

    Resume:
    {resume_text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    analysis_text = response.candidates[0].content.parts[0].text


    # ----------------------------
    # Extract Scores Safely
    # ----------------------------
    def extract_score(label):
        match = re.search(rf"{label}:\s*(\d+)", analysis_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0


    match_score = extract_score("Match Score")

    technical = extract_score("Technical Skills")
    projects = extract_score("Projects")
    experience = extract_score("Experience Depth")
    keywords = extract_score("Keywords")
    presentation = extract_score("Presentation")

    breakdown = {
        "technical_skills": technical,
        "projects": projects,
        "experience_depth": experience,
        "keywords": keywords,
        "presentation": presentation,
    }

    # If Match Score missing, compute average
    if match_score == 0 and breakdown:
        values = [v for v in breakdown.values() if v > 0]
        if values:
            match_score = int(sum(values) / len(values))

    return {
        "final_score": match_score,
        "weighted_score": match_score,
        "breakdown": breakdown,
        "raw_analysis": analysis_text.strip()
    }


# -----------------------------------
# 4️⃣ Generate Optimized Resume HTML
# -----------------------------------
def generate_resume_content(resume_text, survey_data, analysis_text):

    # Convert bytes to string safely
    if isinstance(resume_text, bytes):
        try:
            resume_text = resume_text.decode("utf-8", errors="ignore")
        except Exception:
            resume_text = str(resume_text)

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
    You are a professional resume writer.

    Rewrite and optimize this resume using:
    - Survey Data
    - ATS Feedback

    Return ONLY clean HTML body content.
    No explanations. No markdown.

    Resume:
    {resume_text}

    Survey Data:
    {survey_data}

    ATS Feedback:
    {analysis_text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return response.candidates[0].content.parts[0].text


# -----------------------------------
# 5️⃣ Format Analysis Text
# -----------------------------------
def format_analysis_text(raw_text, breakdown=None):
    if not raw_text:
        return ""

    # 🔥 Remove markdown stars
    raw_text = raw_text.replace("**", "").replace("*", "")
    # Convert single digit scores (like 9) to /100 scale (90)
    # Convert scores out of 10 to out of 100 (only if 1–10)
    # Keep scores strictly between 0–20 (no scaling)
    def convert_score(match):
        score = int(match.group(1))
        score = max(0, min(score, 20))  # safety clamp
        return f": {score}"

    raw_text = re.sub(
        r':\s*(\d{1,2})(?=\s|\n|\))',
        convert_score,
        raw_text
    )



    # Remove existing HTML tags if any
    raw_text = raw_text.replace("<br>", "\n")

    lines = raw_text.split("\n")
    html_output = ""
    in_list = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Section headers
        if line.endswith(":") or re.match(r"^[A-Za-z\s]+:$", line):
            if in_list:
                html_output += "</ul>"
                in_list = False

            title = line.replace(":", "")
            html_output += f"<h3 style='margin-top:20px;'>{title}</h3>"

        # Bullet-style content
        elif (
            (line.startswith("-")) or
            (line and line[0].isdigit()) or
            ("•" in line)
        ):
            if not in_list:
                html_output += "<ul>"
                in_list = True

            cleaned = re.sub(r"^\d+\.\s*", "", line)
            cleaned = cleaned.lstrip("-• ").strip()

            html_output += f"<li>{cleaned}</li>"

        else:
            if in_list:
                html_output += "</ul>"
                in_list = False

            html_output += f"<p>{line}</p>"

    if in_list:
        html_output += "</ul>"

    return html_output
