from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from recipes import models as recipes_models

admin.site.register(recipes_models.User, UserAdmin)


class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')


admin.site.register(recipes_models.Tag, TagsAdmin)


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')


admin.site.register(recipes_models.Ingredient, IngredientsAdmin)


class FollowsAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


admin.site.register(recipes_models.Follow, FollowsAdmin)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'cooking_time',
        'image',
        # 'tags',
        'author',
        # 'ingredients',
        'pub_date'
    )


admin.site.register(recipes_models.Recipe, RecipeAdmin)
