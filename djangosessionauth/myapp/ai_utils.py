import PyPDF2
import re
from google import genai
import os


def extract_pdf_text(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text


def analyze_resume(file_path, target_role, experience_level, company_type):


    client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


    resume_text = extract_pdf_text(file_path)

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

    # -------------------------------
    # NEW LOGIC: Extract and Reweight
    # -------------------------------

    def extract_score(category):
        match = re.search(rf"{category}:\s*(\d+)", analysis_text)
        if match:
            score = int(match.group(1))
            # Convert 0–100 to 0–5 scale
            return min(round((score / 100) * 5, 2), 5)
        return 0

    technical = extract_score("Technical Skills")
    projects = extract_score("Projects")
    experience = extract_score("Experience Depth")
    keywords = extract_score("Keywords")
    presentation = extract_score("Presentation")

    # Each category = 20% weight
    breakdown = {
        "technical_skills": round((technical / 5) * 20, 2),
        "projects": round((projects / 5) * 20, 2),
        "experience_depth": round((experience / 5) * 20, 2),
        "keywords": round((keywords / 5) * 20, 2),
        "presentation": round((presentation / 5) * 20, 2),
    }

    weighted_total = round(sum(breakdown.values()), 2)

    return {
        "raw_analysis": analysis_text,
        "weighted_score": weighted_total,  # out of 100
        "breakdown": breakdown
    }
