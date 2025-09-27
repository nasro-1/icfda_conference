"""
registration/utils.py
Updated utility functions for ICFDA 2025 with hotel reservation emails
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def send_confirmation_email(registration, template='registration'):
    """Send initial registration confirmation email"""
    try:
        subject = f'ICFDA 2025 - Registration Received - {registration.fee_code}'
        
        context = {
            'registration': registration,
            'papers': registration.papers.all(),
            'accompanying': getattr(registration, 'accompanying_person', None),
            'is_initial': True,
            'bank_details': get_bank_details(registration.currency),
            'base_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        }
        
        html_content = render_to_string(f'registration/email_{template}.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[registration.email],
            reply_to=['icfda2025@conference.org']
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Registration confirmation sent to {registration.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send registration email to {registration.email}: {str(e)}")
        return False


def send_payment_confirmation(registration):
    """Send payment confirmation email"""
    try:
        subject = f'ICFDA 2025 - Payment Confirmed - {registration.fee_code}'
        
        context = {
            'registration': registration,
            'papers': registration.papers.all(),
            'accompanying': getattr(registration, 'accompanying_person', None),
            'is_payment': True,
            'base_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        }
        
        html_content = render_to_string('registration/email_payment.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[registration.email],
            reply_to=['icfda2025@conference.org']
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Payment confirmation sent to {registration.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send payment email to {registration.email}: {str(e)}")
        return False


def send_hotel_reservation_email(registration):
    """Send hotel reservation request email for international participants"""
    if registration.location != 'abroad':
        return False
        
    try:
        subject = f'ICFDA 2025 – Reservation Request - {registration.get_full_name()}'
        
        # Calculate total nights needed (assuming conference dates Dec 15-18, 2025)
        conference_nights = 4  # Default conference duration
        total_nights = max(registration.number_of_nights, conference_nights)
        
        accompanying_count = 1 if hasattr(registration, 'accompanying_person') else 0
        
        context = {
            'registration': registration,
            'papers': registration.papers.all(),
            'accompanying': getattr(registration, 'accompanying_person', None),
            'total_nights': total_nights,
            'accompanying_count': accompanying_count,
            'conference_dates': 'December 15-18, 2025',
        }
        
        html_content = render_to_string('registration/email_hotel_reservation.html', context)
        text_content = strip_tags(html_content)
        
        # Hotel staff email addresses as specified
        hotel_recipients = [
            'lynda.kaci@accor.com',
            'H3173-re@accor.com',
            'Amir.BENSAADA@accor.com'
        ]
        
        # CC recipients
        cc_recipients = [
            'Nabil.OULDYAHIA@accor.com',
            'samir.ladaci@g.enp.edu.dz',
            'nasro.mellah@gmail.com'
        ]
        
        # Note: 'Nizar' email address needs to be provided by the organizers
        # You can add it to cc_recipients once available
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=hotel_recipients,
            cc=cc_recipients,
            reply_to=['icfda2025@conference.org']
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Hotel reservation email sent for {registration.get_full_name()}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send hotel reservation email for {registration.email}: {str(e)}")
        return False


def get_bank_details(currency='EUR'):
    """Get bank transfer details based on currency"""
    base_details = {
        'bank': 'Crédit Populaire d\'Algérie (CPA)',
        'branch': 'Agence 146 Bab Ezzouar',
        'account_holder': 'EGT CENTRE GRAND HOTEL MERCURE',
        'swift': 'CPALDZAL',
        'iban_prefix': 'DZ 004'
    }
    
    if currency == 'EUR':
        base_details.update({
            'rib': '00400146520817019018',
            'account_type': 'EUR Account',
            'full_iban': 'DZ 00400146520817019018'
        })
    elif currency == 'USD':
        base_details.update({
            'rib': '00400146520817013974',
            'account_type': 'USD Account',
            'full_iban': 'DZ 00400146520817013974'
        })
    else:  # DZD
        base_details.update({
            'rib': '00400146401708170149',
            'account_type': 'DZD Account',
            'full_iban': 'DZ 00400146401708170149'
        })
    
    return base_details


def validate_paper_number(paper_number):
    """Validate paper number format from PaperCept"""
    import re
    # Adjust pattern based on actual PaperCept format
    pattern = r'^[A-Z0-9][A-Z0-9\-\.]*[A-Z0-9]$'
    return bool(re.match(pattern, paper_number, re.IGNORECASE))


def format_currency(amount, currency='EUR'):
    """Format amount with currency symbol"""
    symbols = {
        'EUR': '€',
        'DZD': 'DA',
        'USD': '$',
    }
    symbol = symbols.get(currency, currency + ' ')
    
    if currency == 'DZD':
        return f"{int(amount):,} {symbol}".replace(',', ' ')
    else:
        return f"{symbol}{amount:,.2f}"


def get_registration_statistics():
    """Get registration statistics for admin dashboard"""
    from django.db.models import Count, Sum, Q
    from .models import Registration
    
    stats = {
        'total_registrations': Registration.objects.count(),
        'completed_registrations': Registration.objects.filter(
            payment_status='completed'
        ).count(),
        'pending_registrations': Registration.objects.filter(
            payment_status='pending'
        ).count(),
        'total_revenue_eur': Registration.objects.filter(
            payment_status='completed',
            currency='EUR'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0'),
        'total_revenue_dzd': Registration.objects.filter(
            payment_status='completed',
            currency='DZD'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0'),
        'by_type': Registration.objects.values('registration_type').annotate(
            count=Count('id')
        ),
        'by_location': Registration.objects.values('location').annotate(
            count=Count('id')
        ),
        'by_period': Registration.objects.values('registration_period').annotate(
            count=Count('id')
        ),
        'with_accommodation': Registration.objects.exclude(
            Q(room_type__isnull=True) | Q(room_type='')
        ).count(),
        'with_tutorials': Registration.objects.filter(
            Q(tutorial_full_day=True) | Q(tutorial_period=True)
        ).count(),
        'international_participants': Registration.objects.filter(
            location='abroad',
            payment_status='completed'
        ).count(),
        'algerian_participants': Registration.objects.filter(
            location='algeria',
            payment_status='completed'
        ).count(),
        'visitor_registrations': Registration.objects.filter(
            registration_type='visitor'
        ).count(),
    }
    
    return stats


def export_registrations_csv():
    """Export registrations to CSV format"""
    import csv
    import io
    from .models import Registration
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = [
        'Registration ID', 'Fee Code', 'First Name', 'Last Name', 'Email',
        'Phone', 'Institution', 'Country', 'National ID', 'Registration Type',
        'Location', 'Payment Status', 'Total Amount', 'Currency',
        'Tutorial Full Day', 'Tutorial Period', 'Gala Dinner', 'Dinner', 'Lunch',
        'Social Program', 'Room Type', 'Nights', 'Created At'
    ]
    writer.writerow(header)
    
    # Write data
    for reg in Registration.objects.all().order_by('-created_at'):
        row = [
            str(reg.registration_id), reg.fee_code, reg.first_name, reg.last_name,
            reg.email, reg.phone, reg.institution, reg.country, reg.national_id or '',
            reg.get_registration_type_display(), reg.get_location_display(),
            reg.get_payment_status_display(), reg.total_amount, reg.currency,
            'Yes' if reg.tutorial_full_day else 'No',
            'Yes' if reg.tutorial_period else 'No',
            'Yes' if reg.gala_dinner else 'No',
            'Yes' if reg.dinner else 'No',
            'Yes' if reg.lunch else 'No',
            'Yes' if reg.social_program else 'No',
            reg.get_room_type_display() if reg.room_type else '',
            reg.number_of_nights,
            reg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        writer.writerow(row)
    
    output.seek(0)
    return output.getvalue()


def send_bulk_email(subject, message, recipient_list, html_message=None):
    """Send bulk email to multiple recipients"""
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[],
            bcc=recipient_list,
            reply_to=['icfda2025@conference.org']
        )
        
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        email.send()
        
        logger.info(f"Bulk email sent to {len(recipient_list)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send bulk email: {str(e)}")
        return False


def generate_invoice_pdf(registration):
    """Generate invoice PDF for registration"""
    # This would require a PDF library like ReportLab
    # Implementation depends on your specific invoice design requirements
    pass


def validate_registration_data(data):
    """Validate registration data for bulk import"""
    errors = []
    
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'institution', 'country']
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate email format
    if data.get('email') and '@' not in data['email']:
        errors.append("Invalid email format")
    
    # Validate registration type
    valid_types = ['full', 'student', 'visitor']
    if data.get('registration_type') and data['registration_type'] not in valid_types:
        errors.append(f"Invalid registration type: {data['registration_type']}")
    
    return errors