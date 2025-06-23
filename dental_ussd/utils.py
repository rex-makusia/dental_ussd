# We will define USSD functions here
# We will define USSD functions here
from annoying.functions import get_object_or_None
from django.forms.models import model_to_dict
from dental_ussd.models import Patient, Appointment, ClinicAvailability
from django.core.exceptions import ObjectDoesNotExist
import structlog

logger = structlog.get_logger(__name__)
def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None

def authenticate_user(ussd_request):
    resp = None
    phone_number = ussd_request.session.get('phone_number')
    print(phone_number)
    patient_reg = get_or_none(Patient, mobile_number=phone_number)
    print(patient_reg)
    if patient_reg is not None:
        resp = patient_reg
    print(f"[*] resp={resp}")
    return resp

def register_user(ussd_request):
    resp = None
    patient_name = ussd_request.session.get('patient_name')
    phone_number = ussd_request.session.get('phone_number')
    patient = Patient.objects.get_or_create(
        mobile_number=phone_number,
        name=patient_name)
    if patient is not None:
        resp = patient
    else:
        resp = "Patient already registered"
    print(f"[*] resp={resp}")
    return resp

def fetch_available_appointment_slot(ussd_request) -> dict[int, str] | None:
    """
    Fetch available appointment slots for a specific appointment type.

    Args:
        ussd_request: The USSD request containing session data

    Returns:
        Dictionary mapping slot IDs to formatted location and time strings,
        or None if no slots are available
    """
    appointment_type = ussd_request.session.get('appointment_type')

    if not appointment_type:
        logger.error("No appointment type found in session")
        return None

    appointment_type = appointment_type.title()
    logger.info(f"Fetching slots for appointment type: {appointment_type}")

    try:
        # Query for available slots
        available_slots = ClinicAvailability.objects.filter(
            appointment_type=appointment_type,
            available_slots__gt=0
        )

        # Return None if no slots are available
        if not available_slots.exists():
            logger.info(f"No available slots found for {appointment_type}")
            return None

        # Build the response dictionary
        slots_dict = {}
        for slot in available_slots:
            formatted_date = slot.appointment_date.strftime('%Y-%m-%d %I %p')
            slots_dict[slot.pk] = f"{slot.clinic_location} ({formatted_date})"

        logger.info(f"Found {len(slots_dict)} available slots for {appointment_type}")
        return slots_dict

    except Exception as e:
        logger.error(f"Error fetching available slots: {str(e)}")
        return None

def book_cleaning(ussd_request):
    resp_menu = None
    appointment_type = ussd_request.session.get('appointment_type')
    try:
        resp_menu = ClinicAvailability.objects.filter(appointment_type=appointment_type, available_slots__gt=0)
        # Check if resp_menu is not empty and not None
        if resp_menu and resp_menu.exists():
            logger.info(
                f"Found {resp_menu.count()} cleaning slots: {list(resp_menu.values('pk', 'clinic_location', 'appointment_date'))}")
            return resp_menu
        else:
            logger.info("No cleaning slots available")
            return None
    except Exception as e:
        logger.error(f"Error fetching clinic availability: {str(e)}")
        return None

def save_appointment_slot(ussd_request):
    selected_slot_pk = ussd_request.session.get('appointment_slot')
    if not selected_slot_pk:
        logger.error("No selected slot found in session (appointment_slot)")
        return None
    try:
        resp_menu = ClinicAvailability.objects.get(pk=selected_slot_pk)
        # Convert to dictionary safely
        slot_dict = model_to_dict(
            resp_menu,
            fields=['pk', 'appointment_type', 'clinic_location', 'appointment_date']
        )
        # Format datetime to string for JSON serialization
        if slot_dict['appointment_date']:
            slot_dict['appointment_date'] = slot_dict['appointment_date'].strftime('%Y-%m-%d %I%p')
        # Store in a new session key to avoid overwriting appointment_slot
        ussd_request.session['selected_appointment_slot'] = slot_dict
        logger.info(f"Stored selected_appointment_slot in session: {slot_dict}")
        return slot_dict

    except ClinicAvailability.DoesNotExist:
        logger.error(f"No ClinicAvailability found for pk: {selected_slot_pk}")
        return None
    except Exception as e:
        logger.error(f"Error fetching clinic availability: {str(e)}")
        return None

def book_appointment(ussd_request):
    resp_menu = None
    appointment = ussd_request.session.get('appointment_slot')
    patient=ussd_request.session.get('phone_number')

    try:
        patient = get_or_none(Patient, mobile_number=patient)
        clinic_slot = ClinicAvailability.objects.get(pk=appointment)
        obj_appointment = Appointment.objects.create(
            patient=patient,
            appointment_type=clinic_slot.appointment_type,
            clinic_location=clinic_slot.clinic_location,
            appointment_date=clinic_slot.appointment_date
        )
        obj_appointment.save()
        if clinic_slot.available_slots > 0:
            clinic_slot.available_slots -= 1
            clinic_slot.save()
        return obj_appointment
    except ClinicAvailability.DoesNotExist:
        print(f"No ClinicAvailability found for pk: {appointment}")
        # resp_menu = "No ClinicAvailability found"
        return None
    except Exception as e:
        print(f"Error creating appointment: {e}")
        # resp_menu = "Error creating appointment"
        return None

def book_checkup(ussd_request):
    resp_menu = None
    _d = {}
    try:
        resp_menu = ClinicAvailability.objects.filter(appointment_type='Checkup', available_slots__gt=0)
    except Exception as e:
        print(f"Error fetching clinic availability: {e}")
        #resp_menu = "Error fetching clinic availability"

    # for i in clinic_availability:
    #     print(f"[*] i={i}")
    #     formatted_date = i.appointment_date.strftime('%Y-%m-%d %I %p')
    #     _d[i.pk] = f"{i.clinic_location} ({formatted_date})"
    return resp_menu

def book_filling(ussd_request):
    resp_menu = None
    _d = {}
    try:
        resp_menu = ClinicAvailability.objects.filter(appointment_type='Filling', available_slots__gt=0)
    except Exception as e:
        print(f"Error fetching clinic availability: {e}")

    return resp_menu

def book_cleaning_slot(ussd_request):
    resp = None
    print(f"[***] {ussd_request.session.get('cleaning_slot_key')}")
    cleaning_slot = ussd_request.session.get('cleaning_slot')
    phone_number = ussd_request.session.get('phone_number')
    patient = get_or_none(Patient, mobile_number=phone_number)
    clinic = get_or_none(ClinicAvailability, pk=cleaning_slot)
    if patient is not None and clinic is not None:
        try:
            appointment = Appointment.objects.create(
                patient=patient,
                appointment_type=clinic.appointment_type,
                clinic_location=clinic.clinic_location,
                appointment_date=clinic.appointment_date
            )
            appointment.save()
        except Exception as e:
            print(f"Error creating appointment: {e}")
    return resp

def check_all_appointments(ussd_request) -> dict | None:
    """
    Check if a patient has any appointments and return them as a dictionary.

    Args:
        ussd_request: The USSD request containing session data

    Returns:
        Dictionary of appointment IDs to formatted strings or None if no appointments exist
    """
    phone_number = ussd_request.session.get('phone_number')
    if not phone_number:
        logger.error("No phone number found in session")
        return None
            
    try:
        appointment_list = Appointment.objects.filter(patient__mobile_number=phone_number)
        
        if not appointment_list.exists():
            logger.info(f"No appointments found for {phone_number}")
            return None
        
        appointments_dict = {}
        for appointment in appointment_list:
            formatted_date = appointment.appointment_date.strftime('%d/%m/%Y')
            appointments_dict[appointment.pk] = f"{appointment.appointment_type} ({appointment.status})"
        
        logger.info(f"Retrieved {len(appointments_dict)} appointments for {phone_number}")
        return appointments_dict
            
    except Exception as e:
        logger.error(f"Error checking appointments: {str(e)}")
        return None

def get_scheduled_appointments(ussd_request):
    _d = {}
    phone_number = ussd_request.session.get('phone_number')
    try:
        appointment_list = Appointment.objects.filter(patient__mobile_number=phone_number, status="scheduled")
        
        # Return None if appointment_list is empty
        if not appointment_list.exists():
            return None
            
    except Exception as e:
        print(f"Error fetching clinic availability: {e}")
        return None

    for i in appointment_list:
        print(f"[*] i={i}")
        formatted_date = i.appointment_date.strftime('%d/%m/%Y')
        _d[i.pk] = f"{i.appointment_type} ({i.status})"
    
    return _d

def save_scheduled_appointment_slot_key(ussd_request):
    scheduled_slot_pk = ussd_request.session.get('selected_appointment')
    phone_number = ussd_request.session.get('phone_number')
    logger.info(f"Attempting to save appointment slot key for phone number: {phone_number}")
    if not scheduled_slot_pk:
        logger.error("No scheduled appointment found in session (selected_appointment)")
        return None
    try:
        resp_menu = Appointment.objects.get(pk=scheduled_slot_pk, patient__mobile_number=phone_number, status="scheduled")
        # Convert to dictionary safely
        slot_dict = model_to_dict(
            resp_menu,
            fields=['pk', 'appointment_type', 'clinic_location', 'appointment_date']
        )
        # Format datetime to string for JSON serialization
        if slot_dict['appointment_date']:
            slot_dict['appointment_date'] = slot_dict['appointment_date'].strftime('%Y-%m-%d %I%p')
        # Store in a new session key to avoid overwriting appointment_slot
        ussd_request.session['scheduled_appointment_slot'] = slot_dict
        logger.info(f"Stored scheduled_appointment_slot in session: {slot_dict}")
        return slot_dict

    except Appointment.DoesNotExist:
        logger.error(f"No Appointments found for pk: {scheduled_slot_pk}")
        return None
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        return None

def fetch_selected_appointment(ussd_request):
    appointment_id = ussd_request.session.get('appointment')
    appointment = get_object_or_None(Appointment, pk=appointment_id)
    return appointment


def cancel_appointment(ussd_request):
    selected_appointment = ussd_request.session.get('selected_appointment')
    print(f"{selected_appointment}")
    appointment = Appointment.objects.get(pk=selected_appointment)
    appointment.status='cancelled'
    appointment.save()
    return None