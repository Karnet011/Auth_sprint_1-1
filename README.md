![tests](https://github.com/v-v-d/Auth_sprint_1/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/v-v-d/Auth_sprint_1/branch/main/graph/badge.svg?token=Q8NOGB813N)](https://codecov.io/gh/v-v-d/Auth_sprint_1)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

# Сервис аутентификации и авторизации

## Ресурсы
- Доска: https://github.com/users/v-v-d/projects/3

Репозитории:
- сервис Auth API: https://github.com/v-v-d/Auth_sprint_1
- сервис API: https://github.com/v-v-d/Async_API_sprint_1
- сервис ETL: https://github.com/v-v-d/ETL
- сервис Admin panel: https://github.com/v-v-d/Admin_panel_sprint_1


## Основные сущности
- Пользователи — логин, email, дата создания, дата изменения, пароль, активность аккаунта, послденее время посещения, роль.
- Роли — имя, описание.
- Роль-Пользователь — пользователь, роль.
- История аутентификации — пользователь, время логирования и выхода, система входа, ip адрес, устройство.

## Основные компоненты системы
- Cервер WSGI — сервер с запущенным приложением.
- Nginx — прокси-сервер, который является точкой входа для веб-приложения.
- PostgreSQL — хранилище данных, в котором лежит вся необходимая информация для сервса.
- Redis — хранилище данных для токенов.
- SQLAlchemy - используется как ORM.
- Jaeger - используется для трассировки, можно зайти в UI на порту 16686

## Используемые технологии
- Flask + gevent
- PostgreSQL
- Redis
- Docker
- Pytest + pytest coverage
- SQLAlchemy
- Jaeger

## Общие правила aka code-style
1. Вся бизнес-логика должна помещаться в провайдерах src/app/services
2. Модели содержат только описание таблиц и специализированные методы по запросам в таблицы
3. Эндпоинты обращаются к провайдеру и вызывают у него необходимый метод. Результат эндпоинта - 
результат работы метода провайдера, т.е. или какая-то структура или исключение 

## Работа с проектом
### Запуск
1. Создать общую сеть для всех проектов практикума, чтобы была связь между всеми контейнерами курса
```shell
docker network create yandex
```
2. Собрать и запустить текущий проект
```shell
docker-compose up --build
```
3. Перейти к документации по адресу 0.0.0.0
4. Создать суперпользователя. В соседнем терминале выполнить
```shell
docker exec -it auth-app python manage.py create-superuser --login <тут логин> --password <тут пароль>

```

### Тестирование
Собрать тестовое окружение и запустить тесты
```shell
docker-compose -f docker-compose.test.yaml up --build --exit-code-from sut
```

### Миграции
Чтобы сгенерировать файлы миграций надо:
1. Поднять проект
```shell
docker-compose up --build
```
2. В соседнем терминале выполнить
```shell
docker exec -it auth-app flask db migrate -m "<Тут короткое текстовое описании миграции>"
```



