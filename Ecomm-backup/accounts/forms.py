from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
#from django.contrib.auth.models import User

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        }),
        min_length=8,
        label="Password",
        help_text="Minimum 8 characters required."
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        min_length=8,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].help_text = "Required. We'll use this email for login."

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        
        if password and password2:
            if password != password2:
                raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        }),
        label='Email Address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control'
        }),
        label='Password'
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Remember me'
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")

            # Authenticate with username
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password.")
            
            if not user.is_active:
                raise forms.ValidationError("This account has been disabled.")

        return cleaned_data


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your first name',
            'class': 'form-control'
        }),
        label='First Name'
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your last name',
            'class': 'form-control'
        }),
        label='Last Name'
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'form-control'
        }),
        label='Username'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        }),
        label='Email Address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password (min 8 characters)',
            'class': 'form-control'
        }),
        label='Password',
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'class': 'form-control'
        }),
        label='Confirm Password'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
    
class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information
    Allows users to update their personal details
    """
    
    # Add custom fields that aren't in the User model but you might want
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)',
            'pattern': r'[\+]?[0-9\s\-\(\)]+',
        }),
        label="Phone Number",
        help_text="Optional. Format: +1 (555) 123-4567 or similar"
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us a bit about yourself (optional)',
            'rows': 4,
            'maxlength': '500',
        }),
        label="Bio / About Me",
        help_text="Optional. Maximum 500 characters."
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': timezone.now().date().strftime('%Y-%m-%d'),  # Can't be future date
        }),
        label="Birth Date",
        help_text="Optional. Your birth date (private information)"
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name',
                'maxlength': '30',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name',
                'maxlength': '30',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'readonly': False,  # Allow email changes
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose your username',
                'maxlength': '150',
            }),
        }
        
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'email': 'Required. We use this for login and important notifications.',
            'first_name': 'Optional. Your first name as you\'d like it displayed.',
            'last_name': 'Optional. Your last name as you\'d like it displayed.',
        }

    def __init__(self, *args, **kwargs):
        # Extract the user instance
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        # Make email required
        self.fields['email'].required = True
        
        # Set initial values for custom fields (if you store them somewhere)
        if self.user:
            # You can extend this if you have a profile model with additional fields
            pass
        
        # Add current date info to birth date help text
        current_year = timezone.now().year
        self.fields['birth_date'].help_text = f"Optional. Must be before {current_year}."
        
        # Custom field ordering
        self.field_order = [
            'first_name', 'last_name', 'username', 'email', 
            'phone_number', 'birth_date', 'bio'
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username is taken by another user
            existing_user = User.objects.filter(username=username).exclude(pk=self.user.pk).first()
            if existing_user:
                raise ValidationError(f"Username '{username}' is already taken. Please choose another.")
            
            # Custom username validation
            if len(username) < 3:
                raise ValidationError("Username must be at least 3 characters long.")
            
            # Check for valid characters
            if not re.match(r'^[\w.@+-]+$', username):
                raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is taken by another user
            existing_user = User.objects.filter(email=email).exclude(pk=self.user.pk).first()
            if existing_user:
                raise ValidationError(f"Email '{email}' is already registered to another account.")
            
            # Additional email validation
            email_lower = email.lower()
            if email_lower != email:
                # Store email in lowercase for consistency
                email = email_lower
        
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and formatting for validation
            phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
            
            # Basic phone number validation
            if not re.match(r'^[\+]?[0-9]{10,15}$', phone_clean):
                raise ValidationError("Please enter a valid phone number (10-15 digits).")
        
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = timezone.now().date()
            
            # Check if birth date is not in the future
            if birth_date > today:
                raise ValidationError("Birth date cannot be in the future.")
            
            # Check for reasonable age limits (optional)
            min_date = today.replace(year=today.year - 120)  # 120 years old max
            max_date = today.replace(year=today.year - 13)   # 13 years old min
            
            if birth_date < min_date:
                raise ValidationError("Please enter a valid birth date.")
            
            if birth_date > max_date:
                raise ValidationError("You must be at least 13 years old to use this service.")
        
        return birth_date

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Remove extra whitespace and validate
            first_name = first_name.strip()
            if len(first_name) > 30:
                raise ValidationError("First name must be 30 characters or less.")
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-\']+$", first_name):
                raise ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Remove extra whitespace and validate
            last_name = last_name.strip()
            if len(last_name) > 30:
                raise ValidationError("Last name must be 30 characters or less.")
            
            # Check for valid characters
            if not re.match(r"^[a-zA-Z\s\-\']+$", last_name):
                raise ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return last_name

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio:
            bio = bio.strip()
            if len(bio) > 500:
                raise ValidationError("Bio must be 500 characters or less.")
        
        return bio

    def save(self, commit=True):
        user = super().save(commit=commit)
        
        # Handle custom fields if you have a separate UserProfile model
        # For now, we'll just save the basic User model fields
        
        if commit:
            # You can extend this to save additional profile fields
            # Example:
            # profile, created = UserProfile.objects.get_or_create(user=user)
            # profile.phone_number = self.cleaned_data.get('phone_number')
            # profile.bio = self.cleaned_data.get('bio')
            # profile.birth_date = self.cleaned_data.get('birth_date')
            # profile.save()
            pass
        
        return user

    class Media:
        """Add custom CSS/JS if needed"""
        css = {
            'all': ()  # Add custom CSS files here if needed
        }
        js = ()  # Add custom JS files here if needed


class ChangePasswordForm(forms.Form):
    """
    Form for changing user password
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password',
            'autofocus': True,
        }),
        label="Current Password"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password',
        }),
        label="New Password",
        min_length=8,
        help_text="Minimum 8 characters. Mix of letters, numbers, and symbols recommended."
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password',
        }),
        label="Confirm New Password"
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if old_password and not self.user.check_password(old_password):
            raise ValidationError("Your current password is incorrect.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("The two new passwords don't match.")
        
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user