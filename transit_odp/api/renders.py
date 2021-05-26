from rest_framework.renderers import BaseRenderer


class XMLRender(BaseRenderer):
    media_type = "text/xml"
    format = "xml"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class BinRenderer(BaseRenderer):
    media_type = "application/bin"
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProtoBufRenderer(BaseRenderer):
    media_type = "application/protobuf"
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data
