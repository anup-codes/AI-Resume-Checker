from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Resume, ResumeSurvey, ResumeAnalysis
import os
from .ai_utils import analyze_resume, generate_resume_content, format_analysis_text
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest
from weasyprint import HTML
import logging
from django.conf import settings
import re

logger = logging.getLogger(__name__)

# --------------------------
# Helper: Parse AI analysis into structured sections
# --------------------------
def parse_analysis(text):
    """
    Convert formatted AI output into structured sections for template rendering.
    """
    sections = {}
    pattern = r"([A-Za-z\s]+:)\s*\n(.*?)(?=\n[A-Za-z\s]+:|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)

    for title, content in matches:
        clean_title = title.strip().replace(":", "")
        sections[clean_title] = content.strip()

    return sections


# -----------------------------------
# Generate PDF from resume + AI optimized content
# -----------------------------------
@login_required
def generate_pdf(request, resume_id):
    # 1️⃣ Fetch resume
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    # 2️⃣ Fetch survey data
    survey = ResumeSurvey.objects.filter(resume=resume).first()
    if not survey:
        return HttpResponseBadRequest("Survey data not found for this resume.")

    # 3️⃣ Extract raw resume text
    resume_text = resume.resume.path and open(resume.resume.path, "rb").read()
    if not resume_text:
        return HttpResponseBadRequest("Unable to extract resume text from file.")

    # 4️⃣ Fetch previous AI analysis or create new
    analysis_obj, _ = ResumeAnalysis.objects.get_or_create(resume=resume)

    # 5️⃣ Generate optimized resume content (HTML)
    new_html_content = generate_resume_content(
        resume_text=resume_text,
        survey_data={
            "target_role": survey.target_role,
            "experience_level": survey.experience_level,
            "company_type": survey.company_type
        },
        analysis_text=analysis_obj.full_analysis or ""
    )

    # 6️⃣ Save / update analysis
    if isinstance(new_html_content, dict):
        html_content_for_render = new_html_content.get("html_content", "")
    else:
        html_content_for_render = new_html_content

    analysis_obj.full_analysis = new_html_content
    analysis_obj.save()

    # 7️⃣ Render HTML template
    html_string = render_to_string(
        "resume_temp.html",
        {"resume_html": html_content_for_render}
    )

    if not html_string.strip():
        return HttpResponseBadRequest("Rendered HTML is empty.")

    # 8️⃣ Convert to PDF
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=optimized_resume.pdf"
    return response


# -----------------------------------
# Upload & analyze resume
# -----------------------------------
@login_required
def resume_analysis_view(request):
    if request.method == "POST" and request.FILES.get("resume"):
        uploaded_file = request.FILES['resume']

        # 1️⃣ Save resume
        resume_instance = Resume.objects.create(user=request.user, resume=uploaded_file)
        file_path = resume_instance.resume.path

        # 2️⃣ Save survey
        survey = ResumeSurvey.objects.create(
            resume=resume_instance,
            target_role=request.POST.get("target_role"),
            experience_level=request.POST.get("experience_level"),
            company_type=request.POST.get("company_type")
        )

        # 3️⃣ Run AI analysis
        raw_result = analyze_resume(
            file_path=file_path,
            target_role=survey.target_role,
            experience_level=survey.experience_level,
            company_type=survey.company_type
        )

        # 4️⃣ Format AI analysis text & fix Match Score
        formatted_ai_text = format_analysis_text(
            raw_text=raw_result.get("raw_analysis", ""),
            breakdown=raw_result.get("breakdown", {})
        )

        # 5️⃣ Update numeric breakdown from formatted text
        breakdown = raw_result.get("breakdown", {})
        weighted_score = raw_result.get("weighted_score", 0)

        # 6️⃣ Save formatted analysis in DB
        analysis = ResumeAnalysis.objects.create(
            resume=resume_instance,
            final_score=weighted_score,
            full_analysis=formatted_ai_text
        )

        # 7️⃣ Prepare 'result' dict for template (matches your template keys)
        result = {
            "weighted_score": weighted_score,
            "breakdown": breakdown,
            "raw_analysis": formatted_ai_text
        }

        # 8️⃣ Parse formatted AI text for structured sections (optional, if needed)
        analysis_sections = parse_analysis(formatted_ai_text)

        # 9️⃣ Render template
        return render(request, "analysis.html", {
            "resume": resume_instance,
            "survey": survey,
            "analysis": analysis,
            "result": result,
            "analysis_sections": analysis_sections,
        })

    # GET request or no file uploaded
    return render(request, "analysis.html")
@login_required
def upload_resume(request):
    if request.method == "POST":
        resume_file = request.FILES.get('resume')

        if not resume_file:
            messages.error(request, "No file uploaded.")
            return redirect('upload_resume')

        ext = resume_file.name.split('.')[-1].lower()
        if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
            messages.error(request, "Only PDF or image files are allowed.")
            return redirect('upload_resume')

        Resume.objects.create(user=request.user, resume=resume_file)
        messages.success(request, "Resume uploaded successfully!")
        return redirect('analysis')

    return render(request, 'resume.html')


@login_required
def update_history(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at').prefetch_related('resumeanalysis_set')
    
    context = {'resumes': resumes}
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_view(request):
    if request.method == "POST":
        resume_file = request.FILES.get('resume')
        if not resume_file:
            messages.error(request, "No file uploaded.")
            return redirect('dashboard')

        ext = resume_file.name.split('.')[-1].lower()
        if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
            messages.error(request, "Only PDF or image files are allowed.")
            return redirect('dashboard')

        Resume.objects.create(user=request.user, resume=resume_file)
        messages.success(request, "Resume uploaded successfully!")
        return redirect('dashboard')

    history = ResumeAnalysis.objects.filter(
    resume__user=request.user
).select_related('resume').order_by('-created_at')[:5]
    context = {'history': history}
    return render(request, "dashboard.html", context)


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


def logout_view(request):
    logout(request)
    return redirect("auth")