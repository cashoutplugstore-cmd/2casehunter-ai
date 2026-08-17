# Architecture

## Flow

Sources -> Research -> Fact Check -> Story Score -> Script -> Voice/Assets -> FFmpeg Render -> Review -> YouTube -> Analytics

## Apps

- `apps/web`: mobile-first dashboard (Next.js + TypeScript)
- `apps/worker`: Python processing API/workers
- `supabase`: migrations, functions, database/storage integration

## Core services

- OpenAI: research assistance, structured script generation and metadata
- YouTube Data API v3: channel/video metadata and official upload/scheduling
- YouTube Analytics API: performance metrics
- FFmpeg: audio/video composition and format conversion
- Supabase/Postgres: persistent state

## Content safety

Use third-party channels as discovery signals only. Final videos must be original and source-backed. Store source URLs and research notes with each story.

## MVP output

- Short: 9:16
- Long: 16:9
- Arabic-first UI/content
