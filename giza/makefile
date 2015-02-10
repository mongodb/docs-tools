nosetests:
	@echo "[testing] running nosetests"
	nosetests
ifeq ($(shell test -f /etc/arch-release && echo arch || echo Linux),arch)
	nosetests2
endif

pyflakes:
	@echo "[testing] running pyflakes:"	
	pyflakes giza

pep8:
	@echo "[testing] running pep8: "	
	pep8 --max-line-length=100 giza

test:nosetests pyflakes pep8
	@echo "[testing]: completed all tests"

release:
ifeq ($(shell test -f /etc/arch-release && echo arch || echo Linux),arch)
	python2 setup.py sdist upload
else
	python setup.py sdist upload
endif
