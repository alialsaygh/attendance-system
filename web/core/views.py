from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import role_required
import requests
from django.conf import settings
from .models import User

API = settings.FLASK_API_URL
from .models import User

from .models import User

@login_required
@role_required('admin')
def admin_dashboard(request):
    try:
        modules = requests.get(f"{API}/modules").json().get('modules', [])
    except Exception:
        modules = []

    students = User.objects.filter(role='student')
    tutors = User.objects.filter(role='tutor')

    return render(request, 'core/admin_dashboard.html', {
        'students': students,
        'tutors': tutors,
        'modules': modules,
    })
    
# Login / Logout
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


# Role-based dashboard redirect

@login_required
def dashboard(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_tutor():
        return redirect('tutor_dashboard')
    else:
        return redirect('student_dashboard')


# Admin dashboard 

@login_required
@role_required('admin')
def admin_dashboard(request):
    try:
        #students = requests.get(f"{API}/students").json().get('students', [])
        students = User.objects.filter(role='student')
        modules = requests.get(f"{API}/modules").json().get('modules', [])
    except Exception:
        students, modules = [], []

    tutors = User.objects.filter(role='tutor')

    return render(request, 'core/admin_dashboard.html', {
        'students': students,
        'modules': modules,
        'tutors': tutors,
    })
    
# Student creation for admin dashboard

@login_required
@role_required('admin')
def create_student(request):
    if request.method == 'POST':
        student_number = request.POST.get('student_number', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([student_number, first_name, last_name, email, username, password]):
            messages.error(request, "All fields are required.")
            return redirect('admin_dashboard')

        try:
            # 1) Create student in Flask system
            r = requests.post(f"{API}/students", json={
                "student_number": student_number,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "status": "active",
            })

            if r.status_code not in [200, 201]:
                messages.error(request, "Failed to create student in Flask API.")
                return redirect('admin_dashboard')

            # 2) Create Django login account
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('admin_dashboard')

            User.objects.create_user(
                username=username,
                password=password,
                role='student',
                student_number=student_number,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )

            messages.success(request, "Student added successfully.")
        except Exception:
            messages.error(request, "Could not add student. Check Flask API connection.")

    return redirect('admin_dashboard')

# Tutor creation for admin dashboard

@login_required
@role_required('admin')
def create_tutor(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        staff_number = request.POST.get('staff_number', '').strip()

        if not all([username, password, first_name, last_name, email, staff_number]):
            messages.error(request, 'All tutor fields are required.')
            return redirect('admin_dashboard')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('admin_dashboard')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('admin_dashboard')

        try:
            # create login account in Django
            User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role='tutor',
                staff_number=staff_number,
            )

            # optional: also create tutor record in Flask
            requests.post(f"{API}/tutors", json={
                "staff_number": staff_number,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "status": "active",
            })

            messages.success(request, 'Tutor account created successfully.')
        except Exception:
            messages.error(request, 'Could not create tutor.')

    return redirect('admin_dashboard')

# Module creation for admin dashboard

@login_required
@role_required('admin')
def create_module(request):
    if request.method == 'POST':
        module_name = request.POST.get('module_name', '').strip()
        module_code = request.POST.get('module_code', '').strip()

        try:
            r = requests.post(f"{API}/modules", json={
                "module_name": module_name,
                "module_code": module_code,
            })
            if r.status_code in [200, 201]:
                messages.success(request, "Module created successfully.")
            else:
                messages.error(request, "Failed to create module.")
        except Exception:
            messages.error(request, "Flask API is not available.")

    return redirect('admin_dashboard')

# Student deletion for admin dashboard
@login_required
@role_required('admin')
def delete_student(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='student')
            user.delete()
            messages.success(request, 'Student removed successfully.')
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')

    return redirect('admin_dashboard')

# Tutor deletion for admin dashboard

@login_required
@role_required('admin')
def delete_tutor(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='tutor')

            if user.staff_number:
                try:
                    requests.delete(f"{API}/tutors/{user.staff_number}")
                except Exception:
                    pass

            user.delete()
            messages.success(request, 'Tutor removed successfully.')
        except User.DoesNotExist:
            messages.error(request, 'Tutor not found.')

    return redirect('admin_dashboard')

# Module assignment to tutor for admin dashboard

@login_required
@role_required('admin')
def assign_module_to_tutor(request):
    if request.method == 'POST':
        tutor_id = request.POST.get('tutor_id')
        module_id = request.POST.get('module_id')

        try:
            tutor = User.objects.get(id=tutor_id, role='tutor')

            r = requests.post(f"{API}/tutor-modules", json={
                "staff_number": tutor.staff_number,
                "module_id": module_id,
            })

            if r.status_code in [200, 201]:
                messages.success(request, 'Module assigned to tutor successfully.')
            else:
                messages.error(request, 'Failed to assign module.')
        except User.DoesNotExist:
            messages.error(request, 'Tutor not found.')
        except Exception:
            messages.error(request, 'Could not connect to Flask API.')

    return redirect('admin_dashboard')

# Tutor dashboard 

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


# Student dashboard 

@login_required
@role_required('student')
def student_dashboard(request):
    return render(request, 'core/student_dashboard.html')