from clld.tests.util import TestWithApp
from clld import RESOURCES


class Tests(TestWithApp):
    def test_robots(self):
        self.app.get('/robots.txt', status=200)

    def test_sitemapindex(self):
        self.app.get('/sitemap.xml', status=200)

    def test_sitemap(self):
        self.app.get('/sitemap.language.0.xml', status=200)

    def test_dataset(self):
        self.app.get('/', status=200)
        self.app.get('/', accept='application/rdf+xml', status=200)
        self.app.get('/void.md.ris', status=200)

    def test_resources(self):
        for rsc in RESOURCES:
            if not rsc.with_index:  # exclude the special case dataset
                continue
            self.app.get('/{0}s/{0}'.format(rsc.name), status=200)
            self.app.get('/{0}s/{0}.rdf'.format(rsc.name), status=200)
            self.app.get('/%ss' % rsc.name, status=200)
            self.app.get('/%ss.rdf' % rsc.name, status=200)
            self.app.get('/%ss?sEcho=1&iDisplayLength=5' % rsc.name, xhr=True, status=200)

    def test_source(self):
        for ext in 'bib en ris mods'.split():
            self.app.get('/sources/source.' + ext, status=200)
            self.app.get('/sources.' + ext, status=200)
