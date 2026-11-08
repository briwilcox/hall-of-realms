PY ?= python3 -E -s
P = pipeline

.PHONY: all fetch borders classify check page site typecheck clean
all: check page

fetch:
	cd $(P) && $(PY) fetch.py
build/borders.json: $(P)/borders.py $(P)/geo.py | fetch
	cd $(P) && $(PY) borders.py
build/mapdata.json: build/borders.json $(P)/classify.py data/manual.json src/hall-of-realms.src.html
	cd $(P) && $(PY) classify.py
borders: build/borders.json
classify: build/mapdata.json
check:
	cd $(P) && $(PY) check.py
page: build/mapdata.json
	cd $(P) && $(PY) build.py
site: build/mapdata.json
	cd $(P) && $(PY) build.py --split
	git archive --format=tar.gz --prefix=hall-of-realms/ -o dist/site/hall-of-realms-source.tar.gz HEAD
	@git diff --quiet HEAD -- . || echo "warning: uncommitted changes are not in the source archive"
typecheck:
	mypy --strict $(P)
clean:
	rm -rf build dist
