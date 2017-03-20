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

.PHONY: all lint-css clean

all: $(TARGETS)

../static/navbar.js: js/*.js | node_modules
	greni
	cp build/navbar.js $@
	cp build/navbar.js.map $@.map

../static/mongodb-docs.css: $(CSS_FILES) | node_modules
	$(MAKE) lint-css
	./node_modules/.bin/cleancss --skip-rebase --semantic-merging -o $@ $(CSS_INPUTS)

lint-css: | node_modules
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules: package.json
	npm update

clean:
	rm -f $(TARGETS) ../static/navbar.js.map build/*
