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

# Установка контейнеров postgres и mongo

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