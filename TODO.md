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
- [x] feat: build config REST resources
  - [x] API key
  - [x] POST
  - [x] GET
  - [x] GET ALL
  - [x] DELETE
- [x] chore: dev env
  - [x] Should I just set up debug by default?
  - [x] Hoist docker compose to monorepo root
  - [x] Can I get fid of local dir?
  - [x] Do I really need UV?
  - [x] Update READMEs to remove consider adding scripts
- [x] feat: build songs REST resources
  - [x] POST
  - [x] GET
  - [x] DELETE
  - [x] PATCH
  - [x] GET ALL
- [x] refactor: common models for rest resources
- [ ] infra: create `song_processing_events` queue
- [ ] infra: build file storage for converted songs
- [ ] build: create CI
- [ ] test: add unit tests
- [ ] terst add web e2e tests
- [ ] feat: build playlist REST resources
- [ ] chore: host OpenAPI spec

## v4

- [ ] feat: default color for version
- [ ] feat: create admin interface
- [ ] refactor: use websocket for song conversion & playlist deployment

## v5

- [ ] feat: create user REST resources
- [ ] feat: implement idp for admin
- [ ] refactor: more types on lambdas
