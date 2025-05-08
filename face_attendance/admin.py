from django.contrib import admin
from .models import (
    Department, Employee, FaceEncoding, Shift, AttendanceRecord,
    PayRate, EmployeePayInfo, PayPeriod, Payroll
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'position', 'is_active')
    list_filter = ('department', 'is_active', 'date_hired')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')

@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date_created', 'is_primary')
    list_filter = ('is_primary', 'date_created')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'department')
    list_filter = ('department',)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in_time', 'check_out_time', 'hours_worked')
    list_filter = ('status', 'date', 'verification_method')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    date_hierarchy = 'date'

@admin.register(PayRate)
class PayRateAdmin(admin.ModelAdmin):
    list_display = ('position', 'hourly_rate', 'overtime_rate')

@admin.register(EmployeePayInfo)
class EmployeePayInfoAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_rate')

@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'payment_date')

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period', 'regular_hours', 'overtime_hours', 'gross_pay', 'net_pay', 'status')
    list_filter = ('status', 'pay_period')
    search_fields = ('employee__first_name', 'employee__last_name')