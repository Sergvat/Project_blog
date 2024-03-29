# Проект платформы для блога.

Данный проект представляет собой полноценную платформу для блогов с функциональностью авторизации, персональными лентами, комментариями и возможностью подписки на авторов.

## Функциональность проекта:

-   Регистрация и авторизация пользователей: Пользователи могут зарегистрироваться на платформе, создавать свои учетные записи и авторизовываться для доступа к функциональности.
-   Персональные ленты: Каждый пользователь имеет свою персональную ленту, где отображаются посты от авторов, на которых он подписан, а также собственные опубликованные посты.
-   Комментарии: Пользователи могут оставлять комментарии к постам, выражая свое мнение, задавая вопросы или обсуждая тему поста.
-   Подписка на авторов: Пользователи могут подписываться на авторов блогов, чтобы получать уведомления о новых постах от них.
-   Управление постами: Пользователи могут создавать, редактировать и удалять свои собственные посты.
-   Управление профилем: Пользователи могут настраивать информацию в своем профиле, включая аватар, описание и другие данные.

## Запуск проекта:

Чтобы запустить проект, выполните следующие шаги:

1.  Клонируйте репозиторий и перейдите в папку проекта в командной строке:
           
    `git clone https://github.com/Sergvat/Yatube_final.git
    cd Yatube_final` 
    
2.  Создайте и активируйте виртуальное окружение:
    
    `python3 -m venv env
    source env/bin/activate` 
    
3.  Установите необходимые зависимости из файла requirements.txt:
       
    `python3 -m pip install --upgrade pip
    pip install -r requirements.txt` 
    
4.  Выполните миграции базы данных:
        
    `python3 manage.py migrate` 
    
5.  Запустите сервер проекта:
        
    `python3 manage.py runserver` 
