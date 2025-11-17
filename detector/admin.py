# detector/admin.py
from django.contrib import admin
from .models import Prediction

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'result', 'confidence', 'created_at', 'image_thumbnail')
    list_filter = ('result', 'created_at', 'user')
    search_fields = ('user__username', 'result')
    readonly_fields = ('created_at',)

    def image_thumbnail(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />'
        return "-"
    image_thumbnail.allow_tags = True
    image_thumbnail.short_description = 'Image'
