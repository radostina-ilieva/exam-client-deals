from django.db import models

class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Agency(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "agencies"

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="clients")
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, null=True, blank=True, related_name="clients")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


