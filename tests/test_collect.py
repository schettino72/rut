
from rut.collect import Collector

class TestCollector:
    def test_init(self):
        col = Collector()
        assert col.mods == []
