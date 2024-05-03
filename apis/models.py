from django.db import models

class Function(models.Model):
    function_name = models.CharField(max_length=100)
    trigger_name = models.CharField(max_length=100)
