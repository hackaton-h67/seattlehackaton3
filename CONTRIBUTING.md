# Contributing to Service-Sense

Thank you for your interest in contributing to Service-Sense!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd seattlehackaton3
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make dev-install
   # or
   pip install -e ".[dev]"
   ```

4. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start databases**
   ```bash
   make docker-up
   ```

6. **Initialize databases**
   ```bash
   make init-db
   ```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking

Format your code before committing:
```bash
make format
make lint
```

### Testing

Write tests for all new features:
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e
```

### Commit Messages

Use clear, descriptive commit messages:
- `feat: Add audio transcription service`
- `fix: Resolve Neo4j connection timeout`
- `docs: Update API documentation`
- `refactor: Simplify entity extraction logic`
- `test: Add integration tests for triage endpoint`

### Pull Requests

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Write/update tests
4. Format and lint your code: `make format && make lint`
5. Run tests: `make test`
6. Commit your changes
7. Push to your fork
8. Open a pull request with a clear description

## Project Structure

```
services/          # Microservices
  api-gateway/    # Main API
  input-processor/ # Text/audio processing
  ...
shared/           # Shared libraries
  models/        # Data models
  utils/         # Utilities
  config/        # Configuration
ml/              # Machine learning
  training/      # Training scripts
  models/        # Trained models
tests/           # Tests
  unit/
  integration/
  e2e/
```

## Adding a New Service

1. Create service directory: `services/your-service/`
2. Add `main.py` with core logic
3. Add `Dockerfile`
4. Add service to `docker-compose.yml`
5. Write tests in `tests/`
6. Update documentation

## Adding a New Endpoint

1. Add endpoint to appropriate service
2. Update OpenAPI schema
3. Add request/response models in `shared/models/`
4. Write integration tests
5. Update API documentation

## Debugging

### View logs
```bash
docker-compose logs -f <service-name>
```

### Connect to databases
```bash
# Neo4j browser
open http://localhost:7474

# PostgreSQL
docker exec -it service-sense-postgres psql -U service_sense

# Redis
docker exec -it service-sense-redis redis-cli
```

### Run individual services
```bash
cd services/api-gateway
uvicorn main:app --reload
```

## Code Review Guidelines

When reviewing PRs, check for:
- [ ] Code follows style guide (Black, Ruff)
- [ ] Tests are included and passing
- [ ] Type hints are used
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Error handling is appropriate
- [ ] Logging is informative
- [ ] Performance considerations

## Questions?

Open an issue or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
