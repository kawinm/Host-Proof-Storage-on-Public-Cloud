from django.db import models


class User(models.Model):
    user_name = models.CharField(max_length=100)
    p = models.CharField(max_length=500)
    g1 = models.CharField(max_length=500)
    g2 = models.CharField(max_length=500)
