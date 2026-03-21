# from django.conf import settings
# from django.utils import timezone
# from ..views import send_mail_

# class AgentApplicationService:
    
#     def approve(self, reviewed_by):
#         """Approve the application, elevate the user, create AgentProfile."""
#         self.status      = 'approved'
#         self.reviewed_by = reviewed_by
#         self.reviewed_at = timezone.now()
#         self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

#         profile = self.user.userprofile
#         profile.user_type = 'agent'
#         profile.save(update_fields=['user_type'])

#         agent_profile, _ = AgentProfile.objects.get_or_create(
#             user=self.user,
#             defaults={
#                 'bio':             self.bio,
#                 'phone':           self.phone,
#                 'assigned_cities': self.areas_of_focus,
#             }
#         )

#         send_mail_(
#             user=self.user,
#             subject='Your agent application has been approved',
#             message=(
#                 f"Hi {self.user.get_full_name() or self.user.username},\n\n"
#                 f"Congratulations! Your application to become an agent on Abuja Rentals "
#                 f"has been approved. You can now list properties and respond to client requests.\n\n"
#                 f"Log in to get started: {settings.SITE_URL}/dashboard/\n\n"
#                 f"Welcome aboard!"
#             )
#         )
#         return agent_profile

#     def reject(self, reviewed_by, reason=''):
#         """Reject the application."""
#         self.status           = 'rejected'
#         self.reviewed_by      = reviewed_by
#         self.reviewed_at      = timezone.now()
#         self.rejection_reason = reason
#         self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

#         if reason:
#             send_mail_(
#                 user=self.user,
#                 subject='Update on your agent application',
#                 message=(
#                     f"Hi {self.user.get_full_name() or self.user.username},\n\n"
#                     f"Thank you for applying. Unfortunately your application was not approved at this time.\n\n"
#                     f"Reason: {reason}\n\n"
#                     f"You're welcome to apply again after addressing the feedback above."
#                 )
#             )

#     def __str__(self):
#         return f"{self.user.username} — {self.get_status_display()}"