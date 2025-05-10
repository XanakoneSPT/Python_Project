from django.urls import path
from . import views

app_name = 'face_attendance'

urlpatterns = [
    path('', views.index, name='index'),

    path('register/', views.register_face, name='register_face'),

    path('register/success/', views.register_success, name='register_success'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('employee_list/', views.employee_list, name='employee_list'),

    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance_list/', views.emp_attendance_list, name='emp_attendance_list'),

    # path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/update/<str:employee_id>/', views.emp_update, name='emp_update'),

    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
    
    # Thêm đường dẫn mới cho tính công và lương
    path('work_units/', views.work_units_list, name='work_units_list'),
    path('salary_calculator/', views.salary_calculator, name='salary_calculator'),
    path('employee_salary/<str:employee_id>/', views.employee_salary, name='employee_salary'),
    path('update_daily_rate/<str:employee_id>/', views.update_daily_rate, name='update_daily_rate'),

    path('emp_authorize/<str:employee_id>/authorize/', views.emp_authorize, name='emp_authorize'),
    path('emp_delete/<str:employee_id>/delete/', views.emp_delete, name='emp_delete'),


    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    

]