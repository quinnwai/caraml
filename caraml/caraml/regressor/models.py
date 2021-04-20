from django.db import models
from caraml.users.models import User

class Dataset(models.Model):
    title = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField()

    # Source: https://stackoverflow.com/questions/13455052/getting-file-extension-in-django-template
    # def extension(self):
    #     name, extension = os.path.splitext(self.file.name)
    #     return extension