from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator, EmailValidator
from django.utils import timezone

class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            MinLengthValidator(1),
            MaxLengthValidator(100)
        ]
    )
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subject"

    def __str__(self):
        return self.subject_name


class Trainer(models.Model):
    trainer_code = models.CharField(
        max_length=20,
        primary_key=True,
        validators=[MinLengthValidator(3)]
    )
    name = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(2),
            MaxLengthValidator(100)
        ]
    )
    email = models.EmailField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        validators=[EmailValidator()]
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(regex=r'^[0-9]{10,15}$', message="Enter a valid phone number (10–15 digits)")
        ]
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainers'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "trainer"
        verbose_name = "Trainer"
        verbose_name_plural = "Trainers"

    def __str__(self):
        return f"{self.name} ({self.trainer_code})"