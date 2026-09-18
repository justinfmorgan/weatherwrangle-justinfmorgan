"""Temperature histograms for the daily_14.json forecast dataset.

Renders a single 2x3 PNG so a person can eyeball the temperature fields for
anomalies (bimodality, zero-range stub days, hemisphere skew, forecast-horizon
narrowing). Reads the cached pandas pickle produced by flatten.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402

PICKLE_PATH = Path(os.environ.get("WW_SCRATCH", ".")) / "daily.pkl"
OUTPUT_PATH = Path(__file__).with_suffix(".png")

KELVIN_OFFSET = 273.15
TEMP_FIELDS = ["temp_day", "temp_min", "temp_max", "temp_night", "temp_eve", "temp_morn"]
FIELD_LABELS = {
    "temp_day": "day",
    "temp_min": "min",
    "temp_max": "max",
    "temp_night": "night",
    "temp_eve": "evening",
    "temp_morn": "morning",
}

BACKGROUND = "#fcfcfb"
INK = "#1f2328"
MUTED_INK = "#6b6f75"
GRID = "#e6e6e2"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]

TEMP_BINS = np.arange(-35, 46, 1.0)
RANGE_BINS = np.arange(0, 33, 0.5)
BAR_KWARGS = {"edgecolor": BACKGROUND, "linewidth": 0.3}
OVERLAY_ALPHA = 0.45
HEADROOM = 1.5  # y-limit multiplier so notes and legends sit above the bars


def load_celsius() -> pd.DataFrame:
    """Load the pickle and add Celsius columns for each temp field."""
    frame = pd.read_pickle(PICKLE_PATH)
    for field in TEMP_FIELDS:
        frame[f"{field}_c"] = frame[field] - KELVIN_OFFSET
    frame["range_c"] = frame["temp_max_c"] - frame["temp_min_c"]
    return frame


def style_axes(ax: Axes, *, title: str, xlabel: str) -> None:
    """Apply the shared panel styling: light surface, no top/right spines, faint grid."""
    ax.set_facecolor(BACKGROUND)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED_INK, labelsize=8, length=0)
    ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold", color=INK, pad=8)
    ax.set_xlabel(xlabel, fontsize=8.5, color=MUTED_INK)
    ax.set_ylabel("rows", fontsize=8.5, color=MUTED_INK)
    ax.set_ylim(0, ax.get_ylim()[1] * HEADROOM)


def add_note(ax: Axes, text: str, *, x: float = 0.98, y: float = 0.96) -> None:
    """Place a short muted annotation inside the panel, right-aligned by default."""
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="right" if x > 0.5 else "left",
        va="top",
        fontsize=7.6,
        color=MUTED_INK,
        linespacing=1.35,
    )


def add_legend(ax: Axes, *, loc: str = "upper left") -> None:
    """Compact legend in muted ink."""
    legend = ax.legend(loc=loc, fontsize=8, frameon=False, labelcolor=INK, handlelength=1.2)
    for handle in legend.legend_handles:
        handle.set_alpha(0.9)


def panel_temp_day(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 1: temp_day across all rows."""
    values = frame["temp_day_c"]
    ax.hist(values, bins=TEMP_BINS, color=SERIES[0], **BAR_KWARGS)
    style_axes(ax, title="1. Daytime temperature, all city-days", xlabel="temp_day (°C)")
    counts, edges = np.histogram(values, bins=TEMP_BINS)
    cold_mode = edges[np.argmax(counts[edges[:-1] < 18])]
    warm_mode = edges[np.where(edges[:-1] >= 18)[0][np.argmax(counts[edges[:-1] >= 18])]]
    add_note(
        ax,
        f"bimodal: modes near {cold_mode:.0f}°C and {warm_mode:.0f}°C\n"
        f"median {values.median():.1f}°C, n = {len(values):,}",
    )


def panel_all_fields(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 2: all six temperature fields overlaid."""
    for color, field in zip(SERIES, TEMP_FIELDS):
        ax.hist(
            frame[f"{field}_c"],
            bins=TEMP_BINS,
            color=color,
            alpha=OVERLAY_ALPHA,
            label=FIELD_LABELS[field],
            **BAR_KWARGS,
        )
    style_axes(ax, title="2. All six temperature fields", xlabel="temperature (°C)")
    add_legend(ax)
    equal_share = (frame["temp_day"] == frame["temp_max"]).mean() * 100
    add_note(ax, f"day == max in {equal_share:.0f}% of rows;\nmin/night/morning cluster ~6°C cooler")


def panel_city_means(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 3: per-city mean temp_day, one value per city_id."""
    city_means = frame.groupby("city_id")["temp_day_c"].mean()
    ax.hist(city_means, bins=TEMP_BINS, color=SERIES[2], **BAR_KWARGS)
    style_axes(ax, title="3. Per-city mean daytime temperature", xlabel="mean temp_day per city (°C)")
    ax.set_ylabel("cities", fontsize=8.5, color=MUTED_INK)
    add_note(
        ax,
        f"{len(city_means):,} cities; same two humps as panel 1\n"
        f"(so it is geography, not day-to-day noise)",
    )


def panel_daily_range(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 4: temp_max - temp_min, with the zero spike called out."""
    rng = frame["range_c"]
    ax.hist(rng, bins=RANGE_BINS, color=SERIES[3], **BAR_KWARGS)
    style_axes(ax, title="4. Daily range (max − min)", xlabel="temp_max − temp_min (°C)")
    zero = frame[rng == 0]
    zero_days = ", ".join(str(d) for d in sorted(zero["day_idx"].unique()))
    ax.annotate(
        f"spike at exactly 0: {len(zero):,} rows ({len(zero) / len(frame) * 100:.1f}%)\n"
        f"all six temps identical, one row per city,\n"
        f"only at day_idx {zero_days} (forecast edge days)",
        xy=(0.25, len(zero)),
        xytext=(0.97, 0.96),
        textcoords="axes fraction",
        ha="right",
        va="top",
        fontsize=7.6,
        color=MUTED_INK,
        linespacing=1.35,
        arrowprops={"arrowstyle": "-", "color": MUTED_INK, "linewidth": 0.7, "shrinkB": 3},
    )
    add_note(ax, f"median range {rng.median():.1f}°C, max {rng.max():.1f}°C", x=0.97, y=0.70)


def panel_hemisphere(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 5: temp_day split by hemisphere."""
    north = frame.loc[frame["lat"] >= 0, "temp_day_c"]
    south = frame.loc[frame["lat"] < 0, "temp_day_c"]
    ax.hist(north, bins=TEMP_BINS, color=SERIES[0], alpha=OVERLAY_ALPHA + 0.2, label=f"north (n={len(north):,})", **BAR_KWARGS)
    ax.hist(south, bins=TEMP_BINS, color=SERIES[1], alpha=OVERLAY_ALPHA + 0.2, label=f"south (n={len(south):,})", **BAR_KWARGS)
    style_axes(ax, title="5. Daytime temperature by hemisphere", xlabel="temp_day (°C)")
    add_legend(ax)
    add_note(
        ax,
        f"south is {len(south) / len(frame) * 100:.0f}% of rows, tight around {south.median():.0f}°C\n"
        f"north carries both humps (median {north.median():.0f}°C)",
        x=0.98,
        y=0.96,
    )


def panel_first_vs_last(ax: Axes, frame: pd.DataFrame) -> None:
    """Panel 6: temp_day on the first forecast day vs the last."""
    first = frame.loc[frame["day_idx"] == 0, "temp_day_c"]
    last = frame.loc[frame["day_idx"] == frame["n_days"] - 1, "temp_day_c"]
    ax.hist(first, bins=TEMP_BINS, color=SERIES[4], alpha=OVERLAY_ALPHA + 0.2, label="day_idx = 0", **BAR_KWARGS)
    ax.hist(last, bins=TEMP_BINS, color=SERIES[5], alpha=OVERLAY_ALPHA + 0.2, label="day_idx = n_days − 1", **BAR_KWARGS)
    style_axes(ax, title="6. First vs last forecast day", xlabel="temp_day (°C)")
    add_legend(ax)
    add_note(
        ax,
        f"last day narrower: sd {last.std():.1f} vs {first.std():.1f}°C,\n"
        f"max {last.max():.0f} vs {first.max():.0f}°C; the warm hump\n"
        f"pulls in toward the middle over the horizon",
        x=0.98,
        y=0.96,
    )


def render(frame: pd.DataFrame) -> None:
    """Lay out the 2x3 grid and write the PNG."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 9), dpi=130)
    fig.patch.set_facecolor(BACKGROUND)
    panels = [
        panel_temp_day,
        panel_all_fields,
        panel_city_means,
        panel_daily_range,
        panel_hemisphere,
        panel_first_vs_last,
    ]
    for ax, panel in zip(axes.flat, panels):
        panel(ax, frame)
    fig.suptitle(
        "Forecast temperatures across 22,635 cities: bimodal, with a zero-range stub day per city",
        x=0.03,
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.03,
        0.935,
        "OpenWeatherMap 16/17-day daily forecast (daily_14.json), 368,909 city-days, Kelvin converted to °C",
        fontsize=9,
        color=MUTED_INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92), h_pad=2.2, w_pad=2.0)
    fig.savefig(OUTPUT_PATH, facecolor=BACKGROUND)


def main() -> None:
    """Entry point."""
    frame = load_celsius()
    render(frame)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
