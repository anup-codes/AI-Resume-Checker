from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class ResumeSurvey(models.Model):

    ROLE_CHOICES = [
        ("backend", "Backend Developer"),
        ("frontend", "Frontend Developer"),
        ("android", "Android Developer"),
        ("ml", "Machine Learning Engineer"),
        ("data", "Data Analyst"),
    ]

    EXPERIENCE_CHOICES = [
        ("fresher", "Fresher"),
        ("junior", "1-3 Years"),
        ("mid", "3-5 Years"),
        ("senior", "5+ Years"),
    ]

    COMPANY_CHOICES = [
        ("startup", "Startup"),
        ("product", "Product Based"),
        ("service", "Service Based"),
        ("faang", "FAANG"),
    ]

    resume = models.OneToOneField(Resume, on_delete=models.CASCADE)
    target_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_CHOICES)
    company_type = models.CharField(max_length=50, choices=COMPANY_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

class ResumeAnalysis(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    final_score = models.FloatField()
    full_analysis = models.JSONField()  # store breakdown & suggestions
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume.user.username} - Score: {self.final_score}"