test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests tests/

lint:
	@echo Running syntax check...
	@flake8 . --ignore=E501 --max-complexity 10

build: test lint
