from django.utils import timezone


def save(self, *args, **kwargs):        
    if self.purpose == 'rent' and not self.rent_duration_months:
        self.rent_duration_months = 12
    
    if self.status == 'available' and not self.published_at:
        self.published_at = timezone.now()
    
    self.save(*args, **kwargs)

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

    city = None
    address = None

    if p.location:

        address = p.location.address

        if p.location.city:
            city = p.location.city.name

    data = {
        "id": p.id,
        "title": p.title,
        "price": str(p.price),
        "purpose": p.purpose,
        "main_image": main_image,
        "bedrooms": p.bedrooms,
        "bathrooms": p.bathrooms,
        "area_sqft": str(p.area_sqft) if p.area_sqft else None,
        "city": city,
        "state": p.location.city.state.name,
        "address": address,
        "furnished": p.furnished,
        "serviced": p.serviced,
        "shared": p.shared,
        "is_featured": p.is_featured,
        "owner": p.owner_id,
        "property_type": p.property_type.display_name if p.property_type else None,
        "status": p.status,
        "rent_duration_months": p.rent_duration_months,
        "description": p.description,
        "views": p.views,
        "school": p.school.name if p.school else None,
        "school_short_name": p.school.short_name if p.school else None,
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