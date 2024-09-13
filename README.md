# Описание

Проект FoodGram позволяет пользователям делиться своими и просматривать рецепты других пользователей. 

Использован Django REST Framework для создания REST API, обеспечивающего взаимодействие с базой данных PostgreSQL и аутентификацию с помощью токенов через Djoser. Проект подготовлен к развертыванию на сервере с использованием Docker контейнеров и оркестрации Docker Compose. Добавлена функциональность для импорта данных в БД из JSON-файлов. 

Реализован процесс CI/CD с помощью GitHub Actions (активация происходит при push в ветку releases). При успешном деплое на сервер происходит отправка сообщения в Telegram.

[Проект с тестовыми данными доступен по адресу](https://51.250.30.138/recipes)


# Авторы проекта

[Шайхутдинов Виктор](https://github.com/drugojkira)

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
[Локальный сервер](http://127.0.0.1:8000/)

```

# Добавление тестовых данных (пользователи, ингредиенты, теги, рецепты)

Выполнить команду import_data в контейнере backend:

```
docker compose exec backend python manage.py import_data
```

# Спецификация

При локальном запуске документация будет доступна по адресу:

```
[Документация API](http://127.0.0.1:8000/api/docs/)

```

## Запуск проекта в dev-режиме

- Клонируйте репозиторий с проектом на свой компьютер. В терминале из рабочей директории выполните команду:
```bash
git clone https://github.com/drugojkira/foodgram.git
```

- Перейдите в папку с проектом:

```bash
cd foodgram
```

- Установить и активировать виртуальное окружение

```bash
python -m venv venv
source /venv/bin/activate
```

- Установить зависимости из файла requirements.txt

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
- Создать файл .env в папке проекта:
```.env
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
DEBUG=0
DJANGO_ENV=production
```

### Выполните миграции:
```bash
python manage.py migrate
```

- В папке с файлом manage.py выполнить команду:
```bash
python manage.py runserver
```

- Создание нового суперпользователя (опционально): 
```bash
python manage.py createsuperuser
```

### Загрузите статику:
```bash
python manage.py collectstatic --no-input
```
### Заполните базу тестовыми данными: 
```bash
python manage.py import_data
```
