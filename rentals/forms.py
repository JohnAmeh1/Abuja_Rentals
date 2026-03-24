from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Property, Report, AgentProfile
from django.utils import timezone
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Email address'
    }))
    phone_number = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Phone number'
        })
    )
    address = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Address (optional)'
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Tell us about yourself...',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'bio', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'first_name', 'last_name']:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': self.fields[field_name].label
            })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password',
            'id': 'p1'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm Password',
            'id': 'p2'
        })
        # FIX: Removed dead `str().isdigit()` line that did nothing.

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Password'
    }))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500',
        'checked': True
    }))


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
        'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                     'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
            'placeholder': 'Last Name',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                     'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
            'placeholder': 'Email Address',
        })
    )

    class Meta:
        model = UserProfile
        # Added profile_picture so enctype="multipart/form-data" on the form saves it
        fields = ['phone_number', 'whatsapp_number', 'address', 'bio', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                         'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
                'placeholder': 'e.g. +234 800 000 0000',
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                         'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
                'placeholder': 'e.g. +234 800 000 0000',
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                         'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition',
                'placeholder': 'Full address',
            }),
            # The bio widget is defined here but the template renders it manually
            # (see comment in profile.html) to avoid the 4-spaces bug.
            # The widget attrs are still used for the id attribute.
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 border border-gray-200 rounded-xl text-sm '
                         'focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none '
                         'transition resize-none',
                'placeholder': 'Tell us about yourself…',
                'rows': 4,
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/png,image/jpeg,image/webp',
                'id': 'avatarInput',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial  = self.user.last_name
            self.fields['email'].initial      = self.user.email

        # Strip leading/trailing whitespace from bio at the field level as a
        # second line of defence against the 4-spaces Django indentation artefact.
        if 'bio' in self.fields:
            self.fields['bio'].strip = True

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name  = self.cleaned_data['last_name']
            self.user.email      = self.cleaned_data['email']
            self.user.save()
        if commit:
            profile.save()
        return profile
class AgentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = AgentProfile
        fields = ['phone', 'whatsapp_number', 'bio', 'website']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Phone Number'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'WhatsApp number'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Tell us about yourself...',
                'rows': 10
            }),
            'website': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Website',
            }),
        }

    def save(self, commit=True):
        agent = super().save(commit=False)
        if commit:
            agent.save()
        return agent


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "title", "description", "property_type", "purpose",
            "bedrooms", "bathrooms", "area_sqft", "price",
            "rent_duration_months", "furnished", "shared", "serviced",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bedrooms'].required          = False
        self.fields['bathrooms'].required         = False
        self.fields['area_sqft'].required         = False
        self.fields['rent_duration_months'].required = False
        self.fields['status'].required            = False
        
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'message']
        widgets = {
            'reason': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Describe the issue in detail (optional)'
            })
        }


class AdminMessageForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Message Title'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Enter your message here...',
            'rows': 5
        })
    )
    MESSAGE_TYPE_CHOICES = [
        ('info', 'Information'), ('warning', 'Warning'),
        ('success', 'Success'), ('alert', 'Alert'), ('maintenance', 'Maintenance'),
    ]
    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'type': 'datetime-local'
        })
    )
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'type': 'datetime-local'
        })
    )
    is_active = forms.BooleanField(required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'})
    )
    show_to_all = forms.BooleanField(required=False, initial=True, label="Show to all non-admin users",
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'})
    )
    show_to_agents = forms.BooleanField(required=False, initial=True, label="Show to property owners",
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'})
    )
    show_to_tenants = forms.BooleanField(required=False, initial=True, label="Show to tenants",
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('start_date'):
            self.fields['start_date'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6, min_length=6, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest',
            'placeholder': '000000', 'inputmode': 'numeric',
            'maxlength': '6', 'autocomplete': 'one-time-code'
        }),
        label='Enter OTP Code'
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code', '').strip()
        if not otp_code.isdigit():
            raise ValidationError('OTP code must contain only digits.')
        return otp_code


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your email address', 'autocomplete': 'email'
        }),
        label='Email Address'
    )


class ForgotPasswordOTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6, min_length=6, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest',
            'placeholder': '000000', 'inputmode': 'numeric',
            'maxlength': '6', 'autocomplete': 'one-time-code'
        }),
        label='Enter OTP Code'
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code', '').strip()
        if not otp_code.isdigit():
            raise ValidationError('OTP code must contain only digits.')
        return otp_code


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter new password', 'autocomplete': 'new-password'
        }),
        label='New Password',
        help_text='At least 8 characters with uppercase, lowercase, and numbers.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm new password', 'autocomplete': 'new-password'
        }),
        label='Confirm Password'
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data