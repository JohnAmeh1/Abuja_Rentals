import cloudinary

class PropertyImageService:
    def save(self, *args, **kwargs):
        res = cloudinary.uploader.upload(
            self.image,
            folder=f"abuja_rentals/properties/{self.property.id}/images",
            public_id=f"image_{self.order}",
            overwrite=True,
        )
        self.image = res['secure_url']
        super().save(*args, **kwargs)