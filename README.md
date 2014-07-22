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
    PYTHONPATH=$PWD nosetests -v --with-cov --cov-report term-missing -s

    or to run a specific test (for example):
    PYTHONPATH=$PWD nosetests -v --with-cov --cov-report term-missing -s tests/test_health_check_view.py


    * PYTHONPATH: set the path modules to be included. You probably don't need
    to change this.
    * -v: verbose
    * --with-cov --cov-report term-missing: calculate unit test coverage showing what's
    not covered.
    * -s: don't capture stdout


### Test requirements
Tests assume there is a local ldap server with a group "essos" and two users: u1 and u2 with passes
p1 and p2 respectively (obviously not real user accounts). u1 is in the essos group which makes u1
an app administrator.

