from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = SimpleRouter()

router.register(
    r'users',
    UserViewSet,
    basename='users'
)

router.register(
    r'tags',
    TagViewSet,
    basename='tags'
)

router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
