# AqQua LatLon-to-Region Converter

## Overview

This package is based on Sara Collins' script (https://github.com/thechisholmlab/Longhurst-Province-Finder ),
published under the MIT license.

It mainly provides one function, `find_region`:  
`find_region` is implemented as a closure.
The outer function creates the necessary data structures for fast region computation.
An alternative province definition file can be supplied to the outer function, if none is supplied an internal definition is used.
The inner function takes as input latitude and longitude coordinates (a single coordinate or a list of coordinates and returns the region (e.g., the Longhurst Province) where each coordinate is located.

- input:
  - latitude: Northerly latitude ranging from -90 to 90
  - longitude: Easterly longitude ranging from -180 to 180
  - out-file: plot map of regions and locations, `None` by default, if set a map
    of provinces and query coordinates is plotted to this file
- output:
  - `dict` with Longhurst province code, name, bounding box and polygon, where the
    coordinate can be found. If the coordinate is on land, or otherwise not associated
    with a province, `None` will be returned. If multiple coordinates are inquired
    a list of `dict` is returned.

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

	find_region_func = latlon_to_region.find_region()
	region = find_region_func(lat, lon)
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
