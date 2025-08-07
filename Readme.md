# Bioprocess Analytics Microservices

- Copy each directory into your project.
- Use `docker-compose up --build` from root for full stack with DBs.
- `gateway` listens on port 8080 and routes to `auth`, `user`, `batch` services.
- See `.env.example` for environment variable templates.

API Docs:
- Gateway: http://localhost:8080/docs
- Auth:    http://localhost:9001/docs
- User:    http://localhost:9002/docs
- Batch:   http://localhost:9003/docs
