.PHONY: test export clean pinyin sources

test:
	python3 -m unittest discover -s tests -v

export:
	python3 -m memearchive export -f all -o dist/互联网梗大全

pinyin:
	python3 scripts/gen_pinyin.py

sources:
	python3 scripts/assign_sources.py

clean:
	rm -rf dist build *.egg-info
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
