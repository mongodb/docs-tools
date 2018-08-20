ROLLUP=./node_modules/.bin/rollup -m
TARGETS=../static/mongodb-docs.css \
        ../static/guides.css \
        ../static/landing.css \
        ../static/navbar.min.css \
        ../static/controller.js \
        ../static/navbar.min.js \
        ../static/landing.min.js
POSTCSS=./node_modules/.bin/postcss

.PHONY: all lint-css clean

all: $(TARGETS)

# All properties
../static/navbar.min.js: navbar/*.js node_modules/.CURRENT
	$(ROLLUP) -c navbar/rollup.config.js -o $@

../static/navbar.min.css: css/navbar/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/navbar/navbar.css -c postcss.config.js -o $@
	# Temporarily copy to the old path to prevent 404s while we transition
	cp $@ ../static/css/navbar.min.css

# Landing pages
../static/landing.min.js: landing/*.js node_modules/.CURRENT
	$(ROLLUP) -c landing/rollup.config.js -o $@

../static/landing.css: css/landing/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/landing/landing.css -c postcss.config.js -o $@

# Manual properties
../static/controller.js: js/*.js node_modules/.CURRENT
	$(ROLLUP) -c rollup.config.js -o $@

../static/mongodb-docs.css: css/manual/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/manual/mongodb-docs.css -c postcss.config.js -o $@

# Guides
../static/guides.css: css/guides/*.css css/*.css postcss.config.js node_modules/.CURRENT
	$(POSTCSS) css/guides/guides.css -c postcss.config.js -o $@

# Utilities
lint-css: node_modules/.CURRENT
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules node_modules/.CURRENT: package.json package-lock.json
	npm install
	touch $@

clean:
	-rm $(TARGETS) ../static/controller.js.map
