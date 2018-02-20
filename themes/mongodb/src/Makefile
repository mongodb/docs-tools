TARGETS=../static/mongodb-docs.css ../static/controller.js
CSS_INPUTS=css/bootstrap-custom.css \
		   css/icomoon.css \
           css/font-awesome.css \
           css/mongodb-docs.css \
           css/feedback.css \
           css/header.css \
           css/mws.css \
           css/tabs.css \
           css/lightbox.css \
           css/code-buttons.css
CSS_FILES=$(CSS_INPUTS) css/basic.css

CSS_ERRORS=errors,empty-rules,duplicate-properties,selector-max-approaching
CSS_WARNINGS=regex-selectors,unqualified-attributes,text-indent

.PHONY: all lint-css clean

all: $(TARGETS)

../static/controller.js: js/*.js node_modules/.CURRENT
	./node_modules/.bin/rollup -m -c rollup.config.js -o $@

../static/mongodb-docs.css: $(CSS_FILES) node_modules/.CURRENT
	$(MAKE) lint-css
	./node_modules/.bin/cleancss -O2 'mergeSemantically:on;restructureRules:on' --skip-rebase --inline local,fonts.googleapis.com -o $@ $(CSS_INPUTS)

lint-css: node_modules/.CURRENT
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules node_modules/.CURRENT: package.json package-lock.json
	npm install
	touch $@

clean:
	-rm $(TARGETS) ../static/controller.js.map
