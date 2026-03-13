from ..models import Inquiry
from django.db.models import Q

def get_inquiry_queryset(self):
    qs = Inquiry.objects.filter(closed=False).exclude(
        inquires_responses__agent=self.user,
        user=self.user
    )

    assigned_cities = self.assigned_cities
    if assigned_cities:
        city_filter = Q()
        for city in assigned_cities:
            city_filter |= Q(cities__contains=city)
        qs = qs.filter(city_filter)

    assigned_school_ids = list(self.assigned_schools.values_list('id', flat=True))
    if assigned_school_ids:
        qs = qs.filter(school_id__in=assigned_school_ids)

    return qs.select_related('user', 'school').order_by('-created_at')
