from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Inquiry, AgentApplication

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'
    fk_name = 'user'

# Extend UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff')
    list_select_related = ('userprofile', )
    
    def get_user_type(self, instance):
        return instance.userprofile.get_user_type_display()
    get_user_type.short_description = 'User Type'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register other models
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone_number', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display  = ('user__username', 'user__email', 'property_type', 'purpose', 'cities', 'closed', 'created_at')
    list_filter   = ('property_type', 'purpose', 'closed', 'cities')
    search_fields = ('user__username', 'user__email', 'notes')
    list_editable = ('closed',)
    readonly_fields = ('created_at',)



@admin.register(AgentApplication)
class AgentApplicationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'status', 'phone', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter   = ('status',)
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    ordering      = ('-created_at',)

    fieldsets = (
        ('Applicant', {
            'fields': ('user', 'phone', 'bio', 'experience', 'areas_of_focus')
        }),
        ('Review', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_applications', 'reject_applications']

    @admin.action(description='Approve selected applications')
    def approve_applications(self, request, queryset):
        count = 0
        for application in queryset.filter(status='pending').select_related('user', 'user__userprofile'):
            application.approve(reviewed_by=request.user)
            count += 1
        self.message_user(request, f'{count} application(s) approved.')

    @admin.action(description='Reject selected applications')
    def reject_applications(self, request, queryset):
        count = 0
        for application in queryset.filter(status='pending').select_related('user'):
            application.reject(reviewed_by=request.user, reason='Did not meet current requirements.')
            count += 1
        self.message_user(request, f'{count} application(s) rejected.')
