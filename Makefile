init:
	rm -rf venv
	python3 -m venv venv

install:
	pip install -r requirements.txt

.PHONY: init