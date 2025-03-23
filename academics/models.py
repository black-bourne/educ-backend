from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields import CharField

User = get_user_model()


class Grade(models.Model):
    level = models.IntegerField(unique=True)

    def __str__(self):
        return f"Grade {self.level}"


class SchoolClass(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classes')
    # Supervisor is a user (teacher) who oversees the class.
    supervisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_classes', limit_choices_to={'role': 'teacher'}
    )
    teachers = models.ManyToManyField(User, related_name='teaching_class') # multiple teachers teaching multiple classes


    def __str__(self):
        return self.name


# Choices for who should see an announcement
TARGET_ROLE_CHOICES = (
    ('both', 'Both'),
    ('teacher', 'Teacher'),
    ('student', 'Student'),
)

# Model for Announcement
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    target_role = models.CharField(max_length=10, choices=TARGET_ROLE_CHOICES, default='both')
    # an announcement can be linked to a specific class.
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements'
    )

    def __str__(self):
        return self.title


# Model for Event
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    allDay = models.BooleanField(default=False)
    # an event can be attached to a class.
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, null=True, blank=True, related_name='events'
    )

    def __str__(self):
        return self.title

class SubjectChoices(models.TextChoices):
    MATHEMATICS = 'mathematics', 'Mathematics'
    ENGLISH = 'english', 'English'
    KISWAHILI = 'kiswahili', 'Kiswahili'
    SCIENCE = 'science', 'Science'
    SOCIAL_STUDIES = 'social_studies', 'Social Studies'
    CRE = 'cre', 'CRE'

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    subject = models.CharField(max_length=20, choices=SubjectChoices)

    class Meta:
        unique_together = ('teacher', 'subject')

    def __str__(self):
        return f"{self.teacher.first_name} - {self.subject}"

class Assignment(models.Model):
    ASSIGNMENT_STATUS = (
        ("pending", "Pending"),
        ("completed", "Completed")
    )

    subject = models.CharField(choices=SubjectChoices, max_length=20,  default=SubjectChoices.MATHEMATICS)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due = models.DateTimeField()
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment')
    classroom = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, related_name='assignment')
    created_at = models.DateField(auto_now_add=True)


    def __str__(self):
        return self.title