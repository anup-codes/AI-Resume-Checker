from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Resume
import os


# =========================
# HOME (PROTECTED)
# =========================
@login_required(login_url='/auth/')
def home(request):
    profile = request.user.username
    return render(request, 'home.html', {"profile": profile})


# =========================
# AUTH PAGE (AJAX)
# =========================
def auth_page(request):

    # 🔥 If already logged in → redirect to home
    if request.user.is_authenticated:
        return redirect('/home/')

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # -------- LOGIN --------
        if form_type == "login":
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid Username"
                })

            user = authenticate(username=username, password=password)

            if user is None:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid Password"
                })

            login(request, user)

            return JsonResponse({
                "status": "success",
                "redirect": "/home/"
            })

        # -------- REGISTER --------
        elif form_type == "register":
            name = request.POST.get('name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')

            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Username already taken!"
                })

            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Email already registered!"
                })

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name
            )

            login(request, user)

            return JsonResponse({
                "status": "success",
                "redirect": "/home/"
            })

    return render(request, 'auth.html')


# =========================
# RESUME UPLOAD (PROTECTED)
# =========================
@login_required(login_url='/auth/')
def upload_resume(request):

    if request.method == "POST":
        resume_file = request.FILES.get('resume')

        if not resume_file:
            return JsonResponse({
                "status": "error",
                "message": "No file uploaded."
            })

        ext = os.path.splitext(resume_file.name)[1].lower()
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']

        if ext not in allowed_extensions:
            return JsonResponse({
                "status": "error",
                "message": "Only PDF or image files are allowed."
            })

        Resume.objects.create(
            user=request.user,
            resume=resume_file
        )

        return JsonResponse({
            "status": "success",
            "message": "Resume uploaded successfully!"
        })

    return render(request, 'resume.html')
