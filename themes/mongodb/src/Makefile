TARGETS=../static/mongodb-docs.css ../static/navbar.js
CSS_INPUTS=css/bootstrap-custom.css \
		   css/icomoon.css \
           css/font-awesome.css \
           css/mongodb-docs.css \
           css/feedback.css \
           css/header.css \
           css/mws.css \
           css/copy-button.css \
           css/tabs.css \
           css/jirapanel.css
CSS_FILES=$(CSS_INPUTS) css/basic.css

CSS_ERRORS=errors,empty-rules,duplicate-properties,selector-max-approaching
CSS_WARNINGS=regex-selectors,unqualified-attributes,text-indent

.PHONY: all lint-js lint-css clean

all: $(TARGETS)

../static/mongodb-docs.css: $(CSS_FILES) | node_modules
	$(MAKE) lint-css
	./node_modules/.bin/cleancss --skip-rebase --semantic-merging -o $@ $(CSS_INPUTS)

../static/navbar.js: build/bundle.es5.min.js
	./node_modules/.bin/sorcery -i $^ -o $@

build/bundle.es5.min.js: build/bundle.es5.js
	./node_modules/.bin/uglifyjs --source-map-inline --source-map-include-sources -cm -o $@ $^

build/bundle.es5.js: build/bundle.js
	./node_modules/.bin/buble $^ -o $@ -t ie:10 -m inline -y dangerousForOf

build/bundle.js: js/*.js
	$(MAKE) lint-js
	./node_modules/.bin/rollup -o $@ -f iife -m inline -- js/navbar.js

lint-css: | node_modules
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

lint-js: | node_modules
	./node_modules/.bin/eslint js/

node_modules: package.json
	npm update

clean:
	rm -f $(TARGETS) build/*
