from django.db import models
from django.contrib.auth.models import User
from osm_field.fields import LatitudeField, LongitudeField, OSMField

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    datetime = models.DateTimeField()
    seats = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)

    def __str__(self):
        return self.name
class UserEventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
