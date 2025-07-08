import logging
import random
import time

import pytest
from latlon_to_region import (
    find_region,
    parseLonghurstXML,
    provinces_make_tree,
)

logger = logging.getLogger(__name__)


def test_find_region_single():
    latitude = -68.999
    longitude = -54.44

    region = find_region(latitude, longitude)

    assert region is not None
    assert "provCode" in region
    assert region["provCode"] == "FKLD"


def test_find_region_list():
    latitudes = [-68.999, 64.234]
    longitudes = [-54.44, 23.542]

    regions = find_region(latitudes, longitudes)

    assert regions is not None
    assert len(regions) == 2
    assert "provCode" in regions[0]
    assert regions[0]["provCode"] == "FKLD"
    assert regions[1]["provCode"] == "ARAB"


def test_find_region_preparsed_xml_list():
    logging.getLogger("utils/latlon_to_longhurst").setLevel(logging.WARNING)

    provinces = parseLonghurstXML()
    latitudes = [-68.999]
    longitudes = [-54.44]

    region = find_region(latitudes, longitudes, provinces)
    logger.info("%s", region)

    assert region is not None
    assert len(region) == 1
    assert "provCode" in region[0]
    assert region[0]["provCode"] == "FKLD"


def test_find_region_preparsed_xml_tree():
    logging.getLogger("utils/latlon_to_longhurst").setLevel(logging.WARNING)
    provinces = parseLonghurstXML()
    provinces_tree, polygons_fids = provinces_make_tree(provinces)
    latitude = -68.999
    longitude = -54.44

    region = find_region(
        latitude,
        longitude,
        provinces,
        provinces_tree=provinces_tree,
        polygons_fids=polygons_fids,
    )

    assert region is not None
    assert "provCode" in region
    assert region["provCode"] == "FKLD"


def test_find_region_preparsed_xml_tree_multiple():
    """Tests that only a single region is found per location (lat/lon)"""
    logging.getLogger("utils/latlon_to_longhurst").setLevel(logging.WARNING)
    provinces = parseLonghurstXML()
    provinces_tree, polygons_fids = provinces_make_tree(provinces)
    lmt = 10000

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    start = time.time()
    _ = find_region(
        latitudes,
        longitudes,
        provinces,
        provinces_tree=provinces_tree,
        polygons_fids=polygons_fids,
    )

    end = time.time()
    logger.info(f"time: {end - start}")


@pytest.mark.skip(reason="only to compare the speed of different implementations")
def test_find_region_speed_list():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("utils/latlon_to_longhurst").setLevel(logging.WARNING)
    provinces = parseLonghurstXML()
    lmt = 10000

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    start = time.time()
    for i in range(lmt):
        _ = find_region(latitudes[i], longitudes[i], provinces)

    end = time.time()
    logger.info(f"time: {end - start}")


@pytest.mark.skip(reason="only to compare the speed of different implementations")
def test_find_region_preparsed_xml_tree_indivdually():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("utils/latlon_to_longhurst").setLevel(logging.WARNING)
    provinces = parseLonghurstXML()
    provinces_tree, polygons_fids = provinces_make_tree(provinces)
    lmt = 10000

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    start = time.time()
    for i in range(lmt):
        _ = find_region(
            latitudes[i],
            longitudes[i],
            provinces,
            provinces_tree=provinces_tree,
            polygons_fids=polygons_fids,
        )

    end = time.time()
    logger.info(f"time: {end - start}")
