+++
date = '2026-10-15T17:47:00+08:00'
draft = true
title = 'About ZedPaper'
tags = ['']
ShowToc = true
author = 'Zed Lee'
summary = ''
ShowBreadCrumbs = false
[cover]
image = ''
alt = ''
source = ''

+++

## Basic Styles

This is footnote-ref. [^1] 

### h3

This is `inline code`.

#### h4

This is code block: 

```cpp
int a;
a = 1;
if (a == 8) {
    return -1;
}
```

##### h5

This is link: [Zed's github](https://zdleeeeee.github.io).

## h2

> This is blockqoute.
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

---

$\frac{e^{x_j}}{\sum^k_{i=0}{e^{x_i}}}$


$$
\frac{e^{x_j}}{\sum^k_{i=0}{e^{x_i}}}
$$

## New Components

### message

Use `message` to show a chat bubble. The content between the shortcodes supports Markdown:

```text
{{</* message name="Alice" avatar="/images/alice.png" align="right" nameColor="#e85d75" backgroundColor="#fff0f3" textColor="#333333" */>}}
Hello, **world**!
{{</* /message */>}}
```

All parameters are optional. `name` sets the displayed name, `avatar` sets the image URL, and `align` is `left` by default or `right`. The color parameters default to `var(--secondary)` for `nameColor`, `var(--entry)` for `backgroundColor`, and `var(--content)` for `textColor`.


[^1]: https://zdleeeeee.github.io 