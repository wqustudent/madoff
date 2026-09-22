import datetime
from datetime import datetime
from pathlib import Path
import random

import matplotlib.pyplot as plt
import polars as pl

from allocator import Allocator


class Visualizer:
    def __init__(self):
        self.HERE = Path(__file__).parent
        self.images_dir = self.HERE / "images"

    def visualize_positions(self, xs: pl.DataFrame, positions: list[float]):
        # calculate current_pair_mids from xs
        print("\nxs")
        print(xs)
        print("\nxs.columns")
        print(xs.columns)

        print("\npositions")
        print(positions)
        pair_quotes = self._calculate_pair_mids(xs)

        fig, ax = plt.subplots(figsize=(15, 10))

        # plot pair cost
        plt.plot(pair_quotes["STRIKE"], pair_quotes["PAIR_MID"], "-b", label="PAIR COST")
        plt.axvline(x=xs['UNDERLYING_LAST'][0], ymin=0.05, ymax=0.9, color='k', linestyle='--', label="UNDERLYING")

        # plot positions
        self._plot_settlement_guarantee(pair_quotes, positions)

        plt.legend()
        plt.title(f"Oct positions imply \nsettlement cash inflow guarantees by market maker")

        fig.savefig(self.images_dir / "positions.png")

    def visualize_move(self, xss: list[pl.DataFrame], positions: list[float], move: tuple[float, float]):
        # calculate prev_pair_mids & new_pair_mids from xs_ & xs
        xs_, xs = xss[0], xss[1]
        pair_quotes_ = self._calculate_pair_mids(xs_)
        pair_quotes = self._calculate_pair_mids(xs)

        fig, ax = plt.subplots(figsize=(15, 10))

        plt.plot(pair_quotes_["STRIKE"], pair_quotes_["PAIR_MID"], "-.b", label="PREVIOUS COST")
        plt.axvline(x=xs_['UNDERLYING_LAST'][0], ymin=0.05, ymax=0.9, color='k', linestyle='-.', label="UNDERLYING")

        plt.plot(pair_quotes["STRIKE"], pair_quotes["PAIR_MID"], "-b", label="CURRENT COST")
        plt.axvline(x=xs['UNDERLYING_LAST'][0], ymin=0.05, ymax=0.9, color='k', linestyle='-', label="UNDERLYING")

        from_, to = move[0], move[1]
        idx = positions.index(from_)
        _ = positions.pop(idx)
        positions.append(to)
        positions.sort()

        cost_ = pair_quotes.filter(
            pl.col("STRIKE") == from_
        )["PAIR_MID"][0]
        plt.plot(from_, cost_, "oy", markersize=10, label="(MOVE) FROM POSITION")
        cost = pair_quotes.filter(
            pl.col("STRIKE") == to
        )["PAIR_MID"][0]
        plt.axhspan(ymin=cost_, ymax=cost, color='g', alpha=0.5, label="Cash Collected")

        self._plot_settlement_guarantee(pair_quotes, positions)
        plt.legend(loc="upper right")

        plt.title(f"Oct positions allow \ncash collection")
        fig.savefig(self.images_dir / "move.png")

    @staticmethod
    def _plot_settlement_guarantee(pair_quotes:pl.DataFrame, positions: list[float]):
        for x in positions:
            y = pair_quotes.filter(
                pl.col("STRIKE") == x
            )["PAIR_MID"][0]
            plt.plot(x, y, "om", markersize=10, label="POSITION")

        # plot settlement guarantee
        assert len(positions) == 4  # Visualizing Oct for now
        positions.sort()
        s0, s1, s2, s3 = positions
        plt.axvspan(xmin=s0, xmax=s3, color='g', alpha=0.5, label="Settlement Cash Guarantee #1")
        plt.axvspan(xmin=s1, xmax=s2, color='g', alpha=0.5, label="Settlement Cash Guarantee #2")

    def _calculate_pair_mids(self, xs: pl.DataFrame):
        pair_quotes = (
            xs
            .with_columns(
                ((pl.col("PAIR_BID") + pl.col("PAIR_ASK")) / 2).alias("PAIR_MID")
            )
            .select(
                pl.col("STRIKE"),
                pl.col("PAIR_MID"),
                pl.col("UNDERLYING_LAST"),
            )
            # .filter(pl.col("STRIKE").is_in(positions))
        )
        print("\npair_quotes")
        print(pair_quotes)
        return pair_quotes


if __name__ == "__main__":
    # use allocator (& ingestor) to find a cross-section / external state
    al = Allocator()
    al.ingest_chain("SNDK")

    qt = al.option_chain.select(
        pl.col("QUOTE_READTIME")
    ).unique().sort("QUOTE_READTIME")[0].item()

    available_expiry_dates = al.find_available_expiry_dates(qt)
    ed = available_expiry_dates[-1]

    quotes_dates, quote_times, xss = ["2026-06-01", "2026-06-15"], [], []
    for qd in quotes_dates:
        qd = datetime.strptime(qd, "%Y-%m-%d")
        qt = al.option_chain.filter(
            pl.col("QUOTE_DATE") == qd
        ).select(
            pl.col("QUOTE_READTIME"),
        ).unique()[0].item()
        print(f"{qt=}")
        quote_times.append(qt)

        xs = al.find_external_state(qt, ed)
        xss.append(xs)

    # sample strikes
    pair_strikes = [1000, 1200, 1400, 1600]

    vis = Visualizer()
    # visualize move
    move = (1200, 1500)
    vis.visualize_move(xss, pair_strikes, move)

    # visualize settlement cash guarantee
    vis.visualize_positions(xss[1], pair_strikes)

