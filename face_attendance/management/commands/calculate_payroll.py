# management/commands/calculate_payroll.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from face_attendance.models import Employee, PayPeriod, Payroll
import datetime

class Command(BaseCommand):
    help = 'Calculate payroll for a specific pay period'

    def add_arguments(self, parser):
        parser.add_argument('pay_period_id', type=int, help='Pay Period ID')

    def handle(self, *args, **options):
        try:
            pay_period_id = options['pay_period_id']
            pay_period = PayPeriod.objects.get(id=pay_period_id)
            
            # Get all active employees
            employees = Employee.objects.filter(is_active=True)
            
            for employee in employees:
                # Check if payroll already exists
                payroll, created = Payroll.objects.get_or_create(
                    employee=employee,
                    pay_period=pay_period,
                    defaults={'status': 'pending'}
                )
                
                # Calculate pay
                payroll.calculate_pay()
                self.stdout.write(self.style.SUCCESS(f'Calculated payroll for {employee.first_name} {employee.last_name}'))
                
            self.stdout.write(self.style.SUCCESS(f'Successfully calculated payroll for pay period {pay_period}'))
        
        except PayPeriod.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Pay period with ID {pay_period_id} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))