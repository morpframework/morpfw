from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class CollectionBatching(object):
    def __init__(
        self,
        request,
        collection,
        query=None,
        order_by=None,
        pagesize=20,
        pagenumber=0,
        page_opt="page",
    ):
        self.collection = collection
        self.request = request
        self.pagesize = pagesize
        self.pagenumber = pagenumber
        self.query = query
        self.order_by = order_by
        self._items = None
        self._total = None
        self.page_opt = page_opt

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
            for k, v in list(qso.items()):
                if isinstance(v, list) and len(v) == 1:
                    v = v[0]
                qso[k] = v
            qso[self.page_opt] = page
            return (
                parsed_url.scheme
                + "://"
                + parsed_url.netloc
                + parsed_url.path
                + "?"
                + urlencode(qso)
            )

        pages = []

        minpage = 0
        if (self.pagenumber - size) > 0:
            minpage = self.pagenumber - size
            if self.total_pages() - self.pagenumber <= size:
                minpage -= 1 + size - (self.total_pages() - self.pagenumber)
                if minpage < 0:
                    minpage = 0
            if (self.pagenumber + 1 + size) < self.total_pages():
                minpage += 1

        maxpage = self.total_pages()
        if (self.pagenumber + 1 + size) < self.total_pages():
            maxpage = self.pagenumber + 1 + size
            if self.pagenumber < size:
                maxpage += size - self.pagenumber
                if maxpage > self.total_pages():
                    maxpage = self.total_pages()
            if (self.pagenumber - size) > 0:
                maxpage -= 1

        if self.pagenumber > 0:
            pages.append(
                {
                    "page": self.pagenumber - 1,
                    "title": "<",
                    "url": get_page_url(self.pagenumber - 1),
                }
            )
        elif self.pagenumber == 0:
            pages.append(
                {"page": self.pagenumber, "title": "<", "state": "disabled",}
            )

        if self.pagenumber - size > 0:
            if minpage > 0:
                if self.pagenumber != 0:
                    pages.append({"page": 0, "title": "1", "url": get_page_url(0)})
                pages.append(
                    {"page": None, "title": "...", "url": None, "state": "disabled"}
                )

        # pre
        if self.pagenumber > 0:

            for i in range(minpage, self.pagenumber):
                qs = qs.copy()
                qs["page"] = i
                pages.append({"page": i, "title": str(i + 1), "url": get_page_url(i)})
        pages.append(
            {
                "page": self.pagenumber,
                "title": str(self.pagenumber + 1),
                "url": None,
                "state": "active",
            }
        )

        # post
        if self.pagenumber < self.total_pages():

            for i in range(self.pagenumber + 1, maxpage):
                qs = qs.copy()
                qs["page"] = i
                pages.append({"page": i, "title": str(i + 1), "url": get_page_url(i)})

        if self.pagenumber + 1 + size < self.total_pages():
            if maxpage < self.total_pages():
                pages.append(
                    {"page": None, "title": "...", "url": None, "state": "disabled"}
                )
                if self.pagenumber != self.total_pages() - 1:
                    pages.append(
                        {
                            "page": self.total_pages() - 1,
                            "title": str(self.total_pages()),
                            "url": get_page_url(self.total_pages() - 1),
                        }
                    )
        if self.pagenumber + 1 < self.total_pages():
            pages.append(
                {
                    "page": self.pagenumber + 1,
                    "title": ">",
                    "url": get_page_url(self.pagenumber + 1),
                }
            )
        elif self.pagenumber + 1 == self.total_pages():
            pages.append(
                {
                    "page": self.pagenumber,
                    "title": ">",
                    "url": None,
                    "state": "disabled",
                }
            )

        return pages
