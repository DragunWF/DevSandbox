from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    search_fields = ["label"]


admin.site.register(Tag, TagAdmin)
