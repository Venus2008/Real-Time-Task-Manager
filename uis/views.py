from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from account.models import User  #
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import status


def login_page(request):
    return render(request, "login.html")



@login_required
def dashboard_view(request):
    managers_count = User.objects.filter(role="MANAGER").count()
    employees_count = User.objects.filter(role="EMPLOYEE").count()

    context = {
        "managers": managers_count,
        "employees": employees_count,
    }
    return render(request, "dashboard.html", context)


