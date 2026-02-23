from django.db import models
from django.contrib.auth.models import User

# =========================================
# Resume Model
# Stores uploaded resumes and associates them with a user
# =========================================
class Resume(models.Model):
    # Link resume to a registered user
    # One user can have multiple resumes
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # FileField automatically handles upload paths
    # Files are stored in MEDIA_ROOT/resumes/
    resume = models.FileField(upload_to='resumes/')

    # Automatically save timestamp of when the file was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # This defines how object will appear in Django admin or when printed
    def __str__(self):
        return self.user.username

# =========================================
# ResumeSurvey Model
# Stores user preferences and context for analysis
# This allows AI scoring to be contextual, not generic
# =========================================
class ResumeSurvey(models.Model):

    # Target role choices; stored value vs human-readable label
    ROLE_CHOICES = [
        ("backend", "Backend Developer"),
        ("frontend", "Frontend Developer"),
        ("android", "Android Developer"),
        ("ml", "Machine Learning Engineer"),
        ("data", "Data Analyst"),
    ]

    # Experience level choices
    EXPERIENCE_CHOICES = [
        ("fresher", "Fresher"),
        ("junior", "1-3 Years"),
        ("mid", "3-5 Years"),
        ("senior", "5+ Years"),
    ]

    # Company type choices
    COMPANY_CHOICES = [
        ("startup", "Startup"),
        ("product", "Product Based"),
        ("service", "Service Based"),
        ("faang", "FAANG"),
    ]

    # One-to-one relationship with Resume
    # Each resume can have exactly one survey
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE)

    # Stores the target role, experience level, and company type
    target_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_CHOICES)
    company_type = models.CharField(max_length=50, choices=COMPANY_CHOICES)

    # Timestamp when the survey was created
    created_at = models.DateTimeField(auto_now_add=True)

# =========================================
# ResumeAnalysis Model
# Stores the output of AI analysis for a resume
# =========================================
class ResumeAnalysis(models.Model):
    # One-to-one relationship with Resume
    # Each resume can have only one analysis
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE)

    # Stores final numeric score (float)
    final_score = models.FloatField()

    # Stores the AI's full analysis in structured JSON format
    # Can include breakdown, suggestions, recommendations
    full_analysis = models.JSONField()  

    # Timestamp when analysis was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Human-readable representation of object
    def __str__(self):
        return f"{self.resume.user.username} - Score: {self.final_score}"

# =========================================
# GeneratedResume Model
# Stores improved/resynthesized resume content as HTML
# Useful for showing the final polished resume on frontend
# =========================================
class GeneratedResume(models.Model):
    # One-to-one relationship with Resume
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE)

    # Stores HTML content of generated resume
    html_content = models.TextField()

    # Timestamp when generated resume was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Human-readable representation
    def __str__(self):
        return f"Generated Resume - {self.resume.user.username}"