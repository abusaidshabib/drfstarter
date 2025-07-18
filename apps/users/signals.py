import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.users.models import MyUser


@receiver(post_delete, sender=MyUser)
def clean_up_imagefile_after_delete(sender, instance, **kwargs):
    if instance.profile_picture and instance.profile_picture.name:
        image_path = instance.profile_picture.path
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Deleted: {image_path}")
        else:
            print(f"File not found: {image_path}")
