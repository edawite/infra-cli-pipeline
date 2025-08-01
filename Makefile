# Makefile for common developer tasks

.PHONY: help install lint test bench docker-build clean

help:
	@echo "Available targets:"
	@echo "  install       Install python dependencies"
	@echo "  lint          Run flake8 on source and tests"
	@echo "  test          Run the test suite via pytest"
	@echo "  bench         Run the built‑in benchmark"
	@echo "  docker-build  Build the Docker image"
	@echo "  clean         Remove build artifacts"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

lint:
	flake8 src tests

test:
	pytest -q

bench:
	python -m infra_cli.main bench --n 500

docker-build:
	docker build -t infra-cli-pipeline -f docker/Dockerfile .

clean:
	rm -rf .pytest_cache __pycache__