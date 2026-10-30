"""Context for /trade/logistics, the Logistics screen."""

from axk_capstone.web import page

no_cache = 1


def get_context(context):
    return page(context, "logistics", "Logistics & Transport · AXK Trade")
