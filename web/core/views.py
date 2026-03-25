from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import role_required
import requests
from django.conf import settings

API = settings.FLASK_API_URL


# ─── Login / Logout ───────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Role-based dashboard redirect ───────────────────────────────

@login_required
def dashboard(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_tutor():
        return redirect('tutor_dashboard')
    else:
        return redirect('student_dashboard')


# ─── Admin dashboard (US2, US5, US6) ─────────────────────────────

@login_required
@role_required('admin')
def admin_dashboard(request):
    # Fetch students and modules from Flask API
    try:
        students = requests.get(f"{API}/students").json().get('students', [])
        modules = requests.get(f"{API}/modules").json().get('modules', [])
    except Exception:
        students, modules = [], []

    return render(request, 'core/admin_dashboard.html', {
        'students': students,
        'modules': modules,
    })


# ─── Tutor dashboard (US3, US7, US11, US12) ──────────────────────

@login_required
@role_required('tutor')
def tutor_dashboard(request):
    try:
        active = requests.get(f"{API}/sessions/active").json()
        modules = requests.get(f"{API}/modules").json().get('modules', [])
    except Exception:
        active, modules = {}, []

    return render(request, 'core/tutor_dashboard.html', {
        'active_session': active,
        'modules': modules,
    })


# ─── Student dashboard (US4, US13) ───────────────────────────────

@login_required
@role_required('student')
def student_dashboard(request):
    return render(request, 'core/student_dashboard.html')