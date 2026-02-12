from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


@csrf_exempt
@require_POST
def register_view(request):
    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse(
            {"error": "Username and password are required"},
            status=400
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"error": "User already exists"},
            status=400
        )

    User.objects.create_user(
        username=username,
        password=password
    )

    return JsonResponse(
        {"message": "User registered successfully"},
        status=201
    )


@csrf_exempt
@require_POST
def login_view(request):
    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse(
            {"error": "Username and password are required"},
            status=400
        )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return JsonResponse(
            {"error": "Invalid credentials"},
            status=401
        )

    login(request, user)

    return JsonResponse(
        {"message": "Login successful"}
    )


@csrf_exempt
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "User not logged in"},
            status=401
        )

    logout(request)

    return JsonResponse(
        {"message": "Logged out successfully"}
    )


@login_required
def protected_view(request):
    return JsonResponse(
        {
            "message": f"Hello {request.user.username}"
        }
    )
