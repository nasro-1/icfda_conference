"""
registration/views.py
Updated views for ICFDA 2025 to handle individual menu selections
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
import json
import logging
import stripe

from .models import Registration, PaymentTransaction, Paper, AccompanyingPerson
from .utils import send_confirmation_email, send_payment_confirmation, send_hotel_reservation_email

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class RegistrationFormView(View):
    template_name = 'registration/form.html'
    
    def get(self, request):
        context = {
            'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
            'current_period': Registration.get_current_period(),
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request):
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            # Create registration instance
            registration = Registration(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', '').lower(),
                phone=data.get('phone', ''),
                national_id=data.get('national_id', ''),
                institution=data.get('institution', ''),
                country=data.get('country', ''),
                location=data.get('location', 'algeria'),
                registration_type=data.get('registration_type', ''),
                paper_count=int(data.get('paper_count', 0)),
                special_requirements=data.get('special_requirements', ''),
            )
            
            # Set registration period
            registration.registration_period = Registration.get_current_period()
            
            # Set IP and user agent for security
            registration.ip_address = self.get_client_ip(request)
            registration.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Process tutorial options (now available for both locations)
            registration.tutorial_full_day = self.parse_bool(data.get('tutorial_full_day', False))
            registration.tutorial_period = self.parse_bool(data.get('tutorial_period', False))
            
            # Process location-specific fields
            if registration.location == 'abroad':
                registration.social_program = self.parse_bool(data.get('social_program', False))
                registration.payment_method = data.get('payment_method', 'transfer')
            else:
                registration.payment_method = 'transfer'
                # No social program for Algeria
                registration.social_program = False
            
            # Process individual dinner selections with menus
            registration.welcome_dinner = self.parse_bool(data.get('welcome_dinner', False))
            registration.welcome_dinner_menu = data.get('welcome_dinner_menu', '') if registration.welcome_dinner else ''
            
            registration.dinner = self.parse_bool(data.get('dinner', False))
            registration.dinner_menu = data.get('dinner_menu', '') if registration.dinner else ''
            
            registration.gala_dinner = self.parse_bool(data.get('gala_dinner', False))
            registration.gala_dinner_menu = data.get('gala_dinner_menu', '') if registration.gala_dinner else ''
            
            registration.lunch = self.parse_bool(data.get('lunch', False))
            
            # Accommodation
            registration.room_type = data.get('room_type', '') if data.get('room_type') else None
            registration.number_of_nights = int(data.get('number_of_nights', 0))
            registration.accommodation_timing = data.get('accommodation_timing', '')
            
            # Validate required fields
            errors = {}
            if not registration.first_name:
                errors['first_name'] = 'First name is required'
            if not registration.last_name:
                errors['last_name'] = 'Last name is required'
            if not registration.email:
                errors['email'] = 'Email is required'
            if not registration.phone:
                errors['phone'] = 'Phone is required'
            if not registration.national_id:
                errors['national_id'] = 'National ID/Passport is required'
            if not registration.institution:
                errors['institution'] = 'Institution is required'
            if not registration.country:
                errors['country'] = 'Country is required'
            if not registration.registration_type:
                errors['registration_type'] = 'Registration type is required'
            
            # Validate menu selections for dinners
            if registration.welcome_dinner and not registration.welcome_dinner_menu:
                errors['welcome_dinner_menu'] = 'Please select a menu for welcome dinner'
            if registration.dinner and not registration.dinner_menu:
                errors['dinner_menu'] = 'Please select a menu for dinner'
            if registration.gala_dinner and not registration.gala_dinner_menu:
                errors['gala_dinner_menu'] = 'Please select a menu for gala dinner'
            
            # Check for duplicate email
            existing_email = Registration.objects.filter(
                email=registration.email,
                payment_status__in=['completed', 'processing']
            ).exists()
            if existing_email:
                errors['email'] = 'This email already has a completed registration'
            
            # Check for duplicate national ID
            existing_id = Registration.objects.filter(
                national_id=registration.national_id,
                payment_status__in=['completed', 'processing']
            ).exists()
            if existing_id:
                errors['national_id'] = 'This ID already has a completed registration'
            
            if errors:
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors}, status=400)
                else:
                    messages.error(request, 'Please correct the errors below.')
                    return render(request, self.template_name, {'errors': errors, 'data': data})
            
            # Calculate initial total
            registration.total_amount = registration.calculate_total()
            
            # Save registration
            registration.save()
            
            # Handle individual paper fields (paper_1, paper_2, etc.)
            paper_count = int(data.get('paper_count', 0))
            papers_added = []
            
            if paper_count > 0:
                # Determine included papers based on registration type
                included_papers = 0
                if registration.location == 'abroad':
                    if registration.registration_type == 'full':
                        included_papers = 2
                    elif registration.registration_type == 'student':
                        included_papers = 1
                    elif registration.registration_type == 'visitor':
                        included_papers = 0
                else:  # Algeria - all papers are free
                    included_papers = paper_count
                
                # Process each paper field
                for i in range(1, paper_count + 1):
                    paper_num = data.get(f'paper_{i}', '').strip()
                    if paper_num:
                        is_additional = (i - 1) >= included_papers
                        paper = Paper.objects.create(
                            registration=registration,
                            paper_number=paper_num,
                            is_additional=is_additional
                        )
                        papers_added.append(paper)
                        
                        # Add cost for additional papers
                        if is_additional and registration.location == 'abroad':
                            registration.total_amount += 100  # €100 per additional paper
            
            # Handle accompanying person if checkbox is checked
            if data.get('accompanying_person_name'):
                accompanying = AccompanyingPerson.objects.create(
                    registration=registration,
                    name=data.get('accompanying_person_name', ''),
                    national_id=data.get('accompanying_national_id', ''),
                    
                    # Individual dinner selections with menus
                    welcome_dinner=self.parse_bool(data.get('accompanying_welcome', False)),
                    welcome_dinner_menu=data.get('accompanying_welcome_menu', ''),
                    
                    dinner=self.parse_bool(data.get('accompanying_dinner', False)),
                    dinner_menu=data.get('accompanying_dinner_menu', ''),
                    
                    gala_dinner=self.parse_bool(data.get('accompanying_gala', False)),
                    gala_dinner_menu=data.get('accompanying_gala_menu', ''),
                    
                    # Lunch selections (no menu needed)
                    welcome_lunch=self.parse_bool(data.get('accompanying_welcome_lunch', False)),
                    lunch_16=self.parse_bool(data.get('accompanying_lunch_16', False)),
                    lunch_17=self.parse_bool(data.get('accompanying_lunch_17', False)),
                )
                
                # Validate accompanying person menu selections
                if accompanying.welcome_dinner and not accompanying.welcome_dinner_menu:
                    errors['accompanying_welcome_menu'] = 'Please select a menu for accompanying person welcome dinner'
                if accompanying.dinner and not accompanying.dinner_menu:
                    errors['accompanying_dinner_menu'] = 'Please select a menu for accompanying person dinner'
                if accompanying.gala_dinner and not accompanying.gala_dinner_menu:
                    errors['accompanying_gala_menu'] = 'Please select a menu for accompanying person gala dinner'
                
                if errors:
                    if is_ajax:
                        return JsonResponse({'success': False, 'errors': errors}, status=400)
                    else:
                        messages.error(request, 'Please correct the errors below.')
                        return render(request, self.template_name, {'errors': errors, 'data': data})
                
                # Add accompanying person cost
                registration.total_amount += accompanying.calculate_cost()
            
            # Save final total
            registration.save()
            
            # Send confirmation email
            try:
                send_confirmation_email(registration)
                
                # Send hotel reservation email for international participants
                if registration.needs_hotel_reservation_email():
                    send_hotel_reservation_email(registration)
                    
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")
            
            # Determine redirect URL based on payment method and amount
            if registration.total_amount > 0:
                if registration.payment_method == 'stripe':
                    redirect_url = reverse('registration:payment', kwargs={'registration_id': registration.registration_id})
                else:
                    redirect_url = reverse('registration:success', kwargs={'registration_id': registration.registration_id})
            else:
                # No payment needed
                redirect_url = reverse('registration:success', kwargs={'registration_id': registration.registration_id})
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': redirect_url,
                    'registration_id': str(registration.registration_id),
                    'fee_code': registration.fee_code
                })
            else:
                messages.success(request, 'Registration submitted successfully!')
                return redirect(redirect_url)
                    
        except Exception as e:
            logger.error(f"Registration error: {e}", exc_info=True)
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': f'An error occurred during registration: {str(e)}'
                }, status=500)
            else:
                messages.error(request, 'An error occurred. Please try again.')
                return render(request, self.template_name, {})
    
    def parse_bool(self, value):
        """Parse boolean value from various formats"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PaymentView(View):
    template_name = 'registration/payment.html'
    
    def get(self, request, registration_id):
        registration = get_object_or_404(Registration, registration_id=registration_id)
        
        # Check if already paid
        if registration.payment_status == 'completed':
            messages.info(request, 'This registration has already been paid.')
            return redirect('registration:success', registration_id=registration_id)
        
        # Check if payment is needed
        if registration.total_amount == 0:
            messages.info(request, 'No payment required for this registration.')
            return redirect('registration:success', registration_id=registration_id)
        
        # Create or retrieve Stripe payment intent for card payments
        if registration.payment_method == 'stripe':
            try:
                if registration.stripe_payment_intent:
                    # Retrieve existing intent
                    intent = stripe.PaymentIntent.retrieve(registration.stripe_payment_intent)
                else:
                    # Create new intent
                    intent = stripe.PaymentIntent.create(
                        amount=int(registration.total_amount * 100),  # Amount in cents
                        currency=registration.currency.lower(),
                        metadata={
                            'registration_id': str(registration.registration_id),
                            'email': registration.email,
                            'name': registration.get_full_name()
                        }
                    )
                    registration.stripe_payment_intent = intent.id
                    registration.save()
                
                context = {
                    'registration': registration,
                    'client_secret': intent.client_secret,
                    'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                    'papers': registration.papers.all(),
                    'accompanying_person': getattr(registration, 'accompanying_person', None)
                }
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {e}")
                messages.error(request, 'Payment system temporarily unavailable. Please try again later.')
                return redirect('registration:success', registration_id=registration_id)
        else:
            # Bank transfer payment
            context = {
                'registration': registration,
                'papers': registration.papers.all(),
                'accompanying_person': getattr(registration, 'accompanying_person', None),
                'bank_details': self.get_bank_details(registration.currency)
            }
        
        return render(request, self.template_name, context)
    
    def get_bank_details(self, currency):
        """Get bank transfer details based on currency"""
        from .utils import get_bank_details
        return get_bank_details(currency)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return HttpResponse(status=400)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self.handle_successful_payment(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self.handle_failed_payment(payment_intent)
        
        return HttpResponse(status=200)
    
    @transaction.atomic
    def handle_successful_payment(self, payment_intent):
        """Handle successful payment"""
        try:
            registration_id = payment_intent['metadata']['registration_id']
            registration = Registration.objects.get(registration_id=registration_id)
            
            # Update registration status
            registration.payment_status = 'completed'
            registration.payment_reference = payment_intent['id']
            registration.save()
            
            # Create transaction record
            PaymentTransaction.objects.create(
                registration=registration,
                transaction_id=payment_intent['id'],
                amount=payment_intent['amount'] / 100,
                currency=payment_intent['currency'].upper(),
                status='success',
                payment_method='stripe',
                gateway_response=payment_intent
            )
            
            # Send payment confirmation email
            send_payment_confirmation(registration)
            
            # Send hotel reservation email for international participants
            if registration.needs_hotel_reservation_email():
                send_hotel_reservation_email(registration)
            
            logger.info(f"Payment successful for registration {registration_id}")
            
        except Registration.DoesNotExist:
            logger.error(f"Registration not found: {registration_id}")
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")
    
    def handle_failed_payment(self, payment_intent):
        """Handle failed payment"""
        try:
            registration_id = payment_intent['metadata']['registration_id']
            registration = Registration.objects.get(registration_id=registration_id)
            
            # Update registration status
            registration.payment_status = 'failed'
            registration.save()
            
            # Create transaction record
            PaymentTransaction.objects.create(
                registration=registration,
                transaction_id=payment_intent['id'],
                amount=payment_intent['amount'] / 100,
                currency=payment_intent['currency'].upper(),
                status='failed',
                payment_method='stripe',
                gateway_response=payment_intent
            )
            
            logger.info(f"Payment failed for registration {registration_id}")
            
        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")


class RegistrationSuccessView(View):
    template_name = 'registration/success.html'
    
    def get(self, request, registration_id):
        registration = get_object_or_404(Registration, registration_id=registration_id)
        context = {
            'registration': registration,
            'papers': registration.papers.all(),
            'accompanying_person': getattr(registration, 'accompanying_person', None)
        }
        return render(request, self.template_name, context)


# API Views for AJAX calls
def check_email(request):
    """Check if email already has a completed registration"""
    email = request.GET.get('email', '').lower()
    exists = Registration.objects.filter(
        email=email,
        payment_status__in=['completed', 'processing']
    ).exists()
    return JsonResponse({'exists': exists})


def check_national_id(request):
    """Check if national ID already has a completed registration"""
    national_id = request.GET.get('national_id', '').strip()
    exists = Registration.objects.filter(
        national_id=national_id,
        payment_status__in=['completed', 'processing']
    ).exists()
    return JsonResponse({'exists': exists})


def calculate_price(request):
    """Calculate price based on selected options"""
    try:
        data = json.loads(request.body)
        
        # Create temporary registration object
        reg = Registration(
            location=data.get('location', 'algeria'),
            registration_type=data.get('registration_type', ''),
            tutorial_full_day=bool(data.get('tutorial_full_day', False)),
            tutorial_period=bool(data.get('tutorial_period', False)),
            social_program=bool(data.get('social_program', False)),
            gala_dinner=bool(data.get('gala_dinner', False)),
            dinner=bool(data.get('dinner', False)),
            welcome_dinner=bool(data.get('welcome_dinner', False)),
            room_type=data.get('room_type', ''),
            number_of_nights=int(data.get('number_of_nights', 0))
        )
        
        # Set registration period
        reg.registration_period = Registration.get_current_period()
        
        # Calculate base total
        total = reg.calculate_total()
        
        # Add accompanying person costs if applicable
        if data.get('accompanying_gala'):
            if reg.location == 'abroad':
                total += 80
            else:
                total += 5000  # Updated price for accompanying gala dinner
                
        if data.get('accompanying_dinner'):
            if reg.location == 'abroad':
                total += 40
            else:
                total += 5500
                
        if data.get('accompanying_welcome'):
            if reg.location == 'abroad':
                total += 40
            else:
                total += 5500
        
        # Add lunches for accompanying person
        if data.get('accompanying_welcome_lunch'):
            if reg.location == 'abroad':
                total += 40
            else:
                total += 5500
                
        if data.get('accompanying_lunch_16'):
            if reg.location == 'abroad':
                total += 40
            else:
                total += 5500
                
        if data.get('accompanying_lunch_17'):
            if reg.location == 'abroad':
                total += 40
            else:
                total += 5500
        
        # Add additional papers cost
        paper_count = int(data.get('paper_count', 0))
        if reg.location == 'abroad' and reg.registration_type != 'visitor':
            if reg.registration_type == 'full':
                included_papers = 2
            else:  # student
                included_papers = 1
            
            additional_papers = max(0, paper_count - included_papers)
            total += additional_papers * 100  # €100 per additional paper
        
        return JsonResponse({
            'total': float(total),
            'currency': reg.currency,
            'period': reg.registration_period,
            'period_display': dict(Registration.REGISTRATION_PERIODS)[reg.registration_period]
        })
        
    except Exception as e:
        logger.error(f"Price calculation error: {e}", exc_info=True)
        return JsonResponse({'error': 'Calculation error'}, status=400)


def get_registration_status(request, registration_id):
    """Get registration status for polling"""
    try:
        registration = Registration.objects.get(registration_id=registration_id)
        return JsonResponse({
            'status': registration.payment_status,
            'fee_code': registration.fee_code
        })
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Registration not found'}, status=404)


def get_current_period_info(request):
    """Get current registration period information"""
    period = Registration.get_current_period()
    period_display = dict(Registration.REGISTRATION_PERIODS)[period]
    
    # Get deadline dates
    from datetime import datetime
    deadlines = {
        'early': '2025-10-15',
        'normal': '2025-11-21',
        'late': None  # No deadline for late
    }
    
    return JsonResponse({
        'period': period,
        'period_display': period_display,
        'deadline': deadlines.get(period)
    })