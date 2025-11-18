# Настройка виртуализации

Открой PowerShell и выполни:
```
Get-CimInstance Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled
```

Если вывод: VirtualizationFirmwareEnabled : True ,то виртуализация включена.

Если False → нужно включать в BIOS/UEFI:
- Для Intel: Intel Virtualization Technology (VT-x)
- Для AMD: SVM Mode

Меню обычно: 
Advanced → CPU Configuration или Advanced → Security.

# Настройка Docker Desktop

Скачать приложение можно с официального сайта. 

После установки убедитесь, что Docker работает:

```
docker --version
```

# Настройка wsl
Этот раздел только для пользователей Windows 
### Включение WSL и виртуализации
Откройте PowerShell от имени администратора и выполните команду:
```
wsl --install
```
или
```
.\wsl --install
```

Эта команда автоматически:
- Включает необходимые компоненты (VirtualMachinePlatform, WindowsSubsystemForLinux)
- Устанавливает WSL 2 как версию по умолчанию
- Загружает и устанавливает Ubuntu (можно выбрать другой дистрибутив позже)

### Обновление WSL (опционально)
```
wsl --update
```

### Проверьте версию WSL:
```
wsl --list --verbose
```

# Установка контейнеров postgres, mongo и minio

Перейдите в директорию neurotutor_api

Запустить:
```
docker compose up -d
```
Остановить:
```
docker compose down
```
Проверить состояние контейнеров:
```
docker compose ps
```

# Доступ к установленным контейнерам
- Postgres: Используем PgAdmin
- Mongo: Compass
- Minio: Web интерфейс

Открыть в браузере: http://localhost:9001
* Логин: minioadmin
* Пароль: minioadmin123

После входа в административную панель создать бакет: ```tutor-courses```

# Установка и настройка виртуального окружения
Версия: Python 3.13

- Создать виртуальное окружение
```
python -m venv venv
```

- Инициализировать виртуально окружение
```
venv\Scripts\activate
```

- Установить зависимости из requirements.txt
```
pip install -r requirements.txt
```

- Запуск приложения FastApi
```
uvicorn main:app --reload
```

- Swagger доступен по ссылке: http://127.0.0.1:8088/docs

# Git

## Работа с ветками

В проекте используются две основные ветки:

- `master` - основная ветка, содержит стабильную версию кода
- `develop` - ветка разработки, куда вливаются все новые функции

### Процесс разработки новой функции:

1. Создание новой ветки от master: feature/{task_name}
2. Разработка функционала в созданной ветке
3. Перед мерджем в develop:
    - Стянуть последние изменения из develop: `git pull origin develop`
    - Разрешить конфликты если они есть
    - Протестировать работоспособность
4. Создать pull request в develop
5. После проверки кода и апрува - выполнить merge в develop
