from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('tutor',   'Tutor'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # For students — links to student_id in Flask/SQLite
    student_number = models.CharField(max_length=50, blank=True, null=True)

    # For tutors — links to tutor sessions
    staff_number = models.CharField(max_length=50, blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin'

    def is_tutor(self):
        return self.role == 'tutor'

    def is_student(self):
        return self.role == 'student'

    def __str__(self):
        return f"{self.username} ({self.role})"