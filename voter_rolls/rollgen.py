# DataFrame to PDF code adapted from:
# https://levelup.gitconnected.com/how-to-write-a-pandas-dataframe-as-a-pdf-5cdf7d525488
import math

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from .models import StationAssignment, VoterRegistration
from .utils import grouper


def _draw_as_table(df, pagesize):
    alternating_colors = [
        ["white"] * len(df.columns),
        ["lightgray"] * len(df.columns),
    ] * len(df)
    alternating_colors = alternating_colors[: len(df)]
    fig, ax = plt.subplots(figsize=pagesize)
    ax.axis("tight")
    ax.axis("off")
    ax.table(
        cellText=df.values,
        rowLabels=df.index,
        colLabels=df.columns,
        rowColours=["lightblue"] * len(df),
        colColours=["lightblue"] * len(df.columns),
        cellColours=alternating_colors,
        loc="center",
    )
    return fig


def dataframe_to_pdf(
    df, filename, numpages=(1, 1), pagesize=(11, 8.5), footer_prefix=""
):
    with PdfPages(filename) as pdf:
        nh, nv = numpages
        rows_per_page = len(df) // nh
        cols_per_page = len(df.columns) // nv
        for i in range(0, nh):
            for j in range(0, nv):
                page = df.iloc[
                    (i * rows_per_page) : min((i + 1) * rows_per_page, len(df)),
                    (j * cols_per_page) : min((j + 1) * cols_per_page, len(df.columns)),
                ]
                fig = _draw_as_table(page, pagesize)
                if nh > 1 or nv > 1:
                    # Add a part/page number at bottom-center of page
                    fig.text(
                        0.5,
                        0.5 / pagesize[0],
                        f"{footer_prefix}Page-{i * nv + j + 1}",
                        ha="center",
                        fontsize=8,
                    )
                pdf.savefig(fig, bbox_inches="tight")

                plt.close()


def split_voters_into_stations(center, delete=True):
    if delete:
        StationAssignment.objects.filter(center=center).delete()
    print(f"Assigning stations for {center.center_id} ({center.center_name})")
    voter_pks = (
        VoterRegistration.objects.filter(center=center)
        .order_by("voter__voter_name")
        .values_list("voter__pk", flat=True)
    )
    for station_id, voter_pk_group in enumerate(grouper(voter_pks, 500), 1):
        StationAssignment.objects.bulk_create(
            [
                StationAssignment(
                    center=center,
                    station_id=station_id,
                    voter_id=voter_pk,
                )
                for voter_pk in voter_pk_group
            ]
        )


def write_station_list(center, station_id):
    voter_names = (
        StationAssignment.objects.filter(
            center=center,
            station_id=station_id,
        )
        .order_by("voter__voter_name")
        .values_list("voter__voter_name", flat=True)
    )
    nrows = len(voter_names)
    if nrows == 0:
        raise ValueError(f"{nrows=} for {center.pk=} and {station_id=}")
    signature_cells = [""] * nrows

    df = pd.DataFrame(
        zip(voter_names, signature_cells),
        columns=["Voter Name", "Signature"],
        index=range(1, nrows + 1),
    )
    num_v_pages = math.ceil(nrows / 40)  # ~40 rows per page (not exact)
    dataframe_to_pdf(
        df,
        f"center_{center.center_id}_{station_id}.pdf",
        numpages=(num_v_pages, 1),
        footer_prefix=f"{center.center_name} ({center.center_id}) Voter List - ",
    )
    return num_v_pages
