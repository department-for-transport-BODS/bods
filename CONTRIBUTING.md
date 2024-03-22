# Contributing to BODS

## Pre-requisites

- The BODS application can run inside and outside of Docker
- We recommend using Docker for the database, celery workers/beat scheduler/flower,
  clam av scanner and django service

## Setup

To get started clone the repository

```sh

git clone git@github.com:department-for-transport-BODS/bods.git
cd ./bods
```

For the project to build and start correctly several environment variables need
to be set.
We use a `.env` to set the variables.
Make a copy of `./config/.env.local.template` in the root directory of the
project, call this file `.env`.

```sh
cp config/.env.local.template .env
```

Open the `.env` file and set the `UID` and `GID` to `1000`.
Build the project using `docker-compose`.

```sh
docker-compose build
```

This will take a while to complete.
Once completed we can start and initialise the dockerised postgres database.

```sh
docker-compose up postgres
```

This will start the database in the foreground, after a minute or so you should see
the following message.

```sh
LOG:  database system is ready to accept connections
```

This indicates that database has been initialised correctly and has started
successfully.

Use `Ctrl+c` to stop the docker container.

Next we need to apply our Django applications migrations to the database. To do this
let's first bring the database container back up, but this time run it in the
background.

```sh
docker-compose up -d postgres
```

After a few seconds you should see the postgres container running when you run

```sh
docker-compose ps
```

Next we'll be using the `docker-compose run` command to run the Django `migrate`
command.

```sh
docker-compose run django python manage.py migrate
```

You will now be able to create a super user. This will ask for a username, email
and password.

```sh
docker-compose run django python manage.py createsuperuser
```

Now that the superuser has been created you can login to the Django Admin site to
ensure everything is running correctly.
First start the application containers.

```sh
docker-compose up
```

Navigate to [admin.localhost:8000/admin](http://admin.localhost:8000/admin) and
login with username and password you have previously created.

There are a few Celery tasks that need to be run to populate the application
with data.

Navigate to the [Periodic Tasks](http://admin.localhost:8000/admin/django_celery_beat/periodictask/)
in the Django Admin.

Select the checkbox for the following periodic tasks

- `run_naptan_etl`
- `update_bods_xsd_zip_files`

Select `Run selected tasks` from the dropdown and click `Go`.

These tasks will populate the tables storing NaPTAN data and also fetch the schema
files required to perform schema checks.

## Upgrade Local Setup

Upgrade the local setup to create images and container using the latest code in the dev branch.

Below are the recommended steps:

Take backup of local database using the below command.

```sh
make local-db-backup
```

Delete existing images and volumes from docker desktop.

Run the below command and ensure vpn is switched off before running the command.

```sh
docker-compose up
```

If there was any failures while building the images, make sure the vpn is disconnected, exit docker desktop (not just close the window) and rerun the above command after running the below command.

```sh
docker builder prune -a
```

Restore the db after the service is up using the below command.

```sh
make local-db-restore
```

## OTC Dataset

BODS utilises the Office of Traffic Commissioners Bus Service dataset for
Compliance and Monitoring functionality.
To synchronise BODS with this data there are two Celery Tasks that need to be run.

1. task_get_all_otc_data
2. task_refresh_otc_data

The first task should be run once on setup to ensure the BODS OTC tables are
populated and the second task should be run periodically to ensure data stays
up to date.
The `task_get_all_otc_data` can take a few hours to initially run as it is doing
a full sync with the OTC data set.

**Note**. Before running these tasks ensure the OTC environment variables are
correctly set in the `.env` file.

## Create a Publisher Account

1. Navigate to [BODS Admin section](http://admin.localhost:8000/)
2. Click [Organisation management](http://admin.localhost:8000/organisations/)
3. Click the [Add new organisation](http://admin.localhost:8000/organisations/new/)
   button
4. Complete the form with "fake" data (make sure the Key contact email is completed)
5. This will send an email to the [MailHog inbox](http://localhost:8025/)
6. Follow the instructions in the email to create a new publisher account, it's
   recommended that you open the link in Incognito/privacy mode
7. Complete the form with a password
8. Your publisher account is created and you can now publish a timetable.

## Publish a Timetable

Publishing a timetable is a good way to check that you have everything setup end
to end.

1. Find a timetable on the production [BODS site](https://data.bus-data.dft.gov.uk/timetable/)
2. Download a good quality timetable that is in a Published and Compliant Status
3. Navigate to the [BODS Publish](http://publish.localhost:8000/) site
4. Select the Timetables radio button and click Continue
5. Fill in the Data set description text boxes
6. Select the Upload data set to Bus Open Data Service radio button and click the
   Choose file button
7. Select the timetable data set you downloaded above, and click Continue
8. After a while the pipeline will complete and you can publish the data set.
