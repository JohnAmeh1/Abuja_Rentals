from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, F, DecimalField, Prefetch

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
from django.core import signing
from datetime import datetime
from decimal import Decimal
from .services.send_mail import _send_notification_email



from .models import (UserProfile, Property, SavedProperty, PropertyVisit, AdminMessage, Report,
                     PropertyVisit, Inquiry, School, OTP, InquiryResponse, AgentProfile, Notification,
                     AgentApplication, PropertyType, Amenity, City, InquiryCity, PropertyImage,
                     Location, PropertyAmenity, InquiryAmenity, AgentPreferredTypes, Area,
                     AgentAssignedSchools, AgentAssignedCities)

from .forms import (CustomUserCreationForm, LoginForm, ProfileUpdateForm, PropertyForm, AdminMessageForm, ReportForm,
                    OTPVerificationForm, ForgotPasswordForm, ForgotPasswordOTPForm, ResetPasswordForm,
                    AgentProfileUpdateForm)
from .services.recommendations import get_property_recommendations
from .services.property_service import serialize_property, get_image_url
from .services.helper import PURPOSE_CHOICES, PROPERTY_STATUS_CHOICES, AGENT_PROPERTY_STATUS_CHOICES
from .onboarding import get_agent_onboarding

        
        


import random
import json
import threading
import cloudinary




def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin'

def is_agent(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.user_type == 'agent'


def trigger_otp_notification(user, notification_type):
    otp = OTP.create_otp(user)
    
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        mode="email",
        message=otp.code,
        sent=False
    )
    
    success = _send_notification_email(notification.id)
    
    if not success:
        otp.delete()
            
    return success

def verify_otp_view(request):
    """View to verify OTP code"""
    user = request.user
    if not user:
        messages.error(request, 'User not found.')
        return redirect('signup')

    profile = user.userprofile

    if profile.email_is_verified:
        messages.info(request, 'Email already verified.')
        login(request, user)
        return redirect('home')

    try:
        otp = OTP.objects.get(user=user)
    except OTP.DoesNotExist:
        resend_otp(request)
        request.method = "GET"

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            if not otp.is_valid():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('verify_otp')

            if otp.verify(otp_code):
                profile.email_is_verified = True
                profile.save()

                messages.success(request, 'Email verified successfully!')
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP code. Please try again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'auth/verify_otp.html', {
        'form': form,
        'user_email': user.email,
    })


def resend_otp(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('signup')

    success = trigger_otp_notification(user, "email_verification")
    
    if success:
        messages.success(request, f'A new verification code was sent to {user.email}')
    else:
        messages.error(request, 'Failed to send email. Please try again.')

    return redirect('verify_otp')


def forgot_password(request):
    """Handle forgot password request - submit email"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                success = trigger_otp_notification(user, "forgot_password")

                if success:
                    request.session['password_reset_user_id'] = user.id
                    messages.success(request, 'Check your email for the reset code.')
                    return redirect('verify_forgot_password_otp')

                else:
                    messages.error(request, 'Failed to send OTP. Please try again later.')
            except User.DoesNotExist:
                messages.info(request, f'Please check the email "{email}"')
                return redirect('login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'auth/forgot_password.html', {'form': form})


def verify_forgot_password_otp(request):
    """Verify OTP during forgot password process"""
    user_id = request.session.get('password_reset_user_id')

    if not user_id:
        messages.error(request, 'Password reset session expired. Please try again.')
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    try:
        otp = OTP.objects.get(user=user)
    except OTP.DoesNotExist:
        messages.error(request, 'OTP not found. Please request a new one.')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ForgotPasswordOTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            if not otp.is_valid():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('forgot_password')

            if otp.verify(otp_code):
                request.session['password_reset_verified'] = True
                profile = user.userprofile
                if not profile.email_is_verified:
                    profile.email_is_verified = True
                    profile.save()

                messages.success(request, 'OTP verified successfully. Please set your new password.')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid OTP code. Please try again.')
    else:
        form = ForgotPasswordOTPForm()

    return render(request, 'auth/verify_forgot_password_otp.html', {
        'form': form,
        'user_email': user.email,
        'user_id': user_id
    })


def reset_password(request):
    """Reset password after OTP verification"""
    if not request.session.get('password_reset_verified'):
        messages.error(request, 'Please verify your OTP first.')
        return redirect('forgot_password')

    user_id = request.session.get('password_reset_user_id')

    if not user_id:
        messages.error(request, 'Password reset session expired. Please try again.')
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['password']

            user.set_password(new_password)
            user.save()

            request.session.pop('password_reset_user_id', None)
            request.session.pop('password_reset_verified', None)

            messages.success(request, 'Password reset successfully! You can now login with your new password.')
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'auth/reset_password.html', {
        'form': form,
        'user_email': user.email
    })


def resend_forgot_password_otp(request, user_id):
    """Resend OTP during forgot password process"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    success = trigger_otp_notification(user, "forgot_password")

    if success:
        messages.success(request, f'OTP resent to {user.email}')
    else:
        messages.error(request, 'Failed to send OTP. Please try again.')

    return redirect('verify_forgot_password_otp')


def home(request):
    available = Property.objects.filter(status='available')

    featured_qs = (
        available.filter(is_featured=True)
        .order_by("?")[:3]
    )
    
    if not featured_qs.exists():
        featured_qs = available.order_by("-views")[:3]

    featured_qs = featured_qs.select_related(
        "location__area",
        "school",
        "agent"
    ).prefetch_related(
        "images",
        "property_amenities__amenity"
    )

    featured_properties = [serialize_property(p) for p in featured_qs]
    
    type_counts = dict(
        available.values_list("property_type_id")
        .annotate(cnt=Count("id"))
    )

    type_choices = PropertyType.objects.only(
        "id", "name", "display_name", "image"
    )

    categories_raw = [
        {
            "id": pt.id,
            "name": pt.name,
            "display_name": pt.display_name,
            "count": f"{(type_counts.get(pt.id, 0) // 100) * 100}",
            "image": pt.image,
        }
        for pt in type_choices
    ]
    random.shuffle(categories_raw)
    from django.core.cache import cache
    
    schools = cache.get("home_schools")
    if not schools:
        schools = list(
            School.objects.order_by("name").values("id", "name", "short_name")[:100]
        )
    cache.set("home_schools", schools, 3600)
    
    cities = cache.get("home_cities")
    if not cities:
        cities = list(City.objects.values("id", "name"))
        cache.set("home_cities", cities, 3600)
        
    amenities = cache.get("home_amenities")
    if not amenities:
        amenities = list(Amenity.objects.values("id", "name"))
        cache.set("home_amenities", amenities, 3600)

    context = {
        'featured_properties': featured_properties,
        'total_properties': round(available.count(), -2),
        'categories': categories_raw[:9],
        'property_types': type_choices,
        'page_title': 'Home',
        'amenity_choices': amenities,
        'schools': schools,
        'cities': cities,
    }

    return render(request, "home.html", context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            user = authenticate(request, username=username, password=password)

            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)

                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username/email or password')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        user = User.objects.filter(email=request.POST.get("email", "")).first()
        if user:
            messages.error(request, "An account has already been linked with this email")
            return redirect('login')
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            success = UserProfile.make_profile(user, {
                "phone_number": form.cleaned_data['phone_number'],
                "address": form.cleaned_data['address'],
                "bio": form.cleaned_data['bio']
            })
            if success != True:
                user.delete()
                return redirect('signup')

            next_url = request.GET.get('next', 'home')
            login(request, user)

            success = trigger_otp_notification(user, "email_verification")
            if success:
                messages.success(request, 'Account created! Please check your email for the OTP code.\nYou can verify in the dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Failed to send OTP email. Please try again.')
                return redirect(next_url)
        else:
            print(f"DEBUG: Form errors: {form.errors}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'auth/signup.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.userprofile, user=request.user)
        if form.is_valid():
            profile = request.user.userprofile
            image_file = request.FILES.get('profile_picture')
            if image_file:
                try:
                    result = cloudinary.uploader.upload(
                        image_file,
                        folder=f'abuja_rentals/tenants/{request.user.id}/',
                        public_id=f'profile_{request.user.id}',
                        overwrite=True,
                        transformation=[{'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}],
                    )
                    profile.profile_picture = result['secure_url']
                    profile.save()
                except Exception as e:
                    messages.error(request, 'Failed to upload image. Please check your connection and try again.')
                    return redirect('profile')
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.userprofile, user=request.user)
    return render(request, 'auth/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)

    if user_profile.user_type == 'admin':
        pending_properties = Property.objects.filter(status='pending', school_id__isnull=True).count()
        pending_student_properties = Property.objects.filter(status='pending', school_id__isnull=False).count()
        pending_agent_applications = AgentApplication.objects.filter(status='pending').count()
        open_reports = Report.objects.all().count()
        context = {
            'page_title': 'Admin Dashboard',
            'total_users': UserProfile.objects.count(),
            'total_properties': Property.objects.count(),
            'pending_properties': pending_properties,
            'pending_student_properties': pending_student_properties,
            'pending_agent_applications': pending_agent_applications,
            'open_reports': open_reports,
        }

    elif user_profile.user_type == 'agent':
        total_properties = Property.objects.filter(agent__user=user).count()
        available_properties = Property.objects.filter(agent__user=user, status='available').count()

        total_value = Property.objects.filter(agent__user=user).aggregate(
            total=Sum('price')
        )['total'] or 0

        potential_agg = Property.objects.filter(
            agent__user=user,
            purpose='rent'
        ).exclude(status='draft').aggregate(
            total=Sum(F('price') * F('rent_duration_months'), output_field=DecimalField())
        )
        potential_earnings = potential_agg['total'] or Decimal('0.00')

        recent_properties = Property.objects.filter(agent__user=user).order_by('-created_at')[:3]
        agent = _require_agent(request)
        context = {
            'page_title': 'Agent Dashboard',
            'total_properties': total_properties,
            'available_properties': available_properties,
            'total_value': total_value,
            'potential_earnings': potential_earnings,
            'recent_properties': recent_properties,
            'show_welcome_modal': not agent.has_seen_welcome,
            **get_agent_onboarding(request.user, agent),
        }

    elif user_profile.user_type == 'tenant':
        saved_properties_count = user.saved_properties.count() if hasattr(user, 'saved_properties') else 0
        booking_count = user.bookings.count() if hasattr(user, 'bookings') else 0

        context = {
            'page_title': 'Tenant Dashboard',
            'saved_properties_count': saved_properties_count,
            'booking_count': booking_count,
            'requests_count': user.inquires.count(),
        }

    else:
        context = {
            'page_title': 'Dashboard',
        }

    return render(request, 'auth/dashboard.html', context)


def encode_cursor(created_at, id):
    return signing.dumps({"created_at": created_at.isoformat(), "id": id})


def decode_cursor(cursor):
    data = signing.loads(cursor)
    return data["created_at"], data["id"]


def get_user_is_admin(request):
    if request.user.is_authenticated:
        try:
            return request.user.userprofile.user_type == "admin"
        except Exception:
            pass
    return False


def _apply_filters(qs, params, user_is_admin=False):

    search = params.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(location__address__icontains=search)
            | Q(location__area__city__name__icontains=search)
            | Q(location__area__name__icontains=search)
            | Q(school__name__icontains=search)
            | Q(property_type__display_name__icontains=search)
        )

    property_type = params.get("property_type", "").strip()
    if property_type:
        qs = qs.filter(property_type_id=property_type)

    purpose = params.get("purpose", "").strip()
    if purpose:
        qs = qs.filter(purpose=purpose)

    city = params.get("city", "").strip()
    if city:
        qs = qs.filter(location__area__city_id=city)
        
    area = params.get("area", "").strip()
    if area:
        qs = qs.filter(location__area_id=area)

    school = params.get("school", "").strip()
    if school:
        qs = qs.filter(school_id=school)

    status = params.get("status", "").strip()
    if status and user_is_admin:
        qs = qs.filter(status=status)

    min_price = params.get("min_price", "").strip()
    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    max_price = params.get("max_price", "").strip()
    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    min_bedrooms = params.get("min_bedrooms", "").strip()
    if min_bedrooms:
        try:
            qs = qs.filter(bedrooms__gte=int(min_bedrooms))
        except (ValueError, TypeError):
            pass

    max_bedrooms = params.get("max_bedrooms", "").strip()
    if max_bedrooms:
        try:
            qs = qs.filter(bedrooms__lte=int(max_bedrooms))
        except (ValueError, TypeError):
            pass

    min_bathrooms = params.get("min_bathrooms", "").strip()
    if min_bathrooms:
        try:
            qs = qs.filter(bathrooms__gte=int(min_bathrooms))
        except (ValueError, TypeError):
            pass

    max_bathrooms = params.get("max_bathrooms", "").strip()
    if max_bathrooms:
        try:
            qs = qs.filter(bathrooms__lte=int(max_bathrooms))
        except (ValueError, TypeError):
            pass

    if params.get("furnished") == "true":
        qs = qs.filter(furnished=True)

    if params.get("serviced") == "true":
        qs = qs.filter(serviced=True)

    if params.get("shared") == "true":
        qs = qs.filter(shared=True)

    if hasattr(params, "getlist"):
        amenities = params.getlist("amenities")
    else:
        amenities = params.get("amenities") or []
        if isinstance(amenities, str):
            amenities = [amenities]

    if amenities:
        qs = qs.filter(property_amenities__amenity_id__in=amenities)

    qs = qs.distinct()
    return qs


SORT_MAP = {
    "price_asc": "price",
    "price_desc": "-price",
    "newest": "-created_at",
}


def get_properties(request):
    user_is_admin = get_user_is_admin(request)
    qs = (
        Property.objects.all()
        if user_is_admin
        else Property.objects.filter(status="available")
    )

    qs = qs.select_related(
        "location",
        "location__area",
        "property_type",
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=PropertyImage.objects.order_by("order"),
        )
    )

    qs = _apply_filters(qs, request.GET, user_is_admin=user_is_admin)

    sort_key = SORT_MAP.get(request.GET.get("sort", ""), None)
    if sort_key:
        qs = qs.order_by(sort_key, "-id")
    else:
        qs = qs.order_by("-created_at", "-id")

    total = qs.count()
    cursor = request.GET.get("cursor")
    if cursor:
        try:
            created_at, pid = decode_cursor(cursor)
            qs = qs.filter(
                Q(created_at__lt=created_at)
                | Q(created_at=created_at, id__lt=pid)
            )
        except Exception:
            pass

    page_size = int(request.GET.get('page_size', 21))
    result = list(qs[:page_size])

    next_cursor = None
    if len(result) == page_size:
        last = result[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    data = [serialize_property(p) for p in result]

    return JsonResponse({
        "properties": data,
        "next_cursor": next_cursor,
        "has_next": next_cursor is not None,
        "total": total,
    })


def properties_view(request):
    user_is_admin = get_user_is_admin(request)

    status_choices = (
        list(PROPERTY_STATUS_CHOICES)
        if user_is_admin
        else []
    )

    active = {
        "search": request.GET.get("search", ""),
        "property_type": request.GET.get("property_type", ""),
        "purpose": request.GET.get("purpose", ""),
        "city": request.GET.get("city", ""),
        "area": request.GET.get("area", ""),
        "status": request.GET.get("status", ""),
        "min_price": request.GET.get("min_price", ""),
        "max_price": request.GET.get("max_price", ""),
        "min_bedrooms": request.GET.get("min_bedrooms", ""),
        "max_bedrooms": request.GET.get("max_bedrooms", ""),
        "min_bathrooms": request.GET.get("min_bathrooms", ""),
        "max_bathrooms": request.GET.get("max_bathrooms", ""),
        "furnished": request.GET.get("furnished", ""),
        "serviced": request.GET.get("serviced", ""),
        "shared": request.GET.get("shared", ""),
        "school": request.GET.get("school", ""),
        "sort": request.GET.get("sort", ""),
        "amenities": request.GET.getlist("amenities"),
    }

    areas_map = {}  
    for area in Area.objects.select_related("city").order_by("name"):
        areas_map.setdefault(area.city_id, []).append({"id": area.id, "name": area.name})

    active_city_id = int(active["city"]) if active["city"].isdigit() else None
    active_areas   = areas_map.get(active_city_id, []) if active_city_id else []

    context = {
        "page_title":     "Available Properties",
        "user_is_admin":  user_is_admin,
        "property_types": PropertyType.objects.all(),
        "status_choices": status_choices,
        "amenity_choices": Amenity.objects.all(),
        "schools":        School.objects.order_by("name"),
        "cities":         City.objects.all().order_by("name"),
        "active_areas":   active_areas,  
        "areas_map_json": areas_map,     
        "active":         active,
    }

    return render(request, "properties.html", context)


@require_http_methods(["GET"])
def areas_by_city_api(request):
    city_id = request.GET.get("city", "")
    if not city_id.isdigit():
        return JsonResponse({"areas": []})

    areas = list(
        Area.objects
        .filter(city_id=int(city_id))
        .order_by("name")
        .values("id", "name")
    )
    return JsonResponse({"areas": areas})


@login_required
def delete_property_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, agent__user=request.user)

    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def update_property_status(request, property_id):
    """Update property status (owner only)"""
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id, agent__user=request.user)

        new_status = request.POST.get('status')

        if new_status in dict(PROPERTY_STATUS_CHOICES):
            property_obj.status = new_status
            property_obj.save()
            messages.success(request, f'Property status updated to {property_obj.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status value.')

        return redirect('property_detail', property_id=property_id)

    return redirect('property_detail', property_id=property_id)


@login_required
@require_http_methods(["POST", "GET"])
def save_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    saved, created = SavedProperty.objects.get_or_create(
        user=request.user, property=property_obj
    )
    if not created:
        saved.delete()
        action = "removed"
    else:
        action = "saved"

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.method == "POST":
        return JsonResponse({"action": action})

    if action == 'removed':
        messages.success(request, "Property removed from saved properties")
    else:
        messages.success(request, "Property added to saved properties")

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def saved_properties_view(request):
    saved = (
        SavedProperty.objects
        .filter(user=request.user)
        .select_related(
            'property',
            'property__location',
            'property__location__area',
            'property__location__area__city',
            'property__location__area__city__state',
            'property__property_type',
            'property__school',
        )
        .prefetch_related(
            'property__images',
            'property__property_amenities__amenity',
        )
    )

    context = {
        'saved_properties': [
            {'property': {**serialize_property(s.property)}, "saved_id": s.id, "created_at": s.created_at}
            for s in saved
        ],
        'page_title': 'Saved Properties',
    }

    return render(request, 'tenant/saved_properties.html', context)


@login_required
def book_property_visit(request, property_id):
    """Handle property visit booking"""
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id)

        if property_obj.agent.user == request.user:
            messages.error(request, 'You cannot book a visit to your own property.')
            return redirect('property_detail', property_id=property_id)

        if property_obj.status != 'available':
            messages.error(request, 'This property is not available for viewing.')
            return redirect('property_detail', property_id=property_id)

        visit_date = request.POST.get('visit_date')
        visit_time = request.POST.get('visit_time')
        notes = request.POST.get('notes', '')

        try:
            visit_date_obj = datetime.strptime(visit_date, '%Y-%m-%d').date()
            if visit_date_obj < timezone.now().date():
                messages.error(request, 'Visit date cannot be in the past.')
                return redirect('property_detail', property_id=property_id)
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('property_detail', property_id=property_id)

        existing_visit = PropertyVisit.objects.filter(
            property=property_obj,
            visitor=request.user,
            status='pending',
            visit_date=visit_date
        ).exists()

        if existing_visit:
            messages.warning(request, 'You already have a pending visit request for this date.')
            return redirect('property_detail', property_id=property_id)

        PropertyVisit.objects.create(
            property=property_obj,
            visitor=request.user,
            visit_date=visit_date,
            visit_time=visit_time,
            notes=notes,
            status='pending'
        )

        messages.success(request, f'Visit booked successfully for {visit_date} at {visit_time}. The property owner will be notified.')
        return redirect('property_detail', property_id=property_id)

    return redirect('property_detail', property_id=property_id)


@login_required
def manage_bookings_view(request):
    """View to manage property bookings for owners"""
    try:
        bookings = PropertyVisit.objects.filter(property__agent__user=request.user).select_related(
            'property', 'visitor'
        ).order_by('-created_at')

        pending_count = bookings.filter(status='pending').count()
        confirmed_count = bookings.filter(status='confirmed').count()
        declined_count = bookings.filter(status='declined').count()
        completed_count = bookings.filter(status='completed').count()
        cancelled_count = bookings.filter(status='cancelled').count()

        context = {
            'bookings': bookings,
            'pending_count': pending_count,
            'confirmed_count': confirmed_count,
            'declined_count': declined_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'total_count': bookings.count(),
            'page_title': 'Manage Bookings',
        }

        return render(request, 'manage_bookings.html', context)

    except Exception as e:
        messages.error(request, f'Error loading bookings: {str(e)}')
        return redirect('dashboard')


@login_required
def update_booking_status(request, booking_id):
    """Update booking status"""
    try:
        booking = get_object_or_404(PropertyVisit, id=booking_id, property__agent__user=request.user)

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'confirm':
                booking.status = 'confirmed'
            elif action == 'decline':
                booking.status = 'declined'
            elif action == 'complete':
                booking.status = 'completed'
            elif action == 'cancel':
                booking.status = 'cancelled'

            booking.owner_response = request.POST.get('response_message', '')
            booking.save()

            messages.success(request, f'Booking {action}d successfully!')

        return redirect('manage_bookings')

    except Exception as e:
        messages.error(request, f'Error updating booking: {str(e)}')
        return redirect('manage_bookings')


@login_required
def my_bookings_view(request):
    """View for tenants to see their booking requests"""
    bookings = PropertyVisit.objects.filter(
        visitor=request.user
    ).select_related('property').order_by('-created_at')

    context = {
        'bookings': bookings,
        'page_title': 'My Bookings'
    }

    return render(request, 'tenant/my_bookings.html', context)


@login_required
def submit_report(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = property_obj.agent.user
            report.property = property_obj
            report.save()
            messages.success(request, 'Report submitted. Admin will review shortly.')
            return redirect('property_detail', property_id=property_id)
    else:
        form = ReportForm()

    return render(request, 'report_modal.html', {'form': form, 'property': property_obj})


@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.user_type == 'admin')
def admin_reports_view(request):
    reports = Report.objects.select_related('reporter', 'reported_user', 'property').order_by('-created_at')
    return render(request, 'admin/reports.html', {'reports': reports, 'page_title': 'Reports'})


@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.user_type == 'admin')
def admin_report_action(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('note', '')

        if action == 'deactivate':
            reported = report.reported_user
            reported.is_active = False
            reported.save()

            report.status = 'resolved'
            report.admin_action = f'Account deactivated. {note}'
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.save()
            messages.success(request, 'User account deactivated and report marked resolved.')

        elif action == 'dismiss':
            report.status = 'dismissed'
            report.admin_action = note
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.save()
            messages.success(request, 'Report dismissed.')

        return redirect('admin_reports')

    return redirect('admin_reports')


@login_required
@require_http_methods(["GET"])
def property_bookings_api(request, property_id):
    """API endpoint to get bookings for a specific property"""
    try:
        bookings = PropertyVisit.objects.filter(property__id=property_id)

        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'visitor_name': booking.visitor.get_full_name() or booking.visitor.username,
                'visitor_email': booking.visitor.email,
                'visitor_phone': booking.visitor.userprofile.phone_number if hasattr(booking.visitor, 'userprofile') else None,
                'visit_date': booking.visit_date.strftime('%Y-%m-%d') if booking.visit_date else None,
                'visit_time': booking.visit_time,
                'status': booking.status,
                'status_display': booking.get_status_display(),
                'notes': booking.notes,
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else None,
                'owner_response': booking.owner_response,
            })

        return JsonResponse({
            'success': True,
            'bookings': bookings_data,
            'total': len(bookings_data)
        })

    except Property.DoesNotExist:
        return JsonResponse({'error': 'Property not found or access denied'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def admin_dashboard_view(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)

    if user_profile.user_type != 'admin':
        return redirect('dashboard')

    context = {
        'page_title': 'Admin Dashboard',
        'total_users': User.objects.count(),
        'total_properties': Property.objects.count(),
    }

    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users_view(request):
    users = User.objects.all().select_related('userprofile')

    user_type = request.GET.get('user_type', '')
    if user_type:
        users = users.filter(userprofile__user_type=user_type)

    status = request.GET.get('status', '')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)

    pending_applications = AgentApplication.objects.filter(
        status='pending'
    ).select_related('user', 'user__userprofile').order_by('-created_at')

    context = {
        'page_title': 'Manage Users',
        'users': users_page,
        'total_users': User.objects.count(),
        'agents_count': UserProfile.objects.filter(user_type='agent').count(),
        'tenants_count': UserProfile.objects.filter(user_type='tenant').count(),
        'admins_count': UserProfile.objects.filter(user_type='admin').count(),
        'pending_applications': pending_applications,
        'pending_applications_count': pending_applications.count(),
    }

    return render(request, 'admin/users.html', context)


@login_required
def check_username_api(request):
    """API endpoint to check if a username exists"""
    username = request.GET.get('username', '').strip()

    if not username:
        return JsonResponse({'exists': False})

    try:
        user = User.objects.get(username=username)
        return JsonResponse({
            'exists': True,
            'username': user.username,
            'full_name': user.get_full_name() or None,
            'user_type': user.userprofile.user_type if hasattr(user, 'userprofile') else None
        })
    except User.DoesNotExist:
        return JsonResponse({'exists': False})


@login_required
@user_passes_test(is_admin)
def admin_properties_view(request):
    """Admin view to manage all properties"""
    regular_properties = Property.objects.filter(school_id__isnull=True).select_related(
        'agent', "location", "location__area__city", "location__area", "property_type",
    ).prefetch_related("images", "property_amenities__amenity")
    
    student_properties = Property.objects.filter(school_id__isnull=False).select_related(
        'agent', "location", "location__area__city", "location__area", "school", "property_type",
    ).prefetch_related("images", "property_amenities__amenity")

    context = {
        'page_title': 'Manage Properties',
        'regular_properties': regular_properties,
        'student_properties': student_properties,
    }

    return render(request, 'admin/properties.html', context)


@login_required
@user_passes_test(is_admin)
def admin_settings_view(request):
    """Admin view for site settings"""
    if request.method == 'POST':
        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_settings')

    context = {
        'page_title': 'Site Settings',
        'total_users': User.objects.count(),
        'total_properties': Property.objects.count(),
        'last_updated': timezone.now(),
    }

    return render(request, 'admin/settings.html', context)


@login_required
@user_passes_test(is_admin)
def update_user_status(request, user_id):
    """Admin update user status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        action = request.POST.get('action')

        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'User {user.username} deactivated.')
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.username} activated.')
        elif action == 'make_admin':
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.user_type = 'admin'
            profile.save()
            messages.success(request, f'User {user.username} is now an admin.')

        return redirect('admin_users')

    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def update_property_status_admin(request, property_id):
    """Admin update property status"""
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id)
        status = request.POST.get('status')

        if status in dict(PROPERTY_STATUS_CHOICES):
            property_obj.status = status
            property_obj.save()
            messages.success(request, f'Property status updated to {property_obj.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status value.')

        return redirect('admin_properties')

    return redirect('admin_properties')


def property_detail_view(request, property_id):
    property_obj = get_object_or_404(
        Property.objects.select_related(
            "agent", "location", "location__area__city", "location__area", "school", "property_type",
        ).prefetch_related(
            "images", "property_amenities__amenity",
        ),
        id=property_id,
    )

    user = request.user
    session_key = f"viewed_property_{property_id}"

    if not request.session.get(session_key):
        Property.objects.filter(id=property_id).update(views=F("views") + 1)
        request.session[session_key] = True

    is_owner = user.is_authenticated and user == property_obj.agent.user

    is_saved = False
    if user.is_authenticated:
        is_saved = SavedProperty.objects.filter(user=user, property=property_obj).exists()

    amenities = [p.amenity for p in property_obj.property_amenities.all()]
    images = property_obj.images.all()
    recommendations = get_property_recommendations(property_obj)
    today = timezone.now().date()

    context = {
        "property": property_obj,
        "agent": property_obj.agent,
        "all_images": images,
        "amenities": amenities,
        "is_owner": is_owner,
        "is_saved": is_saved,
        "today": today,
        "recommendations": recommendations,
    }

    return render(request, "property_detail.html", context)


@login_required
@user_passes_test(is_admin)
def admin_messages_view(request):
    """Admin view to manage messages"""
    messages_list = AdminMessage.objects.all().order_by('-created_at')

    status = request.GET.get('status', '')
    if status == 'active':
        messages_list = messages_list.filter(is_active=True)
    elif status == 'inactive':
        messages_list = messages_list.filter(is_active=False)

    active_count = AdminMessage.objects.filter(is_active=True).count()
    total_count = AdminMessage.objects.count()
    total_users = User.objects.count()

    paginator = Paginator(messages_list, 10)
    page = request.GET.get('page', 1)
    messages_page = paginator.get_page(page)

    context = {
        'page_title': 'Manage Messages',
        'messages': messages_page,
        'active_count': active_count,
        'total_count': total_count,
        'total_users': total_users,
    }

    return render(request, 'admin/messages.html', context)


@login_required
@user_passes_test(is_admin)
def create_admin_message(request):
    if request.method == 'POST':
        form = AdminMessageForm(request.POST)
        if form.is_valid():
            AdminMessage.objects.create(
                title=form.cleaned_data['title'],
                message=form.cleaned_data['message'],
                message_type=form.cleaned_data['message_type'],
                is_active=form.cleaned_data.get('is_active', True),
                show_to_all=form.cleaned_data.get('show_to_all', True),
                show_to_agents=form.cleaned_data.get('show_to_agents', True),
                show_to_tenants=form.cleaned_data.get('show_to_tenants', True),
                start_date=form.cleaned_data.get('start_date') or timezone.now(),
                end_date=form.cleaned_data.get('end_date'),
            )
            messages.success(request, 'Message created successfully!')
            return redirect('admin_messages')
    else:
        form = AdminMessageForm()

    context = {
        'page_title': 'Create Message',
        'form': form,
    }

    return render(request, 'admin/create_message.html', context)


@login_required
@user_passes_test(is_admin)
def edit_admin_message(request, message_id):
    """Edit an existing admin message"""
    message_obj = get_object_or_404(AdminMessage, id=message_id)

    if request.method == 'POST':
        form = AdminMessageForm(request.POST)
        if form.is_valid():
            message_obj.title = form.cleaned_data['title']
            message_obj.message = form.cleaned_data['message']
            message_obj.message_type = form.cleaned_data['message_type']
            message_obj.is_active = form.cleaned_data.get('is_active', True)
            message_obj.show_to_all = form.cleaned_data.get('show_to_all', True)
            message_obj.show_to_agents = form.cleaned_data.get('show_to_agents', True)
            message_obj.show_to_tenants = form.cleaned_data.get('show_to_tenants', True)
            message_obj.start_date = form.cleaned_data.get('start_date') or timezone.now()
            message_obj.end_date = form.cleaned_data.get('end_date')
            message_obj.save()

            messages.success(request, 'Message updated successfully!')
            return redirect('admin_messages')
    else:
        initial_data = {
            'title': message_obj.title,
            'message': message_obj.message,
            'message_type': message_obj.message_type,
            'is_active': message_obj.is_active,
            'show_to_all': message_obj.show_to_all,
            'show_to_agents': message_obj.show_to_agents,
            'show_to_tenants': message_obj.show_to_tenants,
        }

        if message_obj.start_date:
            initial_data['start_date'] = message_obj.start_date.strftime('%Y-%m-%dT%H:%M')
        if message_obj.end_date:
            initial_data['end_date'] = message_obj.end_date.strftime('%Y-%m-%dT%H:%M')

        form = AdminMessageForm(initial=initial_data)

    context = {
        'page_title': 'Edit Message',
        'form': form,
        'message': message_obj,
    }

    return render(request, 'admin/edit_message.html', context)


@login_required
@user_passes_test(is_admin)
def toggle_admin_message(request, message_id):
    """Toggle message active status"""
    if request.method == 'POST':
        message_obj = get_object_or_404(AdminMessage, id=message_id)
        message_obj.is_active = not message_obj.is_active
        message_obj.save()

        status = "activated" if message_obj.is_active else "deactivated"
        messages.success(request, f'Message {status} successfully!')

    return redirect('admin_messages')


@login_required
@user_passes_test(is_admin)
def delete_admin_message(request, message_id):
    """Delete an admin message"""
    if request.method == 'POST':
        message_obj = get_object_or_404(AdminMessage, id=message_id)
        message_obj.delete()
        messages.success(request, 'Message deleted successfully!')

    return redirect('admin_messages')


def get_active_messages(request):
    """Get active messages for the current user (API endpoint)"""
    if request.user.is_authenticated:
        active_messages = []
        for message in AdminMessage.objects.filter(is_active=True):
            if message.should_show_to_user(request.user):
                active_messages.append({
                    'id': message.id,
                    'title': message.title,
                    'message': message.message,
                    'type': message.message_type,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
                })

        return JsonResponse({'messages': active_messages})

    return JsonResponse({'messages': []})


@csrf_exempt
@login_required
def dismiss_admin_message(request):
    """Handle dismissing admin messages"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            session_key = f'dismissed_message_{message_id}'
            request.session[session_key] = True
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@require_http_methods(["POST"])
def property_request(request):
    def to_int(val):
        try:
            return int(val) if val else None
        except (ValueError, TypeError):
            return None

    amenities = list(request.POST.getlist('amenities'))
    cities = list(request.POST.getlist('cities'))

    obj = Inquiry.objects.create(
        user=request.user,
        property_type_id=to_int(request.POST.get('property_type', '')),
        purpose=request.POST.get('purpose', ''),
        budget_min=to_int(request.POST.get('budget_min')),
        budget_max=to_int(request.POST.get('budget_max')),
        bedrooms_min=to_int(request.POST.get('bedrooms_min')),
        bedrooms_max=to_int(request.POST.get('bedrooms_max')),
        bathrooms_min=to_int(request.POST.get('bathrooms_min')),
        bathrooms_max=to_int(request.POST.get('bathrooms_max')),
        furnished=request.POST.get("furnished") == "true",
        shared=request.POST.get("shared") == "true",
        serviced=request.POST.get("serviced") == "true",
        notes=request.POST.get('notes', '').strip(),
    )

    for a in amenities:
        InquiryAmenity.objects.create(amenity_id=a, inquiry=obj)
    for c in cities:
        InquiryCity.objects.create(city_id=c, inquiry=obj)

    if request.POST.get("school"):
        school = get_object_or_404(School, id=request.POST.get('school'))
        obj.school = school
        obj.save()
        
    threading.Thread(
        target=_notify_matching_agents,
        args=(obj.id,),
        daemon=True,
    ).start()

    messages.success(request, "Request Sent!\nOur team will review your requirements and get back to you.")
    return JsonResponse({'ok': True})


def get_details(request):
    schools = [
        {
            "id": int(p.id),
            "name": str(p.name),
            "short_name": str(p.short_name),
            "area": str(p.location.area.name) if p.location and p.location.area else None,
            "city": str(p.location.area.city.name) if p.location and p.location.area.city else None,
            "state": str(p.location.area.city.state.name)
            if p.location and p.location.area.city and p.location.area.city.state
            else None,
        }
        for p in School.objects.select_related("location__area__city__state")
    ]

    ptypes = [
        (int(p.id), str(p.display_name))
        for p in PropertyType.objects.all()
    ]

    cities = [
        (int(p.id), str(p.name).capitalize())
        for p in City.objects.all()
    ]

    amenities = [
        (int(p.id), str(p.display_name), str(p.icon))
        for p in Amenity.objects.all()
    ]

    purpose_choices = [{'value': v, 'label': l} for v, l in PURPOSE_CHOICES]

    return JsonResponse({
        "property_type_choices": ptypes,
        "amenity_choices": amenities,
        "purpose_choices": purpose_choices,
        "cities": cities,
        "schools": schools,
    }, safe=True)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    data = json.loads(request.body)

    message = data.get("message")
    m_type = data.get("type")
    if message:
        if m_type == "success":
            messages.success(request, message)
        elif m_type == "info":
            messages.info(request, message)
        elif m_type == "error":
            messages.error(request, message)

    return JsonResponse({})


@login_required
def dashboard_requests(request):
    response_qs = (
        InquiryResponse.objects
        .select_related('agent', 'property', 'property__location__area__city')
        .prefetch_related('property__images')
        .order_by('-created_at')
    )
 
    inquiries = list(
        Inquiry.objects
        .filter(user=request.user)
        .select_related('school', 'property_type')
        .prefetch_related(
            Prefetch('inquires_responses', queryset=response_qs, to_attr='prefetched_responses'),
            'inquiries_city__city',
            'inquiry_amenities__amenity',
        )
        .order_by('-created_at')
    )
 
    context = {
        'page_title': 'My Requests',
        'inquiries':  inquiries,
    }
    return render(request, 'auth/dashboard_requests.html', context)


@login_required
@require_http_methods(["POST"])
def close_inquiry(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, id=inquiry_id, user=request.user)
    inquiry.closed = True
    inquiry.save(update_fields=['closed'])
    return redirect('dashboard_requests')


@login_required
@require_http_methods(["POST"])
def mark_responses_opened(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, id=inquiry_id, user=request.user)
    inquiry.inquires_responses.filter(opened=False).update(opened=True)
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(["POST"])
def mark_response_opened(request, response_id):
    InquiryResponse.objects.filter(id=response_id).update(opened=True)
    return JsonResponse({'ok': True})


def _require_agent(request):
    """Return AgentProfile or None."""
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.agent_profile
    except AgentProfile.DoesNotExist:
        return None


@login_required
@user_passes_test(is_admin)
def review_agent_application(request, application_id):
    application = get_object_or_404(AgentApplication, id=application_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '')

        if action == 'approve':
            application.approve(request.user)
            messages.success(request, f'{application.user.username} approved as agent.')
        elif action == 'reject':
            application.reject(request.user, rejection_reason)
            messages.success(request, f'Application from {application.user.username} rejected.')
        else:
            messages.error(request, 'Invalid action.')
            return redirect('admin_users')

        status_label = 'Declined' if action == 'reject' else 'Approved'
        type = 'application_denied' if action == 'reject' else 'application_approved'
        Notification.notify_user(
            userid=application.user.id,
            type='application_reviewed',
            message=f"Your agent application request has been {status_label}",
        )

    return redirect('admin_users')

@login_required
def agent_inquiries(request):
    agent = _require_agent(request)
    if not agent:
        return redirect('dashboard')

    base_qs        = agent.get_inquiry_queryset()
    active_purpose = request.GET.get('purpose', '') or agent.preferred_purpose or ''
    active_types   = [int(t) for t in request.GET.getlist('types') if t.isdigit()]

    filtered = base_qs
    if active_purpose:
        filtered = filtered.filter(purpose=active_purpose)
    if active_types:
        filtered = filtered.filter(property_type_id__in=active_types)

    # filtered = filtered.select_related('user', 'school', 'property_type').prefetch_related(
    #     Prefetch(
    #         'inquires_responses',
    #         queryset=InquiryResponse.objects.filter(agent=request.user)
    #             .select_related('property', 'property__location__area__city')
    #             .prefetch_related('property__images'),
    #         to_attr='my_responses',
    #     ),
    #     'inquiries_city__city',
    #     'inquiry_amenities__amenity',
    # )
    

    paginator = Paginator(filtered, 15)
    page      = request.GET.get('page', 1)
    inquiries = paginator.get_page(page)  

    agent_properties = (
        Property.objects
        .filter(agent__user=request.user, status='available')
        .select_related('location__area__city')
        .prefetch_related(Prefetch('images', queryset=PropertyImage.objects.order_by('order')))
        .order_by('-created_at')
    )

    preferred_type_ids = list(
        agent.preferred_types.values_list('type_id', flat=True)
    )

    context = {
        'page_title':         'Client Requests',
        'agent':              agent,
        'inquiries':          inquiries,      
        'paginator':          paginator,
        'active_purpose':     active_purpose,
        'active_types':       active_types,
        'preferred_type_ids': preferred_type_ids,
        'type_choices':       PropertyType.objects.all().order_by('name'),
        'purpose_choices':    PURPOSE_CHOICES,
        'city_choices':       City.objects.all().order_by('name'),
        'agent_properties':   agent_properties,
        'assigned_city_ids':   list(
            agent.assigned_cities.values_list('city_id', flat=True)
        ),
        'assigned_school_ids': list(
            AgentAssignedSchools.objects.filter(agent=agent)
            .values_list('school_id', flat=True)
        ),
        'school_choices': School.objects.select_related('location__area').order_by('name'),
        
    }
    return render(request, 'agent/agent_inquiries.html', context)

@login_required
@require_http_methods(["POST"])
def agent_respond_inquiry(request, inquiry_id):
    agent = _require_agent(request)
    if not agent:
        return JsonResponse({'error': 'forbidden'}, status=403)

    inquiry = get_object_or_404(Inquiry, id=inquiry_id, closed=False)
    property_id = request.POST.get('property_id')

    property_ = get_object_or_404(
        Property,
        id=property_id,
        agent=agent,
        status='available',
    )

    _, created = InquiryResponse.objects.get_or_create(
        agent=agent,
        inquiry=inquiry,
        property=property_,
    )
    
    Notification.notify_user(
        userid=inquiry.user.id, 
        type="inquiry_response",
        message=f"New response to your {inquiry}",
        related_id=inquiry.id,
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'created': created,
            'message': 'Response submitted.' if created else 'Already responded with this property.',
        })
    return redirect('agent_inquiries')


@login_required
def agent_update_preferences(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)
 
    agent = getattr(request.user, 'agent_profile', None)
    if not agent:
        return JsonResponse({'ok': False, 'message': 'Not an agent'}, status=403)
 
    agent.preferred_purpose = request.POST.get('preferred_purpose') or None
    agent.save(update_fields=['preferred_purpose'])
 
    type_ids = [int(t) for t in request.POST.getlist('preferred_types') if t.isdigit()]
    AgentPreferredTypes.objects.filter(agent=agent).delete()
    AgentPreferredTypes.objects.bulk_create([
        AgentPreferredTypes(agent=agent, type_id=tid) for tid in type_ids
    ])
 
    city_ids = [int(c) for c in request.POST.getlist('assigned_cities') if c.isdigit()]
    AgentAssignedCities.objects.filter(agent=agent).delete()
    AgentAssignedCities.objects.bulk_create([
        AgentAssignedCities(agent=agent, city_id=cid) for cid in city_ids
    ])
 
    school_ids = [int(s) for s in request.POST.getlist('assigned_schools') if s.isdigit()]
    AgentAssignedSchools.objects.filter(agent=agent).delete()
    AgentAssignedSchools.objects.bulk_create([
        AgentAssignedSchools(agent=agent, school_id=sid) for sid in school_ids
    ])
 
    return JsonResponse({'ok': True})
 
 
@login_required
def mark_welcome_seen(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)
    
    profile = request.user.agent_profile
    if not profile.has_seen_welcome:
        profile.has_seen_welcome = True
        profile.save(update_fields=['has_seen_welcome'])
    return JsonResponse({'ok': True})

 
@login_required
def mark_profile_shared(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    agent = _require_agent(request)
    agent.has_shared_profile = True
    agent.save(update_fields=['has_shared_profile'])
    return JsonResponse({'ok': True})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def verify_agent(request, agent_id):
    agent = get_object_or_404(AgentProfile, id=agent_id)
    agent.verified = True
    agent.save()
    return JsonResponse({'ok': True})


@login_required
def agent_properties_view(request):
    properties = (
        Property.objects
        .filter(agent__user=request.user)
        .select_related("location__area__city", "location__area", "school", "agent")
        .prefetch_related("images", "property_amenities__amenity")
    )

    context = {
        'properties': [serialize_property(p) for p in properties],
        'page_title': 'Agent Properties',
    }

    return render(request, 'agent/agent_properties.html', context)

@login_required
@user_passes_test(is_agent)
def agent_profile_edit(request):
    agent = request.user.agent_profile
 
    if request.method == 'POST':
        form = AgentProfileUpdateForm(request.POST, instance=agent)
 
        if form.is_valid():
            
            image_file = request.FILES.get('image')
            logo_file = request.FILES.get('logo')
            if image_file:
                try:
                    result = cloudinary.uploader.upload(
                        image_file,
                        folder=f'abuja_rentals/agents/{agent.id}/',
                        public_id=f'profile_{agent.id}',
                        overwrite=True,
                        resource_type="image",
                        transformation=[{'width': 400, 'height': 400, 'crop': 'fill'}],
                        
                    )
                    agent.image = result['public_id']
                except Exception as e:
                    messages.error(request, 'Failed to upload profile image. Please check your connection.')
                    return redirect('agent_profile_edit')

            if logo_file:
                try:
                    result = cloudinary.uploader.upload(
                        logo_file,
                        folder=f'abuja_rentals/agents/{agent.id}/',
                        public_id=f'logo_{agent.id}',
                        overwrite=True,
                        resource_type="image",
                        transformation=[{'width': 800, 'height': 300, 'crop': 'fill'}],
                    )
                    agent.logo = result['public_id']
                except Exception as e:
                    messages.error(request, 'Failed to upload logo. Please check your connection.')
                    return redirect('agent_profile_edit')
 
            raw_phones = request.POST.get('other_phones_json', '[]')
            try:
                phones = [p.strip() for p in json.loads(raw_phones) if p.strip()]
            except (json.JSONDecodeError, TypeError):
                phones = []
            agent.other_phones = phones
 
            area_id = request.POST.get('location_area') or None
            address = request.POST.get('location_address', '').strip()
 
            if area_id or address:
                if agent.location_id:
                    loc = agent.location
                    loc.area_id = area_id
                    loc.address = address
                    loc.save(update_fields=['area_id', 'address'])
                else:
                    loc = Location.objects.create(area_id=area_id, address=address)
                    agent.location = loc
            else:
                agent.location = None
 
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('agent_profile_edit')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = AgentProfileUpdateForm(instance=agent)
 
    context = {
        'page_title': 'Edit Profile',
        'form':       form,
        'agent':      agent,
        'user':       request.user,
        'areas':     Area.objects.all().order_by('city'),
    }
    return render(request, 'agent/agent_profile_edit.html', context)


@login_required
@user_passes_test(is_agent)
@require_http_methods(["POST"])
def request_agent_verification(request):
    agent = request.user.agent_profile

    if agent.verified:
        messages.info(request, 'Your profile is already verified.')
        return redirect('agent_profile_edit')

    admin_ids = User.objects.filter(
        userprofile__user_type='admin'
    ).values_list('id', flat=True)

    for admin_id in admin_ids:
        Notification.notify_user(
            userid=admin_id,
            type='application_request',
            message=f"Agent {request.user.get_full_name() or request.user.username} has requested profile verification.",
        )

    messages.success(request, 'Verification request sent. \nOur team will review your profile shortly.')
    return redirect('agent_profile_edit')

@login_required
def agent_apply(request):
    user = request.user
    profile = request.user.userprofile
    if not profile.email_is_verified:
        messages.info(request, "Please verify your email")
        return redirect('verify_otp')

    profile_data = {
        'phone_number': profile.phone_number,
        'whatsapp_number': profile.whatsapp_number,
        'profile_picture': profile.profile_picture,
        'address': profile.address,
        'bio': profile.bio
    }
    missing = [k for k, v in profile_data.items() if not v]

    if missing:
        labels = ', '.join(k.replace('_', ' ').capitalize() for k in missing)
        messages.info(request, f"Missing ({labels}) in your userprofile please complete the form")
        return redirect('profile')

    if user.userprofile.user_type == 'agent':
        return redirect('agent_inquiries')

    existing = getattr(user, 'agent_application', None)
    if existing and existing.status == 'rejected':
        existing.delete()
        existing = None

    if existing:
        return render(request, 'agent/agent_apply.html', {
            'page_title': 'Agent Application',
            'application': existing,
            'cities': City.objects.all(),
        })

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        experience = request.POST.get('experience', '').strip()
        areas_of_focus = request.POST.getlist('areas_of_focus')

        errors = {}
        if not phone:
            errors['phone'] = 'Phone number is required.'
        if not experience:
            errors['experience'] = 'Please describe your experience.'

        if errors:
            return render(request, 'agent/agent_apply.html', {
                'page_title': 'Become an Agent',
                'errors': errors,
                'post': request.POST,
                'cities': City.objects.all(),
            })

        AgentApplication.objects.create(
            user=user,
            phone=phone,
            bio=bio,
            experience=experience,
            areas_of_focus=areas_of_focus,
        )
        return redirect('agent_apply')

    return render(request, 'agent/agent_apply.html', {
        'page_title': 'Become an Agent',
        'cities': City.objects.all(),
    })


@login_required
@require_http_methods(["POST"])
def agent_application_withdraw(request):
    """Allow user to withdraw a pending application."""
    try:
        application = request.user.agent_application
        if application.status == 'pending':
            application.delete()
    except AgentApplication.DoesNotExist:
        pass
    return redirect('agent_apply')

def agent_public_profile(request, agent_id):
    agent = get_object_or_404(
        AgentProfile.objects.select_related(
            'user', 'location__area__city', 'location__area'
        ),
        id=agent_id,
        user__is_active=True,
    )
 
    properties = (
        Property.objects
        .filter(agent=agent, status='available')
        .select_related('location__area', 'property_type')
        .prefetch_related(
            Prefetch('images', queryset=PropertyImage.objects.order_by('order'))
        )
        .order_by('-created_at')
    )
 
    area_ids = (
        properties
        .exclude(location__area__isnull=True)
        .values_list('location__area_id', flat=True)
        .distinct()
    )
    areas = Area.objects.filter(id__in=area_ids).order_by('name')
 
    context = {
        'page_title':     f"{agent.name if agent.name else agent.user.get_full_name()} — Agent Profile",
        'agent':          agent,
        'properties':     [serialize_property(p) for p in properties],
        'property_types': PropertyType.objects.filter(
            id__in=properties.values_list('property_type_id', flat=True).distinct()
        ),
        'areas':          areas,
    }
    return render(request, 'agent/agent_public_profile.html', context)
 
 
 
RESIDENTIAL_TYPES = ['apartment', 'flat', 'house', 'duplex', 'bungalow', 'mansion', 'studio', 'room', 'self_contain']
 
def is_residential(type_name):
    n = (type_name or '').lower()
    return any(r in n for r in RESIDENTIAL_TYPES)
 
def is_agent(user):
    return (user.is_authenticated
            and hasattr(user, 'userprofile')
            and user.userprofile.user_type == 'agent')
 
 
def _base_context():
    areas_map = {}
    for area in Area.objects.select_related('city').order_by('name'):
        areas_map.setdefault(area.city_id, []).append({
            'id':   area.id,
            'name': area.name.capitalize(),
        })
 
    schools_data = []
    for school in School.objects.select_related('location__area__city').order_by('name'):
        area_id = city_id = None
        if school.location and school.location.area:
            area_id = school.location.area_id
            city_id = school.location.area.city_id
        schools_data.append({
            'id':      school.id,
            'name':    f"{school.name} ({school.short_name})",
            'area_id': area_id,
            'city_id': city_id,
        })
 
    return {
        'property_types':  PropertyType.objects.all(),
        'cities':          City.objects.all().order_by('name'),
        'amenities':       Amenity.objects.all(),
        'areas_map_json':  json.dumps(areas_map),
        'schools_json':    json.dumps(schools_data),
    }
 
 
def _save_location(post, existing=None):
    """Create or update a Location from POST data."""
    area_id = post.get('area') or None
    address = post.get('address', '').strip()
    lat     = post.get('latitude')  or None
    lng     = post.get('longitude') or None
 
    if existing:
        existing.area_id   = area_id
        existing.address   = address
        existing.latitude  = lat
        existing.longitude = lng
        existing.save(update_fields=['area_id', 'address', 'latitude', 'longitude'])
        return existing
 
    return Location.objects.create(
        area_id=area_id, address=address, latitude=lat, longitude=lng
    )
 
 
@login_required
@user_passes_test(is_agent)
def add_property_view(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        
        if form.is_valid():
            property_obj        = form.save(commit=False)
            property_obj.agent  = request.user.agent_profile
            property_obj.status = 'available'
 
            type_obj = property_obj.property_type
            if type_obj and not is_residential(type_obj.name):
                property_obj.bedrooms = property_obj.bathrooms = property_obj.area_sqft = None
 
            property_obj.location  = _save_location(request.POST)
            property_obj.school_id = request.POST.get('school') or None
            property_obj.save()
 
            for amenity_id in request.POST.getlist('amenities'):
                PropertyAmenity.objects.get_or_create(
                    property=property_obj, amenity_id=amenity_id)
 
            for i, img in enumerate(request.FILES.getlist('images')):
                p = PropertyImage.objects.create(
                    property=property_obj, image=img, order=i)
 
            messages.success(request, 'Listing submitted for review.')
            return redirect('agent_properties')
 
        messages.error(request, 'Please fix the errors below.')
    else:
        form = PropertyForm()
 
    return render(request, 'agent/add_property.html', {
        **_base_context(),
        'form':               form,
        'selected_amenities': [],
        'page_title':         'List a Property',
        'initial_city_id':    '',
        'initial_area_id':    '',
        'initial_school_id':  '',
    })
 
 
@login_required
@user_passes_test(is_agent)
def edit_property_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, agent__user=request.user)
 
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            property_obj = form.save(commit=False)
 
            type_obj = property_obj.property_type
            if type_obj and not is_residential(type_obj.name):
                property_obj.bedrooms = property_obj.bathrooms = property_obj.area_sqft = None
 
            property_obj.location  = _save_location(request.POST, property_obj.location)
            property_obj.school_id = request.POST.get('school') or None
            property_obj.save()
 
            delete_ids = request.POST.getlist('delete_images')
            if delete_ids:
                PropertyImage.objects.filter(
                    id__in=delete_ids, property=property_obj).delete()
 
            start = property_obj.images.count()
            for i, img in enumerate(request.FILES.getlist('images')):
                PropertyImage.objects.create(
                    property=property_obj, image=img, order=start + i)
 
            PropertyAmenity.objects.filter(property=property_obj).delete()
            for amenity_id in request.POST.getlist('amenities'):
                PropertyAmenity.objects.create(
                    property=property_obj, amenity_id=amenity_id)
 
            messages.success(request, 'Listing updated.')
            return redirect('agent_properties')
 
        messages.error(request, 'Please fix the errors below.')
    else:
        form = PropertyForm(instance=property_obj)

    selected_amenities = list(
        PropertyAmenity.objects.filter(property=property_obj)
        .values_list('amenity_id', flat=True)
    )

    initial_area_id = initial_city_id = ''
    if property_obj.location and property_obj.location.area:
        initial_area_id = property_obj.location.area_id
        initial_city_id = property_obj.location.area.city_id

    return render(request, 'agent/edit_property.html', {
        **_base_context(),
        'form':               form,
        'property':           property_obj,
        'selected_amenities': selected_amenities,
        'status_choices':     AGENT_PROPERTY_STATUS_CHOICES,
        'page_title':         'Edit listing',
        'initial_city_id':    initial_city_id,
        'initial_area_id':    initial_area_id,
        'initial_school_id':  property_obj.school_id or '',
    })
    
    
from django.views.generic import TemplateView


class SchoolsView(TemplateView):
    template_name = 'schools.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agent_qs = (
            AgentAssignedSchools.objects
            .select_related(
                'agent',
                'agent__user',
            )
            .order_by('-agent__verified', 'agent__user__first_name')
        )

        schools = (
            School.objects
            .select_related('location__area__city')
            .prefetch_related(
                Prefetch('assigned_schools', queryset=agent_qs, to_attr='assigned_agents'),
            )
            .annotate(
                listing_count=Count(
                    'properties',  
                    filter=__import__('django.db.models', fromlist=['Q']).Q(
                        properties__status='available'
                    ),
                    distinct=True,
                )
            )
            .order_by('name')
        )

        ctx['schools'] = schools
        return ctx


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_properties']   = round(Property.objects.filter(status='available').count(), -2)
        ctx['neighbourhood_count'] = City.objects.count()
        ctx['tenant_count']       = (
            UserProfile.objects.filter(user_type='tenant').count()
        )
        return ctx


OPEN_ROLES = [
    {
        'title': 'Full-Stack Django Developer',
        'department': 'Engineering',
        'location': 'Abuja (Hybrid)',
        'type': 'Full-time',
        'summary': 'Build and maintain the core platform — from property search to agent dashboards.',
        'url': 'mailto:careers@abujarentals.com?subject=Application: Full-Stack Django Developer',
    },
]


class CareersView(TemplateView):
    template_name = 'careers.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['open_roles'] = OPEN_ROLES
        return ctx


RENTER_FAQS = []


class FAQView(TemplateView):
    template_name = 'faq.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['renter_faqs'] = RENTER_FAQS
        return ctx


class TermsView(TemplateView):
    template_name = 'terms.html'
    
    
def _notify_matching_agents(inquiry_id):
    try:
        inquiry = Inquiry.objects.select_related('property_type').get(id=inquiry_id)
        city_ids = inquiry.inquiries_city.values_list('city_id', flat=True)
        agents   = (
            AgentProfile.objects
            .filter(assigned_cities__city_id__in=city_ids)
            .select_related('user')
            .distinct()
        )

        if hasattr(inquiry, 'school') and hasattr(inquiry.school, 'id'):
            if inquiry.school:
                school_id = inquiry.school.id
                agents.append(
                    AgentProfile.objects
                    .filter(assigned_schools__school_id=school_id)
                    .select_related('user')
                    .distinct()
                )
        
        notifications = [
            Notification(
                user=agent.user,
                type='new_inquiry',
                message=f"New request for a {inquiry.property_type or 'property'} in your area",
                related_id=inquiry_id,
            )
            for agent in agents
        ]
        
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"_notify_matching_agents failed: {e}")


