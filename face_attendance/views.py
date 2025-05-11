from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    Employee, AttendanceRecord, Department, Shift, Payroll, PayPeriod, CameraConfiguration
)
from django.utils import timezone
from django.db import IntegrityError
import datetime
from datetime import timedelta
from .face_utils import register_employee_face, recognize_face_for_attendance

from django.contrib.auth import authenticate, login, logout

import base64
import numpy as np
import cv2
import face_recognition
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Employee, FaceEncoding
from django.http import HttpResponse

import json
from django.http import JsonResponse
from django.utils import timezone
import csv
from decimal import Decimal  # Import Decimal for handling currency calculations

def index(request):
    # Calculate statistics for the dashboard
    employee_count = Employee.objects.filter(is_active=True).count()
    today = timezone.now().date()
    today_attendance_count = AttendanceRecord.objects.filter(date=today).count()
    yesterday = today - timedelta(days=1)
    yesterday_attendance_count = AttendanceRecord.objects.filter(date=yesterday).count()
    first_day_of_month = today.replace(day=1)
    month_attendance_count = AttendanceRecord.objects.filter(date__gte=first_day_of_month, date__lte=today).count()
    
    # Print values for debugging
    print(f"Employee count: {employee_count}")
    print(f"Today attendance: {today_attendance_count}")
    print(f"Yesterday attendance: {yesterday_attendance_count}")
    print(f"Month attendance: {month_attendance_count}")
    
    context = {
        'employee_count': employee_count,
        'today_attendance_count': today_attendance_count,
        'yesterday_attendance_count': yesterday_attendance_count, 
        'month_attendance_count': month_attendance_count,
    }
    
    return render(request, 'face_attendance/index.html', context)

@login_required
def mark_attendance(request):
    """
    View for marking attendance using facial recognition
    """
    # Get the current user (assuming authentication is set up)
    employee = None
    if request.user.is_authenticated:
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            pass

    # Initialize context with current attendance status if employee exists
    context = {}
    if employee:
        today = timezone.now().date()
        try:
            attendance = AttendanceRecord.objects.get(employee=employee, date=today)
            context['check_in_time'] = attendance.check_in_time
            context['check_out_time'] = attendance.check_out_time
        except AttendanceRecord.DoesNotExist:
            context['check_in_time'] = None
            context['check_out_time'] = None

    # Handle POST request (receiving the captured image)
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            image_data = data.get('image_data', '')
            
            # Remove "data:image/jpeg;base64," from the beginning if present
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in the image
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if not face_locations:
                return JsonResponse({
                    'success': False, 
                    'message': 'No face detected. Please position yourself properly.'
                })
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            if not face_encodings:
                return JsonResponse({
                    'success': False, 
                    'message': 'Could not encode face. Please try again.'
                })
            
            # Get the first face encoding (assuming one person at a time)
            face_encoding = face_encodings[0]
            
            # Get all active employees with face encodings
            all_face_encodings = FaceEncoding.objects.filter(employee__is_active=True)
            
            # Match face with database
            for db_encoding in all_face_encodings:
                # Get the stored encoding
                stored_encoding = np.array(db_encoding.get_encoding())
                
                # Compare faces
                matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
                
                if matches[0]:
                    # Face match found
                    matched_employee = db_encoding.employee
                    today = timezone.now().date()
                    now = timezone.now()
                    
                    # Check if attendance already exists for today
                    attendance, created = AttendanceRecord.objects.get_or_create(
                        employee=matched_employee,
                        date=today,
                        defaults={
                            'check_in_time': now,
                            'status': 'present',
                            'verification_method': 'face'
                        }
                    )
                    
                    if created:
                        # First check-in for the day
                        response_data = {
                            'success': True,
                            'message': f'Đã điểm danh giờ vào thành công: {matched_employee.first_name} {matched_employee.last_name}',
                            'check_in': True,
                            'check_out': False,
                            'check_in_time': attendance.check_in_time.strftime('%H:%M:%S')
                        }
                    else:
                        # Already checked in, mark checkout
                        if attendance.check_out_time is None:
                            attendance.check_out_time = now
                            attendance.calculate_hours()  # Assuming this method exists in your model
                            attendance.save()
                            response_data = {
                                'success': True,
                                'message': f'Đã điểm danh giờ ra thành công: {matched_employee.first_name} {matched_employee.last_name}',
                                'check_in': False,
                                'check_out': True,
                                'check_out_time': attendance.check_out_time.strftime('%H:%M:%S')
                            }
                        else:
                            # Already checked out
                            response_data = {
                                'success': False,
                                'message': f'Bạn đã điểm danh đủ cả vào và ra hôm nay.',
                                'check_in': True,
                                'check_out': True
                            }
                    
                    return JsonResponse(response_data)
            
            # If we get here, no matching face was found
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy khuôn mặt nào trùng khớp. Vui lòng thử lại.'
            })
                
        except Exception as e:
            import traceback
            print(f"Error in mark_attendance: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Đã xảy ra lỗi: {str(e)}'
            })
    
    # For GET request, just render the template
    return render(request, 'face_attendance/mark_attendance.html', context)


# def index(request):
#     """Landing page view"""
#     return render(request, 'face_attendance/index.html')

def employee_list(request):
    """View for listing all employees"""
    # Query all employees from the database
    employees = Employee.objects.all()
    
    # Pass the data to the template with correct context variable
    context = {
        'employees': employees  # Fixed the context variable name
    }
    return render(request, 'face_attendance/employee_list.html', context)

def emp_attendance_list(request):
    """View for employee attendance records with optional CSV export"""
    employees = Employee.objects.filter(is_active=True)
    attendance_records = AttendanceRecord.objects.select_related('employee', 'employee__department').order_by('-date')
    
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('attendance_date', '')
    download = request.GET.get('download_report')

    today = timezone.now().date()

    # Optional: Add search or date filter logic here
    if search_query:
        attendance_records = attendance_records.filter(
            employee__first_name__icontains=search_query
        )

    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)

    # CSV Export logic
    if download == 'true':
        response = HttpResponse(content_type='text/csv', charset='utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename={today} attendance_report.csv'

        writer = csv.writer(response)
        writer.writerow([
            'Emp Name', 'Emp ID', 'Department', 'Position',
            'Date', 'Check-in Time', 'Check-out Time', 'Stayed Time'
        ])

        for record in attendance_records:
            check_in = record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else 'N/A'
            check_out = record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else 'N/A'
            stayed = record.calculate_duration if (record.check_in_time and record.check_out_time) else 'Incomplete'

            writer.writerow([
                f"{record.employee.first_name} {record.employee.last_name}",
                record.employee.employee_id,
                record.employee.department.name if record.employee.department else '',
                record.employee.position,
                record.date,
                check_in,
                check_out,
                stayed
            ])

        return response

    # Render template with latest 30 records
    context = {
        'employees': employees,
        'attendance_records': attendance_records[:30],
        'search_query': search_query,
        'date_filter': date_filter,
    }
    
    return render(request, 'face_attendance/emp_attendance_list.html', context)

@login_required
def dashboard(request):
    """Admin dashboard with overview stats"""
    today = timezone.now().date()
    
    # Count stats for today
    total_employees = Employee.objects.filter(is_active=True).count()
    present_today = AttendanceRecord.objects.filter(
        date=today, 
        status__in=['present', 'late']
    ).count()
    absent_today = total_employees - present_today
    
    departments = Department.objects.all()
    
    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'departments': departments,
        'today': today,
    }
    
    return render(request, 'face_attendance/dashboard.html', context)

def employee_list(request):
    """View for listing all employees"""
    # Query all employees from the database
    employees = Employee.objects.all()
    
    # Pass the data to the template with correct context variable
    context = {
        'employees': employees  # Fixed the context variable name
    }
    return render(request, 'face_attendance/employee_list.html', context)

@login_required
def register_face(request):
    """View for registering employee faces"""
    employees = Employee.objects.all()
    
    # Generate next employee ID for new employee form
    next_employee_id = generate_employee_id()
    
    context = {
        'employees': employees,
        'next_employee_id': next_employee_id  # Add this to the context
    }

    if request.method == 'POST':
        is_new_employee = request.POST.get('is_new_employee') == 'true'
        capture_method = request.POST.get('capture_method', 'camera')
        
        try:
            # Handle new employee creation
            if is_new_employee:
                # Get the form data from the JSON string
                employee_form_data = request.POST.get('employee_form_data', '{}')
                try:
                    form_data = json.loads(employee_form_data)
                except json.JSONDecodeError:
                    messages.error(request, "Invalid employee data format")
                    return render(request, 'face_attendance/register_face.html', context)
                
                # Create a new employee
                employee = Employee(
                    employee_id=form_data.get('employee_id'),
                    first_name=form_data.get('first_name'),
                    last_name=form_data.get('last_name'),
                    email=form_data.get('email'),
                    phone=form_data.get('phone'),
                    position=form_data.get('position'),
                    date_hired=form_data.get('date_hired'),
                    is_active=form_data.get('is_active', True)
                )
                
                # Save the new employee first
                employee.save()
                
                # Handle department association
                department_id = form_data.get('department')
                if department_id:
                    try:
                        department = Department.objects.get(id=department_id)
                        employee.department = department
                        employee.save()
                    except Department.DoesNotExist:
                        # If department doesn't exist, create it based on mapping
                        department_name_map = {
                            "1": "Human Resources",
                            "2": "Information Technology",
                            "3": "Finance",
                            "4": "Marketing",
                            "5": "Operations",
                            "6": "Sales",
                            "7": "Research & Development",
                            "8": "Customer Service",
                            "9": "Administration"
                        }
                        
                        department_name = department_name_map.get(department_id)
                        if department_name:
                            new_dept = Department(name=department_name)
                            new_dept.save()
                            employee.department = new_dept
                            employee.save()
            else:
                # Get existing employee
                employee_id = request.POST.get('employee_id')
                employee = Employee.objects.get(id=employee_id)
            
            # Process the image based on capture method
            if capture_method == 'camera':
                # Process webcam capture
                image_data = request.POST.get('image_data')
                if not image_data:
                    messages.error(request, "No image data received")
                    return render(request, 'face_attendance/register_face.html', context)
                
                # Process the base64 image data
                image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                
                # Convert to numpy array for face_recognition
                np_arr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
            else:  # upload method
                if 'photo' not in request.FILES:
                    messages.error(request, "No file uploaded")
                    return render(request, 'face_attendance/register_face.html', context)
                
                # Process the uploaded file
                uploaded_file = request.FILES['photo']
                
                # Convert to numpy array for face_recognition
                file_bytes = uploaded_file.read()
                np_arr = np.frombuffer(file_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # Use face_recognition to find faces in the image
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_img)
            
            if not face_locations:
                messages.error(request, "No face detected in the image. Please try again.")
                return render(request, 'face_attendance/register_face.html', context)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
            
            if not face_encodings:
                messages.error(request, "Could not encode the face. Please try again.")
                return render(request, 'face_attendance/register_face.html', context)
            
            # Create a new face encoding
            encoding = face_encodings[0]  # Get the first face encoding
            
            # Set any existing face encodings for this employee to not primary
            FaceEncoding.objects.filter(employee=employee, is_primary=True).update(is_primary=False)
            
            # Create new face encoding
            face_encoding = FaceEncoding(employee=employee, is_primary=True)
            face_encoding.set_encoding(encoding)  # Use the custom method from your model
            face_encoding.save()
            
            # Optionally update employee profile image
            if capture_method == 'upload' and 'photo' in request.FILES:
                employee.profile_image = request.FILES['photo']
                employee.save()
            elif capture_method == 'camera':
                # Save the base64 image as a file
                from django.core.files.base import ContentFile
                image_name = f"{employee.employee_id}_face.jpg"
                employee.profile_image.save(image_name, ContentFile(image_bytes), save=True)
            
            messages.success(request, f"Face registered successfully for {employee.first_name} {employee.last_name}")
            return redirect('face_attendance:register_success')  # Redirect to success page
            
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'face_attendance/register_face.html', context)

def generate_employee_id():
    """
    Generate a unique employee ID in the format 'EMP001', 'EMP002', etc.
    Checks existing IDs and increments the highest number found.
    """
    from django.db.models import Max
    from django.db.models.functions import Substr, Cast
    from django.db.models import IntegerField
    
    # Get the latest employee object with the highest ID
    latest_employee = Employee.objects.filter(
        employee_id__startswith='EMP'
    ).annotate(
        # Extract the numeric part (e.g., '001' from 'EMP001')
        id_num=Cast(
            Substr('employee_id', 4, length=3),  # Position 4 (1-indexed), length 3
            IntegerField()
        )
    ).order_by('-id_num').first()
    
    # If no employees exist or no employee with EMP prefix, start with EMP001
    if not latest_employee or not latest_employee.employee_id.startswith('EMP'):
        return 'EMP001'
    
    # Extract the number part and increment
    try:
        id_number = int(latest_employee.employee_id[3:])
        next_id_number = id_number + 1
    except (ValueError, IndexError):
        # If we can't parse the number for some reason, start with 1
        next_id_number = 1
    
    # Format the new ID with leading zeros (EMP001, EMP002, etc.)
    new_id = f'EMP{next_id_number:03d}'
    
    return new_id

def register_success(request):
    return render(request, 'face_attendance/register_success.html')

@login_required
def employee_detail(request, employee_id):
    """View employee details and attendance history"""
    employee = Employee.objects.get(employee_id=employee_id)
    attendance_records = AttendanceRecord.objects.filter(employee=employee).order_by('-date')
    
    # Get current month's attendance
    today = timezone.now().date()
    month_start = today.replace(day=1)
    month_records = attendance_records.filter(date__gte=month_start, date__lte=today)
    
    context = {
        'employee': employee,
        'attendance_records': attendance_records[:30],  # Last 30 records
        'month_records': month_records,
    }
    
    return render(request, 'face_attendance/emp_detail.html', context)

@login_required
def emp_authorize(request, employee_id):
    emp = Employee.objects.get(employee_id=employee_id)
    
    if request.method == 'POST':
        authorized = request.POST.get('authorized', False)
        emp.is_active = bool(authorized)  # ← this may not work as expected
        emp.save()
        return redirect('face_attendance:employee_detail', employee_id=emp.employee_id)
    
    return render(request, 'face_attendance/emp_authorize.html', {'emp': emp})

@login_required
def emp_delete(request, employee_id):
    # emp = get_object_or_404(Employee, pk=pk)
    emp = Employee.objects.get(employee_id=employee_id)
    
    if request.method == 'POST':
        emp.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('face_attendance:employee_list')
    
    return render(request, 'face_attendance/emp_delete_confirm.html', {'emp': emp})

@login_required
def emp_update(request, employee_id):
    """
    Update employee information
    """
    employee = get_object_or_404(Employee, employee_id=employee_id)
    departments = Department.objects.all()
    
    if request.method == 'POST':
        # Process form data
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone')
        employee.position = request.POST.get('position')
        employee.date_hired = request.POST.get('date_hired')
        
        # Department handling removed as requested
        
        # Handle profile image if uploaded
        if 'profile_image' in request.FILES:
            employee.profile_image = request.FILES['profile_image']
        
        # Save the updated employee information
        employee.save()
        
        messages.success(request, f'Thông tin nhân viên {employee.first_name} {employee.last_name} đã được cập nhật.')
        # Make sure you have a URL pattern named 'employee_detail' that matches your structure
        return redirect('face_attendance:employee_detail', employee_id=employee.employee_id)
    
    # For GET requests, render the employee detail page with departments
    context = {
        'employee': employee,
        'departments': departments,
    }
    return render(request, 'face_attendance:employee_detail.html', context)

# View function for user login
def user_login(request):
    # Check if the request method is POST, indicating a form submission
    if request.method == 'POST':
        # Retrieve username and password from the submitted form data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user using the provided credentials
        user = authenticate(request, username=username, password=password)

        # Check if the user was successfully authenticated
        if user is not None:
            # Log the user in by creating a session
            login(request, user)
            # Redirect the user to the student list page after successful login
            return redirect('face_attendance:index')
        else:
            # If authentication fails, display an error message
            messages.error(request, 'Invalid username or password.')

    # Render the login template for GET requests or if authentication fails
    return render(request, 'face_attendance/login.html')


# This is for user logout
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def payroll_list(request):
    """View list of payroll periods"""
    payroll_periods = PayPeriod.objects.all().order_by('-payment_date')
    context = {
        'payroll_periods': payroll_periods
    }
    return render(request, 'face_attendance/payroll_list.html', context)

@login_required
def payroll_detail(request, payroll_id):
    """View detailed payroll information for a specific period"""
    pay_period = get_object_or_404(PayPeriod, id=payroll_id)
    payrolls = Payroll.objects.filter(pay_period=pay_period)
    
    context = {
        'pay_period': pay_period,
        'payrolls': payrolls,
    }
    
    return render(request, 'face_attendance/payroll_detail.html', context)


@login_required
def work_units_list(request):
    """Hiển thị danh sách ngày công của tất cả nhân viên"""
    try:
        search_query = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Mặc định hiển thị dữ liệu của tháng hiện tại
        today = timezone.now().date()
        if not date_from:
            date_from = today.replace(day=1).strftime('%Y-%m-%d')  # Ngày đầu tiên của tháng
        if not date_to:
            date_to = today.strftime('%Y-%m-%d')  # Ngày hiện tại
            
        employees = Employee.objects.filter(is_active=True)
        
        if search_query:
            employees = employees.filter(
                first_name__icontains=search_query) | employees.filter(
                last_name__icontains=search_query) | employees.filter(
                employee_id__icontains=search_query
            )
        
        # Lấy thông tin ngày công cho mỗi nhân viên
        employee_work_data = []
        for employee in employees:
            records = AttendanceRecord.objects.filter(
                employee=employee,
                date__range=[date_from, date_to]
            )
            
            total_hours = sum(record.hours_worked or 0 for record in records)
            total_work_units = sum(record.work_units or 0 for record in records)
            
            # Chuyển đổi sang cùng kiểu dữ liệu trước khi thực hiện phép nhân
            daily_rate = Decimal(str(employee.daily_rate)) if employee.daily_rate else Decimal('0')
            total_work_units = Decimal(str(total_work_units)) if total_work_units else Decimal('0')
            estimated_salary = daily_rate * total_work_units
            
            employee_work_data.append({
                'employee': employee,
                'total_hours': round(total_hours, 2),
                'total_work_units': round(total_work_units, 2),
                'estimated_salary': round(estimated_salary, 2)
            })
        
        # Sắp xếp theo số ngày công giảm dần
        employee_work_data.sort(key=lambda x: x['total_work_units'], reverse=True)
        
        context = {
            'employee_work_data': employee_work_data,
            'search_query': search_query,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        if request.GET.get('download_report') == 'true':
            response = HttpResponse(content_type='text/csv', charset='utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename=work_units_report_{date_from}_to_{date_to}.csv'
            
            writer = csv.writer(response)
            writer.writerow([
                'Mã NV', 'Tên Nhân Viên', 'Phòng Ban', 'Tổng Giờ Làm Việc', 
                'Tổng Công', 'Mức Lương Ngày', 'Lương Dự Kiến'
            ])
            
            for data in employee_work_data:
                writer.writerow([
                    data['employee'].employee_id,
                    f"{data['employee'].first_name} {data['employee'].last_name}",
                    data['employee'].department.name if data['employee'].department else 'N/A',
                    data['total_hours'],
                    data['total_work_units'],
                    float(data['employee'].daily_rate) if data['employee'].daily_rate else 0.0,
                    data['estimated_salary']
                ])
            
            return response
        
        return render(request, 'face_attendance/work_units_list.html', context)
    except Exception as e:
        messages.error(request, f"Lỗi khi hiển thị danh sách ngày công: {str(e)}")
        return redirect('face_attendance:index')

@login_required
def salary_calculator(request):
    """Trang tính lương tổng hợp cho tất cả nhân viên"""
    try:
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Mặc định hiển thị dữ liệu của tháng hiện tại
        today = timezone.now().date()
        if not date_from:
            date_from = today.replace(day=1).strftime('%Y-%m-%d')  # Ngày đầu tiên của tháng
        if not date_to:
            date_to = today.strftime('%Y-%m-%d')  # Ngày hiện tại
        
        employees = Employee.objects.filter(is_active=True)
        
        # Tính toán lương cho mỗi nhân viên
        salary_data = []
        total_salary = 0
        
        for employee in employees:
            records = AttendanceRecord.objects.filter(
                employee=employee,
                date__range=[date_from, date_to]
            )
            
            total_work_units = sum(record.work_units or 0 for record in records)
            
            # Chuyển đổi sang cùng kiểu dữ liệu trước khi thực hiện phép nhân
            daily_rate = Decimal(str(employee.daily_rate)) if employee.daily_rate else Decimal('0')
            total_work_units_float = Decimal(str(total_work_units)) if total_work_units else Decimal('0')
            
            salary = daily_rate * total_work_units_float
            deductions = salary * Decimal('0.2')  # Khấu trừ 20% (thuế + bảo hiểm)
            net_salary = salary - deductions
            
            salary_data.append({
                'employee': employee,
                'total_work_units': round(total_work_units_float, 2),
                'salary': round(salary, 2),
                'deductions': round(deductions, 2),
                'net_salary': round(net_salary, 2)
            })
            
            total_salary += net_salary
        
        # Sắp xếp theo lương giảm dần
        salary_data.sort(key=lambda x: x['net_salary'], reverse=True)
        
        context = {
            'salary_data': salary_data,
            'date_from': date_from,
            'date_to': date_to,
            'total_salary': round(total_salary, 2)
        }
        
        if request.GET.get('download_report') == 'true':
            response = HttpResponse(content_type='text/csv', charset='utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename=salary_report_{date_from}_to_{date_to}.csv'
            
            writer = csv.writer(response)
            writer.writerow([
                'Mã NV', 'Tên Nhân Viên', 'Phòng Ban', 'Tổng Công', 
                'Lương Gộp', 'Khấu Trừ', 'Lương Thực Nhận'
            ])
            
            for data in salary_data:
                writer.writerow([
                    data['employee'].employee_id,
                    f"{data['employee'].first_name} {data['employee'].last_name}",
                    data['employee'].department.name if data['employee'].department else 'N/A',
                    data['total_work_units'],
                    data['salary'],
                    data['deductions'],
                    data['net_salary']
                ])
            
            return response
        
        return render(request, 'face_attendance/salary_calculator.html', context)
    except Exception as e:
        messages.error(request, f"Lỗi khi tính toán lương: {str(e)}")
        return redirect('face_attendance:index')

@login_required
def employee_salary(request, employee_id):
    """Hiển thị chi tiết tính lương cho nhân viên cụ thể"""
    employee = get_object_or_404(Employee, employee_id=employee_id)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Mặc định hiển thị dữ liệu của tháng hiện tại
    today = timezone.now().date()
    if not date_from:
        date_from = today.replace(day=1).strftime('%Y-%m-%d')  # Ngày đầu tiên của tháng
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')  # Ngày hiện tại
    
    # Lấy các bản ghi chấm công
    attendance_records = AttendanceRecord.objects.filter(
        employee=employee,
        date__range=[date_from, date_to]
    ).order_by('date')
    
    # Tính tổng số công và lương
    total_hours = sum(record.hours_worked for record in attendance_records)
    total_work_units = sum(record.work_units for record in attendance_records)
    
    salary = total_work_units * employee.daily_rate
    deductions = salary * Decimal('0.2')  # Khấu trừ 20% (thuế + bảo hiểm) - Convert float to Decimal
    net_salary = salary - deductions
    
    context = {
        'employee': employee,
        'attendance_records': attendance_records,
        'total_hours': round(total_hours, 2),
        'total_work_units': round(total_work_units, 2),
        'salary': round(salary, 2),
        'deductions': round(deductions, 2),
        'net_salary': round(net_salary, 2),
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'face_attendance/employee_salary.html', context)

@login_required
def update_daily_rate(request, employee_id):
    """Cập nhật mức lương ngày công cho nhân viên"""
    employee = get_object_or_404(Employee, employee_id=employee_id)
    
    if request.method == 'POST':
        try:
            daily_rate = request.POST.get('daily_rate')
            if daily_rate:
                employee.daily_rate = float(daily_rate)
                employee.save()
                messages.success(request, f'Cập nhật mức lương thành công cho {employee.first_name} {employee.last_name}')
            else:
                messages.error(request, 'Vui lòng nhập mức lương hợp lệ')
        except ValueError:
            messages.error(request, 'Mức lương không hợp lệ. Vui lòng nhập số.')
            
        return redirect('face_attendance:employee_salary', employee_id=employee.employee_id)
    
    context = {
        'employee': employee
    }
    
    return render(request, 'face_attendance/update_daily_rate.html', context)
