SKILL := argus
RENDER := python3 $(SKILL)/scripts/render_report.py

.PHONY: test examples logo site zip clean

test:
	python3 -m unittest discover -s tests -v

# Regenerate the shipped example reports from their JSON.
examples:
	$(RENDER) $(SKILL)/examples/example-output.json -o $(SKILL)/examples/example-report.md
	$(RENDER) $(SKILL)/examples/example-output.tr.json -o $(SKILL)/examples/example-report.tr.md
	$(RENDER) $(SKILL)/examples/example-output.json -o $(SKILL)/examples/example-report.html
	$(RENDER) $(SKILL)/examples/example-output.tr.json -o $(SKILL)/examples/example-report.tr.html

# Regenerate site/argus.json and site/argus.lite.json (a test checks they are current).
site:
	python3 site/build_site_json.py

# Regenerate the logo SVGs (the PNG banner is rendered from the SVG with a browser).
logo:
	python3 assets/build_logo.py

# ZIP for Claude.ai custom skills: the archive root contains the argus/ folder.
zip:
	rm -f argus-skill.zip
	zip -r argus-skill.zip $(SKILL) -x '*/__pycache__/*' '*.pyc' '.DS_Store'

clean:
	rm -rf argus-skill.zip $$(find . -name __pycache__)
