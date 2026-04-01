from django.urls import path
from . import views

urlpatterns = [

    # Auth 
    path('login/',    views.login_view,  name='login'),
    path('logout/',   views.logout_view, name='logout'),
    path('dashboard/', views.dashboard,  name='dashboard'),

    # Admin 
    path('dashboard/admin/',views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/students/create/', views.create_student, name='create_student'),
    path('dashboard/admin/tutors/create/',views.create_tutor, name='create_tutor'),
    path('dashboard/admin/modules/create/',views.create_module, name='create_module'),
    path('dashboard/admin/students/<int:user_id>/delete/', views.delete_student, name='delete_student'),
    path('dashboard/admin/tutors/<int:user_id>/delete/',views.delete_tutor, name='delete_tutor'),
    path('dashboard/admin/tutors/assign-module/',views.assign_module_to_tutor, name='assign_module_to_tutor'),
    path('dashboard/admin/cards/assign/', views.assign_card, name='assign_card'),
    path('dashboard/admin/cards/assign/',    views.assign_card,   name='assign_card'),
    path('dashboard/admin/students/enrol/',  views.enrol_student, name='enrol_student'),

    # Tutor 
    path('tutor/dashboard/',views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/session/start/', views.session_start, name='session_start'),
    path('tutor/session/close/', views.session_close, name='session_close'),
    path('tutor/scan-station/',views.scan_station, name='scan_station'),
    path('tutor/live-attendance/', views.live_attendance, name='live_attendance'),
    path('tutor/attendance/live-data/',views.live_attendance_data, name='live_attendance_data'),
    

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]