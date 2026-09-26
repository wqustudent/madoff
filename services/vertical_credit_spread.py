import polars as pl


class VerticalCreditSpreadj:
    def __init__(self):
        self.safety_margin_up = None  # strike above underlying
        self.safety_margin_down = None  # strike below underlying

    def calculate_safety_margin(self, chain: pl.DataFrame):
        pass


if __name__ == "__main__":
    svc = VerticalCreditSpread()
