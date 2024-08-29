# Описание

Проект FoodGram позволяет пользователям делиться своими и просматривать рецепты других пользователей. 

Использован Django REST Framework для создания REST API, обеспечивающего взаимодействие с базой данных PostgreSQL и аутентификацию с помощью токенов через Djoser. Проект подготовлен к развертыванию на сервере с использованием Docker контейнеров и оркестрации Docker Compose. Добавлена функциональность для импорта данных в БД из JSON-файлов. 

Реализован процесс CI/CD с помощью GitHub Actions (активация происходит при push в ветку releases). При успешном деплое на сервер происходит отправка сообщения в Telegram.

Запущенный проект с тестовыми данными доступен по адресу: https://thedrugojkira.zapto.org/

Документация к API достпуна по адресу: https://thedrugojkira.zapto.org/api/docs/

Логин администратора : admin@gmail.com
Пароль администратора : admin

# Авторы проекта

[drugojkira](https://github.com/drugojkira)

# Установка и запуск с Docker

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/drugojkira/foodgram
```

```
cd foodgram
```

Запустить сборку проекта:

```
docker compose up
```

Выполнить сбор статики в контейнере backend:

```
docker compose exec backend python manage.py collectstatic
```

Выполнить миграции в контейнере backend:

```
docker compose exec backend python manage.py migrate
```

Проект будет доступен по адресу

```
http://127.0.0.1:8000/
```

# Добавление тестовых данных (пользователи, ингредиенты, теги, рецепты)

Выполнить команду import_data в контейнере backend:

```
docker compose exec backend python manage.py import_data
```

# Спецификация

При локальном запуске документация будет доступна по адресу:

```
http://127.0.0.1:8000/api/docs/
```

