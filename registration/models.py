"""
registration/models.py
Updated models for ICFDA 2025 with new pricing structure and registration types
"""

from django.db import models
from django.core.validators import EmailValidator, MinValueValidator
from django.utils import timezone
import uuid
import secrets
import string
from datetime import datetime, timedelta

class Registration(models.Model):
    REGISTRATION_TYPES = [
        ('full', 'Full Registration'),
        ('student', 'Student Registration'),
        ('without_paper', 'Registration without paper'),
    ]
    
    LOCATION_CHOICES = [
        ('abroad', 'Registration from Abroad'),
        ('algeria', 'Registration from Algeria'),
    ]
    
    MENU_CHOICES = [
        ('meat', 'Meat Menu'),
        ('fish', 'Fish Menu'),
        ('vegetarian', 'Vegetarian Menu'),
    ]
    
    ROOM_TYPES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
    ]
    
    PAYMENT_METHODS = [
        ('card', 'Credit/Debit Card'),
        ('transfer', 'Bank Transfer'),
        ('stripe', 'Stripe Payment'),
    ]
    
    REGISTRATION_PERIODS = [
        ('early', 'Early Registration'),
        ('normal', 'Normal Registration'),
        ('late', 'Late Registration'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Unique identifiers
    registration_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    fee_code = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()], db_index=True)
    phone = models.CharField(max_length=20)
    institution = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    national_id = models.CharField(max_length=50, blank=True, null=True, help_text="National ID or Passport Number")
    
    # Registration Details
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES)
    registration_type = models.CharField(max_length=15, choices=REGISTRATION_TYPES)
    registration_period = models.CharField(max_length=10, choices=REGISTRATION_PERIODS)
    registration_date = models.DateTimeField(default=timezone.now)
    
    # Tutorial Options (available for both locations)
    tutorial_full_day = models.BooleanField(default=False)
    tutorial_period = models.BooleanField(default=False)
    
    # Catering & Events with individual menu selections
    welcome_dinner = models.BooleanField(default=False)
    welcome_dinner_menu = models.CharField(max_length=20, choices=MENU_CHOICES, blank=True, null=True)
    
    dinner = models.BooleanField(default=False)
    dinner_menu = models.CharField(max_length=20, choices=MENU_CHOICES, blank=True, null=True)
    
    lunch = models.BooleanField(default=False)
    
    gala_dinner = models.BooleanField(default=False)
    gala_dinner_menu = models.CharField(max_length=20, choices=MENU_CHOICES, blank=True, null=True)
    
    # Social Program
    social_program = models.BooleanField(default=False)
    
    # Accommodation with date selection
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, blank=True, null=True)
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    number_of_nights = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_intent = models.CharField(max_length=200, blank=True, null=True)
    
    # Paper count (for tracking)
    paper_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Additional Information
    special_requirements = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'payment_status']),
            models.Index(fields=['registration_period', 'registration_type']),
            models.Index(fields=['national_id']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.registration_id}"
    
    def save(self, *args, **kwargs):
        # Generate fee code if not exists
        if not self.fee_code:
            self.fee_code = self.generate_fee_code()
        
        # Set registration period if not set
        if not self.registration_period:
            self.registration_period = self.get_current_period()
        
        # Calculate nights from dates
        if self.check_in_date and self.check_out_date:
            delta = self.check_out_date - self.check_in_date
            self.number_of_nights = max(0, delta.days)
        
        # Calculate total if not set
        if self.total_amount == 0:
            self.total_amount = self.calculate_total()
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def get_current_period():
        """Determine current registration period based on date"""
        today = datetime.now().date()
        early_deadline = datetime(2025, 10, 15).date()
        normal_deadline = datetime(2025, 11, 21).date()
        
        if today <= early_deadline:
            return 'early'
        elif today <= normal_deadline:
            return 'normal'
        return 'late'
    
    def generate_fee_code(self):
        """Generate unique fee code"""
        while True:
            code = 'ICFDA2025-' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Registration.objects.filter(fee_code=code).exists():
                return code
    
    def calculate_total(self):
        """Calculate total registration cost based on selected options"""
        total = 0
        period = self.registration_period or self.get_current_period()
        
        if self.location == 'abroad':
            # Base registration fees for international participants
            if self.registration_type == 'full':
                base_fees = {'early': 250, 'normal': 300, 'late': 350}
                total = base_fees.get(period, 350)
            elif self.registration_type == 'student':
                base_fees = {'early': 150, 'normal': 200, 'late': 250}
                total = base_fees.get(period, 250)
            elif self.registration_type == 'without_paper':
                total = 250  # Fixed price for registration without paper
            
            # Tutorial fees for abroad participants
            if self.tutorial_full_day:
                if self.registration_type == 'student':
                    total += 80 if period == 'late' else 50
                else:
                    total += 100 if period == 'late' else 80
            
            if self.tutorial_period:
                if self.registration_type == 'student':
                    total += 60 if period == 'late' else 40
                else:
                    total += 70 if period == 'late' else 50
            
            # Catering for abroad participants
            if self.gala_dinner:
                total += 45  # Updated price: €45 instead of €80
            if self.dinner:
                total += 40
            if self.welcome_dinner:
                total += 40
            
            # Social program
            if self.social_program:
                total += 20
            
            # Accommodation
            if self.room_type == 'single':
                total += self.number_of_nights * 70
            elif self.room_type == 'double':
                total += self.number_of_nights * 84
            
            self.currency = 'EUR'
            
        else:  # Algeria
            # Base registration fees for Algerian participants
            if self.registration_type == 'full':
                base_fees = {'early': 20000, 'normal': 25000, 'late': 30000}
                total = base_fees.get(period, 30000)
            elif self.registration_type == 'student':
                base_fees = {'early': 15000, 'normal': 20000, 'late': 25000}
                total = base_fees.get(period, 25000)
            elif self.registration_type == 'without_paper':
                total = 20000  # Fixed price for registration without paper
            
            # Tutorial fees for Algerian participants - NEW PRICES
            if self.tutorial_full_day:
                total += 12000  # Fixed price: 12,000 DA
            
            if self.tutorial_period:
                total += 7000  # Fixed price: 7,000 DA
            
            # Catering for Algerian participants
            if self.gala_dinner:
                total += 6000
            if self.dinner:
                total += 5500
            if self.welcome_dinner:
                total += 5500
            
            # Social Program for Algeria - NEW
            if self.social_program:
                total += 500  # 500 DA for social program
            
            # Accommodation
            if self.room_type == 'single':
                total += self.number_of_nights * 10500
            elif self.room_type == 'double':
                total += self.number_of_nights * 12500
            
            self.currency = 'DZD'
        
        return total
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_be_edited(self):
        """Check if registration can still be edited"""
        return self.payment_status in ['pending', 'failed']
    
    def needs_hotel_reservation_email(self):
        """Check if hotel reservation email should be sent"""
        return (self.location == 'abroad' and 
                self.payment_status == 'completed')


class Paper(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='papers')
    paper_number = models.CharField(max_length=50)
    title = models.CharField(max_length=200, blank=True, null=True)
    is_additional = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['registration', 'paper_number']
        ordering = ['added_at']
    
    def __str__(self):
        return f"Paper {self.paper_number} - {self.registration.get_full_name()}"
    
    def calculate_additional_cost(self):
        """Calculate cost for additional papers"""
        if self.is_additional and self.registration.location == 'abroad':
            return 100  # €100 per additional paper
        return 0


class AccompanyingPerson(models.Model):
    registration = models.OneToOneField(
        Registration, 
        on_delete=models.CASCADE, 
        related_name='accompanying_person'
    )
    name = models.CharField(max_length=200)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Dinners with individual menu selections
    welcome_dinner = models.BooleanField(default=False)
    welcome_dinner_menu = models.CharField(max_length=20, choices=Registration.MENU_CHOICES, blank=True, null=True)
    
    dinner = models.BooleanField(default=False)
    dinner_menu = models.CharField(max_length=20, choices=Registration.MENU_CHOICES, blank=True, null=True)
    
    gala_dinner = models.BooleanField(default=False)
    gala_dinner_menu = models.CharField(max_length=20, choices=Registration.MENU_CHOICES, blank=True, null=True)
    
    # Updated Lunches - removed welcome_lunch, added lunch_18
    lunch_16 = models.BooleanField(default=False, help_text="Lunch - December 16th")
    lunch_17 = models.BooleanField(default=False, help_text="Lunch - December 17th")
    lunch_18 = models.BooleanField(default=False, help_text="Lunch - December 18th")
    
    def __str__(self):
        return f"Accompanying: {self.name} for {self.registration.get_full_name()}"
    
    def calculate_cost(self):
        """Calculate cost for accompanying person"""
        cost = 0
        if self.registration.location == 'abroad':
            # Updated gala dinner price for accompanying person
            if self.gala_dinner:
                cost += 45  # Updated to match main participant price
            if self.dinner:
                cost += 40
            if self.welcome_dinner:
                cost += 40
            # Lunch prices for abroad
            if self.lunch_16:
                cost += 40
            if self.lunch_17:
                cost += 40
            if self.lunch_18:
                cost += 40
        else:  # Algeria
            if self.gala_dinner:
                cost += 5000  # Accompanying person gala dinner
            if self.dinner:
                cost += 5500
            if self.welcome_dinner:
                cost += 5500
            # Lunch prices for Algeria
            if self.lunch_16:
                cost += 5500
            if self.lunch_17:
                cost += 5500
            if self.lunch_18:
                cost += 5500
        return cost


class PaymentTransaction(models.Model):
    registration = models.ForeignKey(
        Registration, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ]
    )
    payment_method = models.CharField(max_length=50)
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"