.PHONY: test clean

GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
BASE_PATH := file://$(shell pwd)/src-base/build/${GIT_BRANCH}/html/
TEST_PATH := file://$(shell pwd)/src-test/build/${GIT_BRANCH}/html/

test: node_modules/.CURRENT
	cd src-base && giza make html
	cd src-test && giza make html
	BASE_PATH="${BASE_PATH}" TEST_PATH="${TEST_PATH}" ./node_modules/.bin/mocha index.js

clean:
	git clean -xfd src-base/ src-test/

node_modules node_modules/.CURRENT: package-lock.json package.json
	npm install
	touch $@
