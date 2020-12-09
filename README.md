![i-sense flu](https://res.cloudinary.com/uclfmedia/image/upload/v1563449524/isenseflu/logo_300.svg)

# i-sense flu api

API component of the i-sense flu application. Calculates and serves the model score data displayed by the i-sense flu app component [https://github.com/UCL/isenseflu-app-react](https://github.com/UCL/isenseflu-app-react).

![CI](https://github.com/UCL/isenseflu-api-flask/workflows/CI/badge.svg?branch=master)
![GitHub release](https://img.shields.io/github/release/UCL/isenseflu-api-flask.svg)

## Background

i-sense flu is a multi-module application that uses Google search data to estimate influenza-like illness (flu) rates in England. The i-sense flu api module is responsible of the calculation of the scores and serving of the data to be displayed by the web interface.


## Features

- Calculation of scores via a local (or remote) installation of MATLAB or Octave
- Scheduling of calculation process via APScheduler
- Data available on REST endpoints
- PostgreSQL as database
- Models not included (enquire for details)


## Technologies

- Python
- Flask
- OpenAPI
- Octave/MATLAB
- REST


## API Specification

OpenAPI 3.0.2 Definition Document: https://github.com/UCL/isenseflu-openapi

## Installation

### Requirements

- Python 3.6
- SQLite (for local testing environment)
- PostgreSQL


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

Skip if using an existing instance of PostgreSQL

### Models

The scores are calculated using models for MATLAB/GNU Octave. Deploy both the `MAT` file and `m` script in the `octave` directory (create directory in the application root if it does not exist). The models are licensed separately and not distributed together with the Flask application, please enquire for details.

## Usage

### Flask API component

The API component can be started with a Python WSGI HTTP server like `gunicorn` (included in `requirements.txt`), calling `run.py`. `gunicorn` listens by default on port 8000.

```
[venv/bin]/gunicorn run:APP
```


### Scheduling of calculation of scores

The scheduler component uses Advanced Python Scheduler's (APScheduler) `BlockingScheduler` to help automate the calculation of scores. The `manage.py` script accepts CRON-type definitions for scheduling jobs.

```
[venv/bin]/python manage.py run_model_sched [model-id] "*/30 * * * *'
```

## Testing

Use the following command to run the tests:

```
APP_CONFIG=testing python manage.py test
```

### Test coverage

![coverage](coverage.svg)

Install `coverage` and `coverage-badge` locally ( `. venv/bin/activate required`)

```bash
pip install coverage coverage-badge
```

Run `coverage` against the source directories

```bash
coverage run --source app,scheduler manage.py test
coverage html
coverage-badge -o coverage.svg
```

## Reporting bugs

Please use the GitHub issue tracker for any bugs or feature suggestions:

[https://github.com/UCL/isenseflu-api-flask/issues](https://github.com/UCL/isenseflu-api-flask/issues)


## Contributing

Pull requests are welcome. For major changes, especially changes that require the addition to new dependencies, please open an issue first to discuss what you would like to change.


## Authors

- David Guzman (Github: [@david-guzman](https://github.com/david-guzman))

i-sense flu app is based on the Fludetector tool, designed and developed by:

- Vasileios Lampos
- William Mayor
- David Guzman

More details in the [AUTHORS.md](AUTHORS.md) file.

## Acknowledgements

i-sense flu api is supported by the EPSRC IRC project [i-sense](https://www.i-sense.org.uk/) (Early-Warning Sensing Systems for Infectious Diseases).


## Copyright

i-sense flu api is licensed under the GNU General Public License, v3. A copy of this license is included in the file [LICENSE.md](LICENSE.md).
