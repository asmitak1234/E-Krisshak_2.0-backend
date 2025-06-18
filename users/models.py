from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from users.constants.state_district_data import states_and_districts

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

    @property
    def get_profile_picture(self):
        """Returns the user's profile picture or default female image"""
        if self.profile_picture:
            return self.profile_picture.url
        elif self.gender == 'female':
            return '/media/default_female.png'  # Default image
        return '/media/default_user.png'  # General default image
    
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
        return self.email
    
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
    availability = models.BooleanField(default=False)
    specialization = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    experience = models.CharField(max_length=255)
    ratings = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.price}"

    class Meta:
        verbose_name = "Krisshak"
    
    def to_dict(self):
        return {
            "user_id": self.user.id,
            "username": self.user.email,
            "availability": self.availability,
            "specialization": self.specialization,
            "price": str(self.price),  # Convert to string for JSON
            "experience": self.experience,
            "ratings": float(self.ratings),
            "state": self.state.name if self.state else None,
            "district": self.district.name if self.district else None
        }
    
    def calculate_average_rating(self):
        """Recalculate rating based on all received ratings."""
        all_ratings = Rating.objects.filter(rated_user=self.user).values_list("rating_value", flat=True)
        if all_ratings:
            self.ratings = round(sum(all_ratings) / len(all_ratings), 1)
            self.save()


class BhooswamiProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    land_area = models.DecimalField(max_digits=10, decimal_places=2)
    land_location = models.CharField(max_length=255)
    requirements = models.TextField()
    ratings = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Bhooswami"

    def to_dict(self):
        return {
            "user_id": self.user.id,
            "username": self.user.email,
            "land_area": str(self.land_area),  # Convert to string for JSON
            "land_location": self.land_location,
            "ratings": float(self.ratings),
            "requirements": self.requirements,
            "state": self.state.name if self.state else None,
            "district": self.district.name if self.district else None
        }

    def calculate_average_rating(self):
        """Recalculate rating based on all received ratings."""
        all_ratings = Rating.objects.filter(rated_user=self.user).values_list("rating_value", flat=True)
        if all_ratings:
            self.ratings = round(sum(all_ratings) / len(all_ratings), 1)
            self.save()


User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")  # User who favorites others
    krisshak = models.ForeignKey(KrisshakProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by")
    bhooswami = models.ForeignKey(BhooswamiProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "krisshak", "bhooswami")  # Prevent duplicate favorites
