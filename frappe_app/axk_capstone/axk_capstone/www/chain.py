"""Context for /chain, the chain explorer."""

from axk_capstone.web import _stamp, page

no_cache = 1


def get_context(context):
    page(context, "chain", "Chain explorer")
    context.trace_css_v = _stamp("css/trace.css")
    return context
