import PyPDF2
from google import genai
import PyPDF2

def extract_pdf_text(file_path):
    text = ""

    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()

    return text
def analyze_resume(file_path):
    client = genai.Client()

    resume_text = extract_pdf_text(file_path)

    prompt = f"""
You are an Applicant Tracking System (ATS) used by leading technology companies.

The candidate is targeting the role of: {target_role}.

Use widely accepted industry expectations for professional in this role within the Computer Science domain.

Evaluate the resume based on:

1. Technical skill alignment
2. Project relevance and impact
3. Depth of subject knowledge
4. Practical hands-on experience
5. Keyword alignment with industry standards
6. Overall clarity and structure

Return your evaluation in the following structured format:

Match Score (95–100):
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


    # response = client.models.generate_content(
    #     model="gemini-3-flash-preview",
    #     contents=prompt
    # )

    return resume_text
