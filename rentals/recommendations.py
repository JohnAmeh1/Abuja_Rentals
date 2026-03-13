from django.db.models import (
    F,
    FloatField,
    ExpressionWrapper,
    Case,
    When,
    Value,
    Prefetch
)
from django.db.models.functions import Abs, Coalesce
from django.core.cache import cache
from .models import Property, PropertyImage
from .services.property_service import serialize_property


def get_property_recommendations(property_obj, limit=6):
    cache_key = f"property_recs_{property_obj.id}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    base_queryset = Property.objects.filter(
        purpose=property_obj.purpose,
        status='available'
    ).exclude(
        id=property_obj.id
    ).select_related('owner')

    if property_obj.location and property_obj.location.city:
        base_queryset = base_queryset.filter(
            location__city=property_obj.location.city
        )

    if not base_queryset.exists():
        return Property.objects.none()

    # -------------------------
    # SCORING COMPONENTS
    # -------------------------

    queryset = base_queryset.annotate(

        # Handle NULL bedrooms safely
        bedroom_value=Coalesce(F('bedrooms'), Value(0)),

        # Price difference
        price_diff=Abs(F('price') - property_obj.price),

        # Bedroom difference
        bedroom_diff=Abs(
            Coalesce(F('bedrooms'), Value(0)) -
            (property_obj.bedrooms or 0)
        ),

        # Property type boost
        type_score=Case(
            When(property_type=property_obj.property_type, then=Value(20.0)),
            default=Value(0.0),
            output_field=FloatField()
        ),

        # Featured boost
        featured_score=Case(
            When(is_featured=True, then=Value(10.0)),
            default=Value(0.0),
            output_field=FloatField()
        ),
    ).annotate(

        # Final weighted score
        score=ExpressionWrapper(
            F('type_score') +

            # Price similarity (closer = higher score)
            (1000000.0 / (F('price_diff') + 1)) +

            # Bedroom similarity
            (50.0 / (F('bedroom_diff') + 1)) +

            F('featured_score'),

            output_field=FloatField()
        )

    ).order_by('-score', '-created_at')

    results = list(queryset[:limit])

    # -------------------------
    # FALLBACK STRATEGY
    # -------------------------

    if len(results) < 3:
        fallback = Property.objects.filter(
            purpose=property_obj.purpose,
            status='available'
        ).exclude(
            id=property_obj.id
        ).select_related(
            'owner', 'location', 'location__area',
            'location__area__city', 'property_type',
        ).prefetch_related(
            Prefetch('images', queryset=PropertyImage.objects.order_by('order'))
        ).order_by('-is_featured', '-views')[:limit]

        return [serialize_property(p) for p in fallback]

    # Cache for 10 minutes
    cache.set(cache_key, results, timeout=600)

    return [
        serialize_property(p)
        for p in results
    ]
