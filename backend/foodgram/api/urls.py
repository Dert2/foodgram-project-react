from django.urls import include, path
from rest_framework.routers import SimpleRouter
from . import views

router1 = SimpleRouter()

router1.register(
    r'users',
    views.UserViewSet,
    basename='users'
)

router1.register(
    r'tags',
    views.TagViewSet,
    basename='tags'
)

router1.register(
    r'ingredients',
    views.IngredientViewSet,
    basename='ingredients'
)

router1.register(
    r'recipes',
    views.RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    path('', include(router1.urls)),
    path('auth/', include("djoser.urls.authtoken")),
]
