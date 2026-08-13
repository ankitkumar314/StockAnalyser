import base64
import io
import logging
from pathlib import Path
from typing import Dict, Optional

import matplotlib

matplotlib.use("Agg")  # non-interactive backend; must be set before pyplot import, server has no display
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalChartBuilder:
    """
    Renders a multi-panel technical analysis chart (price + Bollinger Bands, MACD,
    RSI, ADX) and a separate Renko brick chart for one ticker, using matplotlib.

    `indicators` maps indicator name -> the DataFrame returned by that indicator's
    compute(), all sharing the same index as `ohlcv`.
    """

    def __init__(self, ticker: str, ohlcv: pd.DataFrame, indicators: Dict[str, pd.DataFrame]):
        self.ticker = ticker.upper()
        self.ohlcv = ohlcv
        self.indicators = indicators

    def build_main_chart(self) -> plt.Figure:
        fig, (price_ax, macd_ax, rsi_ax, adx_ax) = plt.subplots(
            4, 1, figsize=(12, 14), sharex=True, gridspec_kw={"height_ratios": [3, 1, 1, 1]}
        )

        price_ax.plot(self.ohlcv.index, self.ohlcv["Close"], label="Close", color="black", linewidth=1)
        bb = self.indicators.get("bollinger_bands")
        if bb is not None:
            price_ax.plot(bb.index, bb["UpperBand"], label="Upper Band", color="tab:blue", linewidth=0.8)
            price_ax.plot(bb.index, bb["MiddleBand"], label="Middle Band (SMA)", color="tab:orange", linewidth=0.8)
            price_ax.plot(bb.index, bb["LowerBand"], label="Lower Band", color="tab:blue", linewidth=0.8)
            price_ax.fill_between(bb.index, bb["LowerBand"], bb["UpperBand"], color="tab:blue", alpha=0.08)
        price_ax.set_title(f"{self.ticker} - Price & Bollinger Bands")
        price_ax.legend(loc="upper left", fontsize=8)
        price_ax.grid(alpha=0.3)

        macd = self.indicators.get("macd")
        if macd is not None:
            macd_ax.plot(macd.index, macd["MACD"], label="MACD", color="tab:blue", linewidth=1)
            macd_ax.plot(macd.index, macd["Signal"], label="Signal", color="tab:red", linewidth=1)
            hist = macd["Histogram"].fillna(0)
            colors = ["tab:green" if v >= 0 else "tab:red" for v in hist]
            macd_ax.bar(macd.index, hist, color=colors, width=1.0, alpha=0.4)
            macd_ax.legend(loc="upper left", fontsize=8)
        macd_ax.set_title("MACD")
        macd_ax.grid(alpha=0.3)

        rsi = self.indicators.get("rsi")
        if rsi is not None:
            rsi_ax.plot(rsi.index, rsi["RSI"], label="RSI", color="tab:purple", linewidth=1)
            rsi_ax.axhline(70, color="tab:red", linestyle="--", linewidth=0.7)
            rsi_ax.axhline(30, color="tab:green", linestyle="--", linewidth=0.7)
            rsi_ax.set_ylim(0, 100)
        rsi_ax.set_title("RSI")
        rsi_ax.grid(alpha=0.3)

        adx = self.indicators.get("adx")
        if adx is not None:
            adx_ax.plot(adx.index, adx["ADX"], label="ADX", color="black", linewidth=1)
            adx_ax.plot(adx.index, adx["+DI"], label="+DI", color="tab:green", linewidth=0.8)
            adx_ax.plot(adx.index, adx["-DI"], label="-DI", color="tab:red", linewidth=0.8)
            adx_ax.axhline(25, color="gray", linestyle="--", linewidth=0.7)
            adx_ax.legend(loc="upper left", fontsize=8)
        adx_ax.set_title("ADX / +DI / -DI")
        adx_ax.grid(alpha=0.3)

        fig.autofmt_xdate()
        fig.tight_layout()
        return fig

    def build_renko_chart(self, renko_df: pd.DataFrame) -> Optional[plt.Figure]:
        if renko_df.empty:
            return None

        fig, ax = plt.subplots(figsize=(12, 5))
        for i, row in enumerate(renko_df.itertuples()):
            color = "tab:green" if row.direction > 0 else "tab:red"
            bottom = min(row.open, row.close)
            height = abs(row.close - row.open)
            ax.add_patch(plt.Rectangle((i, bottom), 0.9, height, color=color))

        prices = pd.concat([renko_df["open"], renko_df["close"]])
        ax.set_xlim(0, len(renko_df))
        ax.set_ylim(prices.min() * 0.995, prices.max() * 1.005)
        ax.set_title(f"{self.ticker} - Renko Chart (brick size {renko_df.attrs.get('brick_size', 0):.2f})")
        ax.set_xlabel("Brick #")
        ax.set_ylabel("Price")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        return fig

    @staticmethod
    def _fig_to_base64(fig: plt.Figure) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    @staticmethod
    def _save_fig(fig: plt.Figure, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format="png", dpi=110)
        return path

    def render(
        self,
        renko_df: Optional[pd.DataFrame],
        include_base64: bool,
        save_dir: Optional[Path],
    ) -> Dict[str, Optional[str]]:
        """
        Builds the main chart (and Renko chart, if bricks are available), returning
        base64 PNG string(s) and/or on-disk path(s) per the requested options. Figures
        are always closed after use to avoid leaking matplotlib figure memory across
        requests.
        """
        result: Dict[str, Optional[str]] = {
            "chart_png_base64": None,
            "chart_saved_path": None,
            "renko_chart_png_base64": None,
            "renko_chart_saved_path": None,
        }

        main_fig = self.build_main_chart()
        try:
            if include_base64:
                result["chart_png_base64"] = self._fig_to_base64(main_fig)
            if save_dir is not None:
                path = self._save_fig(main_fig, save_dir / f"{self.ticker}_technical_chart.png")
                result["chart_saved_path"] = str(path)
        finally:
            plt.close(main_fig)

        if renko_df is not None and not renko_df.empty:
            renko_fig = self.build_renko_chart(renko_df)
            if renko_fig is not None:
                try:
                    if include_base64:
                        result["renko_chart_png_base64"] = self._fig_to_base64(renko_fig)
                    if save_dir is not None:
                        path = self._save_fig(renko_fig, save_dir / f"{self.ticker}_renko_chart.png")
                        result["renko_chart_saved_path"] = str(path)
                finally:
                    plt.close(renko_fig)

        return result
