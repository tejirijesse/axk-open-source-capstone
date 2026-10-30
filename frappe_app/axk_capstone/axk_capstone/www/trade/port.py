"""Context for /trade/port, the Port / Terminal screen."""

from axk_capstone.web import page

no_cache = 1


def get_context(context):
    return page(context, "port", "Port / Terminal · AXK Trade")
