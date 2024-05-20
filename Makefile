.PHONY: all install_requirements init_and_update combine_and_remove

PYTHON := $(shell which python3 2>/dev/null || which python)

all: install_requirements init_and_update combine_and_remove readme_list

install_requirements:
	$(PYTHON) -m pip install -r lib/requirements.txt


combine_and_remove:
	$(PYTHON) lib/combine_and_remove.py

validate:
	$(PYTHON) lib/validate.py

readme_list:
	$(PYTHON) lib/readme_list.py

init_and_update:
	$(PYTHON) lib/init_and_update.py

sort:
	$(PYTHON) lib/sort.py