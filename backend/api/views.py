from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
)
from rest_framework.response import Response

from api.paginations import PageLimitPagination
from foodgram.settings import (
    AFSPDF, APPLICATIONPDF, FREE_SANS_FONT, FREE_SANS_FONT_SIZE,
    FREE_SANS_FONT_SIZE_HEADER, INDENT, ROW_AFTER_HEADER, ROW_AFTER_INGRED,
    ROW_HEADER,
)
from recipes.models import (
    Amount, Favorite, Follow, Ingredient, Recipe, ShoppingList, Tag, User,
)

from .filters import IngredientsFilter, RecipesFilter
from .permissions import AdminOrReadOnly, AdminUserOrReadOnly
from .serializers import (
    FollowSerializer, IngredientSerializer, PasswordSerializer,
    RecipeSerializer, RecipeSerializerCreate, ShopAndFavoriteSerializer,
    TagSerializer, UserCreateSerializer, UserFollowSerializer, UserSerializer,
)


class HTTPMethod:
    DELETE = 'DELETE'
    POST = 'POST'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        serializer = PasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
        return Response(
            'Пароль успешно изменен',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == HTTPMethod.POST:
            follow_data = {'author': author.pk, 'user': user.pk}
            follow_serializer = FollowSerializer(data=follow_data)
            follow_serializer.is_valid(raise_exception=True)
            serializer = UserFollowSerializer(
                author,
                context={
                    'request': request,
                    'user': user,
                }
            )
            Follow.objects.create(user=user, author=author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
                )
        Follow.objects.filter(user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        authors_in_follows = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors_in_follows)
        serializer = UserFollowSerializer(
            page,
            many=True,
            context={'user': request.user}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ('get',)
    filter_backends = (IngredientsFilter,)
    pagination_class = None
    search_fields = ('^name',)
    permission_classes = (AdminOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = RecipesFilter
    permission_classes = (AdminUserOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializerCreate
        return RecipeSerializer

    @action(detail=False)
    def download_shopping_cart(self, request):
        shop_list = Amount.objects.filter(
            recipe__shopping_list__user=request.user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by()

        response = HttpResponse(content_type=APPLICATIONPDF)
        response['Content-Disposition'] = AFSPDF
        canvas_blank = canvas.Canvas(response)
        canvas_blank.setFont(FREE_SANS_FONT, FREE_SANS_FONT_SIZE_HEADER)

        row = ROW_HEADER
        canvas_blank.drawString(
            INDENT,
            row,
            'Список покупок:')
        row -= ROW_AFTER_HEADER

        canvas_blank.setFont(FREE_SANS_FONT, FREE_SANS_FONT_SIZE)
        item = 1

        for ingredient in shop_list:
            canvas_blank.drawString(
                INDENT,
                row,
                f'{item}) '
                f'{ingredient["name"]} - '
                f'{ingredient["amount"]}, {ingredient["measurement_unit"]}')
            row -= ROW_AFTER_INGRED
            item += 1

        canvas_blank.showPage()
        canvas_blank.save()
        return response

    @action(methods=('post', 'delete'), detail=True)
    def shopping_cart(self, request, pk=None):
        if request.method == HTTPMethod.POST:
            ShoppingList.objects.get_or_create(
                user=request.user,
                recipe=self.get_object()
            )

        serializer = ShopAndFavoriteSerializer(self.get_object())

        user_has_shoppinglist = ShoppingList.objects.filter(
            user=request.user,
            recipe=self.get_object()
        ).exists()
        if (request.method == HTTPMethod.DELETE and user_has_shoppinglist):
            get_object_or_404(
                ShoppingList,
                user=request.user,
                recipe=self.get_object()
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.data)

    @action(methods=('post', 'delete'), detail=True)
    def favorite(self, request, pk=None):
        if request.method == HTTPMethod.POST:
            Favorite.objects.get_or_create(
                user=request.user,
                recipe=self.get_object())
        serializer = ShopAndFavoriteSerializer(self.get_object())
        user_has_favorite = Favorite.objects.filter(
            user=request.user,
            recipe=self.get_object()
        ).exists()
        if (request.method == HTTPMethod.DELETE and user_has_favorite):
            get_object_or_404(
                Favorite,
                user=request.user,
                recipe=self.get_object()
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.data)
