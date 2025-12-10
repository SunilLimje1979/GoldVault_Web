from django.db import models

class Enquiry(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    response_code = models.IntegerField(null=True, blank=True)
    response_text = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone}"
