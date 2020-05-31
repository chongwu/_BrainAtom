from django.db import models
from organizations.models import Organization, Position
from appeals.models import Appeal
from django.conf import settings

CHOICES = [
    (0, 'плохо'),
    (1, 'ниже среднего'),
    (2, 'средне'),
    (3, 'выше среднего'),
    (4, 'хорошо'),
    (5, 'отчично')
]

TG_ROLES = [
    (0, 'Житель'),
    (1, 'Старщий по дому'),
    (2, 'Сотрудник УК/ТСЖ'),
]


# Create your models here.
class Profile(models.Model):
    external_id = models.IntegerField(null=True, default=0)
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    tg_role = models.SmallIntegerField(choices=TG_ROLES, default=0)

    # phone =
    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.name} {self.surname}'


class Citizen(Profile):
    address = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='citizens')


class Employee(Profile):
    organizations = models.ManyToManyField(Organization, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees')


class Subscription(models.Model):
    appeal = models.OneToOneField(Appeal, on_delete=models.CASCADE, related_name='executor')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='subscriptions')

    # TODO Удалить атрибут auto_now_add, добавлен в качестве заглушки
    plan_date = models.DateTimeField(auto_now_add=True)


class OrganizationRating(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='rating')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='grades')
    rating = models.SmallIntegerField(choices=CHOICES)


class AppealRating(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='appeal_rating')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='appeal_grades')
    appeal = models.OneToOneField(Appeal, on_delete=models.CASCADE, related_name='created_rating')
