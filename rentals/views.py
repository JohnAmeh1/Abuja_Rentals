from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, F, DecimalField
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models.functions import TruncMonth



from datetime import datetime
from decimal import Decimal

from .models import (UserProfile, Property, Transaction, SavedProperty, PropertyVisit, PropertyRental, AdminMessage, Report, StudentProperty, StudentPropertyRental, SavedProperty, PropertyVisit)
from .forms import (CustomUserCreationForm, LoginForm, ProfileUpdateForm, PropertyForm, PropertySearchForm, AdminMessageForm, ReportForm, StudentPropertyForm)
from .recommendations import get_property_recommendations

import random
import json






def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin'

def check_expired_rentals():
    """
    Check and update expired rentals and their property statuses.
    Call this function at key points where property status matters.
    """
    
    # Get all active rentals
    active_rentals = PropertyRental.objects.filter(is_active=True).select_related('property')
    
    for rental in active_rentals:
        # This will update rental status and property status if needed
        rental.check_and_update_status()

def home(request):
    
    check_expired_rentals()
    
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
    
    # Build categories list from DB (unique property_type values), randomized each load
    type_choices = dict(Property.PROPERTY_TYPE_CHOICES)
    types_qs = list(Property.objects.filter(status='available').values_list('property_type', flat=True).distinct())
    random.shuffle(types_qs)
    categories = []
    for t in types_qs:
        label = type_choices.get(t, t.replace('_', ' ').title())
        count = Property.objects.filter(property_type=t, status='available').count()
        categories.append({'code': t, 'label': label, 'count': f"{ (count // 100) * 100 }"})

    # Limit to 8 categories for display
    context['categories'] = categories[:8]
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
            
            # Try to authenticate
            user = authenticate(request, username=username, password=password)
            
            # If authentication fails with username, try with email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                
                # Set session expiry based on "remember me"
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                    
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
            # Debug: Check what user_type is being passed
            print(f"DEBUG View: user_type from form = {form.cleaned_data.get('user_type')}")
            
            user = form.save()

            # Double-check that user_type was saved correctly
            try:
                profile = UserProfile.objects.get(user=user)
                # Force update if needed
                selected_type = form.cleaned_data.get('user_type')
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
def student_properties(request):
    """List properties - different logic for agents vs students"""
    try:
        user_profile = request.user.userprofile
        is_agent = user_profile.user_type == 'agent'
        is_student = user_profile.user_type == 'student'
        is_admin = user_profile.user_type == 'admin'
    except:
        is_agent = False
        is_student = False
        is_admin = False
    
    # Get filter parameters directly from request.GET
    university_filter = request.GET.get('university', '')
    property_type_filter = request.GET.get('property_type', '')
    purpose_filter = request.GET.get('purpose', '')
    city_filter = request.GET.get('city', '')
    search_query = request.GET.get('search', '')
    
    if is_agent:
        # Agents see only their own properties (all statuses)
        properties = StudentProperty.objects.filter(created_by=request.user).order_by('-created_at')
        page_title = 'My Properties (Agent)'
    elif is_admin:
        # Admins see all properties
        properties = StudentProperty.objects.all().order_by('-created_at')
        page_title = 'All Properties (Admin)'
    elif is_student:
        # Students see available properties (approved by admin) and their own
        available_properties = StudentProperty.objects.filter(
            status='available'
        ).order_by('-created_at')
        
        my_properties = StudentProperty.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        # Combine both querysets
        properties = (available_properties | my_properties).distinct().order_by('-created_at')
        page_title = 'Available Properties'
    else:
        # Other user types see only available properties
        properties = StudentProperty.objects.filter(
            status='available'
        ).order_by('-created_at')
        page_title = 'Available Properties'
    
    # Apply filters
    if university_filter:
        properties = properties.filter(university=university_filter)
    
    if property_type_filter:
        properties = properties.filter(property_type=property_type_filter)
    
    if purpose_filter:
        properties = properties.filter(purpose=purpose_filter)
    
    if city_filter:
        properties = properties.filter(city__iexact=city_filter)
    
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(university__icontains=search_query)
        )
    
    # Additional filters for students viewing available properties
    if is_student and not search_query:
        # Students can filter by price
        max_price = request.GET.get('max_price')
        if max_price:
            try:
                max_price_decimal = Decimal(max_price)
                properties = properties.filter(price__lte=max_price_decimal)
            except:
                pass
        
        # Students can filter by amenities
        amenities_filter = request.GET.getlist('amenities')
        if amenities_filter:
            for amenity in amenities_filter:
                properties = properties.filter(amenities__icontains=amenity)
    
    # Pagination
    paginator = Paginator(properties, 12)
    page = request.GET.get('page', 1)
    
    try:
        properties_page = paginator.page(page)
    except PageNotAnInteger:
        properties_page = paginator.page(1)
    except EmptyPage:
        properties_page = paginator.page(paginator.num_pages)
    
    # Create a simple form-like dictionary for the template
    filter_values = {
        'university': university_filter,
        'property_type': property_type_filter,
        'purpose': purpose_filter,
        'city': city_filter,
        'search': search_query,
    }
    
    # Get dynamic choices for dropdowns
    university_choices = StudentProperty.UNIVERSITY_CHOICES
    property_type_choices = StudentProperty.PROPERTY_TYPE_CHOICES
    purpose_choices = StudentProperty.PURPOSE_CHOICES
    
    # Get unique cities from database
    try:
        cities = StudentProperty.objects.values_list('city', flat=True).distinct().order_by('city')
        city_choices = [(city, city.title()) for city in cities if city]
    except:
        city_choices = []
    
    context = {
        'properties': properties_page,
        'filter_values': filter_values,
        'page_title': page_title,
        'is_agent': is_agent,
        'is_student': is_student,
        'is_admin': is_admin,
        'user': request.user,
        # Add choices for dropdowns
        'university_choices': university_choices,
        'property_type_choices': property_type_choices,
        'purpose_choices': purpose_choices,
        'city_choices': city_choices,
    }
    
    return render(request, 'student/properties.html', context)

@login_required
@user_passes_test(is_admin)
def admin_student_properties(request):
    """Admin view of all student properties"""
    properties = StudentProperty.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        properties = properties.filter(status=status_filter)
    
    # Count pending properties
    pending_count = StudentProperty.objects.filter(status='pending').count()
    
    context = {
        'properties': properties,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'page_title': 'Student Properties Management',
    }
    
    return render(request, 'admin/student_properties.html', context)


@login_required
def student_property_detail(request, pk):
    """View student property details (separate from regular property detail)"""
    property = get_object_or_404(StudentProperty, pk=pk)
    
    # Increment view count
    property.increment_views()
    
    # Convert amenities string to list
    amenities_list = property.get_amenities_list()
    
    # Get additional images
    additional_images = []
    for i in range(1, 6):
        image_field = getattr(property, f'image_{i}', None)
        if image_field:
            additional_images.append(image_field)
    
    # Check if user is the creator
    is_owner = request.user == property.created_by
    
    # Calculate platform fee (2% for student properties)
    platform_fee = property.price * Decimal('0.02')
    
    context = {
        'property': property,
        'amenities_list': amenities_list,
        'additional_images': additional_images,
        'is_owner': is_owner,
        'is_admin': is_admin,
        'platform_fee': platform_fee,
        'page_title': property.title,
    }
    
    return render(request, 'student/student_property_detail.html', context)

@login_required
def create_property(request):
    """Create a new student property"""
    # Check if user is student or agent
    try:
        user_profile = request.user.userprofile
        is_agent = user_profile.user_type == 'agent'
        is_student = user_profile.user_type == 'student'
    except UserProfile.DoesNotExist:
        # Create user profile if it doesn't exist
        UserProfile.objects.create(user=request.user, user_type='student')
        is_agent = False
        is_student = True
    
    if request.method == 'POST':
        form = StudentPropertyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                property = form.save(commit=False)
                property.created_by = request.user
                
                # Set status based on user type
                if is_agent:
                    # Agents submit properties for admin review - status: pending
                    property.status = 'pending'
                    status_message = 'Property submitted for admin review. It will be visible to students once approved.'
                elif is_student:
                    # Check if this is a "Save as Draft" or "Publish" submission
                    if 'save_draft' in request.POST:
                        property.status = 'draft'
                        status_message = 'Property saved as draft.'
                    else:
                        # Students need admin approval too
                        property.status = 'pending'
                        status_message = 'Property submitted for admin review.'
                else:
                    # Other users (owners) - default to draft
                    property.status = 'draft'
                    status_message = 'Property saved as draft.'
                
                # Calculate fees if not already done in form
                price = form.cleaned_data.get('price')
                if price:
                    if not isinstance(price, Decimal):
                        price = Decimal(str(price))
                    
                    property.price = price
                    property.platform_fee = price * Decimal('0.02')
                    property.net_amount = price * Decimal('0.98')
                
                # Save the property
                property.save()
                
                # Handle amenities - form.cleaned_data['amenities'] should be a list of strings
                amenities_list = form.cleaned_data.get('amenities', [])
                if amenities_list:
                    property.set_amenities(amenities_list)
                    property.save()
                
                messages.success(request, status_message)
                return redirect('student_properties')
                
            except Exception as e:
                print(f"Error saving property: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating property: {str(e)}')
        else:
            # Debug form errors
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentPropertyForm()
    
    # Get amenities choices from the form (not hardcoded)
    # The form already has AMENITY_CHOICES defined, we don't need to pass them separately
    # But if you want to use them in template for custom display, extract them
    amenities = StudentPropertyForm.AMENITY_CHOICES
    
    context = {
        'form': form,
        'amenities': amenities,  # Pass the choices from the form
        'page_title': 'Create Property',
        'is_agent': is_agent,
        'is_student': is_student,
    }
    
    return render(request, 'student/createproperty.html', context)


@login_required
def edit_student_property(request, pk):
    """Edit a student property (renamed to avoid conflict with regular properties)"""
    property = get_object_or_404(StudentProperty, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = StudentPropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            property = form.save(commit=False)
            
            # Handle university field
            university = form.cleaned_data.get('university')
            if university:
                property.university = university
            
            property.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('student_property_detail', pk=property.pk)
    else:
        # Initialize form with university data
        initial_data = {}
        if property.university:
            if property.university.startswith('custom_'):
                initial_data['university'] = 'other'
                initial_data['custom_university'] = property.university.replace('custom_', '')
            else:
                initial_data['university'] = property.university
        
        form = StudentPropertyForm(instance=property, initial=initial_data)
    
    return render(request, 'student/edit_student_property.html', {'form': form, 'property': property})


@login_required
def delete_student_property(request, pk):
    """Delete a student property (renamed to avoid conflict with regular properties)"""
    property = get_object_or_404(StudentProperty, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        property.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('student_properties')
    
    return render(request, 'student/confirm_delete.html', {'property': property})

@login_required
def toggle_featured(request, pk):
    """Toggle featured status of a property"""
    property = get_object_or_404(StudentProperty, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        property.is_featured = not property.is_featured
        property.save()
        
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'is_featured': property.is_featured
            })
        
        messages.success(request, f'Property {"marked as" if property.is_featured else "removed from"} featured!')
    
    return redirect('property_detail', pk=pk)




@login_required
@user_passes_test(lambda u: hasattr(u, 'userprofile') and u.userprofile.user_type == 'admin')
def approve_student_property(request, pk):
    """Admin approves a student property"""
    property = get_object_or_404(StudentProperty, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            property.status = 'available'
            property.published_at = timezone.now()
            # You could store admin notes in a separate field if needed
            # property.admin_notes = admin_notes
            property.save()
            messages.success(request, f'Property "{property.title}" has been approved and is now available to students.')
            
        elif action == 'reject':
            property.status = 'draft'
            # property.admin_notes = admin_notes
            property.save()
            messages.success(request, f'Property "{property.title}" has been rejected and returned to draft status.')
            
        elif action == 'delete':
            property_title = property.title
            property.delete()
            messages.success(request, f'Property "{property_title}" has been deleted.')
            
        return redirect('admin_properties')
    
    context = {
        'property': property,
        'page_title': f'Review: {property.title}',
    }
    
    return render(request, 'admin/approve_student_property.html', context)

@login_required
@user_passes_test(is_admin)
def review_student_property(request, pk):
    """Admin review and approval of student properties"""
    property = get_object_or_404(StudentProperty, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            property.status = 'available'
            property.save()
            messages.success(request, f'Property "{property.title}" has been approved and is now available.')
            
            # Optional: Notify the agent/creator
            # send_property_approved_notification(property)
            
        elif action == 'reject':
            property.status = 'draft'
            property.save()
            messages.success(request, f'Property "{property.title}" has been rejected and returned to draft status.')
            
        elif action == 'delete':
            property.delete()
            messages.success(request, f'Property "{property.title}" has been deleted.')
            
        return redirect('admin_properties')  # Or create a specific admin view
    
    context = {
        'property': property,
        'page_title': f'Review: {property.title}',
    }
    
    return render(request, 'admin/review_student_property.html', context)
# student/views.py ends here

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
    check_expired_rentals()

    if user_profile.user_type == 'admin':
        # Admin dashboard logic
        # Get platform fees from transactions
        total_platform_fees = 0
        

        # Add pending properties count
        pending_student_properties = StudentProperty.objects.filter(status='pending').count()
        
        context = {
            'page_title': 'Admin Dashboard',
            'total_users': UserProfile.objects.count(),
            'total_properties': Property.objects.count(),
            'total_platform_fees': total_platform_fees,
            'pending_student_properties': pending_student_properties,
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
            'page_title': 'Owner Dashboard',
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

        # Refresh rental statuses and compute active rentals with countdown
        all_rentals = PropertyRental.objects.filter(tenant=user)
        today = timezone.now().date()
        # Ensure expired rentals are flagged inactive
        for r in all_rentals:
            try:
                r.check_and_update_status()
            except Exception:
                # ignore any issues here to avoid breaking dashboard render
                pass

        active_rentals_qs = PropertyRental.objects.filter(tenant=user, is_active=True)
        active_rentals = []
        for r in active_rentals_qs:
            info = r.term_info(today=today)

            active_rentals.append({
                'rental': r,
                'total_days': info.get('total_days'),
                'starts_in': info.get('starts_in'),
                'days_passed': info.get('days_passed'),
                'days_remaining': info.get('days_remaining'),
                'expired_days': info.get('expired_days'),
                'renewal_allowed': info.get('renewal_allowed'),
                'status': info.get('status'),
            })

        context = {
            'page_title': 'Tenant Dashboard',
            'saved_properties_count': saved_properties_count,
            'booking_count': booking_count,
            'active_rentals': active_rentals,
        }
        
    elif user_profile.user_type == 'student':
        # ============ STUDENT DASHBOARD LOGIC ============
        saved_properties_count = user.saved_properties.count() if hasattr(user, 'saved_properties') else 0
        
        # Calculate booking count
        booking_count = user.bookings.count() if hasattr(user, 'bookings') else 0

        today = timezone.now().date()
        
        # Regular property rentals
        all_rentals = PropertyRental.objects.filter(tenant=user)
        for r in all_rentals:
            try:
                r.check_and_update_status()
            except Exception:
                pass

        active_rentals_qs = PropertyRental.objects.filter(tenant=user, is_active=True)
        active_rentals = []
        for r in active_rentals_qs:
            info = r.term_info(today=today)
            active_rentals.append({
                'rental': r,
                'type': 'regular',  # Mark as regular property
                'total_days': info.get('total_days'),
                'starts_in': info.get('starts_in'),
                'days_passed': info.get('days_passed'),
                'days_remaining': info.get('days_remaining'),
                'expired_days': info.get('expired_days'),
                'renewal_allowed': info.get('renewal_allowed'),
                'status': info.get('status'),
            })
        
        # Student property rentals
        all_student_rentals = StudentPropertyRental.objects.filter(tenant=user)
        for r in all_student_rentals:
            try:
                r.check_and_update_status()
            except Exception:
                pass

        active_student_rentals_qs = StudentPropertyRental.objects.filter(tenant=user, is_active=True)
        for r in active_student_rentals_qs:
            info = r.term_info(today=today)
            active_rentals.append({
                'rental': r,
                'type': 'student',  # Mark as student property
                'total_days': info.get('total_days'),
                'starts_in': info.get('starts_in'),
                'days_passed': info.get('days_passed'),
                'days_remaining': info.get('days_remaining'),
                'expired_days': info.get('expired_days'),
                'renewal_allowed': info.get('renewal_allowed'),
                'status': info.get('status'),
            })
        
        # Student-specific statistics
        student_friendly_properties = Property.objects.filter(
            Q(status='available'),
            Q(property_type__in=['apartment', 'house'])
        ).count()
        
        available_student_properties = StudentProperty.objects.filter(
            status='available'
        ).count()
        
        context = {
            'page_title': 'Student Dashboard',
            'saved_properties_count': saved_properties_count,
            'booking_count': booking_count,
            'active_rentals': active_rentals,  # This now includes both types
            'student_friendly_properties': student_friendly_properties,
            'available_student_properties': available_student_properties,
            'is_student': True,
        }

    elif user_profile.user_type == 'agent':
        # Agent dashboard logic - similar to owner but with agent-specific features
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
        
        # Agent-specific: get student-friendly properties count
        student_friendly_properties = Property.objects.filter(
            owner=user,
            status='available'
        ).count()
        
        context = {
            'page_title': 'Agent Dashboard',
            'total_properties': total_properties,
            'available_properties': available_properties,
            'total_value': total_value,
            'potential_earnings': potential_earnings,
            'recent_properties': recent_properties,
            'student_friendly_properties': student_friendly_properties,
        }
    
    else:  # agent or other user types
        context = {
            'page_title': 'Dashboard',
        }
    
    return render(request, 'auth/dashboard.html', context)


@login_required
def student_properties_view(request):
    """View properties filtered for student needs"""
    check_expired_rentals()
    
    # Base query for available properties
    properties = Property.objects.filter(status='available')
    
    # Student-specific filters
    # 1. Filter by price (students typically have lower budgets)
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            properties = properties.filter(price__lte=Decimal(max_price))
        except:
            pass
    
    # 2. Filter by property types suitable for students
    student_property_types = ['apartment', 'house', 'penthouse']
    properties = properties.filter(property_type__in=student_property_types)
    
    # 3. Filter by location near schools/universities (if you have location data)
    # This would depend on your location data structure
    
    # 4. Filter by amenities important for students
    amenities_filter = request.GET.getlist('amenities')
    if amenities_filter:
        # Assuming amenities are stored as comma-separated string
        for amenity in amenities_filter:
            properties = properties.filter(amenities__icontains=amenity)
    
    # Common student amenities to suggest
    student_amenities = [
        ('wifi', 'WiFi'),
        ('furnished', 'Furnished'),
        ('laundry', 'Laundry'),
        ('parking', 'Parking'),
        ('ac', 'Air Conditioning'),
        ('pet_friendly', 'Pet Friendly'),
    ]
    
    # Get saved properties for current user
    saved_property_ids = []
    if request.user.is_authenticated:
        saved_property_ids = SavedProperty.objects.filter(
            user=request.user
        ).values_list('property_id', flat=True)
    
    # Order by price (ascending - cheaper first for students)
    properties = properties.order_by('price')
    
    # Pagination
    paginator = Paginator(properties, 12)
    page = request.GET.get('page', 1)
    properties_page = paginator.get_page(page)
    
    context = {
        'properties': properties_page,
        'page_title': 'Student-Friendly Properties',
        'student_amenities': student_amenities,
        'saved_property_ids': list(saved_property_ids),
        'is_student_view': True,
    }
    
    return render(request, 'student/properties.html', context)

@login_required
def agent_student_properties_view(request):
    """View for agents to see their student-friendly properties"""
    user = request.user
    
    # Get agent's student-friendly properties
    agent_properties = AgentProperty.objects.filter(
        agent=user,
        is_student_friendly=True
    ).select_related('property').order_by('-created_at')
    
    # Get statistics
    total_student_properties = agent_properties.count()
    active_student_properties = agent_properties.filter(property__status='available').count()
    
    # Calculate total student discount value
    total_discount_value = 0
    for agent_prop in agent_properties:
        if agent_prop.property.status == 'available':
            discount_amount = agent_prop.property.price * (agent_prop.student_discount / 100)
            total_discount_value += discount_amount
    
    context = {
        'page_title': 'Student-Friendly Properties',
        'agent_properties': agent_properties,
        'total_student_properties': total_student_properties,
        'active_student_properties': active_student_properties,
        'total_discount_value': total_discount_value,
    }
    
    return render(request, 'agent/student_properties.html', context)


def owner_properties_view(request):
    """
    Public view for REGULAR properties (not student properties).
    Shows available properties to all users, and allows owners to see their own.
    """
    check_expired_rentals()
    
    search_form = PropertySearchForm(request.GET or None)
    
    # Determine which properties to show based on user role and filters
    is_owner_view = False
    user_is_admin = False

    if request.user.is_authenticated:
        try:
            if request.user.userprofile.user_type == 'admin':
                user_is_admin = True
        except Exception:
            user_is_admin = False

    # Admin sees all REGULAR properties (including pending)
    if user_is_admin:
        properties = Property.objects.all()
    else:
        # Check if owner wants to see their own properties
        if request.user.is_authenticated and getattr(request.user, 'userprofile', None) and request.user.userprofile.user_type == 'owner':
            show_my_properties = request.GET.get('my_properties', 'false')
            if show_my_properties == 'true':
                properties = Property.objects.filter(owner=request.user)
                is_owner_view = True
            else:
                properties = Property.objects.filter(status='available')
        else:
            properties = Property.objects.filter(status='available')
            
            
    if search_form.is_valid():
    
        if search_form.cleaned_data.get('property_type'):
            properties = properties.filter(property_type=search_form.cleaned_data['property_type'])
        if search_form.cleaned_data.get('purpose'):
            properties = properties.filter(purpose=search_form.cleaned_data['purpose'])
        if search_form.cleaned_data.get('city'):
            properties = properties.filter(city=search_form.cleaned_data['city'])
        if search_form.cleaned_data.get('status') and (is_owner_view or user_is_admin):
            properties = properties.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('search'):
            search_term = search_form.cleaned_data['search']
            properties = properties.filter(
                Q(title__icontains=search_term) | 
                Q(city__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        

    properties = properties.order_by('-created_at')
    total = len(properties)

    paginator = Paginator(properties, 21)   

    page_number = request.GET.get('page')
    properties = paginator.get_page(page_number)

    context = {
        'properties': properties,  
        'search_form': search_form,
        'page_title': 'My Properties' if is_owner_view else 'Available Properties',
        'is_owner_view': is_owner_view,
        'total': total
    }

    return render(request, 'owner/properties.html', context)




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
    # if request.user.userprofile.user_type != 'owner':
    if request.user.userprofile.user_type not in ['owner', 'agent', 'admin']: 
        messages.error(request, 'You must be a property owner to list properties.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            # New properties are created with status 'pending' (pending review)
            # Enforce posting limit for unverified owners (count non-draft properties)
            if not owner_can_publish_more(request.user):
                messages.error(request, 'You have reached the maximum of 3 properties. Verify your account to post more.')
                return render(request, 'owner/add_property.html', {'form': form, 'page_title': 'Add New Property'})

            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.status = 'pending'
            property_obj.save()
            
            messages.success(request, 'Property submitted for review. An admin will review your listing shortly.')
            return redirect('owner_properties')
    else:
        form = PropertyForm()
    
    context = {
        'form': form,
        'page_title': 'Add New Property'
    }
    
    return render(request, 'owner/add_property.html', context)

@login_required
def edit_property_view(request, property_id):
    if request.user.userprofile.user_type != 'owner':
        messages.error(request, 'You must be a property owner to edit properties.')
        return redirect('dashboard')
    
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
                return render(request, 'owner/edit_property.html', {'form': form, 'property': property_obj, 'page_title': 'Edit Property'})

            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('owner_properties')
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
    
    return render(request, 'owner/edit_property.html', context)

@login_required
def delete_property_view(request, property_id):
    if request.user.userprofile.user_type != 'owner':
        messages.error(request, 'You must be a property owner to delete properties.')
        return redirect('dashboard')
    
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('owner_properties')
    
    return redirect('owner_properties')


@login_required
def calculate_platform_fee(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            price = float(request.GET.get('price', 0))
            platform_fee = price * 0.05
            net_amount = price - platform_fee
            
            return JsonResponse({
                'success': True,
                'platform_fee': f'{platform_fee:,.2f}',
                'net_amount': f'{net_amount:,.2f}'
            })
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid price'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})



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
    """Save or unsave a property"""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if property is already saved
    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property=property_obj
    )
    
    if not created:
        # Property was already saved, so unsave it
        saved_property.delete()
        messages.success(request, 'Property removed from saved list.')
    else:
        messages.success(request, 'Property saved successfully!')
    
    return redirect('property_detail', property_id=property_id)


@login_required
def saved_properties_view(request):
    """View saved properties for the current user"""
    saved_properties = SavedProperty.objects.filter(user=request.user).select_related('property')
    
    context = {
        'saved_properties': saved_properties,
        'page_title': 'Saved Properties'
    }
    
    return render(request, 'tenant/saved_properties.html', context)


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
        
        return render(request, 'owner/manage_bookings.html', context)
        
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
    return render(request, 'owner/report_modal.html', {'form': form, 'property': property_obj})


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

        # Refund action: credit reporter and debit owner where possible
        if action == 'refund':
            amount = report.property.price if report.property and report.property.price else Decimal('0.00')

            if amount > 0:
                Transaction.objects.create( transaction_type='refund', amount=amount, description=f'Refund for property {report.property.title if report.property else "N/A"}', related_property_id=(report.property.id if report.property else None), related_property_title=(report.property.title if report.property else ''))


            report.status = 'resolved'
            report.admin_action = f'Refund of ₦{amount} processed. {note}'
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.save()
            messages.success(request, 'Refund processed and report marked resolved.')

        elif action == 'deactivate':
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



def mark_property_as_sold(property_id, sale_price):
    property = Property.objects.get(id=property_id)
    
    # Mark property as sold
    property.status = 'sold'
    property.save()
    
    # Calculate platform fee (e.g., 5%)
    platform_fee_percentage = Decimal('0.05')
    platform_fee_amount = sale_price * platform_fee_percentage
    

    # Create transaction record for admin
    Transaction.objects.create(
        transaction_type='platform_fee',
        amount=platform_fee_amount,
        description=f'Platform fee from sale of {property.title}',
        property=property,  # Assuming Transaction model has a property field
        reference=f'PF-{property.id}-{timezone.now().strftime("%Y%m%d")}'
    )
    

    
    Transaction.objects.create(
        transaction_type='property_sale',
        amount=sale_price - platform_fee_amount,
        description=f'Sale of {property.title} (after platform fee)',
        property=property,  # Assuming Transaction model has a property field
        reference=f'SALE-{property.id}-{timezone.now().strftime("%Y%m%d")}'
    )
    
    # Update property sale price if you have that field
    property.sale_price = sale_price
    property.sold_at = timezone.now()
    property.save()

# Add these imports at the top

# API Views for property bookings
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


# Make sure ALL these imports are at the top of views.py:


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
    owners_count = UserProfile.objects.filter(user_type='owner').count()
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
        'owners_count': owners_count,
        'tenants_count': tenants_count,
        'admins_count': admins_count,
    }
    
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(is_admin)
def update_student_property_status_admin(request, property_id):
    """Admin update student property status"""
    if request.method == 'POST':
        property_obj = get_object_or_404(StudentProperty, id=property_id)
        status = request.POST.get('status')
        
        # Valid status choices for student properties
        valid_statuses = ['draft', 'pending', 'available', 'rented']
        
        if status in valid_statuses:
            property_obj.status = status
            
            # Set published_at when changing to available
            if status == 'available' and not property_obj.published_at:
                property_obj.published_at = timezone.now()
            
            property_obj.save()
            messages.success(request, f'Student property status updated to {property_obj.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status value.')
        
        return redirect('admin_properties')
    
    return redirect('admin_properties')



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
    
    # Get student properties
    student_properties = StudentProperty.objects.all().select_related('created_by')
    
    # Filter student properties by status if provided
    student_status_filter = request.GET.get('student_status', '')
    if student_status_filter:
        student_properties = student_properties.filter(status=student_status_filter)
    
    # Count pending student properties
    pending_student_properties_count = StudentProperty.objects.filter(status='pending').count()
    
    context = {
        'page_title': 'Manage Properties',
        'regular_properties': regular_properties,
        'student_properties': student_properties,
        'pending_student_properties_count': pending_student_properties_count,
        'student_status_filter': student_status_filter,
    }
    
    return render(request, 'admin/properties.html', context)

@login_required
@user_passes_test(is_admin)
def admin_transactions_view(request):
    """Admin view to see all transactions"""
    transactions = Transaction.objects.all().order_by('-created_at')
    
    # Filter by transaction type
    transaction_type = request.GET.get('transaction_type', '')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by date
    start_date = request.GET.get('start_date', '')
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    
    # Calculate statistics
    total_deposits = Transaction.objects.filter(
        transaction_type='deposit'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_platform_fees = Transaction.objects.filter(
        transaction_type='platform_fee'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_transactions = transactions.count()
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page)
    
    context = {
        'page_title': 'Transaction History',
        'transactions': transactions_page,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_platform_fees': total_platform_fees,
        'total_transactions': total_transactions,
    }
    
    return render(request, 'admin/transactions.html', context)

@login_required
@user_passes_test(is_admin)
def admin_platform_fees_view(request):
    """Admin view to see platform fees breakdown"""
    # Get all properties with platform fees
    properties = Property.objects.all().select_related('owner').order_by('-created_at')
    
    # Calculate totals
    total_fees = properties.aggregate(
        total=Sum('platform_fee')
    )['total'] or Decimal('0.00')
    
    total_value = properties.aggregate(
        total=Sum('price')
    )['total'] or Decimal('0.00')
    
    average_fee = total_fees / properties.count() if properties.count() > 0 else Decimal('0.00')
    
    # Calculate fees by status
    available_fees = Property.objects.filter(status='available').aggregate(
        total=Sum('platform_fee')
    )['total'] or Decimal('0.00')
    
    sold_fees = Property.objects.filter(status='sold').aggregate(
        total=Sum('platform_fee')
    )['total'] or Decimal('0.00')
    
    pending_fees = Property.objects.filter(status='pending').aggregate(
        total=Sum('platform_fee')
    )['total'] or Decimal('0.00')
    
    # Calculate percentages
    available_percentage = (available_fees / total_fees * 100) if total_fees > 0 else 0
    sold_percentage = (sold_fees / total_fees * 100) if total_fees > 0 else 0
    pending_percentage = (pending_fees / total_fees * 100) if total_fees > 0 else 0
    
    # Group by month
    monthly_fees = Property.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_fees=Sum('platform_fee'),
        total_value=Sum('price'),
        property_count=Count('id')
    ).order_by('-month')[:12]
    
    # Group by property type
    fees_by_type = Property.objects.values('property_type').annotate(
        total_fees=Sum('platform_fee'),
        property_count=Count('id')
    ).order_by('-total_fees')
    
    # Add display names
    for item in fees_by_type:
        item['property_type_display'] = dict(Property.PROPERTY_TYPE_CHOICES).get(item['property_type'], item['property_type'])
        item['percentage'] = (item['total_fees'] / total_fees * 100) if total_fees > 0 else 0
    
    # Pagination for properties
    paginator = Paginator(properties, 15)
    page = request.GET.get('page', 1)
    properties_page = paginator.get_page(page)
    
    context = {
        'page_title': 'Platform Fees',
        'properties_with_fees': properties_page,
        'total_fees': total_fees,
        'total_value': total_value,
        'total_properties': properties.count(),
        'average_fee': average_fee,
        'available_fees': available_fees,
        'sold_fees': sold_fees,
        'pending_fees': pending_fees,
        'available_percentage': available_percentage,
        'sold_percentage': sold_percentage,
        'pending_percentage': pending_percentage,
        'monthly_fees': monthly_fees,
        'fees_by_type': fees_by_type,
    }
    
    return render(request, 'admin/platform_fees.html', context)

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
## In your views.py






def property_detail_view(request, property_id):
    """View property details"""
    
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if this property has expired rentals
    property_obj.check_and_expire_rental()
    
    # Refresh property from database to get updated status
    property_obj.refresh_from_db()
    
    user = request.user
    
    # Increment view count (only once per session to avoid inflating views)
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
    
    # Get today's date for booking form
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
    
    return render(request, 'owner/property_detail.html', context)





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
def create_admin_message(request):
    """Create a new admin message"""
    if request.method == 'POST':
        form = AdminMessageForm(request.POST)
        if form.is_valid():
            message = AdminMessage(
                title=form.cleaned_data['title'],
                message=form.cleaned_data['message'],
                message_type=form.cleaned_data['message_type'],
                is_active=form.cleaned_data.get('is_active', True),
                show_to_all=form.cleaned_data.get('show_to_all', True),
                show_to_owners=form.cleaned_data.get('show_to_owners', True),
                show_to_tenants=form.cleaned_data.get('show_to_tenants', True),
                start_date=form.cleaned_data.get('start_date') or timezone.now(),
                end_date=form.cleaned_data.get('end_date'),
                created_by=request.user,
            )
            message.save()
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
