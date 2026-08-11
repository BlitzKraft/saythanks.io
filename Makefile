.PHONY: init test lint run clean-pyc clean-build clean djlint-reformat reformat

#init:
#	pipenv install --dev

test:
	pipenv run pytest --verbose --color=yes tests/

lint:
	pipenv --python python run flake8 --exclude=.tox saythanks

djlint-reformat:
	find saythanks/templates -type f -name '*.htm.j2' -exec .venv/bin/djlint --reformat {} +

reformat: djlint-reformat

#run:
#	pipenv run python saythanks/app.py

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
