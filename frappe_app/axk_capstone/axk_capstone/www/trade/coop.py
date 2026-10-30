"""Context for /trade/coop, the Cooperative screen."""

from axk_capstone.web import page

no_cache = 1


def get_context(context):
    return page(context, "coop", "Cooperative · AXK Trade")
