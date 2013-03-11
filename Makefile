PYTHON_MAJOR_VERSION=$(shell python -c "import sys; print(sys.version_info.major)")

MAIN_REQUIREMENTS=requirements.txt
EXTENDED_REQUIREMENTS=requirements-py$(PYTHON_MAJOR_VERSION).txt



build: test lint

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests tests/

lint:
	@echo Running syntax check...
	@flake8 . --ignore=E501 --max-complexity 10

install:
	@echo Installing dependencies...
	@pip install -r $(MAIN_REQUIREMENTS) --use-mirrors
	-@[ -f $(EXTENDED_REQUIREMENTS) ] && pip install -r $(EXTENDED_REQUIREMENTS) --use-mirrors || \
		echo File "$(EXTENDED_REQUIREMENTS)" doesn\'t exist, skipping version-specific packages
	@echo Finished installing dependencies.

release:
	python setup.py sdist upload
