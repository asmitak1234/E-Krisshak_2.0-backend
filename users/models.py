from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from users.constants.state_district_data import states_and_districts
from django.conf import settings
from appointments.models import Appointment, AppointmentRequest
from django.db.models import Q
from django.utils.timezone import now

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')

    class Meta:
        unique_together = ('name', 'state')

    def __str__(self):
        return f"{self.name}, {self.state.name}"

def enrich_with_appointment_metadata(current_user, other_user):
    metadata = {}

    recent_request = AppointmentRequest.objects.filter(
        sender=current_user,
        recipient=other_user
    ).order_by('-request_time').first()

    if recent_request:
        metadata['recent_request_status'] = recent_request.status
        metadata['recent_request_time'] = recent_request.request_time

    recent_appointment = Appointment.objects.filter(
        Q(krisshak=current_user, bhooswami=other_user) |
        Q(krisshak=other_user, bhooswami=current_user)
    ).order_by('-created_at').first()

    if recent_appointment:
        metadata['appointment_status'] = recent_appointment.status
        metadata['appointment_created_at'] = recent_appointment.created_at
        metadata['appointment_payment_status'] = recent_appointment.payment_status

    return metadata

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if not email:
            raise ValueError("The Email field must be set")
        
        return self.create_user( email, password, **extra_fields)
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('krisshak', 'Krisshak'),
        ('bhooswami', 'Bhooswami'),
        ('state_admin', 'State Admin'),
        ('district_admin', 'District Admin')
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def get_profile_picture(self, request=None):
        if self.profile_picture:
            url = self.profile_picture.url
        elif self.gender == 'female':
            url = '/static/media/default_female.png'
        else:
            url = '/static/media/default_user.png'

        return request.build_absolute_uri(url) if request else url


    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    name = models.CharField(max_length=100,null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=20,null=True, blank=True)

    preferred_language = models.CharField(
        max_length=10, choices=[('en', 'English'), ('hi', 'Hindi')], default='en'
    )  # Added preferred language
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.user_type})"
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
    
    class Meta:
        verbose_name = "User"

class StateAdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    state_code = models.CharField(max_length=255, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.state_code and self.state:
            state_names = sorted(states_and_districts.keys(), key=lambda x: x.upper())
            index = state_names.index(self.state.name) + 1
            self.state_code = f"{self.state.name.upper().replace(' ', '')}{index:02d}@EKrisshak2"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.state.name} Admin"

    class Meta:
        verbose_name = "State Admin"

    def delete(self, *args, **kwargs):
        self.user.delete()
        super().delete(*args, **kwargs)

class DistrictAdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    state_admin = models.ForeignKey(StateAdminProfile, on_delete=models.CASCADE, related_name="districts")
    district_code = models.CharField(max_length=255, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.district_code and self.district and self.district.state:
            districts = sorted(states_and_districts.get(self.district.state.name, []), key=lambda x: x.upper())
            district_index = districts.index(self.district.name) + 1
            state_names = sorted(states_and_districts.keys(), key=lambda x: x.upper())
            state_index = state_names.index(self.district.state.name) + 1
            state_code = f"{self.district.state.name.upper().replace(' ', '')}{state_index:02d}@EKrisshak2"
            self.district_code = f"{self.district.name.upper().replace(' ', '')}{district_index:02d}{state_code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.district.name} Admin"

    class Meta:
        verbose_name = "District Admin"

    def delete(self, *args, **kwargs):
        self.user.delete()
        super().delete(*args, **kwargs)

class Rating(models.Model):
    """Stores individual ratings given by users."""
    rater = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # The user who rates
    rated_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="received_ratings")
    rating_value = models.DecimalField(max_digits=2, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("rater", "rated_user")  # Ensure one rating per user

class KrisshakProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    availability = models.BooleanField(default=True)
    specialization = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    experience = models.CharField(max_length=255, blank=True)
    ratings = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.price}"
        return f"Krisshak #{self.id}"


    class Meta:
        verbose_name = "Krisshak"
    
    def to_dict(self, request=None):
        base = {
            "user_id": self.user.id,
            "name": self.user.name,
            "username": self.user.email,
            "availability": self.availability,
            "specialization": self.specialization,
            "age": self.user.age,
            "gender": self.user.gender,
            "profile_picture": self.user.get_profile_picture(request),
            "price": str(self.price),
            "experience": self.experience,
            "ratings": float(self.ratings),
            "state": self.state.name if self.state else None,
            "district": self.district.name if self.district else None
        }

        if request and hasattr(request, "user") and request.user.is_authenticated:
            meta = enrich_with_appointment_metadata(request.user, self.user)
            base.update(meta)

        return base

    
    def calculate_average_rating(self):
        """Recalculate rating based on all received ratings."""
        all_ratings = Rating.objects.filter(rated_user=self.user).values_list("rating_value", flat=True)
        if all_ratings:
            self.ratings = round(sum(all_ratings) / len(all_ratings), 1)
            self.save()
    
    def delete(self, *args, **kwargs):
        self.user.delete()
        super().delete(*args, **kwargs)


class BhooswamiProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="bhooswamiprofile")
    land_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    land_location = models.CharField(max_length=255, null=True, blank=True)
    requirements = models.TextField()
    ratings = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        if self.user:
            return self.user.email
        return f"Bhooswami #{self.id}"

    class Meta:
        verbose_name = "Bhooswami"

    def to_dict(self, request=None):
        base = {
            "user_id": self.user.id,
            "name": self.user.name,
            "username": self.user.email,
            "land_area": str(self.land_area),
            "land_location": self.land_location,
            "age": self.user.age,
            "gender": self.user.gender,
            "profile_picture": self.user.get_profile_picture(request),
            "ratings": float(self.ratings),
            "requirements": self.requirements,
            "state": self.state.name if self.state else None,
            "district": self.district.name if self.district else None
        }

        if request and hasattr(request, "user") and request.user.is_authenticated:
            meta = enrich_with_appointment_metadata(request.user, self.user)
            base.update(meta)

        return base


    def calculate_average_rating(self):
        """Recalculate rating based on all received ratings."""
        all_ratings = Rating.objects.filter(rated_user=self.user).values_list("rating_value", flat=True)
        if all_ratings:
            self.ratings = round(sum(all_ratings) / len(all_ratings), 1)
            self.save()

    def delete(self, *args, **kwargs):
        self.user.delete()
        super().delete(*args, **kwargs)

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")  # User who favorites others
    krisshak = models.ForeignKey(KrisshakProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by")
    bhooswami = models.ForeignKey(BhooswamiProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "krisshak", "bhooswami")  # Prevent duplicate favorites
