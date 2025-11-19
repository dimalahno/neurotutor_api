## 1 Системный дизайна

### 1.1. Основные сервисы

1. **Frontend (React SPA)**

   * Авторизация через OAuth2/Google или логин-пароль.
   * Работает только с REST-API Backend (FastAPI).

2. **API Backend / Learning Engine (FastAPI + Postgres + Mongo)**
   Логически можно разделить модули:

   * **Auth & Users**

     * управление пользователями, ролями,
     * выдача JWT/refresh,
     * связь с Google OAuth.

   * **Content API (Course Service Gateway)**

     * читает курсы/уроки из Mongo (`courses`, `lessons`),
     * прячет от клиента сложную структуру JSON-урока (SPA получает уже «подчищенные» DTO).

   * **Learning Engine**

     * создаёт/ведёт `sessions`,
     * управляет переходами между units/activities,
     * решает, какое упражнение показать дальше (на основе `user_progress`, `attempts`, ML-рекомендаций),
     * создаёт записи в `attempts`, `pronunciation_samples`, `user_progress`.

   * **User Progress Service (можно как модуль / отдельный сервис)**

     * считает aggregate-метрики по уроку и по курсу,
     * отдаёт дашборды для пользователя/препода.

   * **ML Orchestrator (внутри Backend или отдельный сервис)**

     * ставит запросы на оценку в очередь (RabbitMQ/Kafka/SQS),
     * принимает колбэки от ML-микросервисов,
     * обновляет `attempts.score`, `attempts.feedback`, `pronunciation_samples.score`.

3. **ML-микросервисы**

   * **NLP Scorer**

     * Оценка грамматики/лексики, short-answer-check, writing feedback.
   * **ASR + Pronunciation**

     * Принимает аудио-ключ из S3,
     * Возвращает транскрипт + фонемные скоринги.
   * **LLM Feedback / Dialogue Generator**

     * Работает по шаблонам systemPrompt из Mongo-урока (как у вас в `llmCheck` блоках init_lessons.json ),
     * Генерирует personalized feedback, доп. упражнения.

4. **Хранилища**

   * **MongoDB**

     * Контент курса: `courses`, `lessons` (структура units/activities, ссылки на media, prompts, llmCheck).
   * **Postgres**

     * пользователи, прогресс, попытки, сессии, связи с курсами.
   * **S3/MinIO**

     * медиа-файлы уроков,
     * голосовые записи пользователей.

---

### 1.2. Основные потоки

1. **Начало урока**

* React → `POST /lessons/{lessonId}/sessions`
* Backend:

  * проверяет, что пользователь записан на курс (enrollments),
  * создаёт `sessions` (если нет незаконченной),
  * читает lesson из Mongo,
  * отдаёт клиенту первый unit+activity, плюс id сессии.

2. **Ответ на задание (текст/выбор)**

* React → `POST /lessons/{lessonId}/activities/{exerciseId}/attempts`

  * body: ответ, session_id, тип input.
* Backend:

  * создаёт запись в `attempts` со status='pending' или 'scored' (если правило простое),
  * для rule-based: проверяет на месте → обновляет score/feedback и статус='scored',
  * для LLM/ML: ставит задачу в очередь, оставляет статус='pending'.
* ML-микросервис:

  * обрабатывает → `POST /internal/ml/attempts/{id}/score`
* Backend:

  * обновляет `attempts.score`, `attempts.feedback`, статус='scored',
  * пересчитывает `user_progress` (completion, mastery).

3. **Произношение**

* React:

  * грузит файл на S3 (pre-signed URL) или через Backend.
* Backend:

  * создаёт `pronunciation_samples` с ссылкой на файл и привязкой к `attempt`,
  * ставит задачу в очередь для ASR/Pronunciation service.
* ASR Service:

  * пишет в `transcription`, `transcription_meta`, `score`,
  * возможно триггерит LLM-feedback (короткий текст).

---

## 2. Примерный REST API (без подробного кода)

### 2.1. Auth / Users

* `POST /auth/register`
* `POST /auth/login`
* `POST /auth/oauth/google`
* `POST /auth/refresh`
* `GET  /me`
* `GET  /me/enrollments`
* `GET  /me/progress` — сводка по всем курсам/урокам.

### 2.2. Courses / Lessons (чтение контента из Mongo)

* `GET /courses`
* `GET /courses/{courseId}`
* `POST /courses/{courseId}/enroll` — создать запись в `enrollments`.
* `GET /lessons/{lessonId}` — структура урока (units/activities) с урезанной информацией (без внутренних systemPrompt и т.п.).
* `GET /lessons/{lessonId}/next-activity?sessionId=...` — отдать следующий шаг по логике Learning Engine.

### 2.3. Sessions

* `POST /lessons/{lessonId}/sessions`
* `GET  /sessions/{sessionId}`
* `PATCH /sessions/{sessionId}` — обновить state, завершить сессию (finished_at).

### 2.4. Attempts & Checking

* `POST /lessons/{lessonId}/activities/{exerciseId}/attempts`

  * тело: { sessionId, inputText / options / inputMeta }.
* `GET  /lessons/{lessonId}/activities/{exerciseId}/attempts?limit=...`
* `GET  /attempts/{attemptId}`

**Внутренние ML-эндпоинты (не для фронта):**

* `POST /internal/ml/attempts/{attemptId}/score`
* `POST /internal/ml/pronunciation/{sampleId}/score`

### 2.5. Pronunciation

* `POST /lessons/{lessonId}/activities/{exerciseId}/pronunciation`

  * либо upload, либо уже key S3 в теле.
* `GET  /pronunciation/{sampleId}` — метаданные, score.

### 2.6. Progress

* `GET /me/lessons/{lessonId}/progress` — данные из `user_progress`.
* `GET /me/courses/{courseId}/progress` — агрегированный прогресс по курсу (либо из `enrollments.stats`, либо отдельной таблицы).

