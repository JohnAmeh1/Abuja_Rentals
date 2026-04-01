# context_processors.py
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache

from .models import PropertyType, City, Property, AdminMessage


def admin_messages_context(request):
    if not request.user.is_authenticated:
        return {'admin_messages': []}
    
    try:
        user_type = request.user.userprofile.user_type
    except Exception:
        return {'admin_messages': []}

    if user_type == 'admin':
        return {'admin_messages': []}

    now = timezone.now()
    qs = AdminMessage.objects.filter(
        is_active=True,
        start_date__lte=now,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).only("id", "message", "title")
    if user_type == 'agent':
        qs = qs.filter(show_to_agents=True)
    else:
        qs = qs.filter(show_to_tenants=True)

    messages_to_show = [
        m for m in qs
        if not request.session.get(f'dismissed_message_{m.id}')
    ]
    return {'admin_messages': messages_to_show}


def nav_context(request):
    # FIX: Property.property_type FK has no explicit related_name in the model,
    # so Django auto-generates it as 'property_set'. But looking at the Property
    # model, the field is `property_type = ForeignKey(PropertyType, ...)` with no
    # related_name, so the reverse accessor is 'property_set'.
    # However, using the model name lowercase 'property' also works in annotations.
    # The safest approach is to filter Property directly and build a lookup dict.
    cached = cache.get('nav_context_data')
    if cached:
        return cached
    available_type_ids = (
        Property.objects
        .filter(status='available')
        .values('property_type_id')
        .annotate(cnt=Count('id'))
    )
    count_map = {row['property_type_id']: row['cnt'] for row in available_type_ids}
    property_types = []
    i = 0
    for pt in PropertyType.objects.order_by("display_name"):
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

    result =  {
        'nav_property_types': [{"id": pt.id, "icon": pt.icon, "display_name": pt.display_name, "property_count": pt.property_count} for pt in property_types],
        'nav_cities':         [{'id': c.id, 'name': c.name} for c in nav_cities],
        'total_properties':   total_properties,
        'nav_fallback_areas': ['Maitama', 'Wuse II', 'Asokoro', 'Gwarinpa', 'Jabi', 'Garki', 'Lugbe', 'Kado'],
    }
    cache.set('nav_context_data', result, timeout=1000)
    return result