from django.utils import timezone


class AdminMessageService:
    def __str__(self):
        return f"{self.title} ({self.get_message_type_display()})"
    
        
    def is_current(self):
        """Check if message is currently active"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True

    def should_show_to_user(self, user):
        """Check if message should be shown to specific user"""
        if not self.is_current():
            return False
        
        # Don't show to message creator
        if user == self.created_by:
            return False
        
        # Don't show to admins unless explicitly allowed
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin':
            return False
        
        # Check user type permissions
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
            if user_type == 'agent' and not self.show_to_agents:
                return False
            if user_type == 'tenant' and not self.show_to_tenants:
                return False
        
        return True
