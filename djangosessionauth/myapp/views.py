from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Resume, ResumeSurvey, ResumeAnalysis, GeneratedResume
import os
from .resume_utils import extract_resume_text
from .ai_utils import analyze_resume, generate_resume_content, render_analysis_html
from django.http import HttpResponse, HttpResponseBadRequest
from weasyprint import HTML
import logging
from django.conf import settings
import re

logger = logging.getLogger(__name__)


# -----------------------------------
# Authentication page (login/register)
# -----------------------------------
def auth_page(request):
    """
    Handles login and registration on a single page.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "register":
            # Registration logic
            name = request.POST.get("name")
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")
                return redirect("auth")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")
                return redirect("auth")

            # Create user object
            User.objects.create_user(
                username=username,
                email=email,
                first_name=name,
                password=password
            )
            messages.success(request, "Account created successfully")
            return redirect("auth")

        elif form_type == "login":
            # Login logic
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)

            if user is None:
                messages.error(request, "Invalid username or password")
                return redirect("auth")

            login(request, user)
            return redirect("dashboard")

    return render(request, "auth.html")


# -----------------------------------
# Dashboard: shows user's upload & analysis history
# -----------------------------------

@login_required
def dashboard_view(request):
    """
    Handles resume upload and displays analysis history.
    """

    # ---------- HANDLE UPLOAD ----------
    if request.method == "POST":
        resume_file = request.FILES.get("resume")

        if not resume_file:
            messages.error(request, "No file uploaded.")
            return redirect("dashboard")

        ext = resume_file.name.split(".")[-1].lower()
        if ext not in ["pdf", "jpg", "jpeg", "png"]:
            messages.error(request, "Only PDF or image files are allowed.")
            return redirect("dashboard")

        Resume.objects.create(
            user=request.user,
            resume=resume_file
        )

        messages.success(request, "Resume uploaded successfully.")
        return redirect("dashboard")

    # ---------- FETCH HISTORY ----------
    history = ResumeAnalysis.objects.filter(
        resume__user=request.user
    ).select_related("resume").order_by("-created_at")

    context = {
        "history": history
    }

    return render(request, "dashboard.html", context)

# -----------------------------------
# Upload & analyze resume
# -----------------------------------
@login_required
def resume_analysis_view(request):

    if request.method == "POST" and request.FILES.get("resume"):

        uploaded_file = request.FILES['resume']

        resume_instance = Resume.objects.create(
            user=request.user,
            resume=uploaded_file
        )

        survey = ResumeSurvey.objects.create(
            resume=resume_instance,
            target_role=request.POST.get("target_role"),
            experience_level=request.POST.get("experience_level"),
            company_type=request.POST.get("company_type")
        )

        resume_text = extract_resume_text(resume_instance.resume.path)

        if not resume_text.strip():
            return HttpResponseBadRequest(
                "Could not extract readable text from resume."
            )

        raw_result = analyze_resume(
            resume_text=resume_text,
            target_role=survey.target_role,
            experience_level=survey.experience_level,
            company_type=survey.company_type
        )

        raw_breakdown = raw_result.get("breakdown", {})

        main_params = [
            "Hard Skills & Keywords",
            "Job Title & Level Matching",
            "Education & Certifications",
            "Formatting & Parseability"
        ]

        # Ensure only main parameters are included
        filtered_breakdown = {
            k: float(raw_breakdown.get(k, 0))
            for k in main_params
        }

        result = {
            "weighted_score": float(raw_result.get("weighted_score", 0)),
            "breakdown": filtered_breakdown,
            "raw_analysis": raw_result.get(
                "raw_analysis",
                "AI analysis failed."
            )
        }

        formatted_ai_text = render_analysis_html(result)
        

        ResumeAnalysis.objects.create(
            resume=resume_instance,
            final_score=result["weighted_score"],
            full_analysis=formatted_ai_text
        )

        return render(request, "analysis.html", {
            "result": result,
            "resume": resume_instance,
            "analysis_html": formatted_ai_text
        })

    # GET request fallback
    return render(request, "analysis.html", {
        "result": {
            "weighted_score": 0,
            "breakdown": {}
        }
    })
# --------------------------
# Helper: Parse AI analysis into structured sections
# --------------------------
# def parse_analysis(text):
#     """
#     Convert formatted AI output into structured sections for template rendering.
#     Returns a dictionary where keys are section titles and values are the text/content.
#     """
#     sections = {}
#     # Regex: captures "Section Title:" followed by all content until next section or end of text
#     pattern = r"([A-Za-z\s]+:)\s*\n(.*?)(?=\n[A-Za-z\s]+:|\Z)"
#     matches = re.findall(pattern, text, re.DOTALL)

#     for title, content in matches:
#         clean_title = title.strip().replace(":", "")
#         sections[clean_title] = content.strip()

#     return sections


# -----------------------------------
# Generate PDF from resume + AI optimized content
# -----------------------------------
@login_required
def generate_pdf(request, resume_id):
    """
    Fetch the resume and its AI analysis, generate a rendered HTML,
    convert to PDF using WeasyPrint, and send as downloadable file.
    """
    # 1️⃣ Fetch resume by ID, ensure it belongs to the logged-in user
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    # 2️⃣ Fetch associated survey data
    survey = ResumeSurvey.objects.filter(resume=resume).first()
    if not survey:
        return HttpResponseBadRequest("Survey data not found for this resume.")

    # 3️⃣ Read resume file contents
    if not resume.resume:
        return HttpResponseBadRequest("Resume file missing.")

    resume_text = extract_resume_text(resume.resume.path)

    if not resume_text.strip():
        return HttpResponseBadRequest("Could not extract readable text from resume.")   
    
    # 4️⃣ Fetch previous AI analysis, or create a placeholder if missing
    analysis_obj = ResumeAnalysis.objects.filter(resume=resume).first()

    if not analysis_obj:
        return HttpResponseBadRequest("Analysis not found for this resume.")   
     
    # 5️⃣ Generate HTML content for the optimized resume
    new_html_content = generate_resume_content(
        resume_text=resume_text,
        survey_data={
            "target_role": survey.target_role,
            "experience_level": survey.experience_level,
            "company_type": survey.company_type
        },
        analysis_text=analysis_obj.full_analysis or ""
    )

    # 6️⃣ Save or update analysis HTML content
    if isinstance(new_html_content, dict):
        html_content_for_render = new_html_content.get("html_content", "")
    else:
        html_content_for_render = new_html_content

    from .models import GeneratedResume

    generated_resume = GeneratedResume.objects.filter(resume=resume).first()

    if generated_resume:
        generated_resume.html_content = html_content_for_render
        generated_resume.save()
    else:
        GeneratedResume.objects.create(
            resume=resume,
            html_content=html_content_for_render
        )

    # 7️⃣ Render HTML string from template
    html_string = render_to_string(
        "resume_temp.html",
        {"resume_html": html_content_for_render}
    )

    if not html_string.strip():
        return HttpResponseBadRequest("Rendered HTML is empty.")

    # 8️⃣ Convert rendered HTML to PDF
    pdf_file = HTML(string=html_string).write_pdf()

    # 9️⃣ Return PDF as HTTP response for download
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=optimized_resume.pdf"
    return response


# -----------------------------------
# Logout view
# -----------------------------------
def logout_view(request):
    """
    Logs out the user and redirects to the auth page.
    """
    logout(request)
    return redirect("auth")