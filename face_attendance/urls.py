from django.urls import path
from . import views

app_name = 'face_attendance'

urlpatterns = [
    path('index/', views.index, name='index'),

    path('register/', views.register_face, name='register_face'),

    path('register/success/', views.register_success, name='register_success'),

    path('dashboard/', views.dashboard, name='dashboard'),


    path('employee_list/', views.employee_list, name='employee_list'),


    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance_list/', views.emp_attendance_list, name='emp_attendance_list'),

    # path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/<str:employee_id>/', views.employee_detail, name='employee_detail'),

    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),


    path('emp_authorize/<str:employee_id>/authorize/', views.emp_authorize, name='emp_authorize'),
    path('emp_delete/<str:employee_id>/delete/', views.emp_delete, name='emp_delete'),

    # path('employee/authorize/<str:employee_id>/', views.emp_authorize, name='emp-authorize'),
    # path('employee/delete/<str:employee_id>/', views.emp_delete, name='emp-delete'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # path('camera-config/', views.camera_config_create, name='camera_config_create'),
    # path('camera-config/list/', views.camera_config_list, name='camera_config_list'),
    # path('camera-config/update/<int:pk>/', views.camera_config_update, name='camera_config_update'),
    # path('camera-config/delete/<int:pk>/', views.camera_config_delete, name='camera_config_delete'),
]