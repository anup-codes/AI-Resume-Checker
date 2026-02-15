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

def resume_analysis_view(request):
    resume = Resume.objects.filter(user=request.user).last()

    if not resume:
        return render(request, "analysis.html", {"result": "No resume uploaded."})

    result = analyze_resume(resume.resume.path)

    return render(request, "analysis.html", {"result": result})



@login_required
def dashboard_view(request):
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
