# Deployment Directory

## Current Architecture

PromptCraft-Hybrid now uses a hybrid deployment model:

- **Application Services**: Deployed to Ubuntu VM at 192.168.1.205
- **Vector Database**: External Qdrant instance on Unraid at 192.168.1.16:6333

## Deployment Method

Use the Docker Compose configuration in `docs/planning/docker-compose.yaml` to deploy to the Ubuntu VM.

```bash
# On Ubuntu VM (192.168.1.205)
docker compose -f docs/planning/docker-compose.yaml up -d
```

## Deprecated Azure Deployment

The Azure Bicep templates in `deprecated-azure/` are no longer used as the project has migrated to the Ubuntu VM deployment model. These files are retained for historical reference only.

**Last Azure deployment**: Never used in production
**Migration date**: 2025-06-30
**Reason for deprecation**: Cost optimization and simplified on-premise deployment