from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase


class AdminSearchTest(TestCase):
    """
    Checks that the search fields of every registered admin are valid
    """

    def test_search_fields(self):
        request = RequestFactory().get("/", {"q": "test"})
        request.user = get_user_model().objects.create_superuser(
            username="admin", password="x", email="admin@test.it"
        )
        for model, model_admin in admin.site._registry.items():
            if not model_admin.search_fields:
                continue
            with self.subTest(model=model.__name__):
                queryset, _ = model_admin.get_search_results(
                    request, model.objects.all(), "test"
                )
                # the query is built (and fails) only when evaluated
                list(queryset)
