TARGETS=../static/mongodb-docs.css \
        ../static/guides.css \
        ../static/landing.css \
        ../static/navbar.min.css \
        ../static/controller.js
POSTCSS=./node_modules/.bin/postcss

.PHONY: all lint-css clean

all: $(TARGETS)

../static/controller.js: js/*.js node_modules/.CURRENT
	./node_modules/.bin/rollup -m -c rollup.config.js -o $@

../static/mongodb-docs.css: css/manual/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/manual/mongodb-docs.css -c postcss.config.js -o $@

../static/guides.css: css/guides/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/guides/guides.css -c postcss.config.js -o $@

../static/landing.css: css/landing/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/landing/landing.css -c postcss.config.js -o $@

../static/navbar.min.css: css/navbar/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/navbar/navbar.css -c postcss.config.js -o $@

lint-css: node_modules/.CURRENT
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules node_modules/.CURRENT: package.json package-lock.json
	npm install
	touch $@

clean:
	-rm $(TARGETS) ../static/controller.js.map
