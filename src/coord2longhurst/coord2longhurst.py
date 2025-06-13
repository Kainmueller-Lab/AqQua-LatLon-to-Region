"""This package provides the function `find_region` that takes as input latitude and longitude coordinates and a definition of Longhurst Provinces returns the Longhurst Province where the coordinate is located. It provides a second function `parseLonghurstXML` to separately parse a Longhurst Provinces definition file."""

import argparse
import logging
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import shapely
import shapely.plotting

logger = logging.getLogger(__name__)


def find_region(
    latitude: float,
    longitude: float,
    longhurst_definition: str | Path | dict[str, dict[str, Any]],
    plot_file=None,
) -> dict[str, Any] | None:
    """Function to match query lat/lon coordinates to their Longhurst Province.

    Parameters
    ----------
    latitude : float
        Northerly latitude ranging from -90 to 90
    longitude : float
        Easterly longitude ranging from -180 to 180
    longhurst_definition: str or dict
        Definition of the provinces, either path to the xml file or already parsed definition within a dictionary
    plot_file: str or None
        If provided, a map of the provinces and the query coordinates will be plotted and written to this file.

    Returns
    -------
    region : dict or None
        `dict` with Longhurst province code, name, bounding box and polygon, where the coordinate can be found. If the coordinate is on land, or otherwise not associated with a province, `None` will be returned.

    Raises
    ------
    RuntimeError
        If multiple regions are found (bug in definition?)
    """
    if isinstance(longhurst_definition, (str, Path)):
        provinces = parseLonghurstXML(Path(longhurst_definition))
    else:
        provinces = longhurst_definition
    provincesBB = _findMatchingBoundingBoxes(latitude, longitude, provinces)
    provincesFine = _findMatchingProvinceFine(latitude, longitude, provincesBB)

    if plot_file is not None:
        _exportFigure(plot_file, latitude, longitude, provinces)

    region = None
    if len(provincesFine) == 0:
        logger.debug(f"No province found matching {latitude} N, {longitude}E.  ")
        logger.debug(
            "This coordinate is either on land or it could be in one of these... "
        )
        for fid, p in provincesBB.items():
            print(fid, p["provCode"], p["provName"])

    elif len(provincesFine) == 1:
        region = list(provincesFine.values())[0]
        logger.info(f"Found region: {latitude} N, {longitude} E -->  {region}")

    elif len(provincesFine) > 1:
        raise RuntimeError(f"found multiple regions? ({provincesFine})")

    return region


def parseLonghurstXML(fl: str | Path) -> dict[str, dict[str, Any]]:
    """
    Parse GML data from longhurst.xml

    Parameters
    ----------
    fl : str or Path
        Path to the definition of the Longhurst Provinces (in xml/gml)

    Returns
    -------
    provinces : dict
        `dict` with the parsed provinces, mapping fid to province information (name, code, bounding box, polygon)

    Raises
    ------
    AssertionError
        If input file is formatted incorrectly.
    """
    provinces = {}
    tree = ET.parse("longhurst.xml")

    root = tree.getroot()
    for node in root.iter("{geo.vliz.be/MarineRegions}longhurst"):
        # 1. Get province code, name, bounding box and polygon from file
        fid = node.get("fid")

        provCode = node.find("{geo.vliz.be/MarineRegions}provcode")
        assert provCode is not None
        provCode = provCode.text

        provName = node.find("{geo.vliz.be/MarineRegions}provdescr")
        assert provName is not None
        provName = provName.text

        provBB = node.find("{http://www.opengis.net/gml}boundedBy")
        assert provBB is not None
        provBB = provBB.find("{http://www.opengis.net/gml}Box")
        assert provBB is not None
        provBB = provBB.find("{http://www.opengis.net/gml}coordinates")
        assert provBB is not None
        provBB = provBB.text
        assert provBB is not None
        bb = _parsePolygonCoordinates(provBB)
        logger.debug(f"provBB parsed {bb}")
        bb_Poly = [bb[0], (bb[0][0], bb[1][1]), bb[1], (bb[1][0], bb[0][1]), bb[0]]
        logger.debug(f"provBB parsed {bb_Poly}")
        provBB = shapely.Polygon(bb_Poly)
        logger.debug(f"provBB parsed {provBB}")

        provGeoms = node.find("{geo.vliz.be/MarineRegions}the_geom")
        assert provGeoms is not None
        provGeoms = provGeoms.find("{http://www.opengis.net/gml}MultiPolygon")
        assert provGeoms is not None
        polygons = []
        for polygon in provGeoms.iter("{http://www.opengis.net/gml}Polygon"):
            shell = polygon.find("{http://www.opengis.net/gml}outerBoundaryIs")
            assert shell is not None
            shell = list(shell.iter("{http://www.opengis.net/gml}coordinates"))
            assert len(shell) == 1
            shell = shell[0].text
            assert shell is not None
            shell = _parsePolygonCoordinates(shell)
            logger.debug(f"shell parsed {shell}")
            holes = polygon.find("{http://www.opengis.net/gml}innerBoundaryIs")
            holes_parsed = []
            if holes is not None:
                holes = list(holes.iter("{http://www.opengis.net/gml}coordinates"))
                if len(holes) > 0:
                    for hole in holes:
                        hole = hole.text
                        assert hole is not None
                        hole = _parsePolygonCoordinates(hole)
                        holes_parsed.append(hole)
                logger.debug(f"holes parsed {holes_parsed}")
            polygons.append(shapely.Polygon(shell=shell, holes=holes_parsed))

        logger.info(f"Parsed province {provName} ({provCode})")
        provinces[fid] = {
            "provName": provName,
            "provCode": provCode,
            "provBB": provBB,
            "provGeoms": polygons,
        }

    return provinces


def _parsePolygonCoordinates(coordinates):
    coordinates = coordinates.split(" ")
    coordinates = [s.split(",") for s in coordinates]
    return [(float(x), float(y)) for x, y in coordinates]


def _findMatchingBoundingBoxes(
    lat: float, lon: float, provinces: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Find which candidate provinces our coordinates come from."""

    loc = shapely.Point(lat, lon)
    matchingProvinces = {}
    for fid, p in provinces.items():
        if p["provBB"].contains(loc):
            matchingProvinces[fid] = p

    return matchingProvinces


def _findMatchingProvinceFine(
    lat: float, lon: float, provinces: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Perform Crossings Test on each candidate province."""

    loc = shapely.Point(lat, lon)
    matchingProvinces = {}
    for fid, p in provinces.items():
        for provGeom in p["provGeoms"]:
            if provGeom.contains(loc):
                matchingProvinces[fid] = p
                break

    return matchingProvinces


def _exportFigure(
    filename: Path | str,
    latitude: float,
    longitude: float,
    provinces: dict[str, dict[str, Any]],
):
    logger.info("plotting...")
    fig = plt.gcf()
    fig.set_size_inches(28.5, 20.5)
    plt.ylim(-75, 75)
    plt.xlim(-200, 200)
    for p in provinces.values():
        polygons = p["provGeoms"]
        clr = (random.random(), random.random(), random.random())
        for polygon in polygons:
            center = shapely.centroid(polygon)
            shapely.plotting.plot_polygon(
                polygon, color=clr, linewidth=1.0, add_points=False
            )
            plt.text(center.x, center.y, p["provCode"], fontsize=22)

    plt.plot(
        latitude,
        longitude,
        marker="o",
        markersize=20,
        markeredgecolor="red",
        markerfacecolor="green",
    )
    plt.savefig(filename, dpi=300)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--longhurst-xml-file",
        type=str,
        help="Path to the XML file containing the Longhurst Provinces definition in gml format",
    )
    parser.add_argument(
        "-lon",
        "--longitude",
        type=float,
        help="longitude coordinate of the query location",
    )
    parser.add_argument(
        "-lat",
        "--latitude",
        type=float,
        help="latitude coordinate of the query location",
    )
    parser.add_argument(
        "-o",
        "--out-file",
        type=str,
        default=None,
        help="output location of plot",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logging.getLogger("matplotlib").setLevel(logging.INFO)

    _ = find_region(
        args.latitude, args.longitude, args.longhurst_xml_file, plot_file=args.out_file
    )


if __name__ == "__main__":
    main()
