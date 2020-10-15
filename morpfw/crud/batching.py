from urllib.parse import urlparse, parse_qs, urlencode
from urllib.parse import urlunparse


class CollectionBatching(object):
    def __init__(
        self, request, collection, query=None, order_by=None, pagesize=20, pagenumber=0
    ):
        self.collection = collection
        self.request = request
        self.pagesize = pagesize
        self.pagenumber = pagenumber
        self.query = query
        self.order_by = order_by
        self._items = None
        self._total = None

    def items(self):
        if self._items is None:
            offset = self.pagesize * self.pagenumber
            self._items = self.collection.search(
                query=self.query,
                limit=self.pagesize,
                offset=offset,
                order_by=self.order_by,
            )
        return self._items

    def total(self):
        if self._total is None:
            self._total = self.collection.aggregate(
                query=self.query,
                group={"count": {"function": "count", "field": "uuid"}},
            )[0]["count"]
        return self._total

    def total_pages(self):
        total = self.total()
        return int(total / self.pagesize) + 1

    def next_page(self):
        return self.pagenumber + 1

    def navigator(self, url=None, size=3):
        if url is None:
            url = self.request.url
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)

        def get_page_url(page):
            qso = qs.copy()
            qso["page"] = page
            return (
                parsed_url.scheme
                + "://"
                + parsed_url.hostname
                + parsed_url.path
                + "?"
                + urlencode(qso)
            )

        pages = []
        if self.pagenumber > 0:
            pages.append(
                {
                    "page": self.pagenumber - 1,
                    "title": "Previous",
                    "url": get_page_url(self.pagenumber - 1),
                }
            )
        if self.pagenumber > 0:
            minpage = 0
            if (self.pagenumber - size) > 0:
                minpage = self.pagenumber - size
            for i in range(minpage, self.pagenumber):
                qs = qs.copy()
                qs["page"] = i
                pages.append({"page": i, "title": str(i + 1), "url": get_page_url(i)})
        pages.append({"page": self.pagenumber, "title": str(self.pagenumber + 1)})
        if self.pagenumber < self.total_pages():
            maxpage = self.total_pages()
            if (self.pagenumber + 1 + size) < self.total_pages():
                maxpage = self.pagenumber + 1 + size
            for i in range(self.pagenumber + 1, maxpage):
                qs = qs.copy()
                qs["page"] = i
                pages.append({"page": i, "title": str(i + 1), "url": get_page_url(i)})
        if self.pagenumber + 1 < self.total_pages():
            pages.append(
                {
                    "page": self.pagenumber + 1,
                    "title": "Next",
                    "url": get_page_url(self.pagenumber + 1),
                }
            )
        return pages
