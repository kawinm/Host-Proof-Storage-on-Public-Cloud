from django.db import models


class User(models.Model):
    user_name = models.CharField(max_length=100, unique=True)
    p         = models.CharField(max_length=500)
    g1        = models.CharField(max_length=500)
    g2        = models.CharField(max_length=500)
    bank_name = models.CharField(max_length=200, unique=True)
    bank_id   = models.CharField(max_length=100, unique=True)
    location  = models.CharField(max_length=100)

    def __str__(self):
        return self.bank_name + " " + self.bank_id


class Server(models.Model):
    user_name = models.CharField(max_length=100, unique=True)
    p = models.CharField(max_length=500)
    g1 = models.CharField(max_length=500)
    g2 = models.CharField(max_length=500)
    g3 = models.CharField(max_length=500)
    g4 = models.CharField(max_length=500)
    omega = models.CharField(max_length=500)
    theta = models.CharField(max_length=500)

    def __str__(self):
        return self.user_name + " " + self.p