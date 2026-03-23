# context_processors.py
from .models import AdminMessage
from django.utils import timezone

def admin_messages_context(request):
    """Make active admin messages available in all templates"""
    if request.user.is_authenticated:
        # Get messages that should be shown to current user
        messages_to_show = []
        for message in AdminMessage.objects.filter(is_active=True):
            if message.should_show_to_user(request.user):
                # Check if message is currently active based on dates
                if message.is_current():
                    # Check if user has already dismissed this message
                    session_key = f'dismissed_message_{message.id}'
                    if not request.session.get(session_key):
                        messages_to_show.append(message)
        
        return {'admin_messages': messages_to_show}
    return {'admin_messages': []}




from django.db.models import Count, Q
from .models import PropertyType, City, Property


def nav_context(request):
    # FIX: Property.property_type FK has no explicit related_name in the model,
    # so Django auto-generates it as 'property_set'. But looking at the Property
    # model, the field is `property_type = ForeignKey(PropertyType, ...)` with no
    # related_name, so the reverse accessor is 'property_set'.
    # However, using the model name lowercase 'property' also works in annotations.
    # The safest approach is to filter Property directly and build a lookup dict.
    available_type_ids = (
        Property.objects
        .filter(status='available')
        .values('property_type_id')
        .annotate(cnt=Count('id'))
    )
    count_map = {row['property_type_id']: row['cnt'] for row in available_type_ids}

    property_types = []
    i = 0
    for pt in PropertyType.objects.order_by('display_name'):
        if i == 10:
            break
        cnt = count_map.get(pt.id, 0)
        if cnt > 0:
            pt.property_count = cnt
            property_types.append(pt)
        i += 1

    # Cities — chain: City ← area_set (Area.city, no related_name)
    #                       ← locations (Location.area, related_name='locations')
    #                       ← properties (Property.location, related_name='properties')
    nav_cities = (
        City.objects
        .annotate(
            listing_count=Count(
                'area__locations__properties',
                filter=Q(area__locations__properties__status='available'),
                distinct=True,
            )
        )
        .filter(listing_count__gt=0)
        .order_by('-listing_count')[:8]
    )

    total_properties = Property.objects.filter(status='available').count()

    return {
        'nav_property_types': property_types,
        'nav_cities':         nav_cities,
        'total_properties':   total_properties,
        'nav_fallback_areas': ['Maitama', 'Wuse II', 'Asokoro', 'Gwarinpa', 'Jabi', 'Garki', 'Lugbe', 'Kado'],
    }