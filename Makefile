test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests --with-coverage --cover-package=pycket --cover-erase --with-yanc --with-xtraceback --cover-min-percentage=100 tests/

lint:
	@echo Running syntax check...
	@flake8 . --ignore=E501

build: test lint
