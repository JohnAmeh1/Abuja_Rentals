from django.utils import timezone

class PropertyService:
    def save(self, *args, **kwargs):        
        if self.purpose == 'rent' and not self.rent_duration_months:
            self.rent_duration_months = 12
        
        if self.status == 'available' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        ptype = self.property_type.display_name if self.property_type else "Unknown"
        return f"{self.title} - {ptype} ({self.get_purpose_display()})"



def get_image_url(img):
    if not img.image:
        return None
    name = img.image.name
    if name.startswith("http"):
        return name
    return img.image.url


def serialize_property(p, detail=False):
    main_image = None

    imgs = list(p.images.all())
    main_image = get_image_url(imgs[0]) if imgs else None

    address = None

    if p.location:
        address = p.location.address
        if p.location.area:
            area = p.location.area.name

    data = {
        "id": p.id,
        "title": p.title,
        "price": str(p.price),
        "purpose": p.purpose,
        "main_image": main_image,
        "bedrooms": p.bedrooms,
        "bathrooms": p.bathrooms,
        "area_sqft": str(p.area_sqft) if p.area_sqft else None,
        "area": area,
        "city": p.location.area.city.name if p.location.area.city else None,
        "state": p.location.area.city.state.name if p.location.area.city.state else None,
        "address": address,
        "furnished": p.furnished,
        "serviced": p.serviced,
        "shared": p.shared,
        "is_featured": p.is_featured,
        "agent": p.agent_id,
        "property_type": p.property_type.display_name if p.property_type else None,
        "status": p.status,
        "rent_duration_months": p.rent_duration_months,
        "description": p.description,
        "verified": p.verified,
        "views": p.views,
        "school": p.school.name if p.school else None,
        "school_short_name": p.school.short_name if p.school else None,
        "created_at": p.created_at
    }


    if detail:

        amenities = [
            pa.amenity.display_name
            for pa in p.property_amenities.all()
        ]
        data.update({
            "images": [get_image_url(img) for img in imgs if img.image],
            "amenities": amenities,
        })
    return data