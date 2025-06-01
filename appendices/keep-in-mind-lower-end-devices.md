Keep in mind lower-end devices <span class="bullet">🟢</span>
==============================

It can be **very tempting** to discard older devices or mobile devices when developing a GPU-based application. **But please don't**.

The problem
-----------

**Why is it tempting?** As a developer, **we usually work on a device that is higher end** than what the average user has (and the *average* is not even a good target)! This induces certain consequences:

1. We sometimes **do not even realize** that our code requires a good GPU because, well, "it works on my machine".

2. And some other time, we are well aware that **we assume** that the user device has this or that property. Otherwise it would require **additional care**... and again, "it works on my machine" so why bother, I'm in a hurry.

**Why is this an issue?** Developing for high-end devices only has **very diverse and unfortunate consequences** to keep in mind:

1. **Social accessibility.** Not everybody can afford your higher end device, either because of its pecuniary cost or because of incompatibilities with their lifestyle. Especially if it is **not their work tool**. Ignoring this may increase social exclusion.

2. **Environmental impacts.** This one is **twofold**. First, if we only develop tools for higher-end devices, we are effectively **forcing everybody to upgrade their hardware**. User computing devices (workstations, laptops, phones, tablets, etc.) are already **renewed at a rate that is far from sustainable**, so please don't participate in this. Second, writing better code (i.e., that runs on lower end devices) usually has the nice byproduct of **drawing less power** even on higher end devices.

3. **Economic issues.** Ignoring a significant portion of the existing user devices is usually bad for business. Some potential users/clients are completely excluded, and some other may experience **frustrating lags or failures**. If we step back, software-based obsolescence of perfectly working hardware also causes **macroeconomic issues** since we collectively destroy existing value.

I let you order these issues however you'd like, but at least don't overlook them.

```{tip}
Smartphones are **by far** the most common type of user computing device. Especially in developing countries.
```

> 🤔 Oh but I am doing research, or my app will only get out years from now, so I develop it for future devices.

This is arguably a **"chicken and egg" problem**: the **hardware renewal rate** is not just something you **assume**, it is also something you **trigger** (at least you participate in it) by only targeting new stuff. I guess if all you care about is the direct economic consequences to yourself, then that's fine, but if you're at least slightly concerned by one of the other points, think about it.

If what you write is a **research prototype** rather than an application targeting end users, **this still matters**. Don't underestimate your impact: uncertainty has a cost, so if your research was only tested on top-tier hardware, engineers who eventually **transfer your research** into end products may decide not to **risk** generalizing it to a wider range of devices. In other terms, **showing that a method works on the existing park of devices "as is" is a contribution**.

```{seealso}
For an upcoming talk at SIGGRAPH 2025, we recently surveyed 888 research papers to gathered the devices that authors work with. Turns out that **87% of GPUs reported in research papers** are available to **less than 20% of the consumer-level user base** at publication time. More information here: [https://eliemichel.github.io/sustainable-gpu-usage](https://eliemichel.github.io/sustainable-gpu-usage)
```

Suggested solutions
-------------------

Okey so what do we do in practice?

### Write portable code

You probably already care about this if you have decided to use **WebGPU** rather than an OS or vendor-specific graphics API. What this article is about is to **push the definition of portability a little further**: it's one thing to support some systems of each OS/vendor, it's another to support as many as possible.

It's a question of mindset before anything else: always **consider who you might be abandoning by the roadside** when assuming something about the user device.

I know, writing portable code and writing code that makes better use of the hardware is **sort of contradictory** because one cannot optimize for a specific device then. The thing is, the impacts of hardware renewal is generally **more significant** than the impacts of portability overheads.

Of course, if you have time nothing prevents from also optimizing for the most common devices, but only after making sure you do not disregard anybody's device.

### Do the most out of the default limits

The WebGPU specification defines [default limits](https://www.w3.org/TR/webgpu/#limit-default), which are **designed to be widely available**. Said differently, if you start requiring non-default limits, you are restraining the access to your application.

When requesting the WebGPU device from the WebGPU adapter (see chapters [*The Adapter*](../getting-started/adapter-and-device/the-adapter.md) and [*The Device*](../getting-started/adapter-and-device/the-device.md)), **do not blindly request the maximum supported limits**. Just because the adapter tells you "I can support 16K textures" does not mean you should use more than the default limit of 8K unless you have a good reason to.

My advice would then be **do as much as possible to fit within the default limits**, and whenever you'd really like to ask for more, consider **providing a fallback** for people who do not support it.

For the record, let me mention some if these limits (again, full list is [in the spec](https://www.w3.org/TR/webgpu/#limit-default)):

- `maxTextureDimension2D`: **8192**
- `maxTextureDimension3D`: **2048** (and you probably don't want to reach a $2048^3$ texture, that'd be 32GB per 32bit channel)
- `maxSampledTexturesPerShaderStage`: **16** (maybe you want a texture array if you need to go further?)
- `maxStorageBuffersPerShaderStage`: **8** (maybe you could split your pass, or regroup some buffers?)
- `maxBufferSize`: **256 MiB** (that's quite a lot already, make sure the device actually has that much memory left)
- ...

### Provide a fallback path

Or maybe the higher-end path should be treated as the nice-to-have exception, rather than looking at the default as the painful exception.

Let me reuse this figure from chapter [*The Adapter*](../getting-started/adapter-and-device/the-adapter.md):

```{themed-figure} /images/the-adapter/limit-tiers_{theme}.svg
:align: center
In an advanced use of the adapter/device duality, we can set up multiple limit presets and select one depending on the adapter.
```

The "low quality tier" here should correspond at most to the **default limits and features**, so that there is at least a valid code path. In fact, there is even the possibility to get a **compatibility adapter** for devices that don't support the standard default limits.

You can have as many quality tiers as you want. What matters is that if you disable a feature of your application, it is really because the device cannot support it, and not just because you did not have time to treat that case: **treat the default case first**.

```{note}
Dawn unofficially defines several quality tiers that we can find in [`src/dawn/native/Limits.cpp`](https://github.com/google/dawn/blob/main/src/dawn/native/Limits.cpp).
```

### Test on older devices

It may sound obvious, but we probably do not do it enough. Yet, this is the best way to **effectively check** that our program is indeed **portable**. Maybe you have an old computer gathering dust in your basement, or maybe you can borrow one.

Then, importantly, **report that it works**! For instance, if you are writing an academic paper, it typically includes something like "*we tested our method on a XXXX GPU*": ideally you should let know the lowest end device you could successfully test with, to **help the reader better scope the portability of your method**.

And what about **developing from the lower end device**? A bit more drastic, I admit, but there is value in not upgrading your own workstation too often, so that you do **not as easily inadvertently waste resources**!

### Spread the word

As we've noticed, this is a typical instance of the "chicken and egg" problem. The more developers believe in the idea that users will renew their hardware, the more it becomes a fact, with all the unfortunate consequences mentioned earlier.

So, discuss this at the **cafeteria**, in **meetings**, etc. Bring it to the table as an argument to make **better software**, software that **makes better use of the existing hardware**.

Afterword
---------

### Statistics

It is **not easy** to find accurate data about **the usage rate of a GPU**, i.e., the amount of users that have it at home (or in their pocket). In fact, **the only such public database** that I am aware of is the [Steam's monthly Hardware Survey](https://store.steampowered.com/hwsurvey/). This is incredibly valuable (thanks for sharing Steam), but is however **quite biased** since Steam users are more desktop PC gamers than the average Internet user.

```{note}
🙏 If you ever find public data about the distribution of GPU models among end users, I am very interested, please share!
```

We can however find rather detailed information about the **devices capabilities** thanks to some insightful reports. Specialized hardware websites sometimes share detail reviews and databases, like the [benchmarks](https://www.notebookcheck.net/Benchmarks-Tech.123.0.html) from NotebookCheck or the [GPU Specs Database](https://www.techpowerup.com/gpu-specs) from TechPowerUp.

If you are interested in a **ranking** of GPUs for the task of path tracing, [Blender Open Data](https://opendata.blender.org/) benefits from a very active community. Another very valuable source of information about the specificities of many devices is [GPUinfo](https://gpuinfo.org/), which also relies on **crowd-sourced** reports.

### Feedback

I am well aware that this appendix is **a bit more opinionated** than the rest of the guide. If you would like to discuss this further, I warmly invite you to join [the Discord server](https://discord.gg/2Tar4Kt564)!
