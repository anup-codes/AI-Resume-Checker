from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.conf import settings
import os
from .models import Resume, ResumeSurvey, ResumeAnalysis, GeneratedResume
from .resume_utils import extract_resume_text
from .ai_utils import analyze_resume, generate_resume_content, render_analysis_html

from weasyprint import HTML
import logging
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import google.generativeai as genai
import google as genai
logger = logging.getLogger(__name__)


# -----------------------------------
# Authentication page
# -----------------------------------
def auth_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "register":
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

            User.objects.create_user(
                username=username,
                email=email,
                first_name=name,
                password=password
            )

            messages.success(request, "Account created successfully")
            return redirect("auth")

        elif form_type == "login":
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
# Dashboard
# -----------------------------------
@login_required
def dashboard_view(request):

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

    history = ResumeAnalysis.objects.filter(
        resume__user=request.user
    ).select_related("resume").order_by("-created_at")[:10]

    return render(request, "dashboard.html", {"history": history})


# -----------------------------------
# Resume Analysis (MAIN FIXED PART)
# -----------------------------------
@login_required
def resume_analysis_view(request):

    if request.method == "POST" and request.FILES.get("resume"):

        uploaded_file = request.FILES["resume"]

        # Save resume
        resume_instance = Resume.objects.create(
            user=request.user,
            resume=uploaded_file
        )

        # Save survey data
        survey = ResumeSurvey.objects.create(
            resume=resume_instance,
            target_role=request.POST.get("target_role"),
            experience_level=request.POST.get("experience_level"),
            company_type=request.POST.get("company_type")
        )

        # Extract resume text
        resume_text = extract_resume_text(resume_instance.resume.path)

        if not resume_text.strip():
            return HttpResponseBadRequest(
                "Could not extract readable text from resume."
            )

        # Call AI
        raw_result = analyze_resume(
            resume_text=resume_text,
            target_role=survey.target_role,
            experience_level=survey.experience_level,
            company_type=survey.company_type
        )

        # =========================
        # SCORE EXTRACTION (FIXED)
        # =========================
        import re

        analysis_text = raw_result.get("raw_analysis", "")

        def extract_score(label):
            """
            Extract numeric score like:
            **Hard Skills & Keywords:** 75/100
            """
            pattern = rf"{re.escape(label)}.*?(\d+)\s*/\s*100"
            match = re.search(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
            return float(match.group(1)) if match else 0.0

        hard_skills = extract_score("Hard Skills & Keywords")
        job_match = extract_score("Job Title & Level Matching")
        education = extract_score("Education & Certifications")
        formatting = extract_score("Formatting & Parseability")
        final_score = extract_score("Final ATS Score")

        filtered_breakdown = {
            "Hard Skills & Keywords": hard_skills,
            "Job Title & Level Matching": job_match,
            "Education & Certifications": education,
            "Formatting & Parseability": formatting,
        }

        result = {
            "weighted_score": final_score,
            "breakdown": filtered_breakdown,
            "raw_analysis": analysis_text
        }

        # Render formatted HTML
        formatted_ai_text = render_analysis_html(result)

        # Save analysis in DB
        ResumeAnalysis.objects.create(
            resume=resume_instance,
            final_score=result["weighted_score"],
            full_analysis=formatted_ai_text
        )

        # Send to template
        return render(request, "analysis.html", {
            "result": result,
            "analysis_html": formatted_ai_text,
            "resume": resume_instance
        })

    # GET fallback
    return render(request, "analysis.html", {
        "result": {
            "weighted_score": 0,
            "breakdown": {
                "hard_skills": 0,
                "job_match": 0,
                "education": 0,
                "formatting": 0,
            }
        }
    })
# -----------------------------------
# Generate Optimized Resume PDF
# -----------------------------------
@login_required
def generate_pdf(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    survey = ResumeSurvey.objects.filter(resume=resume).first()
    if not survey:
        return HttpResponseBadRequest("Survey data not found.")

    if not resume.resume:
        return HttpResponseBadRequest("Resume file missing.")

    resume_text = extract_resume_text(resume.resume.path)

    if not resume_text.strip():
        return HttpResponseBadRequest("Could not extract readable text.")

    analysis_obj = ResumeAnalysis.objects.filter(resume=resume).first()
    if not analysis_obj:
        return HttpResponseBadRequest("Analysis not found.")

    new_html_content = generate_resume_content(
        resume_text=resume_text,
        survey_data={
            "target_role": survey.target_role,
            "experience_level": survey.experience_level,
            "company_type": survey.company_type
        },
        analysis_text=analysis_obj.full_analysis or ""
    )

    html_content = (
        new_html_content.get("html_content", "")
        if isinstance(new_html_content, dict)
        else new_html_content
    )

    generated_resume, _ = GeneratedResume.objects.get_or_create(
        resume=resume
    )
    generated_resume.html_content = html_content
    generated_resume.save()

    html_string = render_to_string(
        "resume_temp.html",
        {"resume_html": html_content}
    )

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = (
        "attachment; filename=optimized_resume.pdf"
    )

    return response


# -----------------------------------
# Logout
# -----------------------------------
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("auth")

@csrf_exempt
def chatbot(request):
    response_text = ""

    if request.method == "POST":
        user_input = request.POST.get("user_input")

        try:
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction="You are a helpful AI tutor for beginners.")
            response = model.generate_content(user_input)

            response_text = response.text

        except Exception as e:
            response_text = f"Error: {str(e)}"

    return render(request, "chatbot.html", {"response": response_text})

api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise Exception("Google API key not found")

genai.configure(api_key=api_key)
