# Развёртывание фото-будки на новой машине

Полная инструкция, как скопировать проект на другую машину и запустить
фото-будку (киоск + генерация через OpenRouter + печать на DNP QW410).

---

## 1. Получить код

Склонировать репозиторий (URL замените на актуальный GitLab/GitHub remote):

```bash
git clone <URL-репозитория> VEF_budka_v2
cd VEF_budka_v2
```

## 2. Проверить зависимости машины

Нужны: **git**, **Node.js 20+**, **Docker + docker compose** (для готового стека),
и Python 3.11+ (только если запускать backend напрямую, без Docker).

```bash
git --version
node --version
docker --version
docker compose version
```

## 3. Настроить доступ к модельному API (OpenRouter)

Скопировать примеры env и вписать ключ:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

В `backend/.env` указать реальный провайдер и ключ:

```env
IMAGE_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-image-2
```

Для быстрого теста без ключа оставьте `IMAGE_PROVIDER=demo` (локальная обработка).

> `backend/.env` и `frontend/.env.local` в git **не попадают** (в .gitignore),
> ключ никуда не утекает.

## 4. Управление конфигурацией (важно!)

Все высокоуровневые настройки — формат фото, печать, таймер — лежат в
одном файле **`booth.config.toml`** в корне проекта. Перед запуском
проверьте/поправьте его (комментарии внутри описывают всё подробно):

```toml
[image]
aspect_ratio = "1:1"   # формат генерируемого фото

[print]
enabled = true
queue = "DP-QW410"
media = "w288h288"     # 4x4
width_px = 1200
height_px = 1200
dpi = 300
fit = "fit"            # "fit"=целиком | "fill"=в край

timer:
countdown_seconds = 5
```

Смена формата фото = правая `aspect_ratio` в `[image]` и `media/width_px/height_px`
в `[print]` (пропорции должны совпадать). После правки — перезапустить backend
(и frontend, если меняли `[timer]`).

## 5. Настроить принтер DNP QW410 (Linux/CUPS)

На целевой машине подключите принтер по USB и запустите от root скрипт
(ставит Gutenprint, создаёт очередь `DP-QW410`, убирает белые рамки):

```bash
cd backend/scripts
sudo bash setup-printer.sh
```

Проверка очереди:

```bash
lpstat -p
```

> Скрипт по умолчанию создаёт очередь на **4×6** (`media=w288h432`).
> Для 4×4 замените в скрипте `w288h432` → `w288h288` в строках `lpadmin`
> и `ImageableArea`, либо просто переключите media в `booth.config.toml`.
> Имя очереди (`DP-QW410`) должно совпадать с `print.queue` в конфиге.

## 6. Запуск

### Вариант A — Docker (рекомендуется)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend/API: http://localhost:8000 (health-check: `/health`, конфиг: `/config`)

Печать из контейнера требует доступа к CUPS хоста — при необходимости
пробросьте `/var/run/cups` и `cups` в контейнер backend.

### Вариант B — вручную (разработка)

Терминал 1 — backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Терминал 2 — frontend:

```bash
cd frontend
npm install
npm run dev          # dev-сервер, http://localhost:3000
npm run desktop      # (опц.) полноэкранный киоск Electron
```

## 7. Проверка

```bash
# backend-тесты
cd backend && python3 -m pytest

# frontend: типы + сборка
cd frontend && npm run typecheck && npm run build
```

Эндпоинт `GET /api/config` должен вернуть значения из `booth.config.toml`
(`image`, `print`, `timer`) — это подтверждает, что конфиг прочитан.

## 8. Что проверить в боевом режиме

- Камера доступна (в Docker — проброс `/dev/video0`; в Electron — разрешение камеры).
- Принтер доступен и очередь активна (`lpstat -p`).
- Ключ OpenRouter активен и модель корректно отвечает.
- Имя очереди принтера совпадает с `print.queue` в `booth.config.toml`.
