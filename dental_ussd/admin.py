# Admin View for Dental USSD
# Admin View for Dental USSD
from django.contrib import admin
from .models import Patient, Appointment, ClinicAvailability

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'created_at', 'updated_at')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'appointment_type', 'clinic_location', 'appointment_date', 'status')


@admin.register(ClinicAvailability)
class ClinicAvailibilityAdmin(admin.ModelAdmin):
    list_display = ('clinic_location', 'appointment_type', 'available_slots', 'appointment_date', 'updated_at')