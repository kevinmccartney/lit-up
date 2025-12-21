# TODO

## v1/v2

- [x] Host site on kevinmccartney.is
- [x] Upload actual song files
- [x] Easter egg
- [x] Load songs
- [x] Determine track length from file
- [x] Play next song when last one ends
- [x] Dynamic title
- [x] Finalize layout
- [x] Favicon
- [x] Create themes
  - [x] Fix easter egg hover (add more color weights)
- [x] Bug: Make prev button go back to beginning of track when the track is in flight
- [x] Bug: why are the tracks not auto-advancing when my phone is locked?
- [x] feat: support versioned sites
- [x] chore: deploy v2
- [x] build: have app build task clear out the dist dir
- [x] feat: settings menu

## v3

- [x] refactor: monorepo restructure
- [x] chore: git hooks
- [x] chore: linting/static analysis quality tools
  - [x] eslint
  - [x] prettier
  - [x] isort
  - [x] mypy
  - [x] black
  - [x] pylint/flake8
  - [x] tflint
  - [x] tf format
- [x] chore: add instructions file
- [x] refactor: clean up repo in general (with the help of cursor 🤖)
- [ ] feat: build config REST resources
  - [x] API key
  - [ ] POST
  - [ ] GET
- [ ] chore: dev env
  - [x] Should I just set up debug by default?
  - [x] Hoist docker compose to monorepo root
  - [x] Can I get fid of local dir?
  - [x] Do I really need UV?
  - [x] Update READMEs to remove consider adding scripts
- [ ] feat: build songs REST resources
- [ ] feat: build playlist REST resources
- [ ] chore: host OpenAPI spec
- [ ] infra: build file storage for converted songs
- [ ] build: create CI
- [ ] feat: default color for version
- [ ] feat: create admin interface

## v4

- [ ] feat: host media (image/song) processing services
- [ ] feat: media processing conversion tracking (would I need websocket for this?)

## v5

- [ ] feat: create user REST resources
- [ ] feat: implement idp for admin
