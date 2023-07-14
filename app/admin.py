from django.contrib import admin
from .models import ExtendedUser, Tag
# Register your models here.

admin.site.register(ExtendedUser)
admin.site.register(Tag)