from django_filters.rest_framework import DjangoFilterBackend
from recipes import models
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly
                                        )
from django.shortcuts import get_object_or_404
from . import serializers
from .filters import IngredientsFilter, RecipesFilter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from api.paginations import PageLimitPagination
from rest_framework.pagination import LimitOffsetPagination


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        serializer = serializers.PasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                'Пароль успешно изменен',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(models.User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if models.Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif author == user:
                return Response(
                    {'errors': 'Вы пытаетесь подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            models.Follow.objects.create(user=user, author=author)
            serializer = serializers.UserFollowSerializer(
                author, context={
                    'request': request,
                    'user': user
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        models.Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        authors_in_follows = models.User.objects.filter(following__user=user)
        serializer = serializers.UserFollowSerializer(
            authors_in_follows,
            many=True
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    pagination_class = None
    filterset_class = IngredientsFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = serializers.RecipeSerializer
    filterset_class = RecipesFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.RecipeSerializerCreate
        return serializers.RecipeSerializer

    @action(detail=False)
    def download_shopping_cart(self, request):
        shop_list = list(
            request.user.user_shopping_list.values_list('recipe__components'))
        for item in range(0, len(shop_list)):
            shop_list[item] = shop_list[item][0]
        ingredients_in_recipes = models.Amount.objects.in_bulk(shop_list)

        shop_dictary = {}

        for obj in ingredients_in_recipes.values():
            ingredient = obj.ingredient
            amount = obj.amount
            if ingredient.id in shop_dictary:
                shop_dictary[ingredient.id] = (
                    shop_dictary[ingredient.id][0],
                    shop_dictary[ingredient.id][1] + amount
                )
            else:
                shop_dictary[ingredient.id] = (
                    ingredient.__str__(),
                    amount)

        sorted_list = dict(sorted(
            shop_dictary.items(), key=lambda x: x[1][0]))

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="somefilename.pdf"')
        canvas_blank = canvas.Canvas(response)
        pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))
        canvas_blank.setFont('FreeSans', 18)

        row = 800
        canvas_blank.drawString(
            100,
            row,
            'Список покупок:')
        row -= 40

        canvas_blank.setFont('FreeSans', 14)
        item = 1

        for ingredient_list in sorted_list:
            ingredient_item, amount_item = sorted_list[ingredient_list]
            ingredient_item_capitalize = ingredient_item.capitalize()
            canvas_blank.drawString(
                100,
                row,
                f'{item}) '
                f'{ingredient_item_capitalize} - '
                f'{amount_item}')
            row -= 30
            item += 1

        canvas_blank.showPage()
        canvas_blank.save()
        return response

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            models.ShoppingList.objects.get_or_create(
                user=request.user,
                recipe=self.get_object())

        serializer = serializers.ShopAndFavoriteSerializer(self.get_object())

        flag = models.ShoppingList.objects.filter(
            user=request.user,
            recipe=self.get_object()
        ).exists()
        if (request.method == 'DELETE' and flag):
            get_object_or_404(
                models.ShoppingList,
                user=request.user,
                recipe=self.get_object()
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            models.Favorite.objects.get_or_create(
                user=request.user,
                recipe=self.get_object())

        serializer = serializers.ShopAndFavoriteSerializer(self.get_object())

        flag = models.Favorite.objects.filter(
            user=request.user,
            recipe=self.get_object()
        ).exists()
        if (request.method == 'DELETE' and flag):
            get_object_or_404(
                models.Favorite,
                user=request.user,
                recipe=self.get_object()
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.data)
