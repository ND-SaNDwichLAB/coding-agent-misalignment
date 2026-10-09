from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

SYMPTOM_NAMES = {
    "S1": "Wrong Project Diagnosis",
    "S2": "Misread Developer Intent",
    "S3": "Developer Constraint Violation",
    "S4": "Self-Initiated Overreach",
    "S5": "Faulty Implementation",
    "S6": "Operational Execution Error",
    "S7": "Inaccurate Self-Reporting",
    "S8": "Other / Emerging",
}

CAUSE_COLS = [f"C{i}" for i in range(1, 8)]

CAUSE_NAMES = {
    "C1": "Underspecified Instruction",
    "C2": "Scope Overreach",
    "C3": "Premature Action",
    "C4": "Context Loss",
    "C5": "Default-Driven Override",
    "C6": "Instruction-Following Failure",
    "C7": "Cannot Determine",
}

OUTCOME_NAMES = {
    "DS0": "No damage",
    "DS1": "Effort/trust cost only",
    "DS2": "System damage, easily reversed",
    "DS3": "System damage, hard to reverse",
    "DS4": "Unobservable",
    "DL1": "Code/task state",
    "DL2": "Project state",
    "DL3": "Environment/configuration",
    "DL4": "External state",
}

RESOLUTION_NAMES = {
    "RS1": "Resolved",
    "RS2": "Unknown",
    "RV1": "Agent self-corrected",
    "RV2": "Agent after pushback",
    "RV3": "Developer took over",
}

ALIGNMENT_GOAL_NAMES = {
    "instruction": "Instruction",
    "intention": "Intention",
    "both": "Both",
}

DISPLAY_NAME_MAPS = {
    "symptom": SYMPTOM_NAMES,
    "cause": CAUSE_NAMES,
    "damage_severity": OUTCOME_NAMES,
    "damage_locus": OUTCOME_NAMES,
    "resolution_status": RESOLUTION_NAMES,
    "resolver": RESOLUTION_NAMES,
    "alignment_goal": ALIGNMENT_GOAL_NAMES,
}

RESULTS_DIR = Path("results")


def get_indicator_matrix(df, axis):
    if axis == "symptom":
        cols = [f"S{i}" for i in range(1, 9)]
        mat = df[cols].fillna(False).astype(int)
        mat.columns = cols
        return mat

    if axis == "cause":
        cols = CAUSE_COLS
        mat = df[cols].notna().astype(int)
        mat.columns = cols
        return mat

    dummies = pd.get_dummies(df[axis], dtype=int)
    dummies = dummies.reindex(sorted(dummies.columns), axis=1)
    return dummies


def _get_display_name_map(axis):
    return DISPLAY_NAME_MAPS.get(axis, {})


def _format_display_label(label, axis):
    name_map = _get_display_name_map(axis)
    full_name = name_map.get(label)
    if full_name is None:
        return label
    return f"{label}. {full_name}"


def _apply_pretty_labels(table, row_axis=None, col_axis=None):
    pretty = table.copy()

    if row_axis is not None:
        pretty.index = [
            _format_display_label(label, row_axis) for label in pretty.index
        ]

    if col_axis is not None:
        pretty.columns = [
            _format_display_label(label, col_axis) for label in pretty.columns
        ]

    return pretty


def _format_axis_title(axis):
    return axis.replace("_", " ").title()


def _save_cross_axis_heatmap(
    table, row_axis, col_axis, decimals=2, pretty_labels=True, results_dir=RESULTS_DIR
):
    plot_table = table.copy()
    if pretty_labels:
        plot_table = _apply_pretty_labels(
            plot_table, row_axis=row_axis, col_axis=col_axis
        )

    n_rows, n_cols = plot_table.shape
    fig_width = max(6, n_cols * 1.6)
    fig_height = max(4, n_rows * 0.8)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    im = ax.imshow(plot_table.values, cmap="Blues", aspect="auto")

    ax.set_xticks(range(n_cols))
    ax.set_yticks(range(n_rows))
    ax.set_xticklabels(plot_table.columns, rotation=45, ha="right")
    ax.set_yticklabels(plot_table.index)
    ax.set_title(f"{_format_axis_title(row_axis)} x {_format_axis_title(col_axis)}")
    ax.set_xlabel(_format_axis_title(col_axis))
    ax.set_ylabel(_format_axis_title(row_axis))

    vmax = im.norm.vmax if im.norm.vmax else 0
    threshold = vmax / 2 if vmax else 0
    for i in range(n_rows):
        for j in range(n_cols):
            value = plot_table.iat[i, j]
            color = "white" if value > threshold else "black"
            ax.text(
                j, i, f"{value:.{decimals}f}", ha="center", va="center", color=color
            )

    fig.tight_layout()
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / f"{row_axis}_x_{col_axis}_heatmap.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def axis_value_counts_table(
    df, axis, decimals=2, pretty_labels=True, include_session_type_pct=True
):
    mat = get_indicator_matrix(df, axis)
    counts = mat.sum(axis=0)

    table = pd.DataFrame(
        {
            "count": counts,
            "percent": (counts / len(df) * 100).round(decimals).astype(str) + "%",
        }
    )

    if include_session_type_pct and "session_type" in df.columns:
        ide_mask = df["session_type"].eq("IDE")
        cli_mask = df["session_type"].eq("CLI")

        ide_denom = int(ide_mask.sum())
        cli_denom = int(cli_mask.sum())

        ide_counts = mat.loc[ide_mask].sum(axis=0)
        cli_counts = mat.loc[cli_mask].sum(axis=0)

        table["ide_pct"] = (
            (ide_counts / ide_denom * 100).round(decimals).astype(str) + "%"
            if ide_denom
            else pd.Series(["NA"] * len(table), index=table.index)
        )
        table["cli_pct"] = (
            (cli_counts / cli_denom * 100).round(decimals).astype(str) + "%"
            if cli_denom
            else pd.Series(["NA"] * len(table), index=table.index)
        )

    if pretty_labels:
        table = _apply_pretty_labels(table, row_axis=axis)
    return table


def cross_axis_counts(df, row_axis, col_axis):
    row_mat = get_indicator_matrix(df, row_axis)
    col_mat = get_indicator_matrix(df, col_axis)
    counts = row_mat.T.dot(col_mat)
    counts.index.name = row_axis
    counts.columns.name = col_axis
    return counts


def cross_axis_percent_table(
    df,
    row_axis,
    col_axis,
    decimals=2,
    pretty_labels=True,
    vis_heatmap=False,
    results_dir=RESULTS_DIR,
):
    counts = cross_axis_counts(df, row_axis, col_axis)

    row_pct = counts.div(counts.sum(axis=1), axis=0) * 100
    row_share = counts.sum(axis=1) / counts.values.sum() * 100
    col_share = counts.sum(axis=0) / counts.values.sum() * 100

    table = row_pct.copy()
    table["All"] = row_share
    table.loc["All"] = list(col_share) + [100.0]

    if vis_heatmap:
        _save_cross_axis_heatmap(
            row_pct.round(decimals),
            row_axis=row_axis,
            col_axis=col_axis,
            decimals=decimals,
            pretty_labels=pretty_labels,
            results_dir=results_dir,
        )

    table = table.round(decimals).astype(str) + "%"
    if pretty_labels:
        table = _apply_pretty_labels(table, row_axis=row_axis, col_axis=col_axis)
    return table


def top_within_axis_overlaps(
    df,
    axis,
    min_count=1,
    top_k=15,
    decimals=4,
    pretty_labels=True,
):
    mat = get_indicator_matrix(df, axis)
    counts = mat.T.dot(mat)
    support = mat.sum(axis=0)
    n = len(df)

    rows = []
    labels = list(mat.columns)
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            count = int(counts.loc[left, right])
            if count < min_count:
                continue

            left_support = int(support.loc[left])
            right_support = int(support.loc[right])
            union = left_support + right_support - count

            rows.append(
                {
                    f"{axis}_a": left,
                    f"{axis}_b": right,
                    "count": count,
                    "jaccard": round(count / union, decimals) if union else 0.0,
                    "overlap_coef": (
                        round(count / min(left_support, right_support), decimals)
                        if min(left_support, right_support)
                        else 0.0
                    ),
                    "lift": (
                        round(
                            (count / n) / ((left_support / n) * (right_support / n)),
                            decimals,
                        )
                        if left_support and right_support
                        else 0.0
                    ),
                    "p_b_given_a": (
                        round(count / left_support, decimals) if left_support else 0.0
                    ),
                    "p_a_given_b": (
                        round(count / right_support, decimals) if right_support else 0.0
                    ),
                }
            )

    table = pd.DataFrame(rows).sort_values(
        ["jaccard", "count"], ascending=[False, False]
    )
    table = table.head(top_k).reset_index(drop=True)

    if pretty_labels and not table.empty:
        table[f"{axis}_a"] = table[f"{axis}_a"].map(
            lambda label: _format_display_label(label, axis)
        )
        table[f"{axis}_b"] = table[f"{axis}_b"].map(
            lambda label: _format_display_label(label, axis)
        )

    return table
