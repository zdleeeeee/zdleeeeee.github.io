+++
date = '2026-09-01T17:47:00+08:00'
draft = true
title = 'About ZedPaper'
tags = ['Front-End']
ShowToc = true
author = 'Zed Lee'
summary = ''
ShowBreadCrumbs = false
[cover]
image = ''
alt = ''
source = ''

+++

ZedPaper is a Hugo blog theme substantially adapted from [PaperMod](https://github.com/adityatelange/hugo-PaperMod) and [Stack](https://demo.stack.cai.im/).

## Authors

Set `author` in a post's front matter to list one or more authors. Each author can have an optional link:

```toml
author = [
  { name = "Zed Lee", url = "/" },
  { name = "Alice", url = "https://example.com/" },
  { name = "Bob" }
]
```

Authors are separated by commas. An author without `url` is shown as plain text. Links open in the current tab. `/` links to the domain's root, and `/about/` links to a path from that root. A relative URL such as `about/` is resolved from the configured `baseURL`, rather than the current article's directory. Author URLs in structured data are converted to absolute URLs.

The existing forms `author = "Zed Lee"` and `author = ["Zed Lee", "Alice"]` remain supported. When a post does not set `author`, the theme uses `params.author` from the site configuration, which accepts the same formats. Set `hideAuthor = true` to hide authors from the visible post metadata.

## Basic Styles

This is a footnote-ref. [^1]

### h3

This is an `inline code block`.

#### h4

This is a code block:

```cpp
int a;
a = 1;
if (a == 8) {
    return -1;
}
```

This is a link: [Zed's github](https://zdleeeeee.github.io).

This is a relative reference: [Posts]({{% relref "/posts/" %}}).

> code: `[Posts]({{%/* relref "/posts/" */%}}`

> This is a blockqoute.
>> aldsjflj
>>

1. aaa
2. bbb
3. ccc

- aaa
- bbb
- ccc
  - aaa

|th|th1|th2|
|:---|:---:|---:|
|tr1|11|12|
|tr2|21|22|

$\frac{e^{x_j}}{\sum^k_{i=0}{e^{x_i}}}$


$$
\frac{e^{x_j}}{\sum^k_{i=0}{e^{x_i}}}
$$

---

## Shortcodes

ZedPaper provides the following ten shortcodes. Each example includes its source and rendered output. The image examples use `profile.jpg` from this post's page bundle; the audio and video examples use remote sample files and require an internet connection to play.

Use the exact shortcode names shown below, including the capital letters in `inTextImg`. These templates use named parameters, except that `ltr` and `rtl` also accept a positional Markdown flag.

### message

Use `message` to show a chat bubble. The content between the shortcodes supports Markdown:

```text
{{</* message name="Zed" avatar="profile.jpg" align="right" nameColor="#884fad" background="#fdd76540" textColor="#333333" */>}}
Hello, I'm **Zed**! And this is an example "message"!
{{</* /message */>}}
```

All parameters are optional. `name` sets the displayed name, `avatar` sets the image URL, and `align="right"` moves the avatar and bubble to the right; the default layout is left-aligned. The color parameters default to `var(--secondary)` for `nameColor`, `var(--entry)` for `background`, and `var(--content)` for `textColor`. The background parameter is named `background`, not `backgroundColor`.

{{< message name="Zed" avatar="profile.jpg" align="right" nameColor="#884fad" background="#fdd76540" textColor="#333333" >}}
Hello, I'm **Zed**! And this is an example "message"!
{{< /message >}}

### collapse

Use `collapse` for expandable content. Supply `summary` for the clickable heading; both the heading and body support Markdown. Set `openByDefault=true` to expand it initially. Use the unquoted boolean `true`, rather than the string `"true"`.

```text
{{</* collapse summary="Click to read **more**" openByDefault=true */>}}
This section is expanded by default.

- Write notes with **Markdown**.
- Click the heading to collapse the section.
{{</* /collapse */>}}
```

{{< collapse summary="Click to read **more**" openByDefault=true >}}
This section is expanded by default.

- Write notes with **Markdown**.
- Click the heading to collapse the section.
{{< /collapse >}}

You can also nest `message` inside `collapse`, for example to group a conversation. Omit `openByDefault` to keep it collapsed initially:

```text
{{</* collapse summary="Show the conversation" */>}}
{{</* message name="Zed" avatar="profile.jpg" */>}}
Messages inside a collapsed section still support **Markdown**.
{{</* /message */>}}
{{</* /collapse */>}}
```

{{< collapse summary="Show the conversation" >}}
{{< message name="Zed" avatar="profile.jpg" >}}
Messages inside a collapsed section still support **Markdown**.
{{< /message >}}
{{< /collapse >}}

### figure

Use `figure` to display an image with an optional title, caption, credit, and link. Set `src` to the image URL and `alt` to its text alternative. `width` and `height` set the image dimensions; `align="center"` centers the figure, and `class` adds a custom CSS class.

```text
{{</* figure src="profile.jpg" alt="Zed's profile picture" width="160" align="center" title="Profile picture" caption="A **figure** with a caption. " attr="Zed Lee" attrlink="https://zdleeeeee.github.io/" link="profile.jpg" target="_blank" rel="noopener noreferrer" */>}}
```

{{< figure src="profile.jpg" alt="Zed's profile picture" width="160" align="center" title="Profile picture" caption="A **figure** with a caption. " attr="Zed Lee" attrlink="https://zdleeeeee.github.io/" link="profile.jpg" target="_blank" rel="noopener noreferrer" >}}

`title` is a visible title below the image, rather than a hover tooltip. `caption` is the image description. `attr` is short for attribution: it credits the image's author or source, and `attrlink` makes that credit a link. Both `caption` and `attr` support Markdown; add a trailing space to `caption` if you want a space before the credit. If `alt` is omitted, the template uses the caption's plain text as the text alternative.

`link` makes the image clickable. Its optional `target` and `rel` parameters control the image link only; they do not apply to `attrlink`.

| Parameter | Meaning |
|---|---|
| `target="_self"` | Opens the link in the current tab. This is also the default when `target` is omitted. |
| `target="_blank"` | Usually opens the link in a new tab, depending on browser settings. |
| `rel="noopener"` | Prevents the newly opened page from accessing the original window through `window.opener`. |
| `rel="noreferrer"` | Omits the `Referer` header, hiding the referring page from the destination; it also implies `noopener`. |

For `target="_self"`, you can normally omit `rel`: no new window is created, so `noopener` is unnecessary. Use `noreferrer` only if you also want to hide the referring page. For `target="_blank"`, `rel="noopener"` explicitly states the window-isolation behavior; add `noreferrer` if you want to hide the referrer as well.

For example, this image opens the original file in the current tab without needing either `target` or `rel`:

```text
{{</* figure src="profile.jpg" alt="Zed's profile picture" width="160" link="profile.jpg" caption="Click to view the original in this tab." */>}}
```

### inTextImg

Use `inTextImg` to insert a small image within a line of text. The image parameter is `url`, rather than `src`. `height` defaults to `15` pixels; `alt` provides a text alternative.

```text
Here is Zed {{</* inTextImg url="profile.jpg" height="24" alt="Zed's avatar" */>}} in the middle of a sentence.
```

Here is Zed {{< inTextImg url="profile.jpg" height="24" alt="Zed's avatar" >}} in the middle of a sentence.

### audio

Use `audio` with a `src` URL to embed the browser's audio player. The template enables playback controls and starts muted, so unmute it when listening. It does not autoplay.

```text
{{</* audio src="https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3" */>}}
```

{{< audio src="https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3" >}}

For a local file, place an audio file such as `sample.mp3` beside this post's `index.md` and use `src="sample.mp3"`. This shortcode only reads `src`; playback attributes are fixed by the template.

### video

Use `video` with a `src` URL to embed the browser's video player. Like `audio`, it includes controls, starts muted, and does not autoplay.

```text
{{</* video src="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4" */>}}
```

{{< video src="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4" >}}

For a local file, place a video such as `sample.mp4` beside this post's `index.md` and use `src="sample.mp4"`. This shortcode only reads `src`; options such as `poster`, `loop`, or `autoplay` would require a template change.

### ltr

Use `ltr` to give a block a left-to-right text direction. Set `md=true` to render the body as Markdown. The positional form `{{</* ltr true */>}}` also enables Markdown.

```text
{{</* ltr md=true */>}}
This paragraph flows **from left to right**.

1. First item
2. Second item
{{</* /ltr */>}}
```

{{< ltr md=true >}}
This paragraph flows **from left to right**.

1. First item
2. Second item
{{< /ltr >}}

Use `md=false` to emit the body without Markdown conversion. The same option is available on `rtl`; explicit unquoted booleans make the intended behavior clear.

### rtl

Use `rtl` for a block of right-to-left text, such as Arabic or Hebrew. Its `md` parameter works the same way as `ltr`.

```text
{{</* rtl md=true */>}}
هذه فقرة باللغة **العربية**.

- العنصر الأول
- العنصر الثاني
{{</* /rtl */>}}
```

{{< rtl md=true >}}
هذه فقرة باللغة **العربية**.

- العنصر الأول
- العنصر الثاني
{{< /rtl >}}

### quote

Use `quote` for a quotation with an optional source. The body and the `source` parameter both support Markdown, so you can write the author, title, and source link together without separate parameters. The source appears below the body in smaller, right-aligned text. Write the body directly; no Markdown `>` prefix is needed.

```text
{{</* quote source="— Zed Lee, [About ZedPaper](/posts/20260901about-zedpaper/)" */>}}
Keep the quotation **simple**.

A quotation can contain more than one paragraph.
{{</* /quote */>}}
```

{{< quote source="— Zed Lee, [About ZedPaper](/posts/20260901about-zedpaper/)" >}}
Keep the quotation **simple**.

A quotation can contain more than one paragraph.
{{< /quote >}}

Omit `source` if no attribution is needed. Punctuation such as the dash is written explicitly in `source`, rather than added automatically.

```text
{{</* quote */>}}
A quotation without a source.
{{</* /quote */>}}
```

{{< quote >}}
A quotation without a source.
{{< /quote >}}

### rawhtml

Use `rawhtml` to insert HTML directly. It takes no parameters and emits its body without Markdown conversion. This also works when Goldmark's `unsafe` HTML rendering is disabled, as in this site's current configuration.

```text
{{</* rawhtml */>}}
<p>A native HTML progress indicator: <progress value="70" max="100">70%</progress> <strong>70%</strong></p>
{{</* /rawhtml */>}}
```

{{< rawhtml >}}
<p>A native HTML progress indicator: <progress value="70" max="100">70%</progress> <strong>70%</strong></p>
{{< /rawhtml >}}


[^1]: https://zdleeeeee.github.io
