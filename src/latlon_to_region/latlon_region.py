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
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any

import shapely

logger = logging.getLogger(__name__)


def find_region(
    provinces: dict[str, dict[str, Any]] | None = None,
) -> Callable[
    [list[float] | float, list[float] | float],
    list[dict[str, Any] | None] | dict[str, Any] | None,
]:
    """Function to match query lat/lon coordinates to their Longhurst Province.

    Parameters
    ----------
    provinces: dict or None
        Definition of the provinces, either already parsed definition in a
        dictionary or None (causing definition to get created internally)

    Returns
    -------
    find_region_func : Callable
        Function that takes location(s) in the form of latitude/longitude and
        returns the matching regions

    Raises
    ------
    RuntimeError
        If multiple regions are found (bug in definition?)
    """
    if provinces is None:
        provinces = parse_longhurst_xml()

    provinces_tree, polygons_fids = provinces_make_tree(provinces)

    def find_region_func(
        latitude: list[float] | float, longitude: list[float] | float
    ) -> list[dict[str, Any] | None] | dict[str, Any] | None:
        """Function that takes location(s) in the form of latitude/longitude and
        returns the matching regions

        Parameters
        ----------
        latitude : list of float or float
            Northerly latitude ranging from -90 to 90
        longitude : list of float or float
            Easterly longitude ranging from -180 to 180

        Returns
        -------
        regions : list of dict or dict or None
            `dict` with province code (e.g., Longhurst), name, bounding box and
            polygon, where the coordinate can be found. If the coordinate is on
            land, or otherwise not associated with a province, `None` will be
            returned.
        """
        list_passed = True
        if isinstance(latitude, float):
            list_passed = False
            latitude = [latitude]
            assert isinstance(longitude, float)
        if isinstance(longitude, float):
            assert not list_passed
            longitude = [longitude]

        regions = _find_region_tree(
            latitude, longitude, provinces, provinces_tree, polygons_fids
        )

        if len(latitude) == 1 and not list_passed:
            regions = regions[0]

        return regions

    return find_region_func


def _find_region_tree(
    latitude: list[float],
    longitude: list[float],
    provinces: dict[str, dict[str, Any]],
    provinces_tree: shapely.STRtree,
    polygons_fids: list[str],
) -> list[dict[str, Any] | None]:
    assert len(latitude) == len(longitude)

    loc_ids, region_ids = _find_matching_province_tree(
        latitude, longitude, provinces_tree
    )

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


def parse_longhurst_xml() -> dict[str, dict[str, Any]]:
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
        bb = _parse_polygon_coordinates(provBB)
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
            shell = _parse_polygon_coordinates(shell)
            logger.debug("shell parsed %s", shell)
            holes = polygon.findall("{http://www.opengis.net/gml}innerBoundaryIs")
            holes_parsed = []
            for hole in holes:
                hole = list(hole.iter("{http://www.opengis.net/gml}coordinates"))
                hole = hole[0].text
                assert hole is not None
                hole = _parse_polygon_coordinates(hole)
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


def _parse_polygon_coordinates(coordinates):
    coordinates = coordinates.split(" ")
    coordinates = [s.split(",") for s in coordinates]
    return [(float(lon), float(lat)) for lon, lat in coordinates]


def _find_matching_province_tree(
    latitude: list[float], longitude: list[float], provincesTree: shapely.STRtree
) -> list[list[int]]:
    """Perform Crossings Test on each candidate province."""

    loc = [shapely.Point(lon, lat) for lat, lon in zip(latitude, longitude)]
    return provincesTree.query(loc, predicate="covered_by").tolist()
