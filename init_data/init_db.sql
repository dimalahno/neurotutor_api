-- ============================================
--  БАЗОВАЯ НАСТРОЙКА
-- ============================================

-- CREATE SCHEMA IF NOT EXISTS public;

-- ============================================
--  ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОБНОВЛЕНИЯ updated_at
-- ============================================

CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS trigger AS
$$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_updated_at() IS 'Триггер-функция: автоматически обновляет поле updated_at при изменении строки';

-- ============================================
--  ТАБЛИЦА: d_user_status
--  Статус пользователя
-- ============================================
create table if not exists d_user_status
(
    id          smallserial primary key,
    code        varchar(8)               not null,
    description varchar(32)              not null,
    status      numeric(1) default 1
        constraint d_user_status_status_check
            check (status = ANY (ARRAY [(1)::numeric, (2)::numeric])),
    date_entry  timestamp  default now() not null
);

comment on table d_user_status is 'Статус пользователя';
comment on column d_user_status.id is 'Идентификатор';
comment on column d_user_status.code is 'Код';
comment on column d_user_status.description is 'Описание';
comment on column d_user_status.status is 'Статус(1 - Активный, 2 - Неактивный)';
comment on column d_user_status.date_entry is 'Дата записи';

-- ============================================
--  ТАБЛИЦА: d_user_role
--  Роли пользователя
-- ============================================
create table d_user_role
(
    id          smallserial primary key,
    code        varchar(8)               not null,
    description varchar(32)              not null,
    status      numeric(1) default 1
        constraint d_user_role_status_check
            check (status = ANY (ARRAY [(1)::numeric, (2)::numeric])),
    date_entry  timestamp  default now() not null
);

comment on table d_user_role is 'Роли';
comment on column d_user_role.id is 'Идентификатор';
comment on column d_user_role.code is 'Код';
comment on column d_user_role.description is 'Описание';
comment on column d_user_role.status is 'Статус(1 - Активный, 2 - Неактивный)';
comment on column d_user_role.date_entry is 'Дата записи';

-- ============================================
--  ТАБЛИЦА: users
--  Пользователи системы (ученики / преподаватели / админы)
-- ============================================

CREATE TABLE IF NOT EXISTS users
(
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR     NOT NULL UNIQUE,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    middle_name   VARCHAR(50),
    password_hash VARCHAR(300),
    jwt           VARCHAR(500),
    status_id     SMALLINT,
    created_at    timestamp   NOT NULL DEFAULT now(),
    updated_at    timestamp   NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS 'Пользователи системы: ученики, преподаватели, администраторы';
COMMENT ON COLUMN users.id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN users.email IS 'Основной e-mail пользователя (логин, уникальный)';
COMMENT ON COLUMN users.first_name IS 'Отображаемое имя пользователя (Имя)';
COMMENT ON COLUMN users.last_name IS 'Отображаемое имя пользователя (Фамилия)';
COMMENT ON COLUMN users.middle_name IS 'Отображаемое имя пользователя (Отчество)';
COMMENT ON COLUMN users.password_hash IS 'Хеш пароля пользователя (если не используем внешнюю аутентификацию)';
COMMENT ON COLUMN users.jwt IS 'jwt токен';
COMMENT ON COLUMN users.status_id IS 'Статус пользователя (d_user_status.id)';
COMMENT ON COLUMN users.created_at IS 'Дата и время создания записи о пользователе';
COMMENT ON COLUMN users.updated_at IS 'Дата и время последнего обновления записи о пользователе';

-- Триггер на обновление updated_at
CREATE TRIGGER trg_users_set_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- ============================================
--  ТАБЛИЦА: sessions
--  Сессии прохождения урока пользователем
-- ============================================

CREATE TABLE IF NOT EXISTS sessions
(
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT    NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    lesson_id   varchar   NOT NULL,
    started_at  timestamp NOT NULL DEFAULT now(),
    finished_at timestamp,
    state       JSONB     NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamp NOT NULL DEFAULT now(),
    updated_at  timestamp NOT NULL DEFAULT now()
);

COMMENT ON TABLE sessions IS 'Сессии прохождения конкретного урока пользователем';
COMMENT ON COLUMN sessions.id IS 'Уникальный идентификатор сессии урока';
COMMENT ON COLUMN sessions.user_id IS 'Ссылка на пользователя, который проходит урок';
COMMENT ON COLUMN sessions.lesson_id IS 'Идентификатор урока из MongoDB (строковый ID документа урока)';
COMMENT ON COLUMN sessions.started_at IS 'Дата и время начала сессии';
COMMENT ON COLUMN sessions.finished_at IS 'Дата и время завершения сессии, если урок завершён';
COMMENT ON COLUMN sessions.state IS 'JSON-состояние сессии: текущий шаг, последний exercise_id, вспомогательные данные';
COMMENT ON COLUMN sessions.created_at IS 'Дата и время создания записи о сессии';
COMMENT ON COLUMN sessions.updated_at IS 'Дата и время последнего обновления записи о сессии';

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_lesson ON sessions (lesson_id);

CREATE TRIGGER trg_sessions_set_updated_at
    BEFORE UPDATE
    ON sessions
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- ============================================
--  ТАБЛИЦА: attempts
--  Попытки выполнения упражнений
-- ============================================

CREATE TABLE IF NOT EXISTS attempts
(
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    session_id    BIGINT      REFERENCES sessions (id) ON DELETE SET NULL,
    lesson_id     varchar     NOT NULL,
    exercise_id   varchar     NOT NULL,
    attempt_order SMALLINT    NOT NULL DEFAULT 1,
    input_text    TEXT,
    input_meta    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    score         JSONB,
    feedback      JSONB,
    status        varchar(20) NOT NULL DEFAULT 'scored',
    created_at    timestamp   NOT NULL DEFAULT now(),
    updated_at    timestamp   NOT NULL DEFAULT now()
);

COMMENT ON TABLE attempts IS 'Попытки выполнения отдельных упражнений пользователями';
COMMENT ON COLUMN attempts.id IS 'Уникальный идентификатор попытки';
COMMENT ON COLUMN attempts.user_id IS 'Ссылка на пользователя, сделавшего попытку';
COMMENT ON COLUMN attempts.session_id IS 'Ссылка на сессию урока, в рамках которой выполнено упражнение (может быть NULL)';
COMMENT ON COLUMN attempts.lesson_id IS 'Идентификатор урока из MongoDB, к которому относится упражнение';
COMMENT ON COLUMN attempts.exercise_id IS 'Идентификатор упражнения из MongoDB (exercise_id внутри документа урока)';
COMMENT ON COLUMN attempts.attempt_order IS 'Порядковый номер попытки выполнения данного упражнения пользователем';
COMMENT ON COLUMN attempts.input_text IS 'Текстовый ввод пользователя (ответ, транскрипция речи и т.п.)';
COMMENT ON COLUMN attempts.input_meta IS 'JSON-метаданные входа: ссылки на аудио-файлы, технические параметры, дополнительная информация';
COMMENT ON COLUMN attempts.score IS 'JSON-оценка результата выполнения: баллы по критериям, общий score, вероятности и т.п.';
COMMENT ON COLUMN attempts.feedback IS 'JSON-структура с обратной связью для пользователя: комментарии, подсказки, исправления';
COMMENT ON COLUMN attempts.status IS 'Статус попытки: pending (ожидает проверки), scored (проверена), review_needed (нужен ручной пересмотр)';
COMMENT ON COLUMN attempts.created_at IS 'Дата и время создания записи о попытке';
COMMENT ON COLUMN attempts.updated_at IS 'Дата и время последнего обновления записи о попытке';

CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_attempts_lesson ON attempts (lesson_id);
CREATE INDEX IF NOT EXISTS idx_attempts_exercise ON attempts (exercise_id);

CREATE TRIGGER trg_attempts_set_updated_at
    BEFORE UPDATE
    ON attempts
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- ============================================
--  ТАБЛИЦА: user_progress
--  Агрегированный прогресс пользователя по урокам
-- ============================================

CREATE TABLE IF NOT EXISTS user_progress
(
    id                 BIGSERIAL PRIMARY KEY,
    user_id            BIGINT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    lesson_id          TEXT          NOT NULL,
    completion_percent NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    mastery_level      NUMERIC(5, 3) NOT NULL DEFAULT 0.0,
    last_activity_at   timestamp,                                  -- время последней активности по уроку
    stats              JSONB         NOT NULL DEFAULT '{}'::jsonb, -- агрегированные статистики: {attempts:15, avg_score:0.82}
    created_at         timestamp     NOT NULL DEFAULT now(),
    updated_at         timestamp     NOT NULL DEFAULT now(),
    CONSTRAINT user_progress_unique_user_lesson UNIQUE (user_id, lesson_id)
);

COMMENT ON TABLE user_progress IS 'Агрегированные данные о прогрессе пользователя по каждому уроку';
COMMENT ON COLUMN user_progress.id IS 'Уникальный идентификатор записи прогресса';
COMMENT ON COLUMN user_progress.user_id IS 'Ссылка на пользователя, к которому относится прогресс';
COMMENT ON COLUMN user_progress.lesson_id IS 'Идентификатор урока из MongoDB, по которому считается прогресс';
COMMENT ON COLUMN user_progress.completion_percent IS 'Процент завершения урока (0..100), например отношение выполненных упражнений к общему числу';
COMMENT ON COLUMN user_progress.mastery_level IS 'Уровень освоения материала по уроку (0..1), агрегированный показатель качества выполнения';
COMMENT ON COLUMN user_progress.last_activity_at IS 'Дата и время последней активности пользователя по данному уроку';
COMMENT ON COLUMN user_progress.stats IS 'JSON-статистика: количество попыток, средний score, количество дней подряд и т.п.';
COMMENT ON COLUMN user_progress.created_at IS 'Дата и время создания записи о прогрессе';
COMMENT ON COLUMN user_progress.updated_at IS 'Дата и время последнего обновления записи о прогрессе';

CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_progress (user_id);

CREATE TRIGGER trg_user_progress_set_updated_at
    BEFORE UPDATE
    ON user_progress
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ============================================
--  ТАБЛИЦА: courses
--  Курсы (метаданные + связь с Mongo courses)
-- ============================================

CREATE TABLE IF NOT EXISTS courses
(
    id              BIGSERIAL PRIMARY KEY,
    mongo_course_id VARCHAR(50)  NOT NULL UNIQUE,
    title           VARCHAR(100) NOT NULL,
    description     VARCHAR(256) NOT NULL,
    level           VARCHAR(2),
    created_at      timestamp    NOT NULL DEFAULT now(),
    updated_at      timestamp    NOT NULL DEFAULT now()
);

COMMENT ON TABLE courses IS 'Курсы: метаданные и связь с документами courses в MongoDB';
COMMENT ON COLUMN courses.id IS 'Уникальный идентификатор курса (BIGSERIAL)';
COMMENT ON COLUMN courses.mongo_course_id IS 'Идентификатор курса в MongoDB (например, _id или slug из коллекции courses)';
COMMENT ON COLUMN courses.title IS 'Название курса (отображается пользователю)';
COMMENT ON COLUMN courses.description IS 'Краткое описание курса';
COMMENT ON COLUMN courses.level IS 'Уровень английского, на который рассчитан курс (A2 / B1 / B2 и т.п.)';
COMMENT ON COLUMN courses.created_at IS 'Дата и время создания записи о курсе';
COMMENT ON COLUMN courses.updated_at IS 'Дата и время последнего обновления записи о курсе';

CREATE INDEX IF NOT EXISTS idx_courses_level ON courses (level);

CREATE TRIGGER trg_courses_set_updated_at
    BEFORE UPDATE
    ON courses
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- ============================================
--  ТАБЛИЦА: enrollments
--  Записи пользователей на курсы
-- ============================================

CREATE TABLE IF NOT EXISTS enrollments
(
    id               BIGSERIAL PRIMARY KEY,
    user_id          BIGINT        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    course_id        BIGINT        NOT NULL REFERENCES courses (id) ON DELETE CASCADE,
    status           TEXT          NOT NULL DEFAULT 'active',    -- active / completed / dropped / frozen
    started_at       timestamp     NOT NULL DEFAULT now(),
    completed_at     timestamp,
    last_activity_at timestamp,
    progress_percent NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    stats            JSONB         NOT NULL DEFAULT '{}'::jsonb, -- агрегированные статистики по курсу
    created_at       timestamp     NOT NULL DEFAULT now(),
    updated_at       timestamp     NOT NULL DEFAULT now(),
    CONSTRAINT enrollments_unique_user_course UNIQUE (user_id, course_id)
);

COMMENT ON TABLE enrollments IS 'Записи пользователей на курсы (many-to-many между users и courses)';
COMMENT ON COLUMN enrollments.id IS 'Уникальный идентификатор записи (BIGSERIAL)';
COMMENT ON COLUMN enrollments.user_id IS 'Ссылка на пользователя, который записан на курс';
COMMENT ON COLUMN enrollments.course_id IS 'Ссылка на курс, на который записан пользователь';
COMMENT ON COLUMN enrollments.status IS 'Статус записи: active (проходит), completed (завершил), dropped (бросил), frozen (заморозил)';
COMMENT ON COLUMN enrollments.started_at IS 'Дата и время начала прохождения курса';
COMMENT ON COLUMN enrollments.completed_at IS 'Дата и время завершения курса (если завершен)';
COMMENT ON COLUMN enrollments.last_activity_at IS 'Дата и время последней активности пользователя по этому курсу';
COMMENT ON COLUMN enrollments.progress_percent IS 'Агрегированный прогресс по курсу в процентах (0..100)';
COMMENT ON COLUMN enrollments.stats IS 'JSON-статистика: количество завершенных уроков, средний score, streak по курсу и т.п.';
COMMENT ON COLUMN enrollments.created_at IS 'Дата и время создания записи о зачислении на курс';
COMMENT ON COLUMN enrollments.updated_at IS 'Дата и время последнего обновления записи о зачислении';

CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments (user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments (status);

CREATE TRIGGER trg_enrollments_set_updated_at
    BEFORE UPDATE
    ON enrollments
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ============================================
--  ТАБЛИЦА: lessons_files
--  Аудиозаписи для прослушивания
-- ============================================
create table lessons_files
(
    id         bigserial primary key,
    file_name  varchar(256),
    file_path  varchar(256),
    file_size  bigint,
    mime_type  varchar(256),
    state      numeric(1) default 1,
    created_at timestamp  default now() not null,
    updated_at timestamp  default now() not null
);

comment on table lessons_files is 'Аудио файлы для уроков';
comment on column lessons_files.id is 'Идентификатор';
comment on column lessons_files.file_name is 'Имя файла';
comment on column lessons_files.file_path is 'Путь файла';
comment on column lessons_files.file_size is 'Размер файла';
comment on column lessons_files.mime_type is 'MediaType';
comment on column lessons_files.state is 'Состояние';
comment on column lessons_files.created_at is 'Дата создания';
comment on column lessons_files.updated_at is 'Дата обновления';

create index idx_lessons_files_file_name on lessons_files (file_name);

CREATE TRIGGER trg_lessons_files_set_updated_at
    BEFORE UPDATE
    ON lessons_files
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ============================================
--  ТАБЛИЦА: pronunciation_samples
--  Аудиозаписи произношения (сырые данные + связь с S3/MinIO)
-- ============================================

CREATE TABLE IF NOT EXISTS pronunciation_samples
(
    id                 BIGSERIAL PRIMARY KEY,
    user_id            BIGINT       NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    attempt_id         BIGINT       REFERENCES attempts (id) ON DELETE SET NULL,
    lesson_id          varchar      NOT NULL,
    exercise_id        varchar      NOT NULL,
    file_path          varchar(256) NOT NULL,
    file_name          varchar(256) NOT NULL,
    file_format        varchar(10),
    mime_type          varchar(256),
    transcription      TEXT,
    transcription_meta JSONB        NOT NULL DEFAULT '{}'::jsonb,
    score              JSONB,
    created_at         timestamp    NOT NULL DEFAULT now(),
    updated_at         timestamp    NOT NULL DEFAULT now()
);

COMMENT ON TABLE pronunciation_samples IS 'Аудиозаписи произношения пользователей, хранящиеся в S3/MinIO (метаданные и ссылки)';
COMMENT ON COLUMN pronunciation_samples.id IS 'Уникальный идентификатор аудио-записи';
COMMENT ON COLUMN pronunciation_samples.user_id IS 'Ссылка на пользователя, чей голос записан';
COMMENT ON COLUMN pronunciation_samples.attempt_id IS 'Ссылка на попытку выполнения упражнения, к которой относится данная аудиозапись (может быть NULL при тестах/диагностике)';
COMMENT ON COLUMN pronunciation_samples.lesson_id IS 'Идентификатор урока из MongoDB, для которого сделана запись';
COMMENT ON COLUMN pronunciation_samples.exercise_id IS 'Идентификатор упражнения из MongoDB, к которому относится запись';
COMMENT ON COLUMN pronunciation_samples.file_path IS 'Путь к файлу';
COMMENT ON COLUMN pronunciation_samples.file_name IS 'Имя файлу';
COMMENT ON COLUMN pronunciation_samples.file_format IS 'Формат аудиофайла (например, wav, mp3, ogg)';
COMMENT ON COLUMN pronunciation_samples.mime_type IS 'Mime Type';
COMMENT ON COLUMN pronunciation_samples.transcription IS 'Текстовая расшифровка (ASR) аудиозаписи, если выполнялась';
COMMENT ON COLUMN pronunciation_samples.transcription_meta IS 'JSON-метаданные ASR: модель, язык, confidence, время обработки и т.п.';
COMMENT ON COLUMN pronunciation_samples.score IS 'JSON-оценка произношения: баллы по фонетике, интонации, темпу и пр.';
COMMENT ON COLUMN pronunciation_samples.created_at IS 'Дата и время создания записи об аудио';
COMMENT ON COLUMN pronunciation_samples.updated_at IS 'Дата и время последнего обновления записи об аудио';

CREATE INDEX IF NOT EXISTS idx_pron_samples_user ON pronunciation_samples (user_id);
CREATE INDEX IF NOT EXISTS idx_pron_samples_attempt ON pronunciation_samples (attempt_id);
CREATE INDEX IF NOT EXISTS idx_pron_samples_lesson ON pronunciation_samples (lesson_id);
CREATE INDEX IF NOT EXISTS idx_pron_samples_exercise ON pronunciation_samples (exercise_id);

CREATE TRIGGER trg_pron_samples_set_updated_at
    BEFORE UPDATE
    ON pronunciation_samples
    FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
