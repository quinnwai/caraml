from django.db import models
from caraml.users.models import User
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Dataset(models.Model):
    title = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="datasets")

    def __str__(self):
        return self.title

class Record(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dateTime = models.DateTimeField(default=timezone.now)
    randomState = models.PositiveIntegerField()
    numFolds = models.PositiveIntegerField()
    target = models.CharField(max_length=100)
    features = ArrayField(models.CharField(max_length=100))
    result = models.DecimalField(decimal_places=2, max_digits=4)

    def __str__(self):
        return self.title + " (" + self.dateTime.strftime('%B %d, %Y') + ")"
