.PHONY: init test lint run clean-pyc clean-build clean

init:
	pipenv install --dev

test:
	pipenv run pytest --verbose --color=yes tests/

lint:
	pipenv --python python3 run flake8 --exclude=.tox saythanks

run:
	pipenv run python saythanks/app.py

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean: clean-pyc clean-build
