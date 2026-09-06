from ingester_prepper import IngesterPrepper


class Allocator:
    def __init__(self):
        self.ingester_prepper = IngesterPrepper()
        self.option_chain = None

    def ingest_chain(self):
        sub = self.ingester_prepper
        sub.load_option_chain()
        self.option_chain = sub.process_option_chain()


if __name__ == '__main__':
    svc = Allocator()
    svc.ingest_chain()
    print(svc.option_chain)
