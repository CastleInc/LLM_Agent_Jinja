
```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=genai_kb
MONGO_COLLECTION=cve_details
MONGO_POOL_SIZE=10
MONGO_TIMEOUT=5000
```

## Usage

```python
from mongo_service.connection import get_repository_manager

# Get repository manager
repo_manager = get_repository_manager()

# Use CVE repository
cve = repo_manager.cve_details_repo.find_one({"cve_number": "CVE-2021-44228"})
```
# MongoDB Service Layer

Standalone MongoDB service for CVE database operations.

## Features

- Repository pattern for database access
- Connection pooling and management
- Type-safe data models
- Environment-based configuration
- Reusable across multiple services

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

