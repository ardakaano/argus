SKILL := argus
RENDER := python3 $(SKILL)/scripts/render_report.py

.PHONY: test examples zip clean

test:
	python3 -m unittest discover -s tests -v

# Regenerate the shipped example reports from their JSON.
examples:
	$(RENDER) $(SKILL)/examples/example-output.json -o $(SKILL)/examples/example-report.md
	$(RENDER) $(SKILL)/examples/example-output.tr.json -o $(SKILL)/examples/example-report.tr.md

# ZIP for Claude.ai custom skills: the archive root contains the argus/ folder.
zip:
	rm -f argus-skill.zip
	zip -r argus-skill.zip $(SKILL) -x '*/__pycache__/*' '*.pyc' '.DS_Store'

clean:
	rm -rf argus-skill.zip $$(find . -name __pycache__)
