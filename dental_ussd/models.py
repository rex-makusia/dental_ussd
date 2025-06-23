# This will contain out models for the dental app 
# Models are the backbone of any Django application.
# They define the structure of your database and how data is stored.
# In this case, we will create a simple model for a dental appointment.

# This will contain out models for the dental app 
# Models are the backbone of any Django application.
# They define the structure of your database and how data is stored.
# In this case, we will create a simple model for a dental appointment.
from django.db import models
from django.core.validators import MinValueValidator

class Patient(models.Model):
    mobile_number = models.CharField(max_length=11, null=False, unique=True)
    name = models.CharField(max_length=100, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.mobile_number})"


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=False)
    appointment_type = models.CharField(max_length=50, null=False)
    clinic_location = models.CharField(max_length=100, null=False)
    appointment_date = models.DateTimeField(null=False)
    status = models.CharField(
        max_length=20,
        default='scheduled',
        choices=[
            ('scheduled', 'Scheduled'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return a string representation of the appointment."""
        return f"""
           Type: {self.appointment_type}
           Location: {self.clinic_location}
           Date: {self.appointment_date.strftime('%Y-%m-%d %I:%M%p')}
           Status: {self.status}"""


class ClinicAvailability(models.Model):
    clinic_location = models.CharField(max_length=100, null=False)
    appointment_type = models.CharField(
        max_length=20,
        default='checkup',
        choices=[
            ('Checkup', 'Checkup'),
            ('Cleaning', 'Cleaning'),
            ('Filling', 'Filling'),
            ('Extraction', 'Extraction')
        ]
    )
    available_slots = models.IntegerField(null=False, validators=[MinValueValidator(0)])
    appointment_date = models.DateTimeField(null=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(available_slots__gte=0),
                name='available_slots_non_negative')
        ]

    def __str__(self):
        return f"{self.appointment_type} at {self.clinic_location} on {self.appointment_date}"