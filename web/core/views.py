from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from .decorators import role_required
from .models import User
import requests
from datetime import datetime

API = settings.FLASK_API_URL


# LOGIN / LOGOUT 

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


# DASHBOARD REDIRECT 

@login_required
def dashboard(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_tutor():
        return redirect('tutor_dashboard')
    else:
        return redirect('student_dashboard')


# ADMIN DASHBOARD

@login_required
@role_required('admin')
def admin_dashboard(request):
    try:
        modules = requests.get(f"{API}/modules", timeout=5).json().get('modules', [])
    except Exception:
        modules = []
    students = User.objects.filter(role='student')
    tutors   = User.objects.filter(role='tutor')
    return render(request, 'core/admin_dashboard.html', {
        'students': students,
        'tutors':   tutors,
        'modules':  modules,
    })


# ADMIN: CREATE STUDENT 

@login_required
@role_required('admin')
def create_student(request):
    if request.method == 'POST':
        student_number = request.POST.get('student_number', '').strip()
        first_name     = request.POST.get('first_name', '').strip()
        last_name      = request.POST.get('last_name', '').strip()
        email          = request.POST.get('email', '').strip()
        username       = request.POST.get('username', '').strip()
        password       = request.POST.get('password', '').strip()

        if not all([student_number, first_name, last_name, email, username, password]):
            messages.error(request, 'All fields are required.')
            return redirect('admin_dashboard')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('admin_dashboard')

        try:
            r = requests.post(f"{API}/students", json={
                'student_number': student_number,
                'first_name':     first_name,
                'last_name':      last_name,
                'email':          email,
                'status':         'active',
            }, timeout=5)
            if r.status_code not in [200, 201]:
                messages.error(request, r.json().get('message', 'Flask API error.'))
                return redirect('admin_dashboard')

            User.objects.create_user(
                username=username, password=password,
                role='student', student_number=student_number,
                email=email, first_name=first_name, last_name=last_name,
            )
            messages.success(request, f'Student {first_name} {last_name} created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('admin_dashboard')


# ADMIN: CREATE TUTOR

@login_required
@role_required('admin')
def create_tutor(request):
    if request.method == 'POST':
        username     = request.POST.get('username', '').strip()
        password     = request.POST.get('password', '').strip()
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
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
            User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email, role='tutor', staff_number=staff_number,
            )
            messages.success(request, f'Tutor {first_name} {last_name} created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('admin_dashboard')


# ADMIN: CREATE MODULE 

@login_required
@role_required('admin')
def create_module(request):
    if request.method == 'POST':
        module_code = request.POST.get('module_code', '').strip()
        module_name = request.POST.get('module_name', '').strip()
        if not module_code or not module_name:
            messages.error(request, 'Module code and name are required.')
            return redirect('admin_dashboard')
        try:
            r = requests.post(f"{API}/modules", json={
                'module_code': module_code,
                'module_name': module_name,
            }, timeout=5)
            if r.status_code in [200, 201]:
                messages.success(request, f'Module {module_code} created.')
            else:
                messages.error(request, r.json().get('message', 'Failed.'))
        except Exception as e:
            messages.error(request, f'Flask API error: {e}')
    return redirect('admin_dashboard')


# ADMIN: DELETE STUDENT

@login_required
@role_required('admin')
def delete_student(request, user_id):
    if request.method == 'POST':
        try:
            User.objects.get(id=user_id, role='student').delete()
            messages.success(request, 'Student removed.')
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
    return redirect('admin_dashboard')


# ADMIN: DELETE TUTOR

@login_required
@role_required('admin')
def delete_tutor(request, user_id):
    if request.method == 'POST':
        try:
            User.objects.get(id=user_id, role='tutor').delete()
            messages.success(request, 'Tutor removed.')
        except User.DoesNotExist:
            messages.error(request, 'Tutor not found.')
    return redirect('admin_dashboard')


# ADMIN: ASSIGN MODULE TO TUTOR 

@login_required
@role_required('admin')
def assign_module_to_tutor(request):
    if request.method == 'POST':
        tutor_id  = request.POST.get('tutor_id')
        module_id = request.POST.get('module_id')
        try:
            tutor = User.objects.get(id=tutor_id, role='tutor')
            r = requests.post(f"{API}/tutor-modules", json={
                'staff_number': tutor.staff_number,
                'module_id':    module_id,
            }, timeout=5)
            if r.status_code in [200, 201]:
                messages.success(request, 'Module assigned.')
            else:
                messages.error(request, 'Failed to assign module.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('admin_dashboard')


# ADMIN: ASSIGN CARD TO STUDENT

@login_required
@role_required('admin')
def assign_card(request):
    if request.method == 'POST':
        student_number = request.POST.get('student_id', '').strip()
        card_uid       = request.POST.get('card_uid', '').strip()
        try:
            all_students = requests.get(f"{API}/students", timeout=5).json().get('students', [])
            student = next(
                (s for s in all_students if s['student_number'] == student_number), None
            )
            if not student:
                messages.error(request, 'Student not found in Flask database.')
                return redirect('admin_dashboard')
            r = requests.post(f"{API}/cards/assign", json={
                'student_id': student['student_id'],
                'card_uid':   card_uid,
            }, timeout=5)
            if r.status_code == 200:
                messages.success(request, f'Card {card_uid} assigned to {student_number}.')
            else:
                messages.error(request, r.json().get('message', 'Could not assign card.'))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('admin_dashboard')


# ADMIN: ENROL STUDENT IN MODULE

@login_required
@role_required('admin')
def enrol_student(request):
    if request.method == 'POST':
        student_number = request.POST.get('student_number', '').strip()
        module_id      = request.POST.get('module_id', '').strip()
        try:
            all_students = requests.get(f"{API}/students", timeout=5).json().get('students', [])
            student = next(
                (s for s in all_students if s['student_number'] == student_number), None
            )
            if not student:
                messages.error(request, 'Student not found in Flask database.')
                return redirect('admin_dashboard')
            r = requests.post(f"{API}/enrolments", json={
                'student_id': student['student_id'],
                'module_id':  int(module_id),
            }, timeout=5)
            if r.status_code == 201:
                messages.success(request, f'{student_number} enrolled successfully.')
            else:
                messages.error(request, r.json().get('message', 'Could not enrol.'))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('admin_dashboard')


# TUTOR DASHBOARD 

@login_required
@role_required('tutor')
def tutor_dashboard(request):
    active  = {}
    modules = []
    try:
        active  = requests.get(f"{API}/sessions/active", timeout=5).json()
        modules = requests.get(f"{API}/modules", timeout=5).json().get('modules', [])
    except Exception as e:
        messages.warning(request, f'Could not reach Flask API: {e}')
    return render(request, 'core/tutor_dashboard.html', {
        'active_session': active,
        'modules':        modules,
    })


# TUTOR: START SESSION 

@login_required
@role_required('tutor')
def session_start(request):
    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        try:
            create_resp = requests.post(f"{API}/sessions", json={
                'module_id':  int(module_id),
                'start_time': datetime.utcnow().isoformat(),
            }, timeout=5)
            if create_resp.status_code != 201:
                messages.error(request, 'Could not create session.')
                return redirect('tutor_dashboard')
            session_id = create_resp.json().get('session_id')
            start_resp = requests.post(
                f"{API}/sessions/{session_id}/start", timeout=5
            )
            if start_resp.status_code == 200:
                messages.success(request, 'Session started.')
            else:
                messages.error(request, start_resp.json().get('message', 'Could not start.'))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('tutor_dashboard')


# TUTOR: CLOSE SESSION 

@login_required
@role_required('tutor')
def session_close(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        try:
            resp = requests.post(
                f"{API}/sessions/{session_id}/close", timeout=5
            )
            if resp.status_code == 200:
                messages.success(request, 'Session closed.')
            else:
                messages.error(request, resp.json().get('message', 'Could not close.'))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('tutor_dashboard')


# TUTOR: SCAN STATION 

@login_required
@role_required('tutor')
def scan_station(request):
    active  = {}
    present = []
    late    = []
    try:
        active   = requests.get(f"{API}/sessions/active", timeout=5).json()
        att_data = requests.get(f"{API}/attendance/active", timeout=5).json()
        present  = att_data.get('present', [])
        late     = att_data.get('late', [])
    except Exception as e:
        messages.warning(request, f'Could not reach Flask API: {e}')
    return render(request, 'core/scan_station.html', {
        'active_session': active,
        'present':        present,
        'late':           late,
        'all_scanned':    present + late,
    })


# TUTOR: LIVE ATTENDANCE PAGE 

@login_required
@role_required('tutor')
def live_attendance(request):
    active  = {}
    present = []
    late    = []
    try:
        active   = requests.get(f"{API}/sessions/active", timeout=5).json()
        att_data = requests.get(f"{API}/attendance/active", timeout=5).json()
        present  = att_data.get('present', [])
        late     = att_data.get('late', [])
    except Exception:
        pass
    return render(request, 'core/live_attendance.html', {
        'active_session': active,
        'present':        present,
        'late':           late,
    })


# TUTOR: LIVE DATA JSON 

@login_required
@role_required('tutor')
def live_attendance_data(request):
    try:
        att_data = requests.get(f"{API}/attendance/active", timeout=5).json()
        present  = att_data.get('present', [])
        late     = att_data.get('late', [])
        return JsonResponse({
            "present": present,
            "late":    late,
            "total":   len(present) + len(late),
        })
    except Exception:
        return JsonResponse({"present": [], "late": [], "total": 0})


# TUTOR: MODULE STUDENTS

@login_required
@role_required('tutor')
def tutor_module_students(request, module_id):
    students = []
    module   = {}
    active   = {}
    try:
        enrolments   = requests.get(f"{API}/enrolments", timeout=5).json().get('enrolments', [])
        all_students = requests.get(f"{API}/students", timeout=5).json().get('students', [])
        module       = requests.get(f"{API}/modules/{module_id}", timeout=5).json()
        active       = requests.get(f"{API}/sessions/active", timeout=5).json()

        module_enrolments = [e for e in enrolments if e['module_id'] == module_id]
        student_map       = {s['student_id']: s for s in all_students}

        attendance_map = {}
        if active.get('session_id'):
            records = requests.get(
                f"{API}/sessions/{active['session_id']}/attendance", timeout=5
            ).json().get('records', [])
            attendance_map = {r['student_id']: r['result'] for r in records}

        for e in module_enrolments:
            s = student_map.get(e['student_id'])
            if s:
                students.append({
                    'student_id':     s['student_id'],
                    'student_number': s['student_number'],
                    'name':           f"{s['first_name']} {s['last_name']}",
                    'status':         attendance_map.get(s['student_id'], 'not_scanned'),
                })
    except Exception as e:
        messages.warning(request, f'Could not load data: {e}')

    return render(request, 'core/tutor_module_students.html', {
        'students':       students,
        'module':         module,
        'active_session': active,
    })


# STUDENT DASHBOARD 

@login_required
@role_required('student')
def student_dashboard(request):
    records       = []
    student_found = False
    try:
        all_students = requests.get(f"{API}/students", timeout=5).json().get('students', [])
        my_student   = next(
            (s for s in all_students
            if s['student_number'] == request.user.student_number),
            None
        )
        if my_student:
            student_found = True
            student_id    = my_student['student_id']
            enrolments    = requests.get(f"{API}/enrolments", timeout=5).json().get('enrolments', [])
            all_modules   = {
                m['module_id']: m
                for m in requests.get(f"{API}/modules", timeout=5).json().get('modules', [])
            }
            for e in enrolments:
                if e['student_id'] == student_id:
                    module = all_modules.get(e['module_id'], {})
                    records.append({
                        'module_code': module.get('module_code', ''),
                        'module_name': module.get('module_name', ''),
                        'enrolled_at': e.get('enrolled_at', ''),
                    })
    except Exception as ex:
        messages.warning(request, f'Could not load data: {ex}')

    return render(request, 'core/student_dashboard.html', {
        'records':       records,
        'student_found': student_found,
    })