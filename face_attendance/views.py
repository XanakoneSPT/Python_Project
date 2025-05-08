from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    Employee, AttendanceRecord, Department, Shift, Payroll, PayPeriod, CameraConfiguration
)
from django.utils import timezone
from django.db import IntegrityError
import datetime
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


@login_required
def mark_attendance(request):
    """View for marking attendance with face recognition"""
    context = {}
    
    # If user already has an attendance record for today, get it
    if request.user.is_authenticated and hasattr(request.user, 'employee'):
        today = timezone.now().date()
        try:
            attendance = AttendanceRecord.objects.get(
                employee=request.user.employee,
                date=today
            )
            context['check_in_time'] = attendance.check_in_time
            context['check_out_time'] = attendance.check_out_time
        except AttendanceRecord.DoesNotExist:
            pass
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get image data from the request
            data = json.loads(request.body)
            image_data = data.get('image_data')
            
            if not image_data:
                return JsonResponse({'success': False, 'message': 'No image data received'})
            
            # Process the base64 image data
            # Remove the data:image/jpeg;base64, prefix if it exists
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image_bytes = base64.b64decode(image_data)
            
            # Convert to numpy array for face_recognition
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB for face_recognition
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Detect faces in the image
            face_locations = face_recognition.face_locations(rgb_img)
            
            if not face_locations:
                return JsonResponse({'success': False, 'message': 'No face detected in the image. Please try again.'})
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
            
            if not face_encodings:
                return JsonResponse({'success': False, 'message': 'Could not encode the face. Please try again.'})
            
            # Get the first face encoding
            face_encoding = face_encodings[0]
            
            # Get all active employees with face encodings
            from .models import FaceEncoding
            all_face_encodings = FaceEncoding.objects.filter(employee__is_active=True)
            
            matched_employee = None
            
            for db_encoding in all_face_encodings:
                # Get the stored encoding
                stored_encoding = np.array(db_encoding.get_encoding())
                
                # Compare faces
                matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
                
                if matches[0]:
                    matched_employee = db_encoding.employee
                    break
            
            if not matched_employee:
                return JsonResponse({'success': False, 'message': 'No matching employee found. Please register your face first.'})
            
            # Mark attendance
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
            
            if not created:
                # If already checked in, mark checkout time
                if attendance.check_out_time is None:
                    attendance.check_out_time = now
                    attendance.calculate_hours()
                    attendance.save()
                    return JsonResponse({
                        'success': True, 
                        'message': f'Check-out recorded for {matched_employee.first_name} {matched_employee.last_name}',
                        'action': 'check_out',
                        'time': now.strftime('%H:%M:%S')
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'message': f'{matched_employee.first_name} {matched_employee.last_name} already checked out today'
                    })
            else:
                return JsonResponse({
                    'success': True, 
                    'message': f'Check-in recorded for {matched_employee.first_name} {matched_employee.last_name}',
                    'action': 'check_in',
                    'time': now.strftime('%H:%M:%S')
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return render(request, 'face_attendance/mark_attendance.html', context)

def index(request):
    """Landing page view"""
    return render(request, 'face_attendance/index.html')

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
        response = HttpResponse(content_type='text/csv')
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
    context = {'employees': employees}  # Fixed context variable name

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
        return redirect('face_attendance/employee_list')  # Redirect to the student list after deletion
    
    return render(request, 'face_attendance/emp_delete_confirm.html', {'emp': emp})

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

# @login_required
# def camera_config_create(request):
#     # Check if the request method is POST, indicating form submission
#     if request.method == "POST":
#         # Retrieve form data from the request
#         name = request.POST.get('name')
#         camera_source = request.POST.get('camera_source')
#         threshold = request.POST.get('threshold')

#         try:
#             # Save the data to the database using the CameraConfiguration model
#             CameraConfiguration.objects.create(
#                 name=name,
#                 camera_source=camera_source,
#                 threshold=threshold,
#             )
#             # Redirect to the list of camera configurations after successful creation
#             return redirect('camera_config_list')

#         except IntegrityError:
#             # Handle the case where a configuration with the same name already exists
#             messages.error(request, "A configuration with this name already exists.")
#             # Render the form again to allow user to correct the error
#             return render(request, 'camera_config_form.html')

#     # Render the camera configuration form for GET requests
#     return render(request, 'face_attendance/camera_config_form.html')


# # READ: Function to list all camera configurations
# @login_required
# def camera_config_list(request):
#     # Retrieve all CameraConfiguration objects from the database
#     configs = CameraConfiguration.objects.all()
#     # Render the list template with the retrieved configurations
#     return render(request, 'face_attendance/camera_config_list.html', {'configs': configs})


# # UPDATE: Function to edit an existing camera configuration
# @login_required
# def camera_config_update(request, pk):
#     # Retrieve the specific configuration by primary key or return a 404 error if not found
#     config = get_object_or_404(CameraConfiguration, pk=pk)

#     # Check if the request method is POST, indicating form submission
#     if request.method == "POST":
#         # Update the configuration fields with data from the form
#         config.name = request.POST.get('name')
#         config.camera_source = request.POST.get('camera_source')
#         config.threshold = request.POST.get('threshold')
#         config.success_sound_path = request.POST.get('success_sound_path')

#         # Save the changes to the database
#         config.save()  

#         # Redirect to the list page after successful update
#         return redirect('camera_config_list')  
    
#     # Render the configuration form with the current configuration data for GET requests
#     return render(request, 'face_attendance/camera_config_form.html', {'config': config})


# # DELETE: Function to delete a camera configuration
# @login_required
# def camera_config_delete(request, pk):
#     # Retrieve the specific configuration by primary key or return a 404 error if not found
#     config = get_object_or_404(CameraConfiguration, pk=pk)

#     # Check if the request method is POST, indicating confirmation of deletion
#     if request.method == "POST":
#         # Delete the record from the database
#         config.delete()  
#         # Redirect to the list of camera configurations after deletion
#         return redirect('camera_config_list')

#     # Render the delete confirmation template with the configuration data
#     return render(request, 'face_attendance/camera_config_delete.html', {'config': config})
