from django.urls import path
from . import views

urlpatterns = [
    path('login/',             views.login_view,       name='login'),
    path('logout/',            views.logout_view,      name='logout'),
    path('dashboard/',         views.dashboard,        name='dashboard'),
    path('admin/dashboard/',   views.admin_dashboard,  name='admin_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('tutor/dashboard/',   views.tutor_dashboard,  name='tutor_dashboard'),
    path('student/dashboard/', views.student_dashboard,name='student_dashboard'),
]