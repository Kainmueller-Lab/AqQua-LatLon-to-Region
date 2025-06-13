import logging
import random
import time

import pytest

from longhurst_province_finder import (
    find_region,
    parseLonghurstXML,
    provinces_make_tree,
)

logger = logging.getLogger(__name__)


def test_find_region():
    latitude = -68.999
    longitude = -54.44

    longhurst_definition = "../longhurst.xml"

    region = find_region(latitude, longitude, longhurst_definition)

    assert region is not None


def test_find_region_speed_list():
    longhurst_definition = "../longhurst.xml"
    provinces = parseLonghurstXML(longhurst_definition)
    lmt = 10000
    logging.getLogger("longhurst_province_finder.coord2longhurst").setLevel(
        logging.WARNING
    )

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    start = time.time()
    for i in range(lmt):
        _ = find_region(latitudes[i], longitudes[i], provinces)

    end = time.time()
    logger.info(f"time: {end - start}")

    assert True


def test_find_region_speed_tree():
    longhurst_definition = "../longhurst.xml"
    provinces = parseLonghurstXML(longhurst_definition)
    provinces_tree, polygons_fids = provinces_make_tree(provinces)
    lmt = 10000
    logging.getLogger("longhurst_province_finder.coord2longhurst").setLevel(
        logging.WARNING
    )

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

    assert True


def test_find_region_speed_tree_single():
    longhurst_definition = "../longhurst.xml"
    provinces = parseLonghurstXML(longhurst_definition)
    provinces_tree, polygons_fids = provinces_make_tree(provinces)
    lmt = 10000
    logging.getLogger("longhurst_province_finder.coord2longhurst").setLevel(
        logging.WARNING
    )

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

    assert True
