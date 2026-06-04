from __future__ import annotations

try:  # pragma: no cover
    from itemadapter import ItemAdapter as ItemAdapter
except Exception:  # pragma: no cover - lets unit tests run before dependencies are installed.

    class ItemAdapter:
        def __init__(self, item):
            self.item = item

        def get(self, key, default=None):
            return self.item.get(key, default)

        def __getitem__(self, key):
            return self.item[key]

        def __setitem__(self, key, value):
            self.item[key] = value

        def __iter__(self):
            return iter(self.item)

        def __eq__(self, other):
            return self.item == other

        def items(self):
            return self.item.items()

        def keys(self):
            return self.item.keys()

        def __contains__(self, key):
            return key in self.item

        def __len__(self):
            return len(self.item)

        def __repr__(self):
            return repr(self.item)
