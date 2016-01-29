TARGETS=../mongodb-docs.css
CSS_FILES=css/basic.css \
          css/bootstrap-custom.css \
          css/mongodb-docs.css \
          css/font-awesome.css \
          css/icomoon.css
CSS_ERRORS=errors,empty-rules,duplicate-properties,selector-max-approaching
CSS_WARNINGS=regex-selectors,unqualified-attributes,text-indent

.PHONY: all lint clean

all: $(TARGETS)

../mongodb-docs.css: $(CSS_FILES) | node_modules
	$(MAKE) lint
	./node_modules/.bin/cleancss --skip-rebase --semantic-merging -o $@ $^

lint:
	./node_modules/.bin/csslint --quiet --format=compact --errors=$(ERRORS) --warnings=$(CSS_WARNINGS) css/basic.css css/mongodb-docs.css

node_modules: package.json
	npm update

clean:
	rm -f $(TARGETS)
