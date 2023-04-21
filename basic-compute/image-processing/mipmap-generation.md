Mipmap Generation (🚧WIP)
=================

*Resulting code:* [`step210`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step210)

A first application that I suggest for our newly learnt compute shaders is the **generation of mipmaps**. In the chapter about [Texture Sampling](http://localhost:8000/basic-3d-rendering/texturing/sampler.html#filtering) we saw that before applying a texture on a 3D mesh, we pre-compute different downsampled versions of it.

```{image} /images/min-pyramid-light.svg
:align: center
:class: only-light
```

```{image} /images/min-pyramid-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>The <strong>MIP pyramid</strong>, as a reminder of the Texture Sampling chapter. Each level contains a filtered and downscaled version of the previous level.</em></span>
</p>

At the time, **we were building the pyramid on the CPU**, prior to uploading the texture data to the GPU texture object. But this problem is actually **a very good fit for compute shaders**!

A very parallel problem
-----------------------

The problem of MIP level generation boils down to the following: given a MIP level $n - 1$, we compute a texel $(i,j)$ of the MIP level $n$ by averaging the for texels from MIP level $n - 1$ with coordinates $(2 i + u,2j + v)$, where $u$ and $v$ span in $\{0,1\}$.

A **good property** of this problem is that processing is **very local**: a given texel of MIP level $n$ only depend on a small fixed number of texels from the previous level $n - 1$, and only contributes to one texel of next level $n + 1$.

There might seem to be two ways of treating this problem as a dispatch of parallel jobs:

 - **Option A** One thread per pixel of level $n$, each texel $(i,j)$ of this level fetches 4 texels from the MIP level $n - 1$ and averages them.

 - **Option B** One thread per pixel of level $n - 1$, each texel $(i',j')$ of this level is divided by $4$ (total number of averaged texels) and accumulated in the texel $(i'/2, j'/2)$ of the MIP level $n$.

Option A has 4 times less threads, but each thread does 4 texture reads instead of 1 for Option B. Both options do 1 write per thread.

```{note}
The limiting factor in the case of such a simple mathematical operation is memory access, we do not really care about the computation of the average itself.
```

**Spiler alert:** Option A is the best one in this case, but we will actually implement both. One reason is that Option B raises a typical case of **race condition**. A second reason is that you should not trust me but rather **benchmark** to check which option is better.

Image Storage
-------------

TODO

We first load an image

```C++
// Methods
void initTextureViews();
void saveOutputImage();
void terminateTextureViews();

// [...]

// Attributes
wgpu::Extent3D m_textureSize;
wgpu::Texture m_texture = nullptr;
wgpu::TextureView m_inputTextureView = nullptr;
wgpu::TextureView m_outputTextureView = nullptr;
```

Add [`stb_image.h`](https://raw.githubusercontent.com/nothings/stb/master/stb_image.h) and [`stb_image_write.h`](https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h) to your source tree.

```C++
// In implementations.cpp

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#define __STDC_LIB_EXT1__
#include "stb_image_write.h"
```

TODO:

 - Remove buffers
 - BindGroup and BindGroupLayout
 - Change shader bindings
 - Be careful about texture usage
 - `save_image.h` helper

Option A
--------

Option B
--------

Benchmarking
------------

*Resulting code:* [`step210`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step210)
