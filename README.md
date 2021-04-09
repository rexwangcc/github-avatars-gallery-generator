# github-avatars-gallery-generator

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)]()
[![PyPI](https://img.shields.io/pypi/v/github-avatars-gallery-generator?style=flat-square)](https://pypi.org/project/github-avatars-gallery-generator/)

A naive implementation that collects the avatars of all contributors of a Github repo and makes a gallery SVG for you.

## Install

```
pip install github-avatars-gallery-generator
```

## Why?

The layout is inspired by [Open Collective](https://opencollective.com) 's ability to display contributors as well as Github's own sponsors page.

Recently I need to generate such SVGs for some of my projects, which are not on Open Collective, so I spent some time writing this generator for my own requirements. It's an _ugly_ solution and has certain known issues (slow, large SVG size, etc.), yet works for my needs.

## How?

Using `vuepress` project as an example, either download the `main.py` or install it from PyPI, and run something like:

```
gh-gallery --organization vuejs --repo vuepress
```

after a couple seconds, it will generate an SVG file "contributors_vuejs_vuepress_10.svg" to the current directory. The `10` there means it will put 10 avatars
per row in the resulting SVG. For all available options, use `gh-gallery -h`:

```
A CLI to generate a gallery visualization of contributors of a Github repo.

optional arguments:
  -h, --help            show this help message and exit
  -o ORGANIZATION, --organization ORGANIZATION
                        The Github organization of your repo
  -r REPO, --repo REPO  The Github repository
  -a AVATAR_SIZE, --avatar-size AVATAR_SIZE
                        The size of your avatars in the resulting SVG
  -n NUM_PER_ROW, --num-per-row NUM_PER_ROW
                        The number of avatars you want to display per row
```

### Comparison

With `gh-gallery --organization vuejs --repo vuepress -n 34 -a 24`, I'm
 able to generate a contributors gallery of `vuepress` repo,
I already converted the resulting SVG into PNG using `cairosvg`, here is how it looks:

![](./misc/contributors_vuejs_vuepress_34.png)

You could compare it with their [official one](https://github.com/vuejs/vuepress#code-contributors)

## By the way...

A few things to keep in mind:

1. the resulting SVG may be **very large** and unsuitable
to be stored/shared online, due to the fact this library stores all image contents in the SVG. To resolve it,
you can use libraries such as [`cairosvg`](https://cairosvg.org/documentation/) to convert your SVG into PNG or JPEG files.
2. The avatars in the gallery are sorted by contributions at the time
the library is querying Github API.
3. The generated avatars are clickable and links to each contributor's Github
profile page. However, once you convert it into PNG or JPEG, the links
will get lost.

Thank you and feel free to submit an issue if you find any. Also welcome to submit a PR to improve it.
