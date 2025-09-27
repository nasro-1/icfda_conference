"""
registration/forms.py
Updated forms for ICFDA 2025 to handle individual menu selections for each dinner
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Registration
from datetime import datetime
import re


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
            # Personal Information
            'first_name', 'last_name', 'email', 'phone', 'national_id',
            'institution', 'country', 'location', 'registration_type',
            
            # Papers
            'paper_count', 'paper_numbers',
            
            # Tutorial Options (now available for both locations)
            'tutorial_full_day', 'tutorial_period',
            
            # Individual Dinner Selections with Menus
            'welcome_dinner', 'welcome_dinner_menu',
            'dinner', 'dinner_menu',
            'gala_dinner', 'gala_dinner_menu',
            'lunch',
            
            # Social Program (abroad only)
            'social_program',
            
            # Accompanying Person
            'accompanying_person_name', 'accompanying_national_id',
            'accompanying_welcome', 'accompanying_welcome_menu',
            'accompanying_dinner', 'accompanying_dinner_menu',
            'accompanying_gala', 'accompanying_gala_menu',
            'accompanying_welcome_lunch', 'accompanying_lunch_16', 'accompanying_lunch_17',
            
            # Accommodation
            'room_type', 'number_of_nights', 'accommodation_timing',
            
            # Additional
            'special_requirements'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True,
                'placeholder': '+213 123 456 789'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'National ID or Passport Number'
            }),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'country': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'location': forms.HiddenInput(),
            'registration_type': forms.Select(attrs={'class': 'form-control', 'required': True}),
            
            'paper_count': forms.Select(attrs={'class': 'form-control'}),
            
            # Individual menu selections for main participant
            'welcome_dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            'dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            'gala_dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            
            # Individual menu selections for accompanying person
            'accompanying_welcome_menu': forms.Select(attrs={'class': 'form-control'}),
            'accompanying_dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            'accompanying_gala_menu': forms.Select(attrs={'class': 'form-control'}),
            
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'number_of_nights': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'accommodation_timing': forms.RadioSelect(),
            
            'accompanying_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'accompanying_national_id': forms.TextInput(attrs={'class': 'form-control'}),
            
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Dietary restrictions, accessibility needs, etc.'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set country choices
        self.fields['country'].widget = forms.Select(choices=[
            ('', '-- Select Country --'),
            ('Algeria', 'Algeria'),
            ('Morocco', 'Morocco'),
            ('Tunisia', 'Tunisia'),
            ('Libya', 'Libya'),
            ('Egypt', 'Egypt'),
            ('France', 'France'),
            ('Spain', 'Spain'),
            ('Italy', 'Italy'),
            ('Germany', 'Germany'),
            ('United Kingdom', 'United Kingdom'),
            ('United States', 'United States'),
            ('Canada', 'Canada'),
            ('Other', 'Other'),
        ])
        
        # Set paper count choices
        self.fields['paper_count'].widget = forms.Select(choices=[
            (0, '0 - No papers'),
            (1, '1 paper'),
            (2, '2 papers'),
            (3, '3 papers'),
            (4, '4 papers'),
            (5, '5 papers'),
        ])
        
        # Set menu choices for all menu fields
        menu_choices = [('', '-- Select Menu --')] + Registration.MENU_CHOICES
        menu_fields = [
            'welcome_dinner_menu', 'dinner_menu', 'gala_dinner_menu',
            'accompanying_welcome_menu', 'accompanying_dinner_menu', 'accompanying_gala_menu'
        ]
        
        for field_name in menu_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.Select(choices=menu_choices)
                self.fields[field_name].required = False  # Will be validated conditionally
        
        # Set registration period based on current date
        self.set_registration_period()
        
        # Make fields required
        self.fields['registration_type'].required = True
        self.fields['national_id'].required = True
        self.fields['phone'].required = True
    
    def set_registration_period(self):
        """Set the registration period based on current date"""
        if self.instance:
            self.instance.registration_period = Registration.get_current_period()
    
    def clean_email(self):
        """Validate email and check for duplicates"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("Email is required.")
        
        # Check for duplicate completed registrations
        existing = Registration.objects.filter(
            email=email.lower(),
            payment_status__in=['completed', 'processing']
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        if existing.exists():
            raise ValidationError(
                "An active registration already exists for this email address."
            )
        
        return email.lower()
    
    def clean_national_id(self):
        """Validate national ID/passport and check for duplicates"""
        national_id = self.cleaned_data.get('national_id', '').strip()
        
        if not national_id:
            raise ValidationError("National ID or Passport Number is required.")
        
        # Check for duplicate completed registrations
        existing = Registration.objects.filter(
            national_id=national_id,
            payment_status__in=['completed', 'processing']
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        if existing.exists():
            raise ValidationError(
                "A registration already exists for this National ID/Passport Number."
            )
        
        return national_id
    
    def clean_phone(self):
        """Clean and validate phone number"""
        phone = self.cleaned_data.get('phone', '')
        if not phone:
            raise ValidationError("Phone number is required.")
        return phone
    
    def clean_paper_numbers(self):
        """Validate paper numbers format if papers are selected"""
        paper_numbers = self.cleaned_data.get('paper_numbers', '')
        paper_count = self.cleaned_data.get('paper_count', 0)
        
        if paper_count > 0:
            if not paper_numbers:
                raise ValidationError("Please enter paper numbers for the selected count.")
            
            papers = [p.strip() for p in paper_numbers.strip().split('\n') if p.strip()]
            
            if len(papers) != paper_count:
                raise ValidationError(f"Please enter exactly {paper_count} paper number(s).")
            
            # Check for duplicates
            if len(papers) != len(set(papers)):
                raise ValidationError("Duplicate paper numbers detected.")
            
            # Validate format (basic check)
            for paper in papers:
                if not re.match(r'^[A-Z0-9][A-Z0-9\-\.]*[A-Z0-9]$', paper, re.IGNORECASE):
                    raise ValidationError(
                        f"Invalid paper number format: {paper}. "
                        "Paper numbers should contain only letters, numbers, hyphens, and dots."
                    )
        
        return paper_numbers
    
    def clean_welcome_dinner_menu(self):
        """Validate welcome dinner menu selection"""
        welcome_dinner = self.cleaned_data.get('welcome_dinner', False)
        welcome_dinner_menu = self.cleaned_data.get('welcome_dinner_menu', '')
        
        if welcome_dinner and not welcome_dinner_menu:
            raise ValidationError("Please select a menu type for the welcome dinner.")
        
        return welcome_dinner_menu
    
    def clean_dinner_menu(self):
        """Validate dinner menu selection"""
        dinner = self.cleaned_data.get('dinner', False)
        dinner_menu = self.cleaned_data.get('dinner_menu', '')
        
        if dinner and not dinner_menu:
            raise ValidationError("Please select a menu type for the dinner.")
        
        return dinner_menu
    
    def clean_gala_dinner_menu(self):
        """Validate gala dinner menu selection"""
        gala_dinner = self.cleaned_data.get('gala_dinner', False)
        gala_dinner_menu = self.cleaned_data.get('gala_dinner_menu', '')
        
        if gala_dinner and not gala_dinner_menu:
            raise ValidationError("Please select a menu type for the gala dinner.")
        
        return gala_dinner_menu
    
    def clean_accompanying_welcome_menu(self):
        """Validate accompanying person welcome dinner menu"""
        name = self.cleaned_data.get('accompanying_person_name', '')
        welcome = self.cleaned_data.get('accompanying_welcome', False)
        menu = self.cleaned_data.get('accompanying_welcome_menu', '')
        
        if name and welcome and not menu:
            raise ValidationError("Please select a menu type for accompanying person's welcome dinner.")
        
        return menu
    
    def clean_accompanying_dinner_menu(self):
        """Validate accompanying person dinner menu"""
        name = self.cleaned_data.get('accompanying_person_name', '')
        dinner = self.cleaned_data.get('accompanying_dinner', False)
        menu = self.cleaned_data.get('accompanying_dinner_menu', '')
        
        if name and dinner and not menu:
            raise ValidationError("Please select a menu type for accompanying person's dinner.")
        
        return menu
    
    def clean_accompanying_gala_menu(self):
        """Validate accompanying person gala dinner menu"""
        name = self.cleaned_data.get('accompanying_person_name', '')
        gala = self.cleaned_data.get('accompanying_gala', False)
        menu = self.cleaned_data.get('accompanying_gala_menu', '')
        
        if name and gala and not menu:
            raise ValidationError("Please select a menu type for accompanying person's gala dinner.")
        
        return menu
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        location = cleaned_data.get('location')
        registration_type = cleaned_data.get('registration_type')
        
        # Validate accommodation timing
        room_type = cleaned_data.get('room_type')
        nights = cleaned_data.get('number_of_nights', 0)
        
        if room_type and nights <= 0:
            raise ValidationError("Please specify the number of nights for accommodation.")
        
        if room_type and not cleaned_data.get('accommodation_timing'):
            raise ValidationError("Please select accommodation timing.")
        
        # Tutorial validation for visitor registration
        if registration_type == 'visitor':
            if cleaned_data.get('tutorial_full_day') or cleaned_data.get('tutorial_period'):
                raise ValidationError("Visitor registration does not include tutorial access.")
        
        # Set default payment method
        if location == 'abroad':
            cleaned_data['payment_method'] = 'stripe'
        else:
            cleaned_data['payment_method'] = 'transfer'
        
        return cleaned_data


class BulkRegistrationForm(forms.Form):
    """Form for bulk registration upload (CSV)"""
    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload CSV file with registration data"
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if not file.name.endswith('.csv'):
            raise ValidationError("File must be a CSV file.")
        return file


class RegistrationSearchForm(forms.Form):
    """Form for searching registrations"""
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, email, or fee code',
            'class': 'form-control'
        })
    )
    
    registration_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Registration.REGISTRATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_status = forms.ChoiceField(
        choices=[('', 'All Status')] + Registration.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    location = forms.ChoiceField(
        choices=[('', 'All Locations')] + Registration.LOCATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AccompanyingPersonForm(forms.ModelForm):
    """Form for accompanying person with individual menu selections"""
    
    class Meta:
        model = Registration  # This should be AccompanyingPerson but using Registration for simplicity
        fields = [
            'name', 'national_id',
            'welcome_dinner', 'welcome_dinner_menu',
            'dinner', 'dinner_menu', 
            'gala_dinner', 'gala_dinner_menu',
            'welcome_lunch', 'lunch_16', 'lunch_17'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'welcome_dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            'dinner_menu': forms.Select(attrs={'class': 'form-control'}),
            'gala_dinner_menu': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set menu choices
        menu_choices = [('', '-- Select Menu --')] + Registration.MENU_CHOICES
        menu_fields = ['welcome_dinner_menu', 'dinner_menu', 'gala_dinner_menu']
        
        for field_name in menu_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.Select(choices=menu_choices)
                self.fields[field_name].required = False


class TutorialRegistrationForm(forms.ModelForm):
    """Form for tutorial registration (now available for both locations)"""
    
    class Meta:
        model = Registration
        fields = ['tutorial_full_day', 'tutorial_period']
        
        widgets = {
            'tutorial_full_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tutorial_period': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Get registration type from instance if available
        if hasattr(self, 'instance') and self.instance:
            registration_type = self.instance.registration_type
            
            if registration_type == 'visitor':
                tutorial_full = cleaned_data.get('tutorial_full_day', False)
                tutorial_period = cleaned_data.get('tutorial_period', False)
                
                if tutorial_full or tutorial_period:
                    raise ValidationError("Visitor registration does not include tutorial access.")
        
        return cleaned_data