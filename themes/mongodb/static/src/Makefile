TARGETS=../mongodb-docs.css
CSS_INPUTS=css/bootstrap-custom.css \
		   css/icomoon.css \
           css/font-awesome.css \
           css/mongodb-docs.css \
           css/header.css
CSS_FILES=$(CSS_INPUTS) css/basic.css

CSS_ERRORS=errors,empty-rules,duplicate-properties,selector-max-approaching
CSS_WARNINGS=regex-selectors,unqualified-attributes,text-indent

.PHONY: all lint clean

all: $(TARGETS)

../mongodb-docs.css: $(CSS_FILES) | node_modules
	$(MAKE) lint
	./node_modules/.bin/cleancss --skip-rebase --semantic-merging -o $@ $(CSS_INPUTS)

lint:
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules: package.json
	npm update

clean:
	rm -f $(TARGETS)
