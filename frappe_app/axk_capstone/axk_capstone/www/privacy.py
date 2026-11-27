"""Context for /privacy, the public privacy policy."""

from axk_capstone.web import _stamp, page

no_cache = 1


def get_context(context):
    page(context, "privacy", "Privacy Policy")
    context.trace_css_v = _stamp("css/trace.css")
    return context
