from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        # addition more roles like 'parent' later.
    )

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='students')
    # groups = models.ManyToManyField("auth.Group", related_name="custom_user_groups", blank=True)
    # user_permissions = models.ManyToManyField("auth.Permission", related_name="custom_user_permissions", blank=True)
    school_class = models.ForeignKey('academics.SchoolClass', null=True, blank=True, on_delete=models.SET_NULL, related_name='school_class')
    date_of_birth = models.DateField(verbose_name="Date of birth", null=True, blank=True)
    enrollment_number = models.CharField(max_length=10, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]


    def clean(self):
        from django.core.exceptions import ValidationError
        if self.role == 'student' and not self.school_class:
            raise ValidationError("Students must be assigned to a class.")
        elif self.role == 'teacher' and self.school_class:
            raise ValidationError("Teachers should not be assigned as students.")


    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    def __str__(self):
        return f"{self.email} ({self.role})"
