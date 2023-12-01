from django.contrib import admin

from .models import Category, Post, Location


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'is_published',
    )
    list_editable = (
        'category',
        'is_published'
    )
    list_display_links = (
        'title',
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'slug',
        'is_published',
    )
    list_editable = (
        'is_published',
    )


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
