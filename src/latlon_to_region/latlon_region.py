"""This module provides functionality to convert latitude/longitude coordinates
to their matching Longhurst Province/region.

Functions:
---------
find_region: takes as input latitude and longitude coordinates; returns the
Longhurst Province where the coordinate is located
    latitude: Northerly latitude ranging from -90 to 90
    longitude: Easterly longitude ranging from -180 to 180
    longhurst_definition: if not provided, will be created on-th-fly, preparse
                          with parseLonghurstXML if querying multiple locations
    provinces_tree: if not provided, will be created on-th-fly, pre-create alongside
                    polygons_fids with provinces_make_tree if querying multiple locations
    polygons_fids: if not provided, will be created on-th-fly, pre-create alongside
                   provinces_tree with provinces_make_tree if querying multiple locations
parseLonghurstXML: parses a Longhurst Provinces definition file and returns a dict of provinces
provinces_make_tree: puts the Longhurst provinces polygons into a STRtree for faster querying


List of Provinces
-----------------
List of Provinces in xml file:
['ALSK', 'ANTA', 'APLR', 'ARAB', 'ARCH', 'ARCT', 'AUSE', 'AUSW', 'BENG', 'BERS',
 'BPLR', 'BRAZ', 'CAMR', 'CARB', 'CCAL', 'CHIN', 'CNRY', 'EAFR', 'ETRA', 'FKLD',
 'GFST', 'GUIA', 'GUIN', 'INDE', 'INDW', 'ISSG', 'KURO', 'MEDI', 'MONS', 'NADR',
 'NASE', 'NASW', 'NATR', 'NECS', 'NEWZ', 'NPPF', 'NPSW', 'NPTG', 'NWCS', 'PEQD',
 'PNEC', 'PSAE', 'PSAW', 'REDS', 'SANT', 'SARC', 'SATL', 'SPSG', 'SSTC', 'SUND',
 'TASM', 'WARM', 'WTRA']
+ ['CHIL']

List of Provinces in [doi.org/10.1002/gbc.20089](Dynamic biogeochemical provinces in the global ocean)
['ALSK', 'ANTA', 'APLR', 'ARAB', 'ARCH', 'ARCT', 'AUSE', 'AUSW', 'BENG', 'BERS',
 'BPLR', 'BRAZ', 'CAMR', 'CARB', 'CCAL', 'CHIN', 'CNRY', 'EAFR', 'ETRA', 'FKLD',
 'GFST', 'GUIA', 'GUIN', 'INDE', 'INDW', 'ISSG', 'KURO', 'MEDI', 'MONS', 'NADR',
 'NASE', 'NASW', 'NATR', 'NECS', 'NEWZ', 'NPPF', 'NPSW', 'NPTG', 'NWCS', 'PEQD',
 'PNEC', 'PSAE', 'PSAW', 'REDS', 'SANT', 'SARC', 'SATL', 'SPSG', 'SSTC', 'SUND',
 'TASM', 'WARM', 'WTRA'
]
+ ['C(O)CAL', 'HUMB', 'NPSE']

Notes

- 'HUMB' seems to be the same as 'CHIL' (west coast South America)
- 'NPSE' (Northeast Pacific subtropical) is not contained in xml file (but I also could
  not figure out exactly where it is, somewhere South of Japan maybe)
- 'C(O)CAL' (California current) is not contained in xml file (non-coastal California)
"""

import importlib.resources
import logging
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import shapely
import shapely.plotting

logger = logging.getLogger(__name__)


def find_region(
    latitude: list[float] | float,
    longitude: list[float] | float,
    longhurst_definition: dict[str, dict[str, Any]] | None = None,
    provinces_tree: shapely.STRtree | bool = False,
    polygons_fids: list[str] | None = None,
    plot_file: str | Path | None = None,
) -> list[dict[str, Any] | None] | dict[str, Any] | None:
    """Function to match query lat/lon coordinates to their Longhurst Province.

    Parameters
    ----------
    latitude : list of float or float
        Northerly latitude ranging from -90 to 90
    longitude : list of float or float
        Easterly longitude ranging from -180 to 180
    longhurst_definition: dict or None
        Definition of the provinces, either already parsed definition in a
        dictionary or None (causing definition to get parsed from file)
    provinces_tree: shapely.STRtree or bool
        Precomputed tree of provinces (faster access) or flag to compute it on the fly
    plot_file: str or None
        If provided, a map of the provinces and the query coordinates will be plotted
        and written to this file.

    Returns
    -------
    region : list of dict or dict or None
        `dict` with Longhurst province code, name, bounding box and polygon,
        where the coordinate can be found. If the coordinate is on land, or
        otherwise not associated with a province, `None` will be returned.

    Raises
    ------
    RuntimeError
        If multiple regions are found (bug in definition?)
    """
    if longhurst_definition is None:
        provinces = parseLonghurstXML()

    else:
        provinces = longhurst_definition
        assert provinces_tree is not None

    list_passed = True
    if isinstance(latitude, float):
        list_passed = False
        latitude = [latitude]
        assert isinstance(longitude, float)
    if isinstance(longitude, float):
        assert not list_passed
        longitude = [longitude]

    if plot_file is not None:
        _exportFigure(plot_file, latitude, longitude, provinces)

    if provinces_tree:
        if not isinstance(provinces_tree, shapely.STRtree):
            provinces_tree, polygons_fids = provinces_make_tree(provinces)
        assert polygons_fids is not None, (
            "please provide a list of fids per polygon in addition to a pre-calculated tree"
        )
        regions = _find_region_tree(
            latitude, longitude, provinces, provinces_tree, polygons_fids
        )
    else:
        regions = _find_region_list(latitude, longitude, provinces)

    if len(latitude) == 1 and not list_passed:
        regions = regions[0]

    return regions


def _find_region_list(
    latitude: list[float], longitude: list[float], provinces: dict[str, dict[str, Any]]
) -> list[dict[str, Any]] | list[None]:
    regions = []
    for lat, lon in zip(latitude, longitude):
        provincesBB = _findMatchingBoundingBoxes(lat, lon, provinces)
        matched_regions = _findMatchingProvinceFine(lat, lon, provincesBB)

        region = None
        if len(matched_regions) == 0:
            logger.debug("No province found matching %f N, %f E.  ", lat, lon)
            logger.debug(
                "This coordinate is either on land or it could be in one of these... "
            )
            for fid, p in provincesBB.items():
                logger.debug("%s, %s, %s", fid, p["provCode"], p["provName"])

        elif len(matched_regions) == 1:
            region = list(matched_regions.values())[0]
            logger.debug("Found region: %f N, %f E -->  %s", lat, lon, region)

        elif len(matched_regions) > 1:
            raise RuntimeError(
                f"found multiple regions for lat {lat}, lon {lon}?"
                " ({[p['provCode'] for p in matched_regions.values()]})"
            )
        regions.append(region)

    return regions


def _find_region_tree(
    latitude: list[float],
    longitude: list[float],
    provinces: dict[str, dict[str, Any]],
    provinces_tree: shapely.STRtree,
    polygons_fids: list[str],
) -> list[dict[str, Any] | None]:
    assert len(latitude) == len(longitude)

    loc_ids, region_ids = _findMatchingProvinceTree(latitude, longitude, provinces_tree)

    loc_region_id_map = [[] for i in range(len(latitude))]
    for loc_id, r_id in zip(loc_ids, region_ids):
        loc_region_id_map[loc_id].append(r_id)

    regions = []
    for idx, r in enumerate(loc_region_id_map):
        region = None
        if len(r) == 0:
            logger.debug(
                "No province found matching %f N, %f E.  ",
                latitude[idx],
                longitude[idx],
            )
            logger.debug(
                "This coordinate is either on land or it could be in one of these:"
            )
        elif len(r) == 1:
            polygon_fid = polygons_fids[r[0]]
            region = provinces[polygon_fid]
            logger.debug(
                "Found region: %f N, %f E -->  %s",
                latitude[idx],
                longitude[idx],
                region,
            )

        elif len(r) > 1:
            for idx in r:
                polygon_fid = polygons_fids[idx]
                region = provinces[polygon_fid]
                regions.append(region)
            raise RuntimeError(
                f"found multiple regions for lat {latitude[idx]}, lon {longitude[idx]}? "
                "({r}, {[p['provCode'] for p in regions]})"
            )
        regions.append(region)

    return regions


def parseLonghurstXML() -> dict[str, dict[str, Any]]:
    """
    Parse GML data from longhurst.xml

    Returns
    -------
    provinces : dict
        `dict` with the parsed provinces, mapping fid to province information
        (name, code, bounding box, polygon)

    Raises
    ------
    AssertionError
        If input file is formatted incorrectly.
    """
    provinces = {}
    root = ET.fromstring(
        importlib.resources.read_text(
            "latlon_to_region", "longhurst_definition/longhurst.xml"
        )
    )

    for node in root.iter("{geo.vliz.be/MarineRegions}longhurst"):
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
        logger.debug("provBB parsed %s", bb)
        bb_Poly = [bb[0], (bb[0][0], bb[1][1]), bb[1], (bb[1][0], bb[0][1]), bb[0]]
        logger.debug("provBB parsed %s", bb_Poly)
        provBB = shapely.Polygon(bb_Poly)
        logger.debug("provBB parsed %s", provBB)

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
            logger.debug("shell parsed %s", shell)
            holes = polygon.findall("{http://www.opengis.net/gml}innerBoundaryIs")
            holes_parsed = []
            for hole in holes:
                hole = list(hole.iter("{http://www.opengis.net/gml}coordinates"))
                hole = hole[0].text
                assert hole is not None
                hole = _parsePolygonCoordinates(hole)
                holes_parsed.append(hole)

            polygons.append(shapely.Polygon(shell=shell, holes=holes_parsed))

        logger.debug("Parsed province %s (%s)", provName, provCode)
        provinces[fid] = {
            "provName": provName,
            "provCode": provCode,
            "provBB": provBB,
            "provGeoms": polygons,
        }

    return provinces


def provinces_make_tree(
    provinces: dict[str, dict[str, Any]],
) -> tuple[shapely.STRtree, list[str]]:
    """Function to put the Longhurst provinces polygons into a STRtree for faster querying

    Parameters
    ----------
    provinces: dict of province id to province data
        dict that contains the parsed Longhurst Provinces data

    Returns
    -------
    provinces_tree: shapely.STRtree
        tree of polygons that make up the provinces, allows for faster queries
    polygons_fids:
        maps polygons back to provinces, to get province data after query
    """
    polygons = []
    polygons_fids = []
    for fid, prov in provinces.items():
        polygons.extend(prov["provGeoms"])
        polygons_fids.extend([fid] * len(prov["provGeoms"]))

    provinces_tree = shapely.STRtree(polygons)
    return provinces_tree, polygons_fids


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


def _findMatchingProvinceTree(
    latitude: list[float], longitude: list[float], provincesTree: shapely.STRtree
) -> list[list[int]]:
    """Perform Crossings Test on each candidate province."""

    loc = [shapely.Point(lat, lon) for lat, lon in zip(latitude, longitude)]
    return provincesTree.query(loc, predicate="covered_by").tolist()


def _exportFigure(
    filename: Path | str,
    latitude: list[float],
    longitude: list[float],
    provinces: dict[str, dict[str, Any]],
):
    import matplotlib.pyplot as plt

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

    for lat, lon in zip(latitude, longitude):
        plt.plot(
            lat,
            lon,
            marker="o",
            markersize=10,
            markeredgecolor="red",
            markerfacecolor=(0.0, 1.0, 0.0, 0.5),
        )
    plt.savefig(filename, dpi=300)
