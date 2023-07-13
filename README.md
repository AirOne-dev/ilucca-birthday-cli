# Ilucca birthday cli

## Setup

- Create a `config.ini` with the content of the `config.example.ini` inside
- Update the values to match your need

## Commands

### Without docker

Run `poetry install`

Then run `poetry run update_data`

Available commands :

- `poetry run cli` => cli base version of this project with all options / arguments
- `poetry run all | list` => list all birthdays of each people
- `poetry run next` => show the next birthday
- `poetry run today | current` => show the birthday of the day if there is one
- `poetry run slack` => check if there is a birthday today ans send a message to a slack channel
- `poetry run update_data` => download the birtday data from the ilucca v3 api

### With docker

Run `./docker_build.sh` to build the docker image
Then `./docker_run_server` to run a server that send a message to a slack channel when it's the birthday of someone
