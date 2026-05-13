# Infrastructure

Local dependencies for the legal multi-agent MVP.

```bash
cp ../.env.example ../.env
docker compose --env-file ../.env -f docker-compose.yml up -d
```

Services:

- MySQL: `localhost:3306`
- Redis: `localhost:6379`
- RabbitMQ: `localhost:5672`, management UI `localhost:15672`
- MinIO: API `localhost:9000`, console `localhost:9001`
- Milvus: `localhost:19530`
