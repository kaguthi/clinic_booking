from datetime import datetime, timedelta, time
import uuid
from django.utils import timezone
from .models import Doctor, Appointment

def generate_available_slots(doctor: Doctor, date: datetime.date):
    """
    Generates a list of available 30-minute slots for a given doctor on a specific date.
    """
    available_slots = []
    day_of_week = date.strftime("%A")

    if day_of_week not in doctor.working_hours:
        return []

    working_start_str = doctor.working_hours[day_of_week]["start"]
    working_end_str = doctor.working_hours[day_of_week]["end"]

    working_start_time = datetime.strptime(working_start_str, "%H:%M").time()
    working_end_time = datetime.strptime(working_end_str, "%H:%M").time()

    current_slot_start = timezone.make_aware(datetime.combine(date, working_start_time))
    working_end_datetime = timezone.make_aware(datetime.combine(date, working_end_time))

    booked_appointments = Appointment.objects.filter(
        doctor=doctor,
        start_time__date=date,
        status__in=["booked", "completed"]
    ).order_by("start_time")

    booked_slots = []
    for appt in booked_appointments:
        booked_slots.append((appt.start_time, appt.end_time))

    while current_slot_start + timedelta(minutes=30) <= working_end_datetime:
        current_slot_end = current_slot_start + timedelta(minutes=30)
        is_booked = False

        for booked_start, booked_end in booked_slots:
            if (current_slot_start < booked_end) and (current_slot_end > booked_start):
                is_booked = True
                break
        
        if current_slot_end > timezone.now():
            available_slots.append({
                "slot_id": str(uuid.uuid4()),
                "doctor_id": str(doctor.doctor_id),
                "start_time": current_slot_start,
                "end_time": current_slot_end,
                "is_booked": is_booked
            })

        current_slot_start += timedelta(minutes=30)

    return available_slots
