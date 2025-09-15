from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def login_page(request):
    """Login page with email-based authentication"""
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    
    form_data = {}
    form_errors = {}
    
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        
        print(f"=== LOGIN DEBUG ===")
        print(f"Email: {email}")
        print(f"Password length: {len(password) if password else 0}")
        
        # Store form data for re-display
        form_data = {
            'email': email,
            'password': '',
            'remember_me': remember_me
        }
        
        # Validation
        if not email:
            form_errors['email'] = ['Email address is required.']
        
        if not password:
            form_errors['password'] = ['Password is required.']
        
        # If no validation errors, try to authenticate
        if not form_errors:
            try:
                # Check if user exists
                user_obj = User.objects.get(email=email)
                print(f"Found user: {user_obj.username} ({user_obj.email})")
                print(f"User active: {user_obj.is_active}")
                
                # CORRECT: Use email for authentication since USERNAME_FIELD = 'email'
                authenticated_user = authenticate(
                    request=request,
                    username=email,  # Use email since USERNAME_FIELD = 'email'
                    password=password
                )
                
                print(f"Authentication result: {authenticated_user}")
                
                if authenticated_user and authenticated_user.is_active:
                    print("🎉 Authentication successful!")
                    login(request, authenticated_user)
                    
                    # Handle remember me
                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser close
                    
                    messages.success(request, f"Welcome back, {authenticated_user.get_full_name() or authenticated_user.username}!")
                    
                    # Redirect
                    next_page = request.GET.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect("core:dashboard")
                else:
                    print("❌ Authentication failed")
                    form_errors['__all__'] = ['Invalid email or password.']
                    
            except User.DoesNotExist:
                print(f"❌ User with email {email} does not exist")
                form_errors['__all__'] = ['Invalid email or password.']
            except Exception as e:
                print(f"❌ Login error: {e}")
                form_errors['__all__'] = ['An error occurred during login. Please try again.']
        
        print(f"=== END LOGIN DEBUG ===")
    
    # Create form object for template
    class FormObject:
        def __init__(self, data, errors):
            self.data = data
            self.errors = errors
            
        @property
        def non_field_errors(self):
            return self.errors.get('__all__', [])
            
        @property
        def email(self):
            class Field:
                def __init__(self, value, errors):
                    self.value = value
                    self.errors = errors
            return Field(self.data.get('email', ''), self.errors.get('email', []))
            
        @property  
        def password(self):
            class Field:
                def __init__(self, errors):
                    self.errors = errors
            return Field(self.errors.get('password', []))
    
    form = FormObject(form_data, form_errors)
    
    context = {
        'form': form,
        'page_title': 'Sign In - BlueWave Solutions'
    }
    return render(request, "accounts/login.html", context)

# Keep your other views the same...
def register_page(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    
    form_data = {}
    form_errors = {}
    
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms = request.POST.get('terms')
        
        # Store form data for re-display
        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
        }
        
        # Validation
        if not first_name:
            form_errors['first_name'] = ['First name is required.']
            
        if not last_name:
            form_errors['last_name'] = ['Last name is required.']
            
        if not username:
            form_errors['username'] = ['Username is required.']
        elif User.objects.filter(username=username).exists():
            form_errors['username'] = ['This username is already taken.']
            
        if not email:
            form_errors['email'] = ['Email address is required.']
        elif User.objects.filter(email=email).exists():
            form_errors['email'] = ['An account with this email already exists.']
            
        if not password:
            form_errors['password'] = ['Password is required.']
        elif len(password) < 8:
            form_errors['password'] = ['Password must be at least 8 characters long.']
            
        if not confirm_password:
            form_errors['confirm_password'] = ['Please confirm your password.']
        elif password != confirm_password:
            form_errors['confirm_password'] = ['Passwords do not match.']
        
        if not terms:
            form_errors['terms'] = ['You must agree to the terms and conditions.']
        
        # If no validation errors, create user
        if not form_errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            messages.success(request, "Registration successful! Please log in.")
            return redirect("login_page")
    
    context = {
        'form_data': form_data,
        'form_errors': form_errors,
        'page_title': 'Create Account - BlueWave Solutions'
    }
    return render(request, "accounts/register.html", context)

@login_required
def logout_view(request):
    """Logout user and redirect"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f"Goodbye {user_name}! You have been logged out successfully.")
    return redirect("core:landing_page")

@login_required
def profile_page(request):
    """User profile page"""
    user = request.user
    
    # Calculate user statistics
    user_stats = {
        'days_since_joined': (timezone.now().date() - user.date_joined.date()).days,
        'last_login_days': (timezone.now().date() - user.last_login.date()).days if user.last_login else None,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'id': user.id,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    context = {
        'user_data': user_data,
        'user_stats': user_stats,
        'page_title': f'Profile - {user.username}'
    }
    
    return render(request, "accounts/profile.html", context)

@login_required
def edit_profile_view(request):
    """Edit user profile"""
    if request.method == "POST":
        user = request.user
        
        # Get form data
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        
        # Validation
        errors = []
        
        if not first_name:
            errors.append("First name is required.")
        
        if not last_name:
            errors.append("Last name is required.")
        
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors.append("This email is already registered to another account.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect("profile_page")
    
    context = {
        'page_title': 'Edit Profile'
    }
    return render(request, "accounts/edit_profile.html", context)