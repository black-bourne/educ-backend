from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Grade(models.Model):
    level = models.IntegerField(unique=True, db_index=True)  # Indexed for filtering

    def __str__(self):
        return f"Grade {self.level}"

class SchoolClass(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)  # Indexed for search
    capacity = models.PositiveIntegerField()
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classes')
    supervisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_classes', limit_choices_to={'role': 'teacher'}
    )
    teachers = models.ManyToManyField(User, related_name='teaching_class')
    students = models.ManyToManyField(User, related_name='enrolled_classes', limit_choices_to={'role': 'student'})

    def __str__(self):
        return self.name

class Announcement(models.Model):
    title = models.CharField(max_length=200, db_index=True)  # Indexed for search
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True, db_index=True)  # Indexed for filtering
    target_role = models.CharField(max_length=10, choices=[('both', 'Both'), ('teacher', 'Teacher'), ('student', 'Student')], default='both')
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements'
    )

    def __str__(self):
        return self.title

class Event(models.Model):
    title = models.CharField(max_length=200, db_index=True)  # Indexed for search
    description = models.TextField()
    start = models.DateTimeField(db_index=True)  # Indexed for filtering
    end = models.DateTimeField()
    allDay = models.BooleanField(default=False)
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
    subject = models.CharField(choices=SubjectChoices, max_length=20, default=SubjectChoices.MATHEMATICS, db_index=True)  # Indexed for filtering
    title = models.CharField(max_length=200, db_index=True)  # Indexed for search
    description = models.TextField(blank=True)
    due = models.DateTimeField(db_index=True)  # Indexed for filtering
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='pending', db_index=True)  # Indexed for filtering
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment')
    classroom = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, related_name='assignment')
    created_at = models.DateField(auto_now_add=True, db_index=True)  # Indexed for ordering

    def __str__(self):
        return self.title

class Submission(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    )
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Indexed for ordering
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.first_name} - {self.assignment.title}"