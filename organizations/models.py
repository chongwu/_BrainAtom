from django.db import models
# from account.models import Citizen


# Create your models here.
class Organization(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()


class Position(models.Model):
    name = models.CharField(max_length=50)
