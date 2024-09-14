# xRx Voice AI Assistant

This demo application allows users to record audio, send it to a backend, receive audio responses via WebSocket, and play the received audio. Additionally, it includes a chat interface and a feature to fetch and render markdown data from a backend.

## Getting Started

### Prerequisites

Install `Docker`, `Nodejs`, `npm` with [homebrew](https://formulae.brew.sh/) on MacOS or `apt-get update` on Debian/Ubuntu based Linux systems

```bash
brew install node@18
```

Then set the following environment variable in the  `.env` file:

```bash
# For the shoe store UI
NEXT_PUBLIC_AGENT="shoe-agent"

# For the pizza store UI
NEXT_PUBLIC_AGENT="pizza-agent"
```

### IDE Setup

Add the following to your `.vscode/settings.json`

```
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "always"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}

```

## How To Run

### Locally with Docker

```bash
docker build -t nextjs-docker .
docker run -p 3000:3000 nextjs-docker
```

### Locally without Docker

```bash
npm install
npm run dev  -- -p 3000
```

Once the app/container is up and running, visit the client at [http://localhost:3000](http://localhost:3000)

### Debug Mode Instructions

Add this to your `.vscode/settings.json` and then run the `Next.js: Debug Full Stack` configuration from the debugger tab.

```
{
    "version": "0.2.0",
    "configurations": [

              {
                "type": "node",
                "request": "launch",
                "name": "Next.js: Debug Server-Side",
                "program": "${workspaceFolder}/nextjs-client/node_modules/next/dist/bin/next",
                "args": ["dev"],
                "cwd": "${workspaceFolder}/nextjs-client",
                "console": "integratedTerminal",
                "env": {
                  "NODE_OPTIONS": "--inspect"
                }
              },
              {
                "type": "chrome",
                "request": "launch",
                "name": "Next.js: Debug Client-Side",
                "url": "http://localhost:3000",
                "webRoot": "${workspaceFolder}/nextjs-client"
              },
    ],"compounds": [
        {
          "name": "Next.js: Debug Full Stack",
          "configurations": ["Next.js: Debug Server-Side", "Next.js: Debug Client-Side"]
        }
    ]
}
```