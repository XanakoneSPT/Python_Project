from django.contrib.auth.models import User
from face_attendance.models import Employee, Department

# Create a user
user = User.objects.create_user(username='john', password='test1234')

# Create a department (if needed)
dept = Department.objects.create(name='IT', location='HQ')

# Create an employee
emp = Employee.objects.create(
    user=user,
    employee_id='EMP001',
    first_name='John',
    last_name='Doe',
    email='john@example.com',
    phone='123456789',
    department=dept,
    position='Developer',
    date_hired='2023-01-01'
)
