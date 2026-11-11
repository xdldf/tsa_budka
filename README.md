# «Цифровой алмаз» — ИИ-фотобудка

Touch-first kiosk for the «Цифровой алмаз» forum. It is based on the proven
`VEF_budka_v2` architecture and adds format selection before the visual theme.

## Visitor flow

1. Choose a print format:
   - **10 × 10 cm (1:1)** — one photo;
   - **10 × 15 cm** — one portrait photo;
   - **10 × 15 cm / two strips** — six different captures composed as two
     5 × 15 cm columns, three square photos per column.
2. Choose one of six event themes: Digital Diamond, Lena Pillars, Sakha Anime,
   Arctic Cyberpunk, Pixel Yakutsk, or Mammoth Party.
3. Take one or six photos. Every capture has a retake step and the strip flow
   shows progress from 1 to 6.
4. Wait for AI generation, preview the exact print layout, print, or download
   through the configured QR sharing service.

The two-strip format produces a 1200 × 1800 px sheet for 10 × 15 cm media. A
QW410 can print the sheet directly. Physical separation into two 5 × 15 cm
strips requires center-perforated media or a compatible finishing workflow;
the standard QW410 cutter cuts across the paper path and cannot split this
layout lengthwise.

## Stack

- Next.js 15, TypeScript, Zustand, Tailwind, Electron kiosk shell.
- FastAPI, Pydantic, Pillow, asynchronous in-memory generation jobs.
- Demo image provider for offline development and OpenRouter for production.
- CUPS printing with automatic 10 × 10 / 10 × 15 media selection from the
  generated raster dimensions.

## Run locally

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

Open `http://localhost:3000`. The API runs on `http://localhost:8000`.
`IMAGE_PROVIDER=demo` works without credentials. For real generation:

```env
IMAGE_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-image-2
```

## Desktop kiosk

```bash
cd frontend
npm install
npm run desktop
```

The Electron shell uses a 720 × 1280 portrait kiosk layout and grants camera
access. See [SETUP.md](SETUP.md) for autostart, Docker kiosk, camera and printer
setup.

## Verify

```bash
cd backend && python3 -m pytest -q
cd frontend && npm ci && npm run typecheck && npm run build
cd .. && python3 -m unittest -q tools/test_print_single_strip.py
```

The root `booth.config.toml` controls the QW410 queue, print quality and camera
countdown. Output format is selected per visitor and is no longer fixed by that
file.

## QW410 experimental single-cut tool

`tools/print_single_strip.py` is preserved from the printer experiments. It is
not used by the kiosk's two-strip 10 × 15 layout. Run it with `--preview-only`
before using its experimental direct cutter command.
