# 8090 xRx Voice AI Assistant

This demo application allows users to record audio, send it to a backend, receive audio responses via WebSocket, and play the received audio. Additionally, it includes a chat interface and a feature to fetch and render markdown data from a backend.

## Getting Started

### Prerequisites

Install `Docker`, `Nodejs`, `npm` with [homebrew](https://formulae.brew.sh/) on MacOS or `apt-get update` on Debian/Ubuntu based Linux systems
```bash
brew install node@18
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