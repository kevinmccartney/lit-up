# Lit Up

A platform for creating and hosting custom music playlists with a beautiful, modern web interface.

## Overview

Lit Up enables you to create personalized music playlists that can be shared and played through a web-based music player. The platform handles song processing, playlist generation, and provides a responsive UI optimized for both desktop and mobile devices.

## Architecture

This is a monorepo containing multiple projects that work together to deliver the Lit Up platform:

### Projects

#### 🎨 [`projects/ui`](./projects/ui)

The frontend React application built with Vite, TypeScript, and Tailwind CSS. This is the user-facing music player interface that provides:

- Music playback with auto-advance
- Responsive design for mobile and desktop
- Theme customization
- Progressive Web App (PWA) support
- Versioned deployments

#### 🔧 [`projects/api`](./projects/api)

Python-based scripts for processing and managing playlists. Currently implemented as standalone scripts, these will be refactored into a proper REST API in future versions. Current capabilities include:

- Song processing and conversion
- Playlist concatenation for iOS compatibility
- Configuration generation
- Duration analysis
- Favicon generation

#### 👤 [`projects/admin`](./projects/admin)

Admin interface for managing playlists and songs (coming soon). This will be a React web application that allows administrators to:

- Process songs
- Build playlists
- Manage content

#### ☁️ [`projects/infra`](./projects/infra)

Terraform infrastructure as code for AWS deployment. Manages:

- S3 bucket for static site hosting
- CloudFront distribution for CDN
- Route53 DNS configuration
- SSL certificate management
- Versioned deployments

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.x
- Terraform (for infrastructure)
- AWS credentials configured
- Task (task runner) - install from [taskfile.dev](https://taskfile.dev)

### Quick Start

1. **Set up environment variables**

   ```bash
   cp .env.sample .env
   # Edit .env with your AWS credentials
   ```

2. **Initialize infrastructure** (first time only)

   ```bash
   task infra:init
   task infra:apply
   ```

3. **Run the development server**

   ```bash
   task ui:dev
   ```

4. **Deploy to production**
   ```bash
   task ui:deploy
   ```

## Configuration

Playlists are configured via `lit_up_config.yaml` at the root of the repository. This file defines:

- Header message
- Favicon emoji
- Song list with metadata (title, artist, duration, album art, etc.)
- Secret tracks (easter eggs)

See `lit_up_config.yaml.sample` for an example configuration.

## Development

The project uses [Task](https://taskfile.dev) for task automation. Common tasks include:

- `task ui:dev` - Start development server
- `task ui:build` - Build for production
- `task ui:preview` - Preview production build
- `task ui:deploy` - Deploy to S3/CloudFront
- `task api:process_songs` - Process songs from config
- `task api:generate_config` - Generate app config JSON
- `task infra:plan` - Preview infrastructure changes
- `task infra:apply` - Apply infrastructure changes

See `taskfile.yaml` for the complete list of available tasks.

## Roadmap

For detailed roadmap and planned features, see [TODO.md](./TODO.md).

High-level roadmap:

- **v1/v2**: Core functionality, themes, versioning ✅
- **v3**: Monorepo restructure, REST API, admin interface
- **v4**: Media processing services, conversion tracking
- **v5**: User management, authentication

## License

MIT
