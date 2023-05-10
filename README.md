# yatube_project
Социальная сеть блогеров

### Описание
Социальная сеть в которой пользователи могут оставлять посты от своего имени.

### Требования
* Python 3.7+

### Технологии
Python 3.7
Django 2.2.19

### Запуск проекта в dev-режиме
Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/DeLaMia/hw05_final
```

```
cd hw05_fina
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:
```
python3 manage.py makemigrations
```

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
### Авторы
https://github.com/DeLaMia
