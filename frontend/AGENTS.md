<!-- BEGIN:nextjs-agent-rules -->
# Frontend Notes

- Follow the repo root `AGENTS.md` first.
- This repo uses Next.js 16 and React 19. Read the relevant guide in `node_modules/next/dist/docs/` before changing framework conventions.
- Keep API traffic routed through `NEXT_PUBLIC_API_URL`, with only a guarded local fallback for development.
- Preserve the Cloud Run production start path: `next start -H 0.0.0.0 -p 8080`.
- Extend the existing builder assistant UI instead of replacing it with generic templates.
<!-- END:nextjs-agent-rules -->
