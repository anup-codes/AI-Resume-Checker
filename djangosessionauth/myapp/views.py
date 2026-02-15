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


def home(request):
    return render(request, 'home.html')

def login_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if a user with the provided username exists
        if not User.objects.filter(username=username).exists():
            # Display an error message if the username does not exist
            messages.error(request, 'Invalid Username')
            return redirect('/login/')
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            # Display an error message if authentication fails (invalid password)
            messages.error(request, "Invalid Password")
            return redirect('/login/')
        else:
            login(request, user)
            return redirect('/home/')
    
    return render(request, 'login.html')

# Define a view function for the registration page
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect

def register_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('/register/')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('/register/')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=name  # storing full name here
        )

        user.set_password(password)
        user.save()

        messages.success(request, "Account created successfully!")
        return redirect('/register/')

    return render(request, 'register.html')
