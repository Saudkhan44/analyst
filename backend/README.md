# AI Analytics Dashboard Backend

Production-ready FastAPI backend for an AI Analytics Dashboard application.

## Features

- **User Authentication**: Supabase JWT authentication
- **File Upload**: Support for CSV and Excel files (up to 50MB)
- **Data Processing**: Automatic data analysis with Pandas
- **Dashboard Generation**: Automatic KPI and chart recommendations
- **Chart Engine**: Intelligent chart type recommendations (bar, line, pie, scatter, histogram)
- **AI Chat**: Interactive chat about datasets using Groq API
- **Database**: SQLite local by default, optional PostgreSQL support via `DATABASE_URL`
- **Clean Architecture**: Modular monolith with single responsibility per module

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application factory
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # SQLAlchemy models and database setup
│   │   └── security.py         # JWT verification and auth
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── dependencies.py # JWT dependency injection
│   │   │   └── router.py       # Auth endpoints
│   │   ├── datasets/
│   │   │   ├── router.py       # Dataset endpoints
│   │   │   ├── service.py      # Business logic
│   │   │   └── schemas.py      # Pydantic models
│   │   ├── dashboard/
│   │   │   ├── router.py       # Dashboard endpoints
│   │   │   ├── service.py      # Business logic
│   │   │   ├── chart_engine.py # Chart generation engine
│   │   │   └── schemas.py      # Pydantic models
│   │   └── chat/
│   │       ├── router.py       # Chat endpoints
│   │       ├── service.py      # Business logic
│   │       └── schemas.py      # Pydantic models
│   └── shared/
│       ├── ai_client.py        # Groq API client
│       ├── pandas_utils.py     # Data processing utilities
│       └── storage.py          # File storage operations
├── uploads/                    # Local file storage
├── requirements.txt
├── .env.example
└── README.md
```

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Python**: 3.12
- **Database**: SQLite local by default with SQLAlchemy 2.0
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Authentication**: Supabase JWT
- **AI/LLM**: Groq API
- **Server**: Uvicorn
- **Validation**: Pydantic v2

## Setup Instructions

### Prerequisites

- Python 3.12+
- Python 3.12+
- Supabase account (for authentication)
- Groq API key

### Installation

1. **Clone or download the project**

```bash
cd backend
```

2. **Create and activate virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```
DEBUG=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=sqlite:///./analytics.db
GROQ_API_KEY=your-groq-api-key
UPLOAD_DIRECTORY=./uploads
```

Note: JWT validation now uses Supabase's JWKS public key endpoint, so `SUPABASE_JWT_SECRET` is not required.

5. **Initialize database**

The database tables are automatically created when the application starts:

```bash
python -m app.main
```

Or using Alembic (optional):

```bash
alembic upgrade head
```

6. **Run the application**

```bash
# Development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Authentication

- `GET /auth/me` - Get current user info (requires JWT)

### Datasets

- `POST /datasets/upload` - Upload and process CSV/Excel file
- `GET /datasets` - List user's datasets
- `GET /datasets/{dataset_id}/table` - Get dataset preview
- `DELETE /datasets/{dataset_id}` - Delete dataset

### Dashboard

- `GET /dashboard/{dataset_id}` - Get dashboard with KPIs and charts

### Chat

- `POST /chat` - Send message about dataset
- `GET /chat/{dataset_id}` - Get chat history

## API Usage Examples

### 1. Upload a Dataset

```bash
curl -X POST http://localhost:8000/datasets/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@data.csv"
```

### 2. Get Dashboard

```bash
curl -X GET http://localhost:8000/dashboard/dataset-id \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Send Chat Message

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "dataset-uuid",
    "message": "What is the average sales?"
  }'
```

## Architecture Decisions

### Modular Monolith

The application uses a modular monolith architecture:
- Each module (auth, datasets, dashboard, chat) is self-contained
- Clear separation of concerns with router → service → business logic
- No repository pattern (services interact directly with database)
- Shared utilities in `shared/` folder

### No Over-Engineering

- Single database with simple relationships
- No CQRS, event sourcing, or event buses
- Synchronous processing for simplicity
- Minimal dependencies and layers

### Async Where Appropriate

- File uploads use async handlers
- Chat endpoint is async for I/O operations
- Database operations remain synchronous (better SQLAlchemy support)

## Chart Engine

The chart engine automatically recommends charts based on data:

1. **Bar Charts**: Categorical columns grouped by numeric values
2. **Pie Charts**: Distribution of categorical data
3. **Line Charts**: Time series data
4. **Scatter Plots**: Relationships between numeric variables
5. **Histograms**: Distribution of numeric data

All charts return JSON-formatted data for frontend rendering.

## AI Chat Features

- Dataset-specific context using dashboard summary
- Chat history per dataset per user
- Groq API integration for LLM responses
- Automatic context building from analytics

## Error Handling

The application includes comprehensive error handling:

- **400 Bad Request**: Invalid file types, missing data
- **401 Unauthorized**: Missing or invalid JWT token
- **404 Not Found**: Dataset or resource not found
- **500 Internal Server Error**: Database or processing errors

All errors include descriptive messages for debugging.

## Logging

Structured logging throughout the application:

```python
logger.info(f"Dataset uploaded: {dataset_id}")
logger.error(f"Error processing file: {str(e)}")
logger.warning(f"Could not create bar chart: {column}")
```

Check logs for debugging and monitoring.

## Security

- JWT validation on every protected endpoint
- User ID isolation (users can only access their own data)
- File size validation (50MB limit)
- Supported file types validation
- SQL injection protection via SQLAlchemy ORM

### For Production

1. Update CORS origins to specific domains
2. Use environment-specific configuration
3. Enable HTTPS
4. Use strong database passwords
5. Rotate API keys regularly
6. Set up monitoring and alerting

## Development

### Adding a New Endpoint

1. Create schema in `schemas.py`
2. Implement logic in `service.py`
3. Add route in `router.py`
4. Include router in `main.py`

### Testing

```bash
# Run with test database
TEST_DATABASE_URL=postgresql://test:test@localhost/test_db python -m pytest
```

### Database Migrations

Using Alembic (optional):

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance Considerations

- File uploads are size-limited (50MB)
- DataFrame sampling for large datasets (1000 points for scatter plots)
- Limited chart recommendations (5 charts max)
- Database connection pooling enabled
- Proper indexing on frequently queried columns

## Troubleshooting

### Import Errors

Ensure you're running from the `backend/` directory and the module is in `PYTHONPATH`:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Database Connection Errors

Verify `DATABASE_URL` in `.env`:

```
DATABASE_URL=sqlite:///./analytics.db
```

### JWT Validation Errors

Ensure `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct in your `.env`, and that the frontend sends `Authorization: Bearer <access_token>`.

### File Upload Errors

Check `UPLOAD_DIRECTORY` exists and has write permissions:

```bash
mkdir -p uploads
```

## Future Enhancements

- User file size history and quotas
- Dataset versioning
- Advanced data transformations
- Export dashboard to PDF/PNG
- Real-time collaboration features
- Webhook notifications
- Rate limiting per user
- Caching layer for dashboard data

## License

Proprietary - All rights reserved

## Support

For issues and questions, refer to the documentation or contact the development team.
