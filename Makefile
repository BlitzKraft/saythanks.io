TEMPLATE_TARGETS := $(patsubst %.htm.j2,%,$(notdir $(wildcard saythanks/templates/*.htm.j2)))
PYTHON_SAYTHANKS_TARGETS := $(patsubst %.py,%,$(notdir $(wildcard saythanks/*.py)))
PYTHON_ROOT_TARGETS := $(patsubst %.py,%,$(notdir $(wildcard t.py)))

# Group the python targets together for the .PHONY declaration
PYTHON_TARGETS := $(PYTHON_SAYTHANKS_TARGETS) $(PYTHON_ROOT_TARGETS)

.PHONY: init test lint run clean-pyc clean-build clean \
	djlint-reformat reformat djlint-reformat-win reformat2 \
	$(TEMPLATE_TARGETS) $(PYTHON_TARGETS)

# Target for Jinja Templates
$(TEMPLATE_TARGETS):
	pipenv run djlint saythanks/templates/$@.htm.j2 --lint

# Target for Python files in the saythanks/ directory
$(PYTHON_SAYTHANKS_TARGETS):
	pipenv run flake8 saythanks/$@.py

# Target for the root t.py file
$(PYTHON_ROOT_TARGETS):
	pipenv run flake8 $@.py

#init:
#	pipenv install --dev

test:
	pipenv run pytest --verbose --color=yes tests/

# Lints the entire project
lint:
	pipenv --python python run flake8 --exclude=.tox saythanks

djlint-reformat:
	find saythanks/templates -type f -name '*.htm.j2' -exec .venv/bin/djlint --reformat {} +

djlint-reformat-win:
	find saythanks/templates -type f -name '*.htm.j2' -exec djlint --reformat {} +

reformat: djlint-reformat

reformat2: djlint-reformat-win

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