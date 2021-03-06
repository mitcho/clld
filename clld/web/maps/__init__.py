from markupsafe import Markup
from pyramid.renderers import render

from clld.interfaces import IDataTable, IMapMarker, IIcon
from clld.web.util import helpers
from clld.web.util.htmllib import HTML
from clld.web.adapters import GeoJsonLanguages


class Layer(object):
    """A layer in our terminology is a FeatureCollection in geojson and a FeatureGroup
    in leaflet, i.e. a bunch of points on the map.
    """
    def __init__(self, id_, name, data, **kw):
        self.id = id_
        self.name = name
        self.data = data
        for k, v in kw.items():
            setattr(self, k, v)


class Legend(object):
    """Object holding all data necessary to render a navpill with a dropdown above a map.
    """
    def __init__(self, map_, name, items, label=None, stay_open=False, item_attrs=None):
        self.map = map_
        self.name = name
        self.label = label or name.capitalize()
        self.items = items
        self.stay_open = stay_open
        self.item_attrs = item_attrs or {}

    def format_id(self, suffix=None):
        suffix = suffix or ''
        if suffix:
            suffix = '-' + suffix
        return 'legend-%s%s' % (self.name, suffix)

    def render_item(self, item):
        if not isinstance(item, (tuple, list)):
            item = [item]
        attrs = self.item_attrs
        if self.stay_open:
            class_ = attrs.get('class', attrs.get('class_', ''))
            attrs['class'] = class_ + ' stay-open'
        return HTML.li(*item, **attrs)

    def render(self):
        a_attrs = {
            'class': 'dropdown-toggle',
            'data-toggle': "dropdown",
            'href': "#",
            'id': self.format_id('opener')}
        ul_class = 'dropdown-menu'
        if self.stay_open:
            ul_class += ' stay-open'
        return HTML.li(
            HTML.a(self.label, HTML.b(class_='caret'), **a_attrs),
            HTML.ul(
                *map(self.render_item, self.items),
                **dict(class_=ul_class, id=self.format_id('container'))),
            class_='dropdown',
            id=self.format_id(),
        )


class Map(object):
    """Map objects bridge the technology divide between server side python code and
    client side leaflet maps.
    """
    def __init__(self, ctx, req, eid='map'):
        self.req = req
        self.ctx = ctx
        self.eid = eid
        self._layers = None
        self._legends = None
        self.map_marker = req.registry.getUtility(IMapMarker)

    @property
    def layers(self):
        if self._layers is None:
            self._layers = list(self.get_layers())
        return self._layers

    def get_layers(self):
        route_params = {'ext': 'geojson'}
        if not IDataTable.providedBy(self.ctx):
            route_params['id'] = self.ctx.id
        route_name = self.req.matched_route.name
        if not route_name.endswith('_alt'):
            route_name += '_alt'
        yield Layer(
            getattr(self.ctx, 'id', 'id'),
            '%s' % self.ctx,
            self.req.route_url(route_name, **route_params))

    def options(self):
        return {}

    def render(self):
        return Markup(render(
            'clld:web/templates/map.mako', {'map': self}, request=self.req))

    @property
    def legends(self):
        if self._legends is None:
            self._legends = list(self.get_legends())
        return self._legends

    def get_legends(self):
        if len(self.layers) > 1:
            items = []
            total = 0
            repr_attrs = dict(class_='pull-right stay-open', style="padding-right: 10px;")

            for layer in self.layers:
                representation = ''
                if hasattr(layer, 'representation'):
                    total += layer.representation
                    representation = HTML.span(str(layer.representation), **repr_attrs)
                items.append([
                    HTML.label(
                        HTML.input(
                            class_="stay-open",
                            type="checkbox",
                            checked="checked",
                            onclick=helpers.JS_CLLD.mapToggleLayer(self.eid, layer.id, helpers.JS("this"))),
                        getattr(layer, 'marker', ''),
                        layer.name,
                        class_="checkbox inline stay-open",
                        style="margin-left: 5px; margin-right: 5px;",
                    ),
                    representation,
                ])
            if total:
                items.append(HTML.span(HTML.b(str(total)), **repr_attrs))
            yield Legend(
                self,
                'layers',
                items,
                label='Legend',
                stay_open=True,
                item_attrs=dict(style='clear: right'))
        items = []
        for size in [15, 20, 30, 40]:
            attrs = dict(name="iconsize", value=str(size), type="radio")
            if size == self.options().get('icon_size', 30):
                attrs['checked'] = 'checked'
            items.append(HTML.label(
                HTML.input(onclick=helpers.JS_CLLD.mapResizeIcons(self.eid), **attrs),
                HTML.img(
                    height=str(size),
                    width=str(size),
                    src=self.req.registry.getUtility(IIcon, 'cff6600').url(self.req)),
                class_="radio",
                style="margin-left: 5px; margin-right: 5px;"))
        yield Legend(
            self,
            'iconsize',
            items,
            label='Icon size')


class ParameterMap(Map):
    def get_layers(self):
        if self.ctx.domain:
            for de in self.ctx.domain:
                yield Layer(
                    de.id,
                    de.name,
                    self.req.resource_url(
                        self.ctx, ext='geojson', _query=dict(domainelement=str(de.id))
                    ),
                    marker=helpers.map_marker_img(self.req, de, marker=self.map_marker))
        else:
            yield Layer(
                self.ctx.id, self.ctx.name, self.req.resource_url(self.ctx, ext='geojson'))

    def options(self):
        return {'info_query': {'parameter': self.ctx.pk}, 'hash': True}


class _GeoJson(GeoJsonLanguages):
    def feature_iterator(self, ctx, req):
        return [ctx]


class LanguageMap(Map):
    def get_layers(self):
        geojson = _GeoJson(self.ctx)
        yield Layer(
            self.ctx.id, self.ctx.name, geojson.render(self.ctx, self.req, dump=False))

    def options(self):
        return {
            'center': [self.ctx.latitude, self.ctx.longitude],
            'zoom': 3,
            'no_popup': True,
            'sidebar': True}
