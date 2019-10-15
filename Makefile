.PHONY: lisnt black flake8

lint: isort black flake8

isort:
	isort -y -rc guillotina_evolution

black:
	black guillotina_evolution/

flake8:
	flake8 guillotina_evolution/
