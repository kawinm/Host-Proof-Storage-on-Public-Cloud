from django.db import models

class Server(models.Model):
    user_name = models.CharField(max_length=100, unique=True)
    p = models.CharField(max_length=500)
    g1 = models.CharField(max_length=500)
    g2 = models.CharField(max_length=500)
    g3 = models.CharField(max_length=500)
    g4 = models.CharField(max_length=500)
    A2 = models.CharField(max_length=500)
    B2 = models.CharField(max_length=500)
    x1 = models.CharField(max_length=500)
    a1 = models.CharField(max_length=500)
    b1 = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    bankid = models.CharField(max_length=500)
    bankname = models.CharField(max_length=500)

    def __str__(self):
        return self.user_name + " " + self.p