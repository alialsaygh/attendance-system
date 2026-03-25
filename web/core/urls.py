from django.urls import path
from . import views

urlpatterns = [
    path('login/',             views.login_view,       name='login'),
    path('logout/',            views.logout_view,      name='logout'),
    path('dashboard/',         views.dashboard,        name='dashboard'),
    path('admin/dashboard/',   views.admin_dashboard,  name='admin_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('tutor/dashboard/',   views.tutor_dashboard,  name='tutor_dashboard'),
    
    path('dashboard/admin/modules/create/', views.create_module, name='create_module'),
    path('dashboard/admin/students/create/', views.create_student, name='create_student'),
    
    path('dashboard/admin/tutors/create/', views.create_tutor, name='create_tutor'),
    path('dashboard/admin/students/<int:user_id>/delete/', views.delete_student, name='delete_student'),
    path('dashboard/admin/tutors/<int:user_id>/delete/', views.delete_tutor, name='delete_tutor'),
    path('dashboard/admin/tutors/assign-module/', views.assign_module_to_tutor, name='assign_module_to_tutor'),
    
    path('student/dashboard/', views.student_dashboard,name='student_dashboard'),
]