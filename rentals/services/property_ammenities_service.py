def save(self, *args, **kwargs):
    if self.property is None and self.Inquiry is None:
        return TypeError
    super().save(*args, **kwargs)