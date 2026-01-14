 
format:
	poetry run isort src --profile black
	poetry run black src --safe

lint:
	poetry run flake8 src