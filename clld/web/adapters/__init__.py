from zope.interface import implementer, implementedBy

from clld import RESOURCES
from clld import interfaces
from clld.web.adapters.base import Index, Representation, Json
from clld.web.adapters.geojson import GeoJson, GeoJsonLanguages, GeoJsonParameter
from clld.web.adapters.excel import ExcelAdapter
from clld.web.adapters.md import BibTex, TxtCitation, ReferenceManager
from clld.web.adapters.rdf import Rdf, RdfIndex
from clld.web.adapters import biblio
from clld.lib.rdf import FORMATS as RDF_NOTATIONS


def includeme(config):
    """register adapters
    """
    specs = []
    for rsc in RESOURCES:
        # each resource is available ...
        name, interface = rsc.name, rsc.interface

        # ... as json
        cls = type('Json%s' % rsc.model.mapper_name(), (Json,), {})
        config.registry.registerAdapter(
            cls, (interface,), interfaces.IRepresentation, name=Json.mimetype)

        if rsc.with_index:
            # ... as html index
            specs.append(
                (interface, Index, 'text/html', 'html', name + '/index_html.mako', {}))

        # ... as html details page
        specs.append(
            (interface, Representation, 'text/html', 'html', name + '/detail_html.mako',
             {}))
        # ... as html snippet (if the template exists)
        specs.append(
            (interface, Representation, 'application/vnd.clld.snippet+xml',
             'snippet.html', name + '/snippet_html.mako', {}))

        # ... as RDF in various notations
        for notation in RDF_NOTATIONS.values():
            specs.append((
                interface,
                Rdf,
                notation.mimetype,
                notation.extension,
                name + '/rdf.mako', {'rdflibname': notation.name}))

        # ... as RDF collection index
        rdf_xml = RDF_NOTATIONS['xml']
        specs.append((
            interface,
            RdfIndex,
            rdf_xml.mimetype,
            rdf_xml.extension,
            'index_rdf.mako', {'rdflibname': rdf_xml.name}))

    # citeable resources are available as html page listing available metadata formats:
    for _if in [interfaces.IContribution, interfaces.IDataset]:
        specs.append(
            (_if, Representation, 'application/vnd.clld.md+xml', 'md.html', 'md_html.mako', {}))

    specs.extend([
        (
            interfaces.ILanguage, Index,
            'application/vnd.google-earth.kml+xml',
            'kml',
            'clld:web/templates/language/kml.mako',
            {'send_mimetype': 'application/xml'}),
        (
            interfaces.ILanguage,
            Representation,
            'application/vnd.google-earth.kml+xml',
            'kml',
            'clld:web/templates/language/kml.pt',
            {'send_mimetype': 'application/xml'}),
        (
            interfaces.IContribution,
            Index,
            'text/html',
            'html',
            'contribution/index_html.mako',
            {}),
    ])

    for i, spec in enumerate(specs):
        interface, base, mimetype, extension, template, extra = spec
        extra.update(mimetype=mimetype, extension=extension, template=template)
        cls = type('Renderer%s' % i, (base,), extra)
        config.registry.registerAdapter(
            cls, (interface,), list(implementedBy(base))[0], name=mimetype)

    for cls in [BibTex, TxtCitation, ReferenceManager]:
        for if_ in [interfaces.IRepresentation, interfaces.IMetadata]:
            for adapts in [interfaces.IContribution, interfaces.IDataset]:
                config.registry.registerAdapter(
                    cls,
                    (adapts,),
                    if_,
                    name=cls.mimetype)

    config.registry.registerAdapter(
        GeoJsonLanguages,
        (interfaces.ILanguage,),
        interfaces.IIndex,
        name=GeoJson.mimetype)
    config.registry.registerAdapter(
        GeoJsonParameter,
        (interfaces.IParameter,),
        interfaces.IRepresentation,
        name=GeoJson.mimetype)

    config.include(biblio)


def get_adapters(interface, ctx, req):
    # ctx can be a DataTable instance. In this case we create a resource by instantiating
    # the model class associated with the DataTable
    resource = ctx.model() if hasattr(ctx, 'model') else ctx
    return req.registry.getAdapters([resource], interface)


def get_adapter(interface, ctx, req, ext=None, name=None):
    """
    """
    adapters = dict(get_adapters(interface, ctx, req))

    if not ext and not name and (not req.accept or str(req.accept) == '*/*'):
        # force text/html in case there are no specific criteria to decide
        ext = 'html'

    if ext:
        # find adapter by requested file extension
        adapter = [r for r in adapters.values() if r.extension == ext]
    elif name:
        # or by mime type
        adapter = adapters.get(name)
    else:
        # or by content negotiation
        adapter = adapters.get(req.accept.best_match(adapters.keys()))

    if isinstance(adapter, list):
        if adapter:
            return adapter[0]
        return None
    return adapter
