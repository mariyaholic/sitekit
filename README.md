Made by Maria

# sitekit

Hello! sitekit is my little catalog-driven static-page generator with a browser audit gate. I feed it a room-style catalog and it renders a static page and Markdown. Then it checks the built page in a real browser against the same catalog, so the page and its checks always agree. I kept the scope deliberately narrow, and I like it that way. I hope you find it handy too.

It is free and open source (Apache-2.0). See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Try it

You need [Node.js](https://nodejs.org) 22 or newer. The browser audit is optional and needs Python 3.13 or newer.

```bash
node build.mjs                 # writes dist/ from the example catalog
```

Open the built page in `dist/` and poke around. When I change a catalog entry, I run `node build.mjs --check`. It names the stale generated files and writes nothing.

Want the audit too? It runs the page in a real browser (Edge, Chrome or Playwright's bundled Chromium) and writes `audit-report.json`. The setup and commands are in [Sitekit's guide](https://mariyaholic.github.io/docs/sitekit/) on my site.

Everything stays on your machine: the builder never touches the network, and the audit talks only to a local browser on your own loopback address. I like that part a lot.

## Everything else

The fine detail lives in [Sitekit's guide](https://mariyaholic.github.io/docs/sitekit/) on my site:

- [Build the page and check it](https://mariyaholic.github.io/docs/sitekit/#build)
- [Commands and exit codes](https://mariyaholic.github.io/docs/sitekit/#commands)
- [Audit configuration](https://mariyaholic.github.io/docs/sitekit/#config)
- [The catalog contract](https://mariyaholic.github.io/docs/sitekit/#contract)
- [Project layout](https://mariyaholic.github.io/docs/sitekit/#layout)
- [Privacy and network use](https://mariyaholic.github.io/docs/sitekit/#privacy)
- [Status, trademarks and limits](https://mariyaholic.github.io/docs/sitekit/#limits)
- [The supported catalog, markup and CLI contract](https://github.com/mariyaholic/sitekit/blob/main/docs/CONTRACT.md) in the repository

Not affiliated with MetaQuotes; MetaTrader 5 (MT5) is a MetaQuotes trademark, and sitekit contains no MT5 integration.

Thank you for reading. ♡
