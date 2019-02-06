# isenseflu-api-flask

## Background

### API Specification

OpenAPI 3.0.1 Definition Document: https://github.com/UCL/fludetector-openapi

## Requirements

- Python 3.6
- SQLite (for local testing environment)
- PostgreSQL

## Installation

### Python/Flask

```commandline
python3 -m venv ./venv
. venv/bin/activate
pip install -r requirements.txt
```

### Environment Configuration

Set the variable `APP_CONFIG` to one of these values:

- `development`
- `testing`
- `staging`
- `production-single`: For calling a local instance of MATLAB/Octave
- `production-multi`: For calling a remote instance of MATLAB/Octave

All environments use a remote instance of PostgreSQL 10 as a database server, apart from `testing` that uses an 
in-memory instance of SQLite.

### Database

Set the variable `DATABASE_URL` if using any environment other than `testing`:

```bash
DATABASE_URL="postgresql://dbuser:dbpass@dbhost/dbname"
```

#### Optional:

If testing against an empty database, create the database tables in PostgreSQL with the following series of commands:
```commandline
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```
Skip if an existing instance of PostgreSQL

## Testing

```
APP_CONFIG=testing python manage.py test
```

### Test coverage

![coverage](coverage.svg)

```bash
coverage run --source app,scheduler manage.py test
coverage html
coverage-badge -o coverage.svg
```