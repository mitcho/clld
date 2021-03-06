import datetime
from string import Template as StringTemplate

from zope.interface import implementer, implementedBy, providedBy

from clld import interfaces
from clld.web.adapters.base import Representation
from clld.lib import bibtex


class Metadata(Representation):
    @property
    def unapi_name(self):
        return getattr(self, 'unapi', self.extension)


@implementer(interfaces.IRepresentation, interfaces.IMetadata)
class BibTex(Metadata):
    """Render a resource's metadata as BibTex record.
    """
    __label__ = 'BibTeX'
    unapi = 'bibtex'
    extension = 'md.bib'
    mimetype = 'text/x-bibtex'

    def rec(self, ctx, req):
        data = {}
        if interfaces.IContribution.providedBy(ctx):
            genre = 'inbook'
            data['author'] = [
                c.name for c in
                list(ctx.primary_contributors) + list(ctx.secondary_contributors)]
            data['booktitle'] = req.dataset.description
            data['editor'] = [c.contributor.name for c in list(req.dataset.editors)]
        else:
            genre = 'book'
            data['editor'] = [c.contributor.name for c in list(ctx.editors)]

        return bibtex.Record(
            genre,
            ctx.id,
            title=getattr(ctx, 'citation_name', ctx.__unicode__()),
            url=req.resource_url(ctx),
            address=req.dataset.publisher_place,
            publisher=req.dataset.publisher_name,
            year=str(req.dataset.published.year),
            **data)

    def render(self, ctx, req):
        return self.rec(ctx, req).__unicode__()


@implementer(interfaces.IRepresentation, interfaces.IMetadata)
class ReferenceManager(BibTex):
    __label__ = 'RIS'
    unapi = 'ris'
    extension = 'md.ris'
    mimetype = "application/x-research-info-systems"

    def render(self, ctx, req):
        return self.rec(ctx, req).format('ris')


@implementer(interfaces.IRepresentation, interfaces.IMetadata)
class TxtCitation(Metadata):
    """Render a resource's metadata as plain text string.
    """
    __label__ = 'Text'
    extension = 'md.txt'
    mimetype = 'text/plain'

    def render(self, ctx, req):
        if interfaces.IContribution.providedBy(ctx):
            self.template = 'contribution/md_txt.mako'
        else:  # if interfaces.IDataset.providedBy(ctx):
            self.template = 'dataset/md_txt.mako'
        return super(TxtCitation, self).render(ctx, req)
