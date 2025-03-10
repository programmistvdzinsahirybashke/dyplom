from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline
from goods.models import Service
from django.db.models import Q

def q_search(query):
    if query.isdigit() and len(query) <= 5:
        return Service.objects.filter(id=int(query))

    vector = SearchVector("service_name", "service_description")
    query = SearchQuery(query)

    result = (
        Service.objects.annotate(rank=SearchRank(vector, query))
        .filter(rank__gt=0)
        .order_by("-rank")
    )

    result = result.annotate(
        headline=SearchHeadline(
            "service_name",
            query,
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        )
    )
    result = result.annotate(
        bodyline=SearchHeadline(
            "service_description",
            query,
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        )
    )
    return result
