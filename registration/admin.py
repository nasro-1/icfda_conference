"""
registration/admin.py
Updated admin interface for ICFDA 2025 with individual menu field support
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import Registration, Paper, AccompanyingPerson, PaymentTransaction


class PaperInline(admin.TabularInline):
    model = Paper
    extra = 0
    fields = ('paper_number', 'title', 'is_additional')
    readonly_fields = ('added_at',)


class AccompanyingPersonInline(admin.StackedInline):
    model = AccompanyingPerson
    extra = 0
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'national_id')
        }),
        ('Dinner Events with Menu Selection', {
            'fields': (
                ('welcome_dinner', 'welcome_dinner_menu'),
                ('dinner', 'dinner_menu'),
                ('gala_dinner', 'gala_dinner_menu'),
            ),
            'description': 'Select dinners and corresponding menu types'
        }),
        ('Lunch Events', {
            'fields': ('welcome_lunch', 'lunch_16', 'lunch_17'),
            'description': 'Lunch events do not require menu selection'
        }),
        ('Legacy Field', {
            'fields': ('menu_type',),
            'classes': ('collapse',),
            'description': 'Legacy menu field - use individual dinner menu fields instead'
        }),
    )


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ('transaction_id', 'amount', 'currency', 'status', 
                      'payment_method', 'created_at', 'updated_at')
    can_delete = False


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('fee_code', 'full_name', 'email', 'registration_type', 
                   'location', 'payment_status_badge', 'total_amount_display', 
                   'has_tutorials', 'has_dinners', 'created_at')
    list_filter = ('registration_type', 'location', 'payment_status', 
                  'registration_period', 'country', 'room_type', 
                  'tutorial_full_day', 'tutorial_period', 'social_program',
                  'welcome_dinner', 'dinner', 'gala_dinner')
    search_fields = ('fee_code', 'first_name', 'last_name', 'email', 
                    'phone', 'institution', 'national_id')
    readonly_fields = ('registration_id', 'fee_code', 'created_at', 
                      'updated_at', 'ip_address', 'user_agent')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Registration Information', {
            'fields': ('registration_id', 'fee_code', 'registration_type', 
                      'registration_period', 'location')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 
                      'national_id', 'institution', 'country')
        }),
        ('Conference Options', {
            'fields': ('paper_count', 'tutorial_full_day', 'tutorial_period', 
                      'social_program')
        }),
        ('Catering Events with Individual Menu Selection', {
            'fields': (
                ('welcome_dinner', 'welcome_dinner_menu'),
                ('dinner', 'dinner_menu'),
                ('gala_dinner', 'gala_dinner_menu'),
                'lunch',
            ),
            'description': 'Individual dinner selections with specific menu types'
        }),
        ('Legacy Menu Field', {
            'fields': ('menu_type',),
            'classes': ('collapse',),
            'description': 'Legacy field - use individual dinner menu fields instead'
        }),
        ('Accommodation', {
            'fields': ('room_type', 'number_of_nights', 'accommodation_timing')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'total_amount', 
                      'currency', 'payment_reference', 'stripe_payment_intent')
        }),
        ('Additional Information', {
            'fields': ('special_requirements',)
        }),
        ('System Information', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PaperInline, AccompanyingPersonInline, PaymentTransactionInline]
    
    actions = ['mark_as_paid', 'mark_as_pending', 'export_to_csv', 
               'send_confirmation_emails', 'send_payment_reminders',
               'export_menu_summary', 'export_accommodation_summary']
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Name'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'processing': '#17A2B8',
            'completed': '#28A745',
            'failed': '#DC3545',
            'refunded': '#6C757D',
            'cancelled': '#6C757D',
        }
        color = colors.get(obj.payment_status, '#6C757D')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px; font-weight:bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def total_amount_display(self, obj):
        if obj.currency == 'EUR':
            return f"€{obj.total_amount:,.2f}"
        elif obj.currency == 'USD':
            return f"${obj.total_amount:,.2f}"
        else:
            return f"{obj.total_amount:,.0f} DA"
    total_amount_display.short_description = 'Total Amount'
    
    def has_tutorials(self, obj):
        tutorials = []
        if obj.tutorial_full_day:
            tutorials.append('Full Day')
        if obj.tutorial_period:
            tutorials.append('Per Period')
        return ', '.join(tutorials) if tutorials else '—'
    has_tutorials.short_description = 'Tutorials'
    
    def has_dinners(self, obj):
        dinners = []
        if obj.welcome_dinner:
            menu = f" ({obj.get_welcome_dinner_menu_display()})" if obj.welcome_dinner_menu else ""
            dinners.append(f'Welcome{menu}')
        if obj.dinner:
            menu = f" ({obj.get_dinner_menu_display()})" if obj.dinner_menu else ""
            dinners.append(f'Dinner{menu}')
        if obj.gala_dinner:
            menu = f" ({obj.get_gala_dinner_menu_display()})" if obj.gala_dinner_menu else ""
            dinners.append(f'Gala{menu}')
        return ', '.join(dinners) if dinners else '—'
    has_dinners.short_description = 'Dinners & Menus'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f'{updated} registrations marked as paid.')
    mark_as_paid.short_description = 'Mark selected as paid'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(payment_status='pending')
        self.message_user(request, f'{updated} registrations marked as pending.')
    mark_as_pending.short_description = 'Mark selected as pending'
    
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Fee Code', 'Name', 'Email', 'Phone', 'Institution', 
                        'Country', 'Type', 'Location', 'Payment Status', 
                        'Total Amount', 'Currency', 'Papers', 'Tutorials',
                        'Welcome Dinner', 'Welcome Menu', 'Dinner', 'Dinner Menu',
                        'Gala Dinner', 'Gala Menu', 'Room Type', 'Nights', 'Created'])
        
        for reg in queryset:
            writer.writerow([
                reg.fee_code,
                reg.get_full_name(),
                reg.email,
                reg.phone,
                reg.institution,
                reg.country,
                reg.get_registration_type_display(),
                reg.get_location_display(),
                reg.get_payment_status_display(),
                reg.total_amount,
                reg.currency,
                reg.paper_count,
                f"{'Full Day' if reg.tutorial_full_day else ''}{', Per Period' if reg.tutorial_period else ''}".strip(', '),
                'Yes' if reg.welcome_dinner else 'No',
                reg.get_welcome_dinner_menu_display() if reg.welcome_dinner_menu else '',
                'Yes' if reg.dinner else 'No',
                reg.get_dinner_menu_display() if reg.dinner_menu else '',
                'Yes' if reg.gala_dinner else 'No',
                reg.get_gala_dinner_menu_display() if reg.gala_dinner_menu else '',
                reg.get_room_type_display() if reg.room_type else '',
                reg.number_of_nights,
                reg.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_to_csv.short_description = 'Export selected to CSV'
    
    def export_menu_summary(self, request, queryset):
        """Export detailed menu summary for catering planning"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="menu_summary.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Event', 'Menu Type', 'Count', 'Participant Type', 'Names'])
        
        # Main participants
        events = [
            ('Welcome Dinner', 'welcome_dinner', 'welcome_dinner_menu'),
            ('Dinner', 'dinner', 'dinner_menu'),
            ('Gala Dinner', 'gala_dinner', 'gala_dinner_menu'),
        ]
        
        for event_name, event_field, menu_field in events:
            # Group by menu type
            from django.db.models import Q
            for menu_choice in Registration.MENU_CHOICES:
                menu_code, menu_display = menu_choice
                participants = queryset.filter(**{
                    event_field: True,
                    menu_field: menu_code,
                    'payment_status__in': ['completed', 'processing']
                })
                
                if participants.exists():
                    names = ', '.join([p.get_full_name() for p in participants])
                    writer.writerow([event_name, menu_display, participants.count(), 'Main Participant', names])
        
        # Accompanying persons
        for event_name, event_field, menu_field in events:
            for menu_choice in Registration.MENU_CHOICES:
                menu_code, menu_display = menu_choice
                accompanying = AccompanyingPerson.objects.filter(
                    **{event_field: True, menu_field: menu_code},
                    registration__payment_status__in=['completed', 'processing'],
                    registration__in=queryset
                )
                
                if accompanying.exists():
                    names = ', '.join([f"{a.name} (with {a.registration.get_full_name()})" for a in accompanying])
                    writer.writerow([event_name, menu_display, accompanying.count(), 'Accompanying Person', names])
        
        return response
    export_menu_summary.short_description = 'Export menu summary for catering'
    
    def export_accommodation_summary(self, request, queryset):
        """Export accommodation summary for hotel planning"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="accommodation_summary.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Phone', 'Room Type', 'Nights', 'Timing', 
                        'Accompanying Person', 'Payment Status', 'Fee Code'])
        
        accommodations = queryset.exclude(room_type__isnull=True).exclude(room_type='')
        
        for reg in accommodations:
            accompanying_name = reg.accompanying_person.name if hasattr(reg, 'accompanying_person') else 'None'
            writer.writerow([
                reg.get_full_name(),
                reg.email,
                reg.phone,
                reg.get_room_type_display(),
                reg.number_of_nights,
                reg.get_accommodation_timing_display() if reg.accommodation_timing else '',
                accompanying_name,
                reg.get_payment_status_display(),
                reg.fee_code
            ])
        
        return response
    export_accommodation_summary.short_description = 'Export accommodation summary'
    
    def send_confirmation_emails(self, request, queryset):
        from .utils import send_confirmation_email
        count = 0
        for registration in queryset:
            if send_confirmation_email(registration):
                count += 1
        self.message_user(request, f'Confirmation emails sent to {count} registrations.')
    send_confirmation_emails.short_description = 'Send confirmation emails'
    
    def send_payment_reminders(self, request, queryset):
        from .utils import send_confirmation_email
        pending = queryset.filter(payment_status='pending')
        count = 0
        for registration in pending:
            if send_confirmation_email(registration):
                count += 1
        self.message_user(request, f'Payment reminders sent to {count} registrations.')
    send_payment_reminders.short_description = 'Send payment reminders'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('accompanying_person').prefetch_related('papers', 'transactions')


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('paper_number', 'registration_link', 'is_additional', 'added_at')
    list_filter = ('is_additional', 'added_at')
    search_fields = ('paper_number', 'title', 'registration__email', 
                    'registration__first_name', 'registration__last_name')
    date_hierarchy = 'added_at'
    
    def registration_link(self, obj):
        url = reverse('admin:registration_registration_change', args=[obj.registration.id])
        return format_html('<a href="{}">{}</a>', url, obj.registration.get_full_name())
    registration_link.short_description = 'Registration'


@admin.register(AccompanyingPerson)
class AccompanyingPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_link', 'dinner_summary', 'lunch_summary')
    list_filter = ('welcome_dinner', 'dinner', 'gala_dinner', 
                  'welcome_dinner_menu', 'dinner_menu', 'gala_dinner_menu',
                  'welcome_lunch', 'lunch_16', 'lunch_17')
    search_fields = ('name', 'national_id', 'registration__email', 
                    'registration__first_name', 'registration__last_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'national_id')
        }),
        ('Dinner Events with Menu Selection', {
            'fields': (
                ('welcome_dinner', 'welcome_dinner_menu'),
                ('dinner', 'dinner_menu'),
                ('gala_dinner', 'gala_dinner_menu'),
            )
        }),
        ('Lunch Events', {
            'fields': ('welcome_lunch', 'lunch_16', 'lunch_17')
        }),
        ('Legacy Field', {
            'fields': ('menu_type',),
            'classes': ('collapse',),
        }),
    )
    
    def registration_link(self, obj):
        url = reverse('admin:registration_registration_change', args=[obj.registration.id])
        return format_html('<a href="{}">{}</a>', url, obj.registration.get_full_name())
    registration_link.short_description = 'Registration'
    
    def dinner_summary(self, obj):
        dinners = []
        if obj.welcome_dinner:
            menu = f" ({obj.get_welcome_dinner_menu_display()})" if obj.welcome_dinner_menu else ""
            dinners.append(f'Welcome{menu}')
        if obj.dinner:
            menu = f" ({obj.get_dinner_menu_display()})" if obj.dinner_menu else ""
            dinners.append(f'Dinner{menu}')
        if obj.gala_dinner:
            menu = f" ({obj.get_gala_dinner_menu_display()})" if obj.gala_dinner_menu else ""
            dinners.append(f'Gala{menu}')
        return ', '.join(dinners) if dinners else '—'
    dinner_summary.short_description = 'Dinners & Menus'
    
    def lunch_summary(self, obj):
        lunches = []
        if obj.welcome_lunch:
            lunches.append('Welcome')
        if obj.lunch_16:
            lunches.append('Dec 16')
        if obj.lunch_17:
            lunches.append('Dec 17')
        return ', '.join(lunches) if lunches else '—'
    lunch_summary.short_description = 'Lunches'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'registration_link', 'amount', 
                   'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('transaction_id', 'registration__email', 
                    'registration__fee_code')
    readonly_fields = ('transaction_id', 'registration', 'amount', 'currency',
                      'status', 'payment_method', 'gateway_response', 
                      'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def registration_link(self, obj):
        url = reverse('admin:registration_registration_change', args=[obj.registration.id])
        return format_html('<a href="{}">{}</a>', url, obj.registration.fee_code)
    registration_link.short_description = 'Registration'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Admin site customization
admin.site.site_header = "ICFDA 2025 Registration Admin"
admin.site.site_title = "ICFDA 2025 Admin"
admin.site.index_title = "Conference Registration Management"


# Additional admin configuration for better organization
class MenuSummaryFilter(admin.SimpleListFilter):
    title = 'Menu Selection'
    parameter_name = 'menu_selection'
    
    def lookups(self, request, model_admin):
        return (
            ('has_menus', 'Has Menu Selections'),
            ('no_menus', 'No Menu Selections'),
            ('incomplete_menus', 'Incomplete Menu Selections'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'has_menus':
            return queryset.filter(
                models.Q(welcome_dinner=True, welcome_dinner_menu__isnull=False) |
                models.Q(dinner=True, dinner_menu__isnull=False) |
                models.Q(gala_dinner=True, gala_dinner_menu__isnull=False)
            )
        elif self.value() == 'no_menus':
            return queryset.filter(
                welcome_dinner=False, dinner=False, gala_dinner=False
            )
        elif self.value() == 'incomplete_menus':
            return queryset.filter(
                models.Q(welcome_dinner=True, welcome_dinner_menu__isnull=True) |
                models.Q(dinner=True, dinner_menu__isnull=True) |
                models.Q(gala_dinner=True, gala_dinner_menu__isnull=True)
            )


# Add the custom filter to RegistrationAdmin
RegistrationAdmin.list_filter = RegistrationAdmin.list_filter + (MenuSummaryFilter,)