dist: version
	python setup.py sdist

lint:
	cd image2ipfs && pylint --rcfile pylint.rc *.py

test:
	cd image2ipfs && python -m unittest discover


clean:
	rm -fr image2ipfs/*.pyc
	rm -fr dist/ build/ *.egg-info

install: clean version
	python setup.py install
	image2ipfs --version

version:
	@git describe --match 'v[0-9]*' --dirty='.m' --always > image2ipfs/git-revision
	@cat image2ipfs/git-revision

upload: clean
	python setup.py sdist upload

