from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q, F, DecimalField
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
from django.core import signing

from datetime import datetime
from decimal import Decimal

from .models import (UserProfile, Property, SavedProperty, PropertyVisit, AdminMessage, Report,  SavedProperty, PropertyVisit, Inquiry)
from .forms import (CustomUserCreationForm, LoginForm, ProfileUpdateForm, PropertyForm, PropertySearchForm, AdminMessageForm, ReportForm)
from .recommendations import get_property_recommendations

import random
import json






def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin'

def home(request):
        
    # Try to use featured properties if set, otherwise sample available properties
    featured_qs = Property.objects.filter(status='available', is_featured=True)
    if featured_qs.exists():
        featured_properties = featured_qs.order_by('?')[:3]
    else:
        featured_properties = Property.objects.filter(status='available').order_by('views')[:3]

    total_properties = Property.objects.filter(status='available').count()

    context = {
        'featured_properties': featured_properties,
        'total_properties': total_properties,
        'page_title': 'Home',
    }
    
    type_choices = dict(Property.PROPERTY_TYPE_CHOICES)
    types_qs = list(Property.objects.filter(status='available').values_list('property_type', flat=True).distinct())
    random.shuffle(types_qs)
    categories = []
    for t in types_qs:
        label = type_choices.get(t, t.replace('_', ' ').title())
        count = Property.objects.filter(property_type=t, status='available').count()
        categories.append({'code': t, 'label': label, 'count': f"{ (count // 100) * 100 }"})

    context['categories'] = categories[:9]
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
        if form.is_valid():
            
            user = form.save()

            # Double-check that user_type was saved correctly
            try:
                profile = UserProfile.objects.get(user=user)
                # Force update if needed
                selected_type = "tenant"
                if selected_type and profile.user_type != selected_type:
                    profile.user_type = selected_type
                    profile.save()
                    print(f"DEBUG View: Updated user_type to {selected_type}")
            except Exception as e:
                print(f"DEBUG View: Error checking profile: {e}")
                # Create profile if it doesn't exist
                UserProfile.objects.create(
                    user=user,
                    user_type=form.cleaned_data.get('user_type', 'tenant'),
                    phone_number=form.cleaned_data.get('phone_number', ''),
                    address=form.cleaned_data.get('address', ''),
                    bio=form.cleaned_data.get('bio', '')
                )

            # Auto-login after signup
            login(request, user)
            request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            return redirect('home')
        else:
            # Show form errors for debugging
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
        # Admin dashboard logic
        # Get platform fees from transactions
        total_platform_fees = 0
        

        # Add pending properties count
        pending_properties = Property.objects.filter(status='pending').count()
        
        context = {
            'page_title': 'Admin Dashboard',
            'total_users': UserProfile.objects.count(),
            'total_properties': Property.objects.count(),
            'total_platform_fees': total_platform_fees,
            'pending_properties': pending_properties,
        }
        
    elif user_profile.user_type == 'owner':
        total_properties = Property.objects.filter(owner=user).count()
        available_properties = Property.objects.filter(owner=user, status='available').count()
        
        # Calculate total value of properties
        total_value = Property.objects.filter(owner=user).aggregate(
            total=Sum('price')
        )['total'] or 0
        
        # Calculate potential earnings as price * rent_duration_months for rental properties
        potential_agg = Property.objects.filter(
            owner=user,
            purpose='rent'
        ).exclude(status='draft').aggregate(
            total=Sum(F('price') * F('rent_duration_months'), output_field=DecimalField())
        )
        potential_earnings = potential_agg['total'] or Decimal('0.00')
        
        # Get recent properties
        recent_properties = Property.objects.filter(owner=user).order_by('-created_at')[:3]
        
        context = {
            'page_title': 'Agent Dashboard',
            'total_properties': total_properties,
            'available_properties': available_properties,
            'total_value': total_value,
            'potential_earnings': potential_earnings,
            'recent_properties': recent_properties,
        }
    
    elif user_profile.user_type == 'tenant':
        # Tenant dashboard logic
        # Calculate saved properties
        saved_properties_count = user.saved_properties.count() if hasattr(user, 'saved_properties') else 0
        
        # Calculate booking count
        booking_count = user.bookings.count() if hasattr(user, 'bookings') else 0
    
        context = {
            'page_title': 'Tenant Dashboard',
            'saved_properties_count': saved_properties_count,
            'booking_count': booking_count,
        }
        
    else:  
        context = {
            'page_title': 'Dashboard',
        }
    
    return render(request, 'auth/dashboard.html', context)

def encode_cursor(created_at, id):
    return signing.dumps({
        "created_at": created_at.isoformat(),
        "id": id
    })

def decode_cursor(cursor):
    data = signing.loads(cursor)
    return (
        data["created_at"],
        data["id"]
    )

def get_user_is_admin(request):
    """Helper to avoid repeating admin-check logic."""
    if request.user.is_authenticated:
        try:
            return request.user.userprofile.user_type == 'admin'
        except Exception:
            pass
    return False


def get_properties(request):
    search_form = PropertySearchForm(request.GET or None)
    user_is_admin = get_user_is_admin(request)

    if user_is_admin:
        properties = Property.objects.all()
    else:
        properties = Property.objects.filter(status='available')

    if search_form.is_valid():
        if search_form.cleaned_data.get('property_type'):
            properties = properties.filter(property_type=search_form.cleaned_data['property_type'])
        if search_form.cleaned_data.get('purpose'):
            properties = properties.filter(purpose=search_form.cleaned_data['purpose'])
        if search_form.cleaned_data.get('city'):
            properties = properties.filter(city=search_form.cleaned_data['city'])
        if search_form.cleaned_data.get('status') and user_is_admin:
            properties = properties.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('search'):
            search_term = search_form.cleaned_data['search']
            properties = properties.filter(
                Q(title__icontains=search_term) |
                Q(city__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        if search_form.cleaned_data.get("amenities"):
            
            amenities = request.GET.getlist('amenities')
            for amenity in amenities:
                properties = properties.filter(amenities__contains=amenity)

    properties = properties.order_by("-created_at", "-id")
    cursor = request.GET.get("cursor")

    if cursor:
        created_at, id = decode_cursor(cursor)
        properties = properties.filter(
            Q(created_at__lt=created_at) |
            Q(created_at=created_at, id__lt=id)
        )

    page_size = 21
    result = list(properties[:page_size])

    next_cursor = None
    if len(result) == page_size:
        last = result[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    data = [
        {
            "title": p.title,
            "main_image": p.main_image if p.main_image else None,
            "price": p.price,
            "purpose": p.purpose,
            "id": p.id,
            "city": p.city,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "area_sqft": p.area_sqft,
            "description": p.description,
            "owner": p.owner.id,
        }
        for p in result
    ]
    
    print(len(properties))

    return JsonResponse({
        "properties": data,
        "next_cursor": next_cursor,
        "has_next": next_cursor is not None,
        "total": len(properties)
    })


def properties_view(request):
    user_is_admin = get_user_is_admin(request)

    purposes = "All Purposes"
    status = ""
    ptype = "All Types"

    for v in Property.PURPOSE_CHOICES:
        purposes += ',' + v[0]

    for v in Property.STATUS_CHOICES:
        status += ',' + v[0]

    for v in Property.PROPERTY_TYPE_CHOICES:
        ptype += ',' + v[0]

    search_form_options = {
        "search": "",
        "purpose": purposes,
        "status": status,
        "city": 'All Locations,Gwarinpa,Jahi,Wuse,Wuye,Apo,Dutse,Kubwa,Bwari,Gwagwalada,Lugbe,Kuje,Kwali,Abaji',
        "property_type": ptype,
    }

    search_form = PropertySearchForm(request.GET or None)
    search_form_data = {}

    if search_form.is_valid():
        if search_form.cleaned_data.get('property_type'):
            search_form_data["ptype"] = str(search_form.cleaned_data.get('property_type'))
        if search_form.cleaned_data.get('purpose'):
            search_form_data["purpose"] = str(search_form.cleaned_data.get('purpose'))
        if search_form.cleaned_data.get('city'):
            search_form_data["city"] = str(search_form.cleaned_data.get('city'))
        if search_form.cleaned_data.get('status') and user_is_admin:
            search_form_data["status"] = str(search_form.cleaned_data.get('status'))
        if search_form.cleaned_data.get('search'):
            search_form_data["search"] = str(search_form.cleaned_data.get('search'))
        if search_form.cleaned_data.get('amenities'):
            search_form_data["amenities"] = str(search_form.cleaned_data.get('amenities'))

    context = {
        'search_form_options': search_form_options,
        'search_form_data': search_form_data,
        'page_title': 'Available Properties',
        'property_type_choices':  Property.PROPERTY_TYPE_CHOICES,
        'amenity_choices':Property.AMENITY_CHOICES
    }

    return render(request, 'properties.html', context)




def owner_can_publish_more(user):
    """Return True if the owner is allowed to publish another property.

    Verified owners (user.userprofile.email_verified) have no limit.
    Unverified owners may have up to 3 non-draft properties.
    """
    try:
        if getattr(user, 'userprofile', None) and user.userprofile.email_verified:
            return True
    except Exception:
        # If something unexpected, default to restrictive behavior
        return False

    current_count = Property.objects.filter(owner=user).exclude(status='draft').count()
    return current_count < 3

@login_required
def add_property_view(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            # New properties are created with status 'pending' (pending review)
            # Enforce posting limit for unverified owners (count non-draft properties)
            if not owner_can_publish_more(request.user):
                messages.error(request, 'You have reached the maximum of 3 properties. Verify your account to post more.')
                return render(request, 'add_property.html', {'form': form, 'page_title': 'Add New Property'})

            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.status = 'pending'
            property_obj.save()
            
            messages.success(request, 'Property submitted for review. An admin will review your listing shortly.')
            return redirect('properties')
    else:
        form = PropertyForm()
    
    context = {
        'form': form,
        'page_title': 'Add New Property'
    }
    
    return render(request, 'add_property.html', context)

@login_required
def edit_property_view(request, property_id):
    
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            # If changing from draft -> published (non-draft), enforce limit for unverified owners
            new_status = form.cleaned_data.get('status') or property_obj.status
            was_draft = (property_obj.status == 'draft')
            will_publish = (new_status != 'draft') and was_draft

            if will_publish and not owner_can_publish_more(request.user):
                messages.error(request, 'Publishing this property would exceed your 3-property limit. Verify your account to publish more.')
                return render(request, 'edit_property.html', {'form': form, 'property': property_obj, 'page_title': 'Edit Property'})

            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('properties')
        else:
            # Debug: print form errors
            print("Form errors:", form.errors)
    else:
        form = PropertyForm(instance=property_obj)
    
    context = {
        'form': form,
        'property': property_obj,
        'page_title': 'Edit Property'
    }
    
    return render(request, 'edit_property.html', context)

@login_required
def delete_property_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('properties')
    
    return redirect('properties')


@login_required
def book_property_visit(request, property_id):
    """
    Handle property visit booking
    """
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Ensure user is not the owner
        if property_obj.owner == request.user:
            messages.error(request, 'You cannot book a visit to your own property.')
            return redirect('property_detail', property_id=property_id)
        
        # Ensure property is available
        if property_obj.status != 'available':
            messages.error(request, 'This property is not available for viewing.')
            return redirect('property_detail', property_id=property_id)
        
        visit_date = request.POST.get('visit_date')
        visit_time = request.POST.get('visit_time')
        notes = request.POST.get('notes', '')
        
        # Here you would create a PropertyVisit model instance
        # For now, just show success message
        messages.success(request, f'Visit booked successfully for {visit_date} at {visit_time}. The property owner will be notified.')
        
        return redirect('property_detail', property_id=property_id)
    
    return redirect('property_detail', property_id=property_id)

@login_required
def contact_property_owner(request, property_id):
    """
    Handle contact form submission to property owner
    """
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Ensure user is not the owner
        if property_obj.owner == request.user:
            messages.error(request, 'You cannot contact yourself.')
            return redirect('property_detail', property_id=property_id)
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        # Here you would send an email or create a message record
        # For now, just show success message
        messages.success(request, 'Your message has been sent to the property owner. They will contact you soon.')
        
        return redirect('property_detail', property_id=property_id)
    
    return redirect('property_detail', property_id=property_id)

@login_required
def update_property_status(request, property_id):
    """
    Update property status (owner only)
    """
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
        
        new_status = request.POST.get('status')
        
        if new_status in dict(Property.STATUS_CHOICES):
            property_obj.status = new_status
            property_obj.save()
            messages.success(request, f'Property status updated to {property_obj.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status value.')
        
        return redirect('property_detail', property_id=property_id)
    
    return redirect('property_detail', property_id=property_id)

@login_required
def save_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property=property_obj
    )
    
    if not created:
        saved_property.delete()
        messages.success(request, 'Property removed from saved list.')
    else:
        messages.success(request, 'Property saved successfully!')
    
    # Redirects the user back to the previous page they were viewing
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def saved_properties_view(request):
    """View saved properties for the current user"""
    saved_properties = SavedProperty.objects.filter(user=request.user).select_related('property')
    
    context = {
        'saved_properties': saved_properties,
        'page_title': 'Saved Properties'
    }
    
    return render(request, 'saved_properties.html', context)

@login_required
def book_property_visit(request, property_id):
    """
    Handle property visit booking
    """
    if request.method == 'POST':
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Ensure user is not the owner
        if property_obj.owner == request.user:
            messages.error(request, 'You cannot book a visit to your own property.')
            return redirect('property_detail', property_id=property_id)
        
        # Ensure property is available
        if property_obj.status != 'available':
            messages.error(request, 'This property is not available for viewing.')
            return redirect('property_detail', property_id=property_id)
        
        visit_date = request.POST.get('visit_date')
        visit_time = request.POST.get('visit_time')
        notes = request.POST.get('notes', '')
        
        # Validate date is not in the past
        try:
            visit_date_obj = datetime.strptime(visit_date, '%Y-%m-%d').date()
            if visit_date_obj < timezone.now().date():
                messages.error(request, 'Visit date cannot be in the past.')
                return redirect('property_detail', property_id=property_id)
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('property_detail', property_id=property_id)
        
        # Check for existing pending visits for same property by same user
        existing_visit = PropertyVisit.objects.filter(
            property=property_obj,
            visitor=request.user,
            status='pending',
            visit_date=visit_date
        ).exists()
        
        if existing_visit:
            messages.warning(request, 'You already have a pending visit request for this date.')
            return redirect('property_detail', property_id=property_id)
        
        # Create PropertyVisit instance
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
        # Get all property visits for properties owned by current user
        bookings = PropertyVisit.objects.filter(property__owner=request.user).select_related(
            'property', 'visitor'
        ).order_by('-created_at')
        
        # Calculate counts for each status
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
        booking = get_object_or_404(PropertyVisit, id=booking_id, property__owner=request.user)
        
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
            report.reported_user = property_obj.owner
            report.property = property_obj
            report.save()
            messages.success(request, 'Report submitted. Admin will review shortly.')
            return redirect('property_detail', property_id=property_id)
    else:
        form = ReportForm()

    # If reached via GET (should be modal/form submission), render modal template
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
        # Check if property exists and belongs to user
        property = Property.objects.get(id=property_id, owner=request.user)
        
        # Get bookings
        bookings = property.bookings.all().order_by('-created_at')
        
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

@login_required
@require_http_methods(["GET"])
def booking_details_api(request, booking_id):
    """API endpoint to get booking details"""
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if user owns the property
        if booking.property.owner != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = {
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
            'property_title': booking.property.title,
            'property_address': f"{booking.property.address or booking.property.city}",
        }
        
        return JsonResponse({'success': True, **data})
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def booking_respond_api(request, booking_id):
    """API endpoint to respond to a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if user owns the property
        if booking.property.owner != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = json.loads(request.body)
        action = data.get('action')
        response_message = data.get('response_message', '')
        
        if action not in ['confirm', 'decline']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # Update booking
        booking.status = action + 'ed'  # 'confirmed' or 'declined'
        booking.owner_response = response_message
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Booking {action}ed successfully'
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def booking_complete_api(request, booking_id):
    """API endpoint to mark booking as complete"""
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if user owns the property
        if booking.property.owner != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        booking.status = 'completed'
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking marked as completed'
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# In your admin views.py
def admin_dashboard_view(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)
    
    if user_profile.user_type != 'admin':
        # Redirect non-admin users
        return redirect('dashboard')

    # Calculate total platform fees from all admin transactions
    total_platform_fees = 0
  
    # Get platform fees from sold properties
    sold_properties = Property.objects.filter(status='sold')
    completed_sales_count = sold_properties.count()
    
    # Calculate total platform fees from sold properties (5% of sale price)
    total_sales_value = sold_properties.aggregate(total=Sum('sale_price'))['total'] or 0
    calculated_platform_fees = total_sales_value * Decimal('0.05')
    
    context = {
        'page_title': 'Admin Dashboard',
        'total_users': User.objects.count(),
        'total_properties': Property.objects.count(),
        'total_platform_fees': total_platform_fees,
        'calculated_platform_fees': calculated_platform_fees,
        'completed_sales_count': completed_sales_count,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users_view(request):
    """Admin view to manage users"""
    users = User.objects.all().select_related('userprofile')
    
    # Filtering
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
    
    # Statistics
    agents_count = UserProfile.objects.filter(user_type='agent').count()
    tenants_count = UserProfile.objects.filter(user_type='tenant').count()
    admins_count = UserProfile.objects.filter(user_type='admin').count()
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'page_title': 'Manage Users',
        'users': users_page,
        'total_users': User.objects.count(),
        'agents_count': agents_count,
        'tenants_count': tenants_count,
        'admins_count': admins_count,
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
    """Admin view to manage all properties including student properties"""
    # Get regular properties
    regular_properties = Property.objects.all().select_related('owner')
    
    # Count pending student properties
    
    context = {
        'page_title': 'Manage Properties',
        'regular_properties': regular_properties,
    }
    
    return render(request, 'admin/properties.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings_view(request):
    """Admin view for site settings"""
    if request.method == 'POST':
        # Handle settings updates here
        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_settings')
    
    # Get statistics for display
    total_users = User.objects.count()
    total_properties = Property.objects.count()
    total_platform_fees = Property.objects.aggregate(
        total=Sum('platform_fee')
    )['total'] or Decimal('0.00')
    
    context = {
        'page_title': 'Site Settings',
        'total_users': total_users,
        'total_properties': total_properties,
        'total_platform_fees': total_platform_fees,
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
        
        if status in dict(Property.STATUS_CHOICES):
            property_obj.status = status
            property_obj.save()
            messages.success(request, f'Property status updated to {property_obj.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status value.')
        
        return redirect('admin_properties')
    
    return redirect('admin_properties')

        
        
        # In your views.py

def property_detail_view(request, property_id):
    """View property details"""
    
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.refresh_from_db()
    user = request.user
    
    session_key = f'viewed_property_{property_id}'
    if not request.session.get(session_key):
        property_obj.views += 1
        property_obj.save()
        request.session[session_key] = True
    
    # Check if user is owner
    is_owner = user.is_authenticated and user == property_obj.owner
    
    # Check if property is saved by user
    is_saved = False
    if user.is_authenticated:
        is_saved = SavedProperty.objects.filter(user=user, property=property_obj).exists()
    
    platform_fee = Decimal('0.00')
    
    if user.is_authenticated and not is_owner:
        platform_fee = property_obj.price * Decimal('0.05')
    
    # Get additional images
    additional_images = property_obj.images
    
    today = timezone.now().date()
    recommendations = get_property_recommendations(property_obj)

    
    context = {
        'property': property_obj,
        'additional_images': additional_images,
        'all_images': [property_obj.main_image] + additional_images if additional_images else [property_obj.main_image],
        'is_owner': is_owner,
        'is_saved': is_saved,
        'today': today,
        'platform_fee': platform_fee,
        'recommendations': recommendations
    }
    
    return render(request, 'property_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_messages_view(request):
    """Admin view to manage messages"""
    messages_list = AdminMessage.objects.all().order_by('-created_at')
    
    # Filtering
    status = request.GET.get('status', '')
    if status == 'active':
        messages_list = messages_list.filter(is_active=True)
    elif status == 'inactive':
        messages_list = messages_list.filter(is_active=False)
    
    # Statistics
    active_count = AdminMessage.objects.filter(is_active=True).count()
    total_count = AdminMessage.objects.count()
    total_users = User.objects.count()
    
    # Pagination
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
            message_obj.show_to_owners = form.cleaned_data.get('show_to_owners', True)
            message_obj.show_to_tenants = form.cleaned_data.get('show_to_tenants', True)
            message_obj.start_date = form.cleaned_data.get('start_date') or timezone.now()
            message_obj.end_date = form.cleaned_data.get('end_date')
            message_obj.save()
            
            messages.success(request, 'Message updated successfully!')
            return redirect('admin_messages')
    else:
        # Pre-populate the form with existing data
        initial_data = {
            'title': message_obj.title,
            'message': message_obj.message,
            'message_type': message_obj.message_type,
            'is_active': message_obj.is_active,
            'show_to_all': message_obj.show_to_all,
            'show_to_owners': message_obj.show_to_owners,
            'show_to_tenants': message_obj.show_to_tenants,
        }
        
        # Format dates for datetime-local input
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
            
            # Store in session that user has dismissed this message
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

    amenities = ','.join(request.POST.getlist('amenities'))

    obj = Inquiry.objects.create(
        user          = request.user,
        full_name     = request.POST.get('full_name', '').strip(),
        phone         = request.POST.get('phone', '').strip(),
        email         = request.POST.get('email', '').strip(),
        property_type = request.POST.get('property_type', ''),
        purpose       = request.POST.get('purpose', ''),
        city          = request.POST.get('city', ''),
        budget_min    = to_int(request.POST.get('budget_min')),
        budget_max    = to_int(request.POST.get('budget_max')),
        bedrooms_min  = to_int(request.POST.get('bedrooms_min')),
        bedrooms_max  = to_int(request.POST.get('bedrooms_max')),
        bathrooms_min = to_int(request.POST.get('bathrooms_min')),
        bathrooms_max = to_int(request.POST.get('bathrooms_max')),
        amenities     = amenities,
        notes         = request.POST.get('notes', '').strip(),
    )
    
    print(obj)

    return JsonResponse({'ok': True})



def get_details(request):
    return JsonResponse({
        'property_type_choices': list(Property.PROPERTY_TYPE_CHOICES),
        'amenity_choices':Property.AMENITY_CHOICES,
        'purpose_choices':Property.PURPOSE_CHOICES,
        'cities':Property.CITIES,
    })