from app.models import *

def checkOrganizerPlan(organizer):

    checkOrganizerPlan = OrganizerDetail.objects.filter(organizer = organizer)

    if not checkOrganizerPlan.exists():
        raise ValueError("Organizer has not selected a payment plan")
    if not checkOrganizerPlan[0].payment_plan:
        raise ValueError("Organizer has not selected a payment plan")
    return checkOrganizerPlan[0].payment_plan