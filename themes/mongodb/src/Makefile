TARGETS=../static/mongodb-docs.css ../static/guides.css ../static/controller.js
CLEANCSS=./node_modules/.bin/cleancss -O2 'mergeSemantically:on;restructureRules:on' --skip-rebase --inline local,fonts.googleapis.com

.PHONY: all lint-css clean

all: $(TARGETS)

../static/controller.js: js/*.js node_modules/.CURRENT
	./node_modules/.bin/rollup -m -c rollup.config.js -o $@

../static/mongodb-docs.css: css/manual/*.css css/*.css node_modules/.CURRENT
	$(CLEANCSS) -o $@ css/manual/mongodb-docs.css

../static/guides.css: css/guides/*.css css/*.css node_modules/.CURRENT
	$(CLEANCSS) -o $@ css/guides/guides.css

lint-css: node_modules/.CURRENT
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules node_modules/.CURRENT: package.json package-lock.json
	npm install
	touch $@

clean:
	-rm $(TARGETS) ../static/controller.js.map
