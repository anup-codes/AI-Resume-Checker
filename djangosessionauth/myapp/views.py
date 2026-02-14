from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from .models import Resume
import os

def home(request):
    profile = request.user.username

    return render(request, 'home.html',{"profile":profile})

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
def register_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Username must be unique
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('/register/')

        # Email must be unique
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('/register/')

        # Create user properly
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name  # store full name here
        )

        messages.success(request, "Account created successfully!")
        return redirect('/login/')

    return render(request, 'register.html')


@login_required
def upload_resume(request):
    if request.method == "POST":
        resume_file = request.FILES.get('resume')

        if not resume_file:
            messages.error(request, "No file uploaded.")
            return redirect('/resume/')

        ext = os.path.splitext(resume_file.name)[1].lower()

        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']

        if ext not in allowed_extensions:
            messages.error(request, "Only PDF or image files are allowed.")
            return redirect('/resume/')

        Resume.objects.create(
            user=request.user,
            resume=resume_file
        )

        messages.success(request, "Resume uploaded successfully!")
        return redirect('/resume/')

    return render(request, 'resume.html')