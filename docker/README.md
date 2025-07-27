# Docker Directory

This directory contains Docker configuration files.

## Docker Files
- **Dockerfile** - Main container image definition
- **docker-compose.yml** - Local development setup
- **docker-compose.remote.yml** - Remote deployment setup

## Usage
`ash
# Local development
docker-compose up

# Remote deployment
docker-compose -f docker-compose.remote.yml up
`
