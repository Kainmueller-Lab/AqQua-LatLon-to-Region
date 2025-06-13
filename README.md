# Longhurst-Province-Finder

## Overview

This package is based on Sara Collins' script (https://github.com/thechisholmlab/Longhurst-Province-Finder ), published under the MIT license.

It mainly provide two functions:

- `find_region` that takes as input latitude and longitude coordinates and a definition of Longhurst Provinces returns the Longhurst Province where the coordinate is located.

  - input:
  - latitude: Northerly latitude ranging from -90 to 90
  - longitude: Easterly longitude ranging from -180 to 180
  - `longhurst.xml`: A .gml file that contains the coordinates that bound each province
  - output:
  - `dict` with Longhurst province code, name, bounding box and polygon, where the coordinate can be found. If the coordinate is on land, or otherwise not associated with a province, `None` will be returned.

- `parseLonghurstXML` that parses a xml/gml Longhurst Provinces definition into a dict
  - input:
  - fl: path to definition file
  - output:
  - `dict` containing definitions

## Usage

We recommend using `uv` (https://docs.astral.sh/uv)

To install the dependencies:

```
	uv sync --locked
```

To run it in the command line:

```
	uv run src/coord2longhurst/coord2longhurst.py -l longhurst.xml -lat -68.999 -lon -54.44  -o plot.png
```

To use it in your code:

```
	import coord2longhurst

	[...]

	region = coord2longhurst.find_region(lat, lon, <path/to/longhurst.xml>)
```
