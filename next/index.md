Learn WebGPU
============

*For native graphics in C++.*

This documentation walks you through the use of the [WebGPU](https://www.w3.org/TR/webgpu) graphics API to create **native 3D applications** in C++ from scratch, for Windows, Linux and macOS.

`````{admonition} Quick Start! (Click Me)
:class: foldable quickstart

*Do you want to understand every bit of GPU code you write?*

````{admonition} Yes, write WebGPU code **from scratch**!
:class: foldable yes

That's great! You can simply proceed to the [introduction](introduction.md) and **read all chapters** sequentially.
````

````{admonition} No, I'd rather **skip the initial boilerplate**.
:class: foldable no

This perfectly makes sense, you can always **come back to the [basic steps](getting-started/index.md) later**.

You probably want to check out the _**Resulting code**_ link at the beginning and end of **each page**, e.g.:

```{image} /images/intro/resulting-code-light.png
:class: only-light with-shadow
```

```{image} /images/intro/resulting-code-dark.png
:class: only-dark with-shadow
```

*Are you ok with using a shallow wrapper for easier reading?*

```{admonition} Yes, I prefer **C++ styled** code.
:class: foldable yes

Use the "**With webgpu.hpp**" tab.
```

```{admonition} No, show me the **raw C WebGPU API**!
:class: foldable no

Use the "**Vanilla webgpu.h**" tab. The *Resulting code* for vanilla WebGPU is less up to date, but this tab also switches **all the code blocks** inside the guide, and these are **up to date**.
```

To **build this base code**, refer to the [Building](getting-started/project-setup.md#building) section of the project setup chapter. You may add `-DWEBGPU_BACKEND=WGPU` (default) or `-DWEBGPU_BACKEND=DAWN` to the `cmake -B build` line to pick respectively [`wgpu-native`](https://github.com/gfx-rs/wgpu-native) or [Dawn](https://dawn.googlesource.com/dawn/) as a backend.

*How far do you want the base code to go?*

```{admonition} A simple triangle
:class: foldable quickstart

Check out the [Hello Triangle](basic-3d-rendering/hello-triangle.md) chapter.
```

```{admonition} A 3D mesh viewer with basic interaction
:class: foldable quickstart

I recommend starting from the end of the [Lighting control](basic-3d-rendering/some-interaction/lighting-control.md) chapter.
```

````

```{admonition} I want things to **run on the Web** as well.
:class: foldable warning

The main body of the guide misses a few extra lines, refer to the [Building for the Web](appendices/building-for-the-web.md) appendix to **adapt the examples** so that they run on the Web!
```

`````

```{admonition}  🚧 Work in progress
This is the "Next" version of the guide, which is not meant to be stable. Chapters are based on an early prerelease of [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution), namely [`v0.3.0-gamma`](https://github.com/eliemichel/WebGPU-distribution/releases/tag/v0.3.0-gamma). They do not always work with wgpu-native, and require to use emdawnwebgpu when building for the web.
```

Contents
--------

```{toctree}
:titlesonly:

introduction
getting-started/index
basic-3d-rendering/index
basic-compute/index
appendices/index
```
