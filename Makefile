default:

install-dev:
	pip install -r requirements-dev.txt

install:
	pip install -r requirements.txt

lint:
	black autoproject
	pylint autoproject
