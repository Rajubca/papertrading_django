# signals/views_feed.py
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# If you want to require login for this page, keep @login_required.
# Remove the decorator if it's a public page.
@method_decorator(login_required, name="dispatch")
class SignalFeedPage(TemplateView):
    template_name = "signals/feed.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["symbol"] = self.kwargs.get("symbol")  # None => all symbols
        return ctx
