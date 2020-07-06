init:
	rm -rf venv
	python3 -m venv venv
	echo 'Now run "source venv/bin/activate && make install"'

install:
	pip install -r requirements.txt

.PHONY: init