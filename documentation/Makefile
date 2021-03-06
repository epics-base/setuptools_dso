PYTHON ?= python3
SPHINXOPTS    =
SPHINXBUILD   = $(PYTHON) -m sphinx
BUILDDIR      = $(CURDIR)/_build

ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(CURDIR)

all: html

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
clean:
	rm -rf $(BUILDDIR)

commit: html
	touch _build/html/.nojekyll
	./commit-gh.sh _build/html documentation/_build/html

.PHONY: all html clean commit
