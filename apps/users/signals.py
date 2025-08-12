import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.users.models import AppFeature, Company, MyUserDetails


@receiver(post_delete, sender=MyUserDetails)
def clean_up_profile_imagefile_after_delete(sender, instance, **kwargs):
    if instance.profile_picture and instance.profile_picture.name:
        image_path = instance.profile_picture.path
        if os.path.exists(image_path):
            os.remove(image_path)


@receiver(post_delete, sender=Company)
def clean_up_logo_company(sender, instance, **kwargs):
    if instance.logo and instance.logo.name:
        image_path = instance.logo.path
        if os.path.exists(image_path):
            os.remove(image_path)
    if instance.fav_icon and instance.fav_icon.name:
        image_path = instance.fav_icon.path
        if os.path.exists(image_path):
            os.remove(image_path)


@receiver(post_delete, sender=AppFeature)
def clean_up_features_icon(sender, instance, **kwargs):
    if instance.icon and instance.icon.name:
        image_path = instance.icon.path
        if os.path.exists(image_path):
            os.remove(image_path)
