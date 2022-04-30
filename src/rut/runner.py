
from .collect import Collector

class Runner:
    def __init__(self):
        pass

    def execute(self, collector: Collector):
        """execute tests"""
        for name, test in collector.tests.items():
            try:
                if 'cls' in test:
                    obj = test['cls']()
                    test['func'](obj)
                else:
                    test['func']()
            except Exception:
                result = 'ERROR'
            else:
                result = 'PASS'
            test['result'] = result
            print(f"{name}: {result}")
