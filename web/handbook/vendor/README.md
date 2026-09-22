# Markdown renderer provenance

The handbook embeds the browser UMD distribution of **marked 18.0.14**, MIT licensed.
Its license is preserved in `marked-LICENSE.txt`. It is a rendering dependency, not a
model, service or agent tool. Pages need no CDN or package installation to read it.

- Package: `marked@18.0.14`, obtained with `npm pack`.
- Registry integrity: `sha512-mBHK6FBHuBAlhgRe88w9F0O1AbwwXJUcQibUbC/QcdTbVGAD7aWza+xt3N6oT/jCZx3/OMeS+8rnuiHZcQ9s7A==`
- Browser asset: package `lib/marked.umd.js`.
- SHA-256: `21568877a938d2c4e7d74e27f18e60da96bb73a68809610ca39216e1efebae62`.

The handbook disables raw HTML execution and unsafe link schemes in its renderer.
Source text, search results, and route errors must not become executable markup.
Update the pinned asset, license, checksum and rendering tests together.
