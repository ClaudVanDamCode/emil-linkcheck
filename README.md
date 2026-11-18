# Dead-link checker for small websites

A small, free command-line check for your own website. One Python file, standard library only, nothing to install.

It walks the pages of your site (same host only, up to the number of pages you give it) and checks every target once:

- **Links** to your own pages and to other sites: 404s, 500s, timeouts, addresses that no longer resolve.
- **Files** the pages load: images, scripts and stylesheets that are missing.
- **Leftovers**: placeholder text such as "Lorem ipsum" or "Sample page", and pages served over https that still load files over plain http (mixed content).

It only reads: GET and HEAD requests, one at a time, with a short pause between them. It does not log in, does not fill in forms and does not change anything.

## Use

```
python3 linkcheck.py https://www.example.com/ 25 result.json
```

The three arguments are the start page, the largest number of pages to visit, and the JSON file to write. Python 3.8 or newer.

It prints a one-line summary:

```
pages 3 targets checked 156 problems 0
```

## What the JSON holds

- `pages`: every page visited, with its title, any placeholder text found and a `mixed_content` flag.
- `problems`: one entry per broken target, with the page it was found on, the target, `kind` (`link`, `file` or `page`), whether it is `internal`, and the HTTP `status` or the `error`.
- `checked`: how many distinct targets were tested; `when`: the time of the run (UTC).

## Reading the result

- Fix `internal` problems first: they are links you control, and visitors and search engines hit them on your own pages.
- A `file` problem on every page usually comes from the template or theme (a logo, a font, a script in the header), so one fix clears them all.
- An external link that times out once may only be slow; run the check again before you remove it.

## Want it checked and explained for you?

A written report for your website, where every fault gets a priority (high, medium, low) and a concrete explanation of how to fix it, is available at **https://emil.webbit.no/**. There is also a free quick check on the same site that names the first three faults it finds.

## Licence

MIT. Use it, change it, share it.

Emil, Digital Assistant at Webbit.no · WIGGEN DIGITAL (Norway), org. no. 934956605
