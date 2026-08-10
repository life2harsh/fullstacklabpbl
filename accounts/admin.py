from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Block, Follow, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ["username", "email", "is_staff", "date_joined"]
    search_fields = ["username", "email"]
    list_filter = ["is_staff", "is_active"]


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ["follower", "following", "created_at"]
    search_fields = ["follower__username", "following__username"]
    list_filter = ["created_at"]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ["blocker", "blocked", "created_at"]
    search_fields = ["blocker__username", "blocked__username"]
