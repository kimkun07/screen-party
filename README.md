# Screen Party

[프로젝트 설명]

## Install

1. Prerequisites:

   - [Node.js](https://github.com/nvm-sh/nvm?tab=readme-ov-file#usage) v20+ (Developed with v23.5.0)
   - [pnpm](https://pnpm.io/installation#using-npm) v9+ (Developed with v9.15.2)

1. Clone the repository:

   ```sh
   git clone https://github.com/kimkun07/screen-party.git
   cd screen-party
   ```

1. Install dependencies:

   ```sh
   pnpm install --frozen-lockfile
   ```

## Usage

### Development

- Run all applications simultaneously:
  ```sh
  pnpm run dev
  ```
- Run specific applications:

  ```sh
  # Run electron app
  pnpm run dev --filter=desktop

  # Run web app
  pnpm run dev --filter=web
  ```

### Build [Not tested]

- Build all applications:
  ```sh
  pnpm run build
  ```
- Build specific applications:

  ```sh
  # Build electron app
  pnpm run build --filter=desktop

  # Build web app
  pnpm run build --filter=web
  ```

## Workflows

- `ci.yml`: prettier and eslint

## Monorepo Structure

```
screen-party/
├── apps/
│   ├── desktop/    # Electron host application
│   └── web/        # SvelteKit web client
└── packages/       # Shared packages and utilities
```
