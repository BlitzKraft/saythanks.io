
.PHONY: clean-pyc init lint test

lint:
	flake8 --exclude=.tox

#init: 
#	pip install -r requirements.txt 

test:	
	pytest --verbose --color=yes $(TEST_PATH)
	
clean-pyc:
	echo "Cleaning, TBD"

