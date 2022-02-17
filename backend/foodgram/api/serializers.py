import base64
import uuid

from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from foodgram.settings import MAX_INGREDIENT_AMOUNT
from recipes.models import (Amount, Favorite, Follow, Ingredient, Recipe,
                            ShoppingList, Tag, User)
from rest_framework import serializers


class CustomBase64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name_id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(imgstr), name=name_id.urn[9:] + '.' + ext)
        return super(CustomBase64ImageField, self).to_internal_value(data)


class ShopAndFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        )
        read_only_fields = ('id', )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = ('id', 'username', 'email', 'first', 'last_name')

    def get_is_subscribed(self, obj):
        try:
            if self.context['request'].user.is_anonymous:
                return False
            user = self.context['request'].user
        except KeyError:
            user = self.instance
        return Follow.objects.filter(user=user, author=obj).exists()


class UserFollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        name='get_is_subscribed'
    )
    recipes = UserRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(
        name='get_recipes_count'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('user')
        return user.follower.filter(author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = (
            'user',
            'author'
        )

    def validate(self, data):
        if Follow.objects.filter(
            user=data['user'],
            author=data['author']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )
        elif data['user'] == data['author']:
            raise serializers.ValidationError(
                'Вы пытаетесь подписаться на себя'
            )
        return data


class PasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            'new_password',
            'current_password'
        )

    def validate_current_password(self, value):
        if check_password(value, self.context.get('request').user.password):
            return value
        raise serializers.ValidationError('Неверный текущий пароль')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class AmountSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(
        name='get_name'
    )
    measurement_unit = serializers.SerializerMethodField(
        name='get_measurement_unit'
    )

    class Meta:
        model = Amount
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_name(self, obj):
        return obj.ingredient.name


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = AmountSerializer(many=True, source='components')
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        name='get_is_in_shopping_cart'
    )
    is_favorited = serializers.SerializerMethodField(
        name='get_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):

        if self.context['request'].user.is_anonymous:
            return False

        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):

        if self.context['request'].user.is_anonymous:
            return False

        return ShoppingList.objects.filter(
            user=self.context['request'].user,
            recipe=obj).exists()


class AmountSerializerCreate(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = Amount
        fields = (
            'id',
            'amount',
        )


class RecipeSerializerCreate(serializers.ModelSerializer):
    ingredients = AmountSerializerCreate(
        many=True,
        source='components'
    )
    image = CustomBase64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть '
                'целым числом и не менее 1 минуты!'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('components')
        tags = validated_data.pop('tags')
        user = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.add_tags_and_components_to_recipe(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('components')
        tags = validated_data.pop('tags')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_tags_and_components_to_recipe(instance, ingredients, tags)
        instance.save()
        return instance

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(
                'Должено быть не меньше ингредиент!')
        set_id = set()
        for item in value:
            if item['ingredient'].id in set_id:
                raise serializers.ValidationError(
                    'Ингредиенты в рецепте должны быть уникальными!')
            set_id.add(item['ingredient'].id)
            if item['amount'] < MAX_INGREDIENT_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть '
                    'целым числом, а значение не менее 1!')
        return value

    def validate(self, data):
        if self.instance is None:
            return data
        if self.context['request'].user != self.instance.author:
            raise serializers.ValidationError('Нельзя изменить чужой рецепт!')
        return data

    def add_tags_and_components_to_recipe(self, obj, ingredients, tags):
        for ingredient in ingredients:
            Amount.objects.create(
                recipe=obj,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        for tag in tags:
            new_tag = get_object_or_404(Tag, id=tag.id)
            obj.tags.add(new_tag)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
