# AqQua LatLon-to-Region Converter

## Overview

This package is based on Sara Collins' script (https://github.com/thechisholmlab/Longhurst-Province-Finder ),
published under the MIT license.

It mainly provide three functions:

- `find_region` that takes as input latitude and longitude coordinates and a definition of
  Longhurst Provinces returns the Longhurst Province where the coordinate is located.

  - input:
    - latitude: Northerly latitude ranging from -90 to 90
    - longitude: Easterly longitude ranging from -180 to 180
    - `longhurst.xml`: A .gml file that contains the coordinates that bound each province
    - use-tree: flag to switch to tree-based matching mode
    - out-file: plot map of regions and locations
  - output:
    - `dict` with Longhurst province code, name, bounding box and polygon, where the
      coordinate can be found. If the coordinate is on land, or otherwise not associated
      with a province, `None` will be returned.

- `parseLonghurstXML` that parses a xml/gml Longhurst Provinces definition into a dict

  - input:
    - fl: path to definition file
  - output:
    - `dict` containing definitions

- ` provinces_make_tree` that takes a `dict` of Longhurst definitions and creates a
  `shapely.STRtree` of their polygons
  - input:
    - provinces: `dict` containing Longhurst definitions (as returned by `parseLonghurstXML`
  - output:
    - `shapely.STRtree` of the provinces polygons

## Usage

We recommend using `uv` (https://docs.astral.sh/uv)

To install the dependencies:

```
	uv sync --locked
```

To run it in the command line:

```
	uv run scripts/find_region -lat -68.999 -lon -54.44  -o plot.png
```

To use it in your code:

```
	import latlon_to_region

	[...]

	region = latlon_to_region.find_region(lat, lon, <path/to/longhurst.xml>)
```

## List of Provinces

### List of Provinces in xml file:

```
[
	'ALSK', 'ANTA', 'APLR', 'ARAB', 'ARCH', 'ARCT', 'AUSE', 'AUSW', 'BENG',
	'BERS', 'BPLR', 'BRAZ', 'CAMR', 'CARB', 'CCAL', 'CHIN', 'CNRY', 'EAFR',
	'ETRA', 'FKLD', 'GFST', 'GUIA', 'GUIN', 'INDE', 'INDW', 'ISSG', 'KURO',
	'MEDI', 'MONS', 'NADR', 'NASE', 'NASW', 'NATR', 'NECS', 'NEWZ', 'NPPF',
	'NPSW', 'NPTG', 'NWCS', 'PEQD', 'PNEC', 'PSAE', 'PSAW', 'REDS', 'SANT',
	'SARC', 'SATL', 'SPSG', 'SSTC', 'SUND', 'TASM', 'WARM', 'WTRA'
]
	+ ['CHIL']
```

### List of Provinces in [doi.org/10.1002/gbc.20089](Dynamic biogeochemical provinces in the global ocean)

```
[
	'ALSK', 'ANTA', 'APLR', 'ARAB', 'ARCH', 'ARCT', 'AUSE', 'AUSW', 'BENG',
	'BERS', 'BPLR', 'BRAZ', 'CAMR', 'CARB', 'CCAL', 'CHIN', 'CNRY', 'EAFR',
	'ETRA', 'FKLD', 'GFST', 'GUIA', 'GUIN', 'INDE', 'INDW', 'ISSG', 'KURO',
	'MEDI', 'MONS', 'NADR', 'NASE', 'NASW', 'NATR', 'NECS', 'NEWZ', 'NPPF',
	'NPSW', 'NPTG', 'NWCS', 'PEQD', 'PNEC', 'PSAE', 'PSAW', 'REDS', 'SANT',
	'SARC', 'SATL', 'SPSG', 'SSTC', 'SUND', 'TASM', 'WARM', 'WTRA'
]
	+ ['C(O)CAL', 'HUMB', 'NPSE']
```

### Notes

- `HUMB` seems to be the same as `CHIL` (west coast South America)
- `NPSE` (Northeast Pacific subtropical) is not contained in xml file (but I also could not
  figure out exactly where it is, somewhere South of Japan maybe)
- `C(O)CAL` (California current) is not contained in xml file (non-coastal California)
