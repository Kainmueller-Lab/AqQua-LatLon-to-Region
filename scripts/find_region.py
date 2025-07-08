import argparse
import logging

logger = logging.getLogger(__name__)

from latlon_to_region import find_region


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-lon",
        "--longitude",
        type=float,
        required=True,
        help="longitude coordinate of the query location",
    )
    parser.add_argument(
        "-lat",
        "--latitude",
        type=float,
        required=True,
        help="latitude coordinate of the query location",
    )
    parser.add_argument(
        "-o",
        "--out-file",
        type=str,
        default=None,
        help="output location of plot",
    )
    parser.add_argument("-t", "--use-tree", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logging.getLogger("matplotlib").setLevel(logging.INFO)

    _ = find_region(
        args.latitude,
        args.longitude,
        longhurst_definition=None,
        plot_file=args.out_file,
        provinces_tree=args.use_tree,
    )


if __name__ == "__main__":
    main()
