# Сайт Foodgram - «Продуктовый помощник»
### Описание
На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
### Технологии
 - Python 3.9
 - Django 2.2.16
 - REST Framework 3.12.4
 - PyJWT 2.1.0
 - Django filter 21.1
 - Docker
 - Nginx
 - Postgres
### Запуск
- После клонирования репозитория необходимо создать git secrets::
```
ALLOWED_HOSTS: разрешенные хосты, по умолчанию "*"
DB_ENGINE: django.db.backends.postgresql
DB_HOST: db
DB_NAME: postgres
DB_PORT: 5432
DEBUG: False
DOCKER_PASSWORD: (пароль от вашего аккаунта в Docker)
DOCKER_USERNAME: (username вашего аккаунта в Docker)
EMAIL_ADMIN: (ваш e-mail)
HOST: (публичный адрес вашего сервера)
PASSPHRASE: (пароль SHH ключа)
POSTGRES_PASSWORD: (пароль доступа к базе данных)
POSTGRES_USER: (userame админа базы данных)
SECRET_KEY: (secret key django)
SSH_KEY: (SSH key для доступа к вашему серверу)
USER: (username для доступа к серверу)
```
- После чего выполнить push в репозиторий.
- Произойдет автоматическое тестирование, сборка образа, загрузка образа в Docker, закачивание и запуск образа на сервере.
- Затем, на сервере применяем миграции, создаем администратора:
```
docker-compose exec web python manage.py migrate --noinput

docker-compose exec web python manage.py createsuperuser
```
### Автор
- Кулеш Иван