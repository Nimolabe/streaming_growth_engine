"""Nachbau des Firestore-Python-Clients (nur der genutzte Teil), für Tests ohne Netzwerk und ohne Kosten.

Bildet die Regeln nach, auf die sich der Adapter verlässt: create() scheitert bei vorhandenem Dokument,
update() scheitert bei veralteter Vorbedingung oder fehlendem Dokument, Listen in Listen sind verboten.
"""

from __future__ import annotations

import copy
import itertools
from typing import Any


class AlreadyExists(Exception):
    pass


class FailedPrecondition(Exception):
    pass


class NotFound(Exception):
    pass


class ServiceUnavailable(Exception):
    pass


def _check_no_nested_arrays(value: Any, in_array: bool = False) -> None:
    if isinstance(value, list):
        if in_array:
            raise ValueError("Firestore erlaubt keine Listen direkt in Listen.")
        for v in value:
            _check_no_nested_arrays(v, True)
    elif isinstance(value, dict):
        for v in value.values():
            _check_no_nested_arrays(v, False)


class _Snap:
    def __init__(self, doc_id: str, data: dict | None, update_time: int | None):
        self.id, self._data, self.update_time = doc_id, data, update_time

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return copy.deepcopy(self._data)


class _WriteOption:
    def __init__(self, last_update_time: int):
        self.last_update_time = last_update_time


class FakeClient:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, tuple[dict, int]]] = {}
        self._clock = itertools.count(1)
        self._ids = itertools.count(1)
        self.down = False

    def _guard(self) -> None:
        if self.down:
            raise ServiceUnavailable("simulierter Ausfall")

    def collection(self, path: str) -> "FakeCollection":
        return FakeCollection(self, path)

    def write_option(self, last_update_time: int) -> _WriteOption:
        return _WriteOption(last_update_time)


class FakeDoc:
    def __init__(self, client: FakeClient, coll: str, doc_id: str):
        self.client, self.coll, self.id = client, coll, doc_id

    @property
    def _bucket(self) -> dict:
        return self.client.store.setdefault(self.coll, {})

    def get(self) -> _Snap:
        self.client._guard()
        item = self._bucket.get(self.id)
        return _Snap(self.id, item[0] if item else None, item[1] if item else None)

    def create(self, data: dict) -> None:
        self.client._guard()
        _check_no_nested_arrays(data)
        if self.id in self._bucket:
            raise AlreadyExists(f"{self.coll}/{self.id}")
        self._bucket[self.id] = (copy.deepcopy(data), next(self.client._clock))

    def set(self, data: dict) -> None:
        self.client._guard()
        _check_no_nested_arrays(data)
        self._bucket[self.id] = (copy.deepcopy(data), next(self.client._clock))

    def update(self, data: dict, option: _WriteOption | None = None) -> None:
        self.client._guard()
        _check_no_nested_arrays(data)
        item = self._bucket.get(self.id)
        if item is None:
            raise NotFound(f"{self.coll}/{self.id}")
        if option is not None and option.last_update_time != item[1]:
            raise FailedPrecondition("update_time passt nicht")
        merged = {**item[0], **copy.deepcopy(data)}
        self._bucket[self.id] = (merged, next(self.client._clock))

    def collection(self, name: str) -> "FakeCollection":
        return FakeCollection(self.client, f"{self.coll}/{self.id}/{name}")


class FakeCollection:
    def __init__(self, client: FakeClient, path: str, filters: list | None = None, limit: int | None = None):
        self.client, self.path, self.filters, self._limit = client, path, filters or [], limit

    def document(self, doc_id: str) -> FakeDoc:
        return FakeDoc(self.client, self.path, doc_id)

    def add(self, data: dict) -> tuple[None, FakeDoc]:
        doc = self.document(f"auto{next(self.client._ids):06d}")
        doc.create(data)
        return None, doc

    def where(self, field: str, op: str, value: Any) -> "FakeCollection":
        assert op == "=="
        return FakeCollection(self.client, self.path, [*self.filters, (field, value)], self._limit)

    def limit(self, n: int) -> "FakeCollection":
        return FakeCollection(self.client, self.path, self.filters, n)

    def stream(self):
        self.client._guard()
        out = []
        for doc_id, (data, t) in sorted(self.client.store.get(self.path, {}).items()):
            if all(data.get(f) == v for f, v in self.filters):
                out.append(_Snap(doc_id, copy.deepcopy(data), t))
        return iter(out[: self._limit] if self._limit else out)
