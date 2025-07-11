import logging
import random
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import shapely
import shapely.plotting

from latlon_to_region import parse_longhurst_xml

logger = logging.getLogger(__name__)


def plot_latlon_region(
    filename: Path | str,
    latitude: list[float] | float,
    longitude: list[float] | float,
    provinces: dict[str, dict[str, Any]] | None = None,
):
    """Function that takes location(s) in the form of latitude/longitude and
    returns the matching regions

    Parameters
    ----------
    latitude : list of float or float
        Northerly latitude ranging from -90 to 90
    longitude : list of float or float
        Easterly longitude ranging from -180 to 180
    plot_file: str or None
        If provided, a map of the provinces and the query coordinates will be
        plotted and written to this file.

    Returns
    -------
    regions : list of dict or dict or None
        `dict` with province code (e.g., Longhurst), name, bounding box and
        polygon, where the coordinate can be found. If the coordinate is on
        land, or otherwise not associated with a province, `None` will be
        returned.
    """

    if provinces is None:
        provinces = parse_longhurst_xml()

    logger.info("plotting...")

    fig = plt.gcf()
    fig.set_size_inches(28.5, 20.5)
    plt.ylim(-75, 75)
    plt.xlim(-200, 200)
    for p in provinces.values():
        polygons = p["provGeoms"]
        clr = (random.random(), random.random(), random.random())
        for idx, polygon in enumerate(polygons):
            center = shapely.centroid(polygon)
            shapely.plotting.plot_polygon(
                polygon, color=clr, linewidth=1.0, add_points=False
            )
            plt.text(center.x, center.y, p["provCode"] + str(idx), fontsize=12)

    list_passed = True
    if isinstance(latitude, float):
        list_passed = False
        latitude = [latitude]
        assert isinstance(longitude, float)
    if isinstance(longitude, float):
        assert not list_passed
        longitude = [longitude]

    for lat, lon in zip(latitude, longitude):
        plt.plot(
            lon,
            lat,
            marker="o",
            markersize=10,
            markeredgecolor="red",
            markerfacecolor=(0.0, 1.0, 0.0, 0.5),
        )
    plt.savefig(filename, dpi=300)
