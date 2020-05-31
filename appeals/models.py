from django.db import models
from organizations.models import Organization

PRIORITY = [
    (0, 'Обычный'),
    (1, 'Срочный'),
    (2, 'Всеьма срочный')
]


class Categories(models.Model):
    name = models.CharField(max_length=50)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY)


# Create your models here.
class Appeal(models.Model):
    # author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appeals_created', on_delete=models.CASCADE)
    author = models.ForeignKey(to='account.Citizen', related_name='appeals_created', on_delete=models.CASCADE)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name='appeals')
    description = models.TextField(blank=True)
    created = models.DateField(auto_now_add=True, db_index=True)
