import logging
import random
import time

from latlon_to_region import (
    find_region,
)

logger = logging.getLogger(__name__)


def test_find_region_single():
    latitude = -68.999
    longitude = -54.44

    region = find_region()(latitude, longitude)

    assert region is not None
    assert "provCode" in region
    assert region["provCode"] == "APLR"


def test_find_region_list():
    latitudes = [-68.999, 64.234]
    longitudes = [-54.44, 23.542]

    regions = find_region()(latitudes, longitudes)

    assert regions is not None
    assert len(regions) == 2
    assert "provCode" in regions[0]
    assert regions[0]["provCode"] == "APLR"
    assert regions[1]["provCode"] == "NECS"


def test_find_region_multiple():
    """Tests that only a single region is found per location (lat/lon)"""
    logging.getLogger("latlon_region").setLevel(logging.WARNING)
    lmt = 10000

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    start = time.time()
    _ = find_region()(
        latitudes,
        longitudes,
    )

    end = time.time()
    logger.info(f"time: {end - start}")


def test_find_region_multiple_indivdually():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("latlon_region").setLevel(logging.WARNING)
    lmt = 10000

    latitudes = [random.randint(-200000, 200000) / 1000 for _ in range(lmt)]
    longitudes = [random.randint(-75000, 75000) / 1000 for _ in range(lmt)]

    func = find_region()
    start = time.time()
    for i in range(lmt):
        _ = func(
            latitudes[i],
            longitudes[i],
        )

    end = time.time()
    logger.info(f"time: {end - start}")
