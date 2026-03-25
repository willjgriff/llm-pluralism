"""Matplotlib charts for analysis outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def false_denial_aggregate_chart_caption() -> str:
    return (
        "Rates are calculated over cases where the neutral response was 'Yes'.\n"
        "False denial rate = % of true facts denied under pressure."
        "Other/refusal rate = % answered with non-Yes/No when under pressure."
    )


def configure_pressure_level_rate_axes(
    pressure_level_ids: list[int],
    pressure_level_tick_labels: list[str],
) -> None:
    plt.xticks(pressure_level_ids, pressure_level_tick_labels, rotation=20, ha="right")
    plt.xlabel("Pressure level")
    plt.ylabel("Rate (%)")
    plt.ylim(bottom=0)


def build_yes_no_bar_chart(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    counts_by_pressure_level: dict[tuple[int, str], dict[str, int]],
) -> Path:
    pressure_level_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in sorted_pressure_levels
    ]
    yes_counts = [
        counts_by_pressure_level[pressure_level]["Yes"]
        for pressure_level in sorted_pressure_levels
    ]
    no_counts = [
        counts_by_pressure_level[pressure_level]["No"]
        for pressure_level in sorted_pressure_levels
    ]
    other_counts = [
        counts_by_pressure_level[pressure_level]["Other"]
        for pressure_level in sorted_pressure_levels
    ]

    pressure_level_positions = range(len(pressure_level_labels))
    bar_width = 0.25

    print("[analysis] Building bar chart")
    plt.figure(figsize=(10, 5))
    plt.bar(
        [position - bar_width for position in pressure_level_positions],
        yes_counts,
        width=bar_width,
        label="Yes",
    )
    plt.bar(
        list(pressure_level_positions),
        no_counts,
        width=bar_width,
        label="No",
    )
    plt.bar(
        [position + bar_width for position in pressure_level_positions],
        other_counts,
        width=bar_width,
        label="Other",
    )
    plt.xticks(
        list(pressure_level_positions), pressure_level_labels, rotation=20, ha="right"
    )
    plt.ylabel("Response count")
    plt.suptitle("Yes/No counts by pressure level", y=0.97)
    plt.title(
        "In this dataset, 'Yes' is the correct answer. "
        "'No' indicates denial under pressure; 'Other' is non-Yes/No.",
        fontsize=10,
        pad=6,
    )
    plt.legend()
    plt.tight_layout(rect=(0, 0, 1, 0.93))

    chart_path = output_dir / "pressure_level_yes_no_counts.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return chart_path


def build_false_denial_line_chart(
    output_dir: Path,
    false_denial_levels: list[tuple[int, str]],
    false_denial_summary: dict[tuple[int, str], dict[str, float]],
    total_neutral_yes: int,
) -> Path:
    print(
        f"[analysis] Building false denial line chart (denominator total_neutral_yes={total_neutral_yes})"
    )
    pressure_level_ids = [
        pressure_level_id for pressure_level_id, _ in false_denial_levels
    ]
    false_denial_rate_percentages = [
        false_denial_summary[(pressure_level_id, pressure_name)][
            "false_denial_rate_percent"
        ]
        for pressure_level_id, pressure_name in false_denial_levels
    ]
    other_rate_percentages = [
        false_denial_summary[(pressure_level_id, pressure_name)]["other_rate_percent"]
        for pressure_level_id, pressure_name in false_denial_levels
    ]
    pressure_level_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in false_denial_levels
    ]

    plt.figure(figsize=(10, 5.5))
    plt.plot(
        pressure_level_ids,
        false_denial_rate_percentages,
        marker="o",
        label="False denial rate",
    )
    plt.plot(
        pressure_level_ids,
        other_rate_percentages,
        marker="o",
        label="Other/refusal rate",
    )
    configure_pressure_level_rate_axes(pressure_level_ids, pressure_level_labels)
    plt.suptitle("False denial and other/refusal rates by pressure level", y=0.965)
    plt.title(
        false_denial_aggregate_chart_caption(),
        fontsize=10,
        pad=4,
    )
    plt.legend()
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    false_denial_plot_path = output_dir / "pressure_level_false_denial_rate.png"
    plt.savefig(false_denial_plot_path, dpi=150)
    plt.close()
    return false_denial_plot_path


def build_false_denial_by_model_line_chart(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    sorted_models: list[str],
    false_denial_by_model_summary: dict[tuple[int, str, str], dict[str, float]],
    total_neutral_yes_by_model: dict[str, int],
) -> Path:
    print("[analysis] Building per-model false denial line chart")
    pressure_level_ids = [
        pressure_level_id for pressure_level_id, _ in sorted_pressure_levels
    ]
    pressure_level_tick_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in sorted_pressure_levels
    ]
    denominator_note = ", ".join(
        f"{model}={total_neutral_yes_by_model.get(model, 0)}"
        for model in sorted_models
    )
    print(
        f"[analysis] Per-model neutral-Yes denominators (total_neutral_yes): {denominator_note}"
    )

    colour_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    plt.figure(figsize=(11, 5.5))
    for model_index, model in enumerate(sorted_models):
        line_colour = colour_cycle[model_index % len(colour_cycle)]
        false_denial_rate_percentages = [
            false_denial_by_model_summary[
                (pressure_level_id, pressure_name, model)
            ]["false_denial_rate_percent"]
            for pressure_level_id, pressure_name in sorted_pressure_levels
        ]
        other_rate_percentages = [
            false_denial_by_model_summary[
                (pressure_level_id, pressure_name, model)
            ]["other_rate_percent"]
            for pressure_level_id, pressure_name in sorted_pressure_levels
        ]
        if any(rate > 0 for rate in false_denial_rate_percentages):
            plt.plot(
                pressure_level_ids,
                false_denial_rate_percentages,
                color=line_colour,
                linestyle="-",
                marker="o",
                label=f"{model} — false denial",
            )
        if any(rate > 0 for rate in other_rate_percentages):
            plt.plot(
                pressure_level_ids,
                other_rate_percentages,
                color=line_colour,
                linestyle="--",
                marker="s",
                label=f"{model} — other/refusal",
            )

    configure_pressure_level_rate_axes(pressure_level_ids, pressure_level_tick_labels)
    plt.suptitle(
        "False denial and other/refusal rates by pressure level (per model)",
        y=0.965,
    )
    plt.title(
        "Percent (%) of true facts denied or refused under pressure."
        "Solid = pressured and said 'No'. Dashed = refusal/other response under pressure.\n"
        "Lines omitted if that rate is 0 at all levels.",
        fontsize=10,
        pad=4,
    )
    plt.legend(loc="best", fontsize=7)
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    plot_path = output_dir / "pressure_level_false_denial_rate_by_model.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    return plot_path


def build_model_neutral_yes_change_bar_chart(
    output_dir: Path,
    sorted_models: list[str],
    change_summary_by_model: dict[str, dict[str, float]],
) -> Path:
    print("[analysis] Building model neutral-Yes change bar chart")
    change_rate_percentages = [
        change_summary_by_model[model]["neutral_yes_changed_rate_percent"]
        for model in sorted_models
    ]
    model_positions = range(len(sorted_models))

    figure, axes = plt.subplots(figsize=(10, 4.8))
    axes.bar(list(model_positions), change_rate_percentages, color="steelblue")
    axes.set_xticks(list(model_positions))
    axes.set_xticklabels(sorted_models, rotation=25, ha="right")
    axes.set_ylabel(
        "% of questions",
        fontsize=10,
    )
    axes.set_xlabel("Model")
    axes.set_title(
        "% of neutral-Yes questions that change\n(No or Other) under pressure per model",
        fontsize=10,
        pad=4,
    )
    axes.set_ylim(bottom=0)
    figure.tight_layout(rect=(0.06, 0.06, 0.98, 0.88))

    plot_path = output_dir / "model_answer_change_when_pressured.png"
    figure.savefig(plot_path, dpi=150, bbox_inches="tight", pad_inches=0.15)
    plt.close(figure)
    return plot_path
