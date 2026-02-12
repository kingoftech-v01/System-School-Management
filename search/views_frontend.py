from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from core.models import NewsAndEvents

from .forms import AdvancedSearchForm
from .utils import execute_search


class SearchView(LoginRequiredMixin, ListView):
    template_name = "search/search_view.html"
    paginate_by = 20
    count = 0

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["count"] = self.count or 0
        context["query"] = self.request.GET.get("q")
        context["search_form"] = AdvancedSearchForm(self.request.GET or None)
        context["search_type"] = self.request.GET.get("search_type", "all")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")
        return context

    def get_queryset(self):
        request = self.request

        # Defensive tenant check
        if not getattr(request, 'tenant', None):
            return NewsAndEvents.objects.none()

        query = request.GET.get("q", None)

        if query is not None and len(query.strip()) >= 2:
            search_type = "all"
            date_from = None
            date_to = None

            form = AdvancedSearchForm(request.GET)
            if form.is_valid():
                search_type = form.cleaned_data.get("search_type", "all") or "all"
                date_from = form.cleaned_data.get("date_from")
                date_to = form.cleaned_data.get("date_to")

            queryset = execute_search(
                query.strip(),
                search_type=search_type,
                date_from=date_from,
                date_to=date_to,
            )
            self.count = len(queryset)
            return queryset

        return NewsAndEvents.objects.none()
