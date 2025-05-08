from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import json

class Department(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.CharField(max_length=100)
    date_hired = models.DateField()
    is_active = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='employee_profiles/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

class FaceEncoding(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='face_encodings')
    encoding_data = models.TextField()  # Will store JSON string of face encoding array
    date_created = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=True)
    
    def set_encoding(self, encoding_array):
        self.encoding_data = json.dumps(encoding_array.tolist())
    
    def get_encoding(self):
        return json.loads(self.encoding_data)
    
    def __str__(self):
        return f"Face encoding for {self.employee.first_name} {self.employee.last_name}"

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name}: {self.start_time} - {self.end_time}"

class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
    )
    
    VERIFICATION_CHOICES = (
        ('face', 'Face Recognition'),
        ('manual', 'Manual Entry'),
        ('override', 'Admin Override'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_CHOICES)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.date} - {self.status}"
    
    def calculate_hours(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            self.hours_worked = round(duration.total_seconds() / 3600, 2)
            self.save()

    @property
    def calculate_duration(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            total_minutes = duration.total_seconds() / 60
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            return f"{hours}h {minutes}m"
        return None  # or return "Incomplete"

class PayRate(models.Model):
    position = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.position}: ${self.hourly_rate}/hr"

class EmployeePayInfo(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='pay_info')
    pay_rate = models.ForeignKey(PayRate, on_delete=models.SET_NULL, null=True)
    bank_account = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Pay info for {self.employee.first_name} {self.employee.last_name}"

class PayPeriod(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    
    def __str__(self):
        return f"Pay period {self.start_date} to {self.end_date}"

class Payroll(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE)
    regular_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Payroll for {self.employee.first_name} {self.employee.last_name} - {self.pay_period}"
    
    def calculate_pay(self):
        """Calculate pay based on attendance records within the pay period"""
        attendance_records = AttendanceRecord.objects.filter(
            employee=self.employee,
            date__range=(self.pay_period.start_date, self.pay_period.end_date)
        )
        
        total_hours = 0
        for record in attendance_records:
            if record.check_in_time and record.check_out_time:
                # Calculate hours worked
                duration = record.check_out_time - record.check_in_time
                hours = duration.total_seconds() / 3600
                total_hours += hours
        
        # Get employee's hourly rate
        hourly_rate = self.employee.pay_info.pay_rate.hourly_rate
        
        # Calculate standard hours (assuming 8 hours per day)
        standard_hours = 8 * 5  # 40 hours per week
        
        if total_hours <= standard_hours:
            self.regular_hours = total_hours
            self.overtime_hours = 0
        else:
            self.regular_hours = standard_hours
            self.overtime_hours = total_hours - standard_hours
        
        # Calculate pay
        overtime_rate = self.employee.pay_info.pay_rate.overtime_rate
        self.gross_pay = (self.regular_hours * hourly_rate) + (self.overtime_hours * overtime_rate)
        
        # Deductions would typically be calculated here
        self.deductions = self.gross_pay * 0.2  # Placeholder for tax/deductions
        
        self.net_pay = self.gross_pay - self.deductions
        self.save()

class CameraConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Give a name to this camera configuration")
    camera_source = models.CharField(max_length=255, help_text="Camera index (0 for default webcam or RTSP/HTTP URL for IP camera)")
    threshold = models.FloatField(default=0.6, help_text="Face recognition confidence threshold")

    def __str__(self):
        return self.name