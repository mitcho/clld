from zope.interface import implementer, implementedBy
from pyramid.response import Response
from pyramid.renderers import render as pyramid_render

from clld import interfaces


class Renderable(object):
    """Virtual base class for adapters

    Adapters can provide custom behaviour either by specifying a template to use for
    rendering, or by overwriting the render method.

    >>> r = Renderable(None)
    >>> assert r.label == 'Renderable'
    """
    template = None
    mimetype = 'text/plain'
    extension = None
    send_mimetype = None

    def __init__(self, obj):
        self.obj = obj

    @property
    def label(self):
        return getattr(self, '__label__', self.__class__.__name__)

    @property
    def charset(self):
        return 'utf-8' \
            if self.mimetype.startswith('text/') \
            or 'xml' in self.mimetype \
            or 'kml' in self.mimetype \
            else None

    def render_to_response(self, ctx, req):
        res = Response(self.render(ctx, req))
        res.vary = 'Accept'
        res.content_type = self.send_mimetype or self.mimetype
        if self.charset:
            res.content_type += '; charset=%s' % self.charset
        return res

    def render(self, ctx, req):
        return pyramid_render(self.template, {'ctx': ctx}, request=req)


@implementer(interfaces.IRepresentation)
class Representation(Renderable):
    """Base class for adapters implementing IRepresentation
    """
    pass


@implementer(interfaces.IRepresentation)
class Json(Renderable):
    """
    """
    mimetype = 'application/json'
    extension = 'json'

    def render(self, ctx, req):
        return pyramid_render('json', ctx, request=req)


@implementer(interfaces.IIndex)
class Index(Renderable):
    """Base class for adapters implementing IIndex
    """
    pass


ADAPTER_COUNTER = 0


def adapter_factory(template, mimetype='text/html', extension='html', base=None):
    global ADAPTER_COUNTER
    base = base or Representation
    extra = dict(mimetype=mimetype, extension=extension, template=template)
    cls = type('AdapterFromFactory%s' % ADAPTER_COUNTER, (base,), extra)
    ADAPTER_COUNTER += 1
    return cls
