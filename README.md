# ESSOS: eScholarship Research Centre Single Sign on Service


## Synopsis

A single sign on service for the other apps. Handles user auth with token passing
to partner services and user privileges / management.

## Configuration

The app is configured via configuration external to the app. That is,
point development.ini / production.ini at the centralised app config.

The specific configuration directive is:

    # application configuration
    app.config = %(here)s/config/config

## Running the application

Assuming you have the required dependencies installed and pserve is in your path then it should be as simple as:

    pserve --reload development.ini

Then navigate to http://{IP OF YOUR DEV SERVER}:3000

## Running the tests
    cd essos
    nosetests -v --with-cov --cov-report term-missing

