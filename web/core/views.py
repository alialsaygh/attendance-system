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
import os
from django.conf import settings as django_settings

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

# helper function to check if a photo has been uploaded for a student
def student_has_photo(student_number):
    photo_path = os.path.join(
        django_settings.MEDIA_ROOT,
        'student_photos',
        student_number + '.jpg'
    )
    return os.path.exists(photo_path)

# ADMIN DASHBOARD

@login_required
@role_required('admin')
def admin_dashboard(request):
    modules = []
    try:
        response = requests.get(API + "/modules")
        modules = response.json().get('modules', [])
    except:
        print("could not connect to flask api")

    # get students and tutors from django database
    raw_students = User.objects.filter(role='student')
    tutors       = User.objects.filter(role='tutor')

    # check photo status for each student
    students = []
    for s in raw_students:
        students.append({
            'id':             s.id,
            'username':       s.username,
            'first_name':     s.first_name,
            'last_name':      s.last_name,
            'email':          s.email,
            'student_number': s.student_number,
            'is_active':      s.is_active,
            'has_photo':      student_has_photo(s.student_number) if s.student_number else False,
        })

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

#  ADMIN VIEWS ALL ATTENDANCE RECORDS
@login_required
@role_required('admin')
def admin_attendance(request):
    records  = []
    modules  = []
    sessions = []

    # Filters from GET params
    filter_module  = request.GET.get('module', '')
    filter_status  = request.GET.get('status', '')
    filter_session = request.GET.get('session', '')
    search_query   = request.GET.get('search', '').strip().lower()

    try:
        all_students = {
            s['student_id']: s
            for s in requests.get(f"{API}/students", timeout=5).json().get('students', [])
        }
        all_modules = {
            m['module_id']: m
            for m in requests.get(f"{API}/modules", timeout=5).json().get('modules', [])
        }
        modules  = list(all_modules.values())
        sessions = requests.get(
            f"{API}/sessions/all", timeout=5
        ).json().get('sessions', [])

        # Collect all attendance records across all sessions
        for session in sessions:
            session_id = session['session_id']
            module     = all_modules.get(session['module_id'], {})

            att = requests.get(
                f"{API}/sessions/{session_id}/attendance", timeout=5
            ).json()

            for r in att.get('records', []):
                student = all_students.get(r['student_id'], {})
                records.append({
                    'session_id':     session_id,
                    'module_code':    module.get('module_code', ''),
                    'module_name':    module.get('module_name', ''),
                    'student_number': student.get('student_number', ''),
                    'student_name':   f"{student.get('first_name','')} {student.get('last_name','')}".strip(),
                    'date':           session.get('start_time', '')[:10],
                    'time':           session.get('start_time', '')[11:16],
                    'tap_time':       r.get('tap_time', '')[:16].replace('T', ' '),
                    'status':         r.get('result', ''),
                    'session_status': session.get('status', ''),
                })

        # Apply filters
        if filter_module:
            records = [r for r in records if r['module_code'] == filter_module]
        if filter_status:
            records = [r for r in records if r['status'] == filter_status]
        if filter_session:
            records = [r for r in records if str(r['session_id']) == filter_session]
        if search_query:
            records = [
                r for r in records
                if search_query in r['student_name'].lower()
                or search_query in r['student_number'].lower()
                or search_query in r['module_code'].lower()
            ]

        # Sort newest first
        records.sort(key=lambda x: (x['date'], x['time']), reverse=True)

    except Exception as ex:
        messages.warning(request, f'Could not load records: {ex}')

    # Summary counts
    summary = {
        'total':   len(records),
        'present': len([r for r in records if r['status'] == 'present']),
        'late':    len([r for r in records if r['status'] == 'late']),
        'absent':  len([r for r in records if r['status'] == 'absent']),
    }

    return render(request, 'core/admin_attendance.html', {
        'records':        records,
        'modules':        modules,
        'sessions':       sessions,
        'summary':        summary,
        'filter_module':  filter_module,
        'filter_status':  filter_status,
        'filter_session': filter_session,
        'search_query':   search_query,
    })


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
    students_list = []
    module_info   = {}
    active_session = {}

    try:
        enrolments   = requests.get(API + "/enrolments").json().get('enrolments', [])
        all_students = requests.get(API + "/students").json().get('students', [])
        module_info  = requests.get(API + "/modules/" + str(module_id)).json()
        active_session = requests.get(API + "/sessions/active").json()

        # only enrolments for this module
        this_module = [e for e in enrolments if e['module_id'] == module_id]

        students_dict = {s['student_id']: s for s in all_students}

        # get live attendance if session is active
        attendance_dict = {}
        if active_session.get('session_id'):
            sid = active_session['session_id']
            att = requests.get(API + "/sessions/" + str(sid) + "/attendance").json()
            for r in att.get('records', []):
                attendance_dict[r['student_id']] = r['result']

        # build student rows
        for enrolment in this_module:
            sid     = enrolment['student_id']
            student = students_dict.get(sid)
            if not student:
                continue

            live_status = attendance_dict.get(sid, 'not_scanned')

            # get attendance summary for this student
            percentage     = None
            classification = 'No sessions yet'
            try:
                summary_resp = requests.get(API + "/students/" + str(sid) + "/attendance-summary")
                if summary_resp.status_code == 200:
                    summary_data = summary_resp.json()
                    # find this module in the summary
                    for mod_summary in summary_data.get('modules', []):
                        if mod_summary['module_id'] == module_id:
                            percentage     = mod_summary.get('percentage')
                            classification = mod_summary.get('classification', 'No sessions yet')
                            break
            except:
                # not critical if this fails
                pass

            students_list.append({
                'student_id':     sid,
                'student_number': student['student_number'],
                'name':           student['first_name'] + ' ' + student['last_name'],
                'live_status':    live_status,
                'percentage':     percentage,
                'classification': classification,
            })

    except Exception as e:
        print("module students error:", e)
        messages.warning(request, 'Could not load student list.')

    return render(request, 'core/tutor_module_students.html', {
        'students':       students_list,
        'module':         module_info,
        'active_session': active_session,
    })


# STUDENT DASHBOARD 
# ── STUDENT ATTENDANCE VIEW ────────────────────────────────
@login_required
@role_required('student')
def student_dashboard(request):
    records       = []
    student_found = False
    summary         = None
    overall_pct     = None
    
    selected_module = request.GET.get('module', '')
    selected_status = request.GET.get('status', '')

    try:
        # find this student in flask using their student number
        all_students = requests.get(API + "/students").json().get('students', [])

        my_student = None
        for s in all_students:
            if s['student_number'] == request.user.student_number:
                my_student = s
                break

        if my_student is not None:
            student_found = True
            my_id = my_student['student_id']

            # get attendance summary including percentages
            summary_resp = requests.get(API + "/students/" + str(my_id) + "/attendance-summary")
            if summary_resp.status_code == 200:
                summary_data = summary_resp.json()
                summary      = summary_data.get('modules', [])
                overall_pct  = summary_data.get('overall_percentage', None)

            # get all modules and enrolments for the records table
            all_modules = {}
            for m in requests.get(API + "/modules").json().get('modules', []):
                all_modules[m['module_id']] = m
                
            all_enrolments = requests.get(API + "/enrolments").json().get('enrolments', [])
            my_enrolments  = [e for e in all_enrolments if e['student_id'] == my_id]

            all_sessions = requests.get(API + "/sessions/all").json().get('sessions', [])

            # build attendance records for the table
            for enrolment in my_enrolments:
                mod = all_modules.get(enrolment['module_id'], {})
                module_sessions = [s for s in all_sessions if s['module_id'] == enrolment['module_id']]

                for session in module_sessions:
                    sid = session['session_id']
                    att = requests.get(API + "/sessions/" + str(sid) + "/attendance").json()

                    my_record = None
                    for r in att.get('records', []):
                        if r['student_id'] == my_id:
                            my_record = r
                            break

                    status = my_record['result'] if my_record else 'absent'

                    records.append({
                        'module_code': mod.get('module_code', ''),
                        'module_name': mod.get('module_name', ''),
                        'session_id':  sid,
                        'date':        session.get('start_time', '')[:10],
                        'time':        session.get('start_time', '')[11:16],
                        'status':      status,
                        'tap_time':    my_record['tap_time'][:16].replace('T', ' ') if my_record and my_record.get('tap_time') else '-',
                    })
                    
        # apply filters
        if selected_module:
            records = [r for r in records if r['module_code'] == selected_module]
        if selected_status:
            records = [r for r in records if r['status'] == selected_status]

        # sort newest first
        records.sort(key=lambda x: x['date'], reverse=True)

    except Exception as e:
        print("student dashboard error:", e)
        messages.warning(request, 'Could not load attendance. Is Flask running?')

    module_codes = list(set([r['module_code'] for r in records]))

    return render(request, 'core/student_dashboard.html', {
        'records':       records,
        'student_found': student_found,
        'selected_module': selected_module,
        'selected_status': selected_status,
        'module_codes':  module_codes,
        'student':       request.user,
        'summary':       summary,
        'overall_pct':   overall_pct,
    })

# STUDENT PROFILE VIEW
@login_required
@role_required('student')
def student_profile(request):
    my_student = None
    my_modules = []
    
    try:
        # get all students from flask and find this one by student number
        all_students = requests.get(API + "/students").json().get('students', [])
        
        for s in all_students:
            if s['student_number'] == request.user.student_number:
                my_student = s
                break

        if my_student is None:
            # student exists in django but not in flask database
            print("student not found in flask:", request.user.student_number)

        else:
            my_id = my_student['student_id']

            # get modules this student is enrolled in
            all_enrolments = requests.get(API + "/enrolments").json().get('enrolments', [])
            my_enrolments = [e for e in all_enrolments if e['student_id'] == my_id]

            # get all modules so we can look up names
            all_modules = requests.get(API + "/modules").json().get('modules', [])
            modules_dict = {}
            for m in all_modules:
                modules_dict[m['module_id']] = m

            # build the list of modules the student is enrolled in
            for e in my_enrolments:
                mod = modules_dict.get(e['module_id'])
                if mod:
                    my_modules.append({
                        'module_code': mod['module_code'],
                        'module_name': mod['module_name'],
                        'enrolled_at': e.get('enrolled_at', '')[:10],
                    })
    except Exception as e:
        print("student profile error:", e)
        messages.warning(request, 'Could not load profile data. Is Flask running?')

    return render(request, 'core/student_profile.html', {
        'my_student': my_student,
        'my_modules': my_modules,
        'user':       request.user,
    })
    
# tutor attendance history 
@login_required
@role_required('tutor')
def tutor_attendance_history(request, module_id):
    sessions_data = []
    module_info = {}
    try:
        # module details
        module_info = requests.get(API + "/modules/" + str(module_id)).json()
        
        # get all sessions for this module
        all_sessions = requests.get(API + "/sessions/all").json().get('sessions', [])
        module_sessions = [s for s in all_sessions if s['module_id'] == module_id]
        
        # sort newest first
        module_sessions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        # get all students for lookup
        all_students = requests.get(API + "/students").json().get('students', [])
        students_dict = {s['student_id']: s for s in all_students}
        
        # for each session get attendance records
        for session in module_sessions:
            sid = session['session_id']
            att = requests.get(API + "/sessions/" + str(sid) + "/attendance").json()
            records = att.get('records', [])
            
            # count each status
            present_count = len([r for r in records if r['result'] == 'present'])
            late_count    = len([r for r in records if r['result'] == 'late'])
            absent_count  = len([r for r in records if r['result'] == 'absent'])
            total         = present_count + late_count + absent_count
            
            # build student rows for this session
            student_rows = []
            for r in records:
                student = students_dict.get(r['student_id'], {})
                student_rows.append({
                    'name':           student.get('first_name', '') + ' ' + student.get('last_name', ''),
                    'student_number': student.get('student_number', ''),
                    'status':         r['result'],
                    'tap_time':       r.get('tap_time', '')[:16].replace('T', ' ') if r.get('tap_time') else '-',
                })

            sessions_data.append({
                'session_id':    sid,
                'date':          session.get('start_time', '')[:10],
                'time':          session.get('start_time', '')[11:16],
                'status':        session.get('status', ''),
                'present_count': present_count,
                'late_count':    late_count,
                'absent_count':  absent_count,
                'total':         total,
                'student_rows':  student_rows,
            })

    except Exception as e:
        print("history error:", e)
        messages.warning(request, 'Could not load attendance history.')
    
    return render(request, 'core/tutor_attendance_history.html', {
        'module':   module_info,
        'sessions': sessions_data,
    })
    
# upload student photo for facial recognition
# photo is saved as media/student_photos/<student_number>.jpg
@login_required
@role_required('admin')
def upload_student_photo(request, student_number):
    if request.method == 'POST':
        # check a file was actually uploaded
        if 'photo' not in request.FILES:
            messages.error(request, 'No file selected.')
            return redirect('admin_dashboard')

        photo = request.FILES['photo']

        # check file type 
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if photo.content_type not in allowed_types:
            messages.error(request, 'Only JPG and PNG files are allowed.')
            return redirect('admin_dashboard')

        # check file extension
        name_lower = photo.name.lower()
        if not (name_lower.endswith('.jpg') or name_lower.endswith('.jpeg') or name_lower.endswith('.png')):
            messages.error(request, 'File must be a JPG or PNG image.')
            return redirect('admin_dashboard')

        try:
            # create the folder if it doesnt exist yet
            photos_folder = os.path.join(django_settings.MEDIA_ROOT, 'student_photos')
            os.makedirs(photos_folder, exist_ok=True)

            # save as student_number.jpg - replaces old photo if one exists
            # we always save as .jpg even if it was a png for consistency
            file_path = os.path.join(photos_folder, student_number + '.jpg')

            # write the file to disk
            with open(file_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)

            messages.success(request, 'Photo uploaded for student ' + student_number + '.')
            print("photo saved to:", file_path)  # debug

        except Exception as e:
            print("photo upload error:", e)
            messages.error(request, 'Could not save photo. Error: ' + str(e))

    return redirect('admin_dashboard')