from transit_odp.common.views import BaseTemplateView


class PublishGateKeeperView(BaseTemplateView):
    template_name = "publish/gatekeeper.html"


class PublishAbodsGateKeeperView(BaseTemplateView):
    template_name = "publish/abods-gatekeeper.html"
