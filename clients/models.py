from django.db import models
from django.db.models.functions import Lower
from django.core.validators import MinLengthValidator

MIN_NAME_LENGTH = 2

class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(MIN_NAME_LENGTH)])

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_sector_name_ci",
                violation_error_message="A sector with this name already exists.",
            ),
        ]

    def __str__(self):
        return self.name

class Client(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(MIN_NAME_LENGTH)])
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="clients")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_client_name_ci",
                violation_error_message="A client with this name already exists.",
            ),
        ]

    def __str__(self):
        return self.name


