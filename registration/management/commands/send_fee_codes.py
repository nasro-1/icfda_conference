# registration/management/commands/send_fee_codes.py

from django.core.management.base import BaseCommand
from registration.models import Registration
from registration.utils import send_confirmation_email

class Command(BaseCommand):
    help = 'Send fee codes to pending registrations'
    
    def handle(self, *args, **options):
        pending_registrations = Registration.objects.filter(
            fee_code__isnull=True,
            payment_status='pending'
        )
        
        for registration in pending_registrations:
            # Generate fee code
            registration.fee_code = registration.generate_fee_code()
            registration.save()
            
            # Send email
            send_confirmation_email(registration)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Fee code sent to {registration.email}'
                )
            )