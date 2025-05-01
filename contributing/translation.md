Translation
===========

Adding a new language
---------------------

### Config

Before translating a page, make sure that your target language is listed in `config.py`, in the `translation_languages` entry (around the end):

```python
translation_languages = [
    ("en", "🇺🇸", "English", ""),
    ("fr", "🇫🇷", "Français", "French"),
    ("kr", "🇰🇷", "한국인", "Korean"),
    ("it", "🇮🇹", "Italiano", "Italian"),
]
```

If not, **add a new entry** at the end with:

 - The language's short name, used in URLs (e.g. "fr")
 - The language's [flag emoji](https://emojipedia.org/flags) (e.g., "🇫🇷")
 - The language's name, in its native form (e.g., "Français")
 - The language's name, in English (e.g., "French")

### Files

When adding a new language, create a **subdirectory in `translation`** that has **exactly** the name of the language's short name (e.g., "fr"). Add an `index.md` file that is a translation of the English root `index.md`.

### Table of Content

One last thing to ensure when adding a new language: link it to the **global table of content** in `toc.md`:

````text
```{toctree}
:titlesonly:

index
fr/index
kr/index
it/index
* insert new language here! *

contributing/index
```
````

Translating a page
------------------

### Files

Once your target language exists, translating a page consists in creating a document that has **the very same file name** as the original English page (this may eventually no longer be needed, but stick with the same name for now).

### Admonitions

**Importantly**, insert right after the title the following special directive:

````text
```{translation-warning} Outdated Translation, /introduction.md
This is a **community translation** of [the original English page](%original%), which **has been updated** since it was translated and may thus no longer be in sync. You are welcome to [contribute](%contribute%)!
```
````

This does multiple things:

 - It **instructs the documentation builder** that the page is the translation of `/introduction.md` (although, again, we still rely on the fact that files have the same name in some parts of the code)

 - It displays the message content **only if a commit** in the translated document is more recent than the last commit affecting the translated page. This way, **outdated translations** are easily spotted by readers.

You can also add an extra admonition when even the latest version of the translation is not up to date with the (typically because it is a work in progress):

````text
```{admonition} Incomplete Translation
This is a **community translation** of [the original English page](/introduction.md), which is **not fully translated yet**. You are welcome to [contribute](https://github.com/eliemichel/LearnWebGPU/edit/main/translation/fr/introduction.md)!
```
````

You may **translate these admonitions**, in which case make sure that all pages of the same language use the same translation!

### Content

Then just translate the whole chapter, nothing special here!
