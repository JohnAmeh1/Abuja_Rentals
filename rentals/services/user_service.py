class UserProfileService:
    @classmethod
    def make_profile(cls, user, details, *args, **kwargs):
        profile, created = cls.objects.get_or_create(
                user=user,
                defaults={'user_type': 'tenant'}
            )
        if not created:
            return True
        
        if details['phone_number']:
            profile.phone_number = details['phone_number']
            
        if details['address']:
            profile.address = details['address']

        if details['bio']:
            profile.bio = details['bio']
            
        profile.save(*args, **kwargs)
        return True