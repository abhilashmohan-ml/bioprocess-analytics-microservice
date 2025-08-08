# Bioprocess Analytics : Design Specs

**Folder Structure**

bioprocess-analytics-micro/
├── README.md
├── docker-compose.yml
├── .env.example
├── gateway/
│   ├── main.py
│   ├── requirements.txt
├── services/
│   ├── auth/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api.py
│   │   │   ├── models.py
│   │   │   ├── db.py
│   │   │   ├── auth.py
│   │   │   ├── exceptions.py
│   │   │   └── utils.py
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   └── Dockerfile
│   ├── user/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api.py
│   │   │   ├── models.py
│   │   │   ├── db.py
│   │   │   ├── users.py
│   │   │   ├── exceptions.py
│   │   │   └── utils.py
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   └── Dockerfile
│   └── batch/
│       ├── app/
│       │   ├── main.py
│       │   ├── api.py
│       │   ├── models.py
│       │   ├── db.py
│       │   ├── batches.py
│       │   ├── qcbatches.py
│       │   ├── exceptions.py
│       │   └── utils.py
│       ├── requirements.txt
│       ├── alembic.ini
│       ├── alembic/
│       └── Dockerfile



**System Architecture**

```mermaid
graph TD
  Client((Client))
  Client --> Gateway[API Gateway]
  Gateway --> AuthSVC[Auth Service]
  Gateway --> UserSVC[User Service]
  Gateway --> BatchSVC[Batch Service]
  AuthSVC --> AuthDB[(PostgreSQL Auth DB)]
  UserSVC --> UserDB[(PostgreSQL User DB)]
  BatchSVC --> BatchDB[(PostgreSQL Batch DB)]
```



**Batch Entity Relationship**

```mermaid
erDiagram
    USER ||--o{ BATCH: created_by
    USER ||--o{ QC_BATCH: created_by
    BATCH ||--|{ BATCH_PARAMETER: has
    QC_BATCH ||--|{ QC_PARAMETER: has
    BATCH_PARAMETER ||--|{ PARAMETER_READING: has
    QC_PARAMETER ||--|{ QC_READING: has
    BATCH }o--|| QC_BATCH: "references qc_batch_id"

```

