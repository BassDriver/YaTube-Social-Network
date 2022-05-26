from django.contrib import admin

from .models import Comment, Follow, Post, Group

admin.site.register(Group)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'post',
        'author',
        'text',
        'created',
    )


admin.site.register(Comment, CommentAdmin)


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
    )


admin.site.register(Follow, FollowAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
        'image',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
