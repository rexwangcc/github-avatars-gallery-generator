# -*- coding: utf-8 -*-
"""
This module implements a naive approach to generate a SVG that visualizes
Github contributor gallery. The resulting SVG's layout and interactions are
largely inspired by OpenCollective and the Github's Sponsors page. Since
I haven't found a good open source solution that mimics the aforementioned
layout, i.e. Click-able Cicular Avatarts on a rectangle area, I spent a
night and implemented this module.

Warning:
    1. Due to the limited time I can commit for this module, I did not try using
    SVG or XML libraries to build the SVG, instead, I went with a naive, not-elegant
    yet working string-templating approach to build the SVG, which fullfills my need --
    a CLI that will be run as a Cron Job. So DO NOT deploy it on your server without
    thinking through potential security risks of this approach!
    2. The size of the resulting SVG will grow proportionally to the number of
    contributors, it's on one of my TODOs to compress the size. For now, please
    live with that.

Example:
    To use the module, pass in `organization` and `repo` you want to generate
    the contributor gallery for, and a `contributors_organization_repo_avatar_per_row.svg` will
    be saved to your current working directory, if everything goes well:

        $ python generate_contrib_svg.py --organization taichi-dev --repo taichi

    to check more available arguments, use `--help`.

TODO:
    1. Compress the size of the resulting SVG.
    2. Switch to a more elegant way of generating SVGs, such as using a XML lib.
"""

import argparse
import base64
import io
import sys
from typing import List

import requests
from PIL import Image, ImageChops, ImageDraw
from tenacity import retry, stop_after_attempt
from tqdm import tqdm

ELEMENT_TEMPLATE = """
    <a xlink:href="{html_url}" class="contributor-gallery" target="_blank" rel="nofollow">
        <image x="{x}" y="{y}" width="{avatar_size}" height="{avatar_size}" xlink:href="data:image/png;base64,{avatar_data}" />
    </a>
"""

SVG_TEMPLATE = """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{image_width}" height="{image_height}">
    <style>.contributor-gallery {{ cursor: pointer; }}</style>
    {elements}
</svg>
"""


class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        """Print help message by default."""
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(2)


@retry(stop=stop_after_attempt(3))
def get_all_contributor_avatars_for_repo(organization: str, repo: str) -> List[dict]:
    """Return a list of contributors, sorted on the number of contributions,
    loop over all pages with 100 per page but ignore anonymous users."""
    url = f"https://api.github.com/repos/{organization}/{repo}/contributors"
    headers = {"Accept": "application/vnd.github.v3+json"}
    params = {"per_page": 100}
    response = requests.get(url=url, headers=headers, params=params)
    all_contributors = response.json()
    while "next" in response.links.keys():
        response = requests.get(response.links["next"]["url"], headers=headers, params=params)
        all_contributors.extend(response.json())
    return all_contributors


@retry(stop=stop_after_attempt(3))
def url_to_image(url: str) -> requests.models.Response:
    """Convert (open) a URL of an image to a Response object,
    raise if it failed to get the image. For each image,
    retry up to 3 times."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return response


def bytes_to_base64(data: bytes) -> bytes:
    """Base64 encode a bytes array."""
    return base64.b64encode(data)


def crop_to_circle(im: Image):
    """Crop an image to a crcular one, in-place.

    Reference:
        https://stackoverflow.com/questions/890051/how-do-i-generate-circular-thumbnails-with-pil
    """
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)


def main(arguments=None):
    parser = DefaultHelpParser(
        description="A CLI to generate a gallery visualization of contributors of a Github repo."
    )
    parser.add_argument(
        "-o",
        "--organization",
        help="The Github organization of your repo",
        required=True,
        type=str,
        metavar="\b",
    )
    parser.add_argument(
        "-r", "--repo", help="The Github repository", required=True, type=str, metavar="\b"
    )
    parser.add_argument(
        "-a",
        "--avatar-size",
        dest="avatar_size",
        help="The size of your avatars in the resulting SVG",
        default=48,
        type=int,
        metavar="\b",
    )
    parser.add_argument(
        "-n",
        "--num-per-row",
        dest="num_per_row",
        help="The number of avatars you want to display per row",
        default=10,
        type=int,
        metavar="\b",
    )

    args = parser.parse_args(arguments)

    if not sys.argv[1:]:
        parser.error("No commands or arguments provided!")

    # initialize the avatar position coordinates (x, y), col and row num counter
    x, y, ncol, nrow = 2, 2, 1, 1

    # initialize the elements string
    elements = ""

    # loop over all contributors of the repository
    all_contributors = get_all_contributor_avatars_for_repo(args.organization, args.repo)
    for contributor in tqdm(all_contributors, desc='Gallery generation progress'):
        # grab the avatar and the html url to the contributor
        avatar, html_url = url_to_image(contributor["avatar_url"]), contributor["html_url"]

        # process avatar image with Pillow in-place
        # sadly this in-place operation is holding me back
        # from turning the whole loop to a functional map-ish call
        avatar_img = Image.open(avatar.raw).convert("RGBA")
        crop_to_circle(avatar_img)

        # dump the processed image to bytes array
        img_byte_arr = io.BytesIO()
        avatar_img.save(img_byte_arr, format="PNG")

        # base64 encode the image content
        element = bytes_to_base64(img_byte_arr.getvalue()).decode("utf-8")

        # accumulate to the elements string
        elements += ELEMENT_TEMPLATE.format(
            html_url=html_url, x=x, y=y, avatar_size=args.avatar_size, avatar_data=element
        )

        # keep track of number of avatars per row
        # change line and reset when it reaches the limit
        if ncol >= args.num_per_row:
            nrow += 1
            ncol = 1
            x = 2
            y += args.avatar_size + 2
        else:
            ncol += 1
            x += args.avatar_size + 2

    # compute the size of SVG
    _width = 2 + (args.avatar_size + 2) * args.num_per_row
    _height = 2 + (2 + args.avatar_size) * nrow

    # generate the SVG
    with open(f"contributors_{args.organization}_{args.repo}_{args.num_per_row}.svg", "w") as fp:
        # use the remembered `y` to avoid overflow but fit the height with a border
        fp.write(SVG_TEMPLATE.format(elements=elements, image_width=_width, image_height=_height))


if __name__ == "__main__":
    main()
