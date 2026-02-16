from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Resume
from .models import *
import os
from .ai_utils import analyze_resume
from .models import Resume

from django.contrib.auth.decorators import login_required
from .models import Resume, ResumeSurvey
from .ai_utils import analyze_resume



@login_required
def resume_analysis_view(request):
    if request.method == "POST" and request.FILES.get("resume"):

        resume_file = request.FILES["resume"]

        target_role = request.POST.get("target_role")
        experience_level = request.POST.get("experience_level")
        company_type = request.POST.get("company_type")
        
        if not target_role or not experience_level or not company_type:
            return render(request, "dashboard.html", {
                "error": "Please complete the survey before submitting."
            })


        # 1️⃣ Save Resume
        resume_instance = Resume.objects.create(
            user=request.user,
            resume=resume_file
        )

        # 2️⃣ Save Survey Linked to Resume
        ResumeSurvey.objects.create(
            resume=resume_instance,
            target_role=target_role,
            experience_level=experience_level,
            company_type=company_type,
        )

        # 3️⃣ Run AI with contextual data
        result = analyze_resume(
            resume_instance.resume.path,
            target_role,
            experience_level,
            company_type
        )

        return render(request, "analysis.html", {"result": result})

    return render(request, "dashboard.html")



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
def dashboard_view(request):
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

    return render(request, "dashboard.html")


def auth_page(request):

    # If already logged in → go to dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")   # using URL name (recommended)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # ---------------- REGISTER ----------------
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

        # ---------------- LOGIN ----------------
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
