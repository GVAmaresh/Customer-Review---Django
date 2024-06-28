from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.login, name="login"),
    path("signup", views.signup, name="signup"),
    path("add-review", views.review, name="add_review"),
    path("file-upload", views.file_upload, name="file_upload"),
    path("job-status", views.job_status, name="check_job")
]