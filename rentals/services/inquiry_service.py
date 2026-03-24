class InquiryService:
    def save(self, *args, **kwargs):
        if self.bathrooms_min and self.bathrooms_max and self.bathrooms_min > self.bathrooms_max:
            self.bathrooms_max = self.bathrooms_min
        if self.bedrooms_min and self.bedrooms_max and self.bedrooms_min > self.bedrooms_max:
            self.bedrooms_max = self.bedrooms_min
        if self.budget_min and self.budget_max and self.budget_min > self.budget_max:
            self.budget_max = self.budget_min
        
        super().save(*args, **kwargs)


    def __str__(self):
        user = self.user.username if self.user else "Anonymous"
        return f"{user} — {self.property_type or 'any'} ({self.created_at:%d %b %Y})"

    def amenities_list(self):
        """Return amenities as a Python list."""
        return [a.strip() for a in self.amenities.split(',') if a.strip()]
