Mipmap Generation (🚧WIP)
=================

*Resulting code:* [`step210`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step210)

A first application that I suggest for our newly learnt compute shaders is the **generation of mipmaps**. In the chapter about [Texture Sampling](../../basic-3d-rendering/texturing/sampler.md#filtering) we saw that before applying a texture on a 3D mesh, we pre-compute different downsampled versions of it.

```{image} /images/mipmap-generation/problem-light.png
:align: center
:class: only-light
```

```{image} /images/mipmap-generation/problem-dark.png
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>Comparison of the output MIP level #1 and the input MIP level #0. Each texel of #1 is the average of 4 texels in #0.</em></span>
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

**Spoiler alert:** Option A is the best one in this case, but we will actually implement both. One reason is that Option B raises a typical case of **race condition**. A second reason is that you should not trust me but rather **benchmark** to check which option is better.

Input/Output
------------

Whether we use Option A or B, we first need to load an input texture and save the output to check that the process worked well. For our test, we use **a single texture with 2 MIP levels**: MIP level 0 is the input image, MIP level 1 is the output of the compute shader.

### Loading

As an example, we are going to load the following [`input.jpg`](../../images/mipmap-generation/input.jpg):

```{figure} /images/mipmap-generation/input.jpg
:align: center
:class: with-shadow
Our example input image.
```

Add new init steps and texture-related attributes to the `Application` class:

```C++
// In Application.h
void initTexture();
void terminateTexture();

void initTextureViews();
void terminateTextureViews();

// [...]

wgpu::Extent3D m_textureSize;
wgpu::Texture m_texture = nullptr;
wgpu::TextureView m_inputTextureView = nullptr;
wgpu::TextureView m_outputTextureView = nullptr;
```

The `initTexture()` method starts like [our texture loading procedure](../../basic-3d-rendering/texturing/loading-from-file.md), only we do not include the mipmap generation:

```C++
void Application::initTexture() {
    // Load image data
    int width, height, channels;
    uint8_t* pixelData = stbi_load(RESOURCE_DIR "/input.jpg", &width, &height, &channels, 4 /* force 4 channels */);
    if (nullptr == pixelData) throw std::runtime_error("Could not load input texture!");
    m_textureSize = { (uint32_t)width, (uint32_t)height, 1 };

    // Create texture
    TextureDescriptor textureDesc;
    textureDesc.dimension = TextureDimension::_2D;
    textureDesc.format = TextureFormat::RGBA8Unorm;
    textureDesc.size = m_textureSize;
    textureDesc.sampleCount = 1;
    textureDesc.viewFormatCount = 0;
    textureDesc.viewFormats = nullptr;

    textureDesc.usage = (
        TextureUsage::TextureBinding | // to read the texture in a shader
        TextureUsage::StorageBinding | // to write the texture in a shader
        TextureUsage::CopyDst | // to upload the input data
        TextureUsage::CopySrc   // to save the output data
    );

    // We start with 2 MIP levels:
    //  - level 0 is given by the input.jpg file
    //  - level 1 is filled by the compute shader
    textureDesc.mipLevelCount = 2;

    m_texture = m_device.createTexture(textureDesc);

    // [...] Upload texture data for MIP level 0 to the GPU

    // Free CPU-side data
    stbi_image_free(pixelData);
}
```

````{note}
We use the [`stb_image.h`](https://raw.githubusercontent.com/nothings/stb/master/stb_image.h) file to load the image. DO not forget to include it and add in `implementations.cpp` the following:

```C++
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```
````

Once we have the texture, we only populate the MIP level 0:

```C++
Queue queue = m_device.getQueue();

// Upload texture data for MIP level 0 to the GPU
ImageCopyTexture destination;
destination.texture = m_texture;
destination.origin = { 0, 0, 0 };
destination.aspect = TextureAspect::All;
destination.mipLevel = 0;
TextureDataLayout source;
source.offset = 0;
source.bytesPerRow = 4 * m_textureSize.width;
source.rowsPerImage = m_textureSize.height;
queue.writeTexture(destination, pixelData, (size_t)(4 * width * height), source, m_textureSize);

#if !defined(WEBGPU_BACKEND_WGPU)
    wgpuQueueRelease(queue);
#endif
```

The `initTextureViews()` is pretty straightforward, the only difference between the input and output view is the MIP level:

```C++
void Application::initTextureViews() {
    TextureViewDescriptor textureViewDesc;
    textureViewDesc.aspect = TextureAspect::All;
    textureViewDesc.baseArrayLayer = 0;
    textureViewDesc.arrayLayerCount = 1;
    textureViewDesc.dimension = TextureViewDimension::_2D;
    textureViewDesc.format = TextureFormat::RGBA8Unorm;

    // Each view must correspond to only 1 MIP level at a time
    textureViewDesc.mipLevelCount = 1;

    textureViewDesc.baseMipLevel = 0;
    textureViewDesc.label = "Input View";
    m_inputTextureView = m_texture.createView(textureViewDesc);

    textureViewDesc.baseMipLevel = 1;
    textureViewDesc.label = "Output View";
    m_outputTextureView = m_texture.createView(textureViewDesc);
}
```

### Saving

To save the output image, we use [`stb_image_write.h`](https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h), the companion of `stb_image.h` for writing files, and add to `implementations.cpp` the following:

```C++
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define __STDC_LIB_EXT1__
#include "stb_image_write.h"
```

The high-level process for reading a texture back to the CPU is the following:

 1. Create a GPU buffer with the same byte size as the MIP level you want to save.
 2. Copy the texture to this buffer using `encoder.copyTextureToBuffer(...)`.
 3. Map this buffer like we did with the `mapBuffer` in the previous chapter.
 4. In the map callback, use `stbi_write_png` to write the image to disk.

I leave the details as an exercise, you may simply include this [`save_texture.h `](https://gist.github.com/eliemichel/0a94203fd518c70f3c528f3b2c7f73c8) file into your project, and at the end of `onCompute()`:

```C++
saveTexture(RESOURCE_DIR "/output.png", m_device, m_texture, 1 /* output MIP level */);
```

```{note}
Everything related to the buffers of the previous chapter can be removed.
```

### Bindings

In `initBindGroupLayout` and `initBindGroup`, we replace the buffer bindings with bindings for our texture views.

The layout for **input binding** is similar to texture bindings used in 3D rendering, the only difference being the `visibility`:

```C++
// In initBindGroupLayout():
// Input image: MIP level 0 of the texture
bindings[0].binding = 0;
bindings[0].texture.sampleType = TextureSampleType::Float;
bindings[0].texture.viewDimension = TextureViewDimension::_2D;
bindings[0].visibility = ShaderStage::Compute;
```

Define a corresponding binding in the **shader**:

```rust
@group(0) @binding(0) var previousMipLevel: texture_2d<f32>;
```

The **output binding** is different, because a `texture` binding is always ready-only. What we need here is a **storage texture** binding:

```C++
// In initBindGroupLayout():
// Output image: MIP level 1 of the texture
bindings[1].binding = 1;
bindings[1].storageTexture.access = StorageTextureAccess::WriteOnly;
bindings[1].storageTexture.format = TextureFormat::RGBA8Unorm;
bindings[1].storageTexture.viewDimension = TextureViewDimension::_2D;
bindings[1].visibility = ShaderStage::Compute;
```

This corresponds in the **shader** to the following variable declaration:

```rust
@group(0) @binding(1) var nextMipLevel: texture_storage_2d<rgba8unorm,write>;
```

A texture storage has **more detailed format information** than a texture: the `rgba8unorm` means that the underlying format of the texture is 4 channels of 8 bits, and that we manipulate texels in the shader as "unsigned normalized" values, i.e., floats in range $(0, 1)$.

```{note}
Only the `write` access is allowed for `texture_storage_2d`. Other accesses may be introduced in later versions of WebGPU.
```

In `initBindGroup`, the entries are very simple:

```C++
// Input buffer
entries[0].binding = 0;
entries[0].textureView = m_inputTextureView;

// Output buffer
entries[1].binding = 1;
entries[1].textureView = m_outputTextureView;
```

Great, everything is in place here, we can now focus on the actual compute shader.

Computation
-----------

### Dispatch

I suggest we use a workgroup size of $8 \times 8$: this treats both $X$ and $Y$ axes symmetrically and sums up to 64 threads, which is a reasonable multiple of a typical warp size.

```rust
@workgroup_size(8, 8)
```

We then need to compute the number of workgroup to dispatch. This depends on the expected number of thread, which itself depends on which one of Option A or B we chose:

```C++
uint32_t invocationCountX = /* depends on the option */;
uint32_t invocationCountY = /* depends on the option */;
uint32_t workgroupSizePerDim = 8;
// This ceils invocationCountX / workgroupSizePerDim
uint32_t workgroupCountX = (invocationCountX + workgroupSizePerDim - 1) / workgroupSizePerDim;
uint32_t workgroupCountY = (invocationCountY + workgroupSizePerDim - 1) / workgroupSizePerDim;
computePass.dispatchWorkgroups(workgroupCountX, workgroupCountY, 1);
```

```{note}
The input image I provided above has a size that is a **power of 2**, which always makes things easier as there is no wasted thread.
```

### Option A

This option consists in running **1 thread per texel** of the **output** MIP level.

```C++
uint32_t invocationCountX = m_textureSize.width / 2;
uint32_t invocationCountY = m_textureSize.height / 2;
```

For each texel, we use `textureLoad` 4 times to average corresponding texels from the previous MIP level, then `textureStore` to write in the new MIP level:

```rust
@compute @workgroup_size(8, 8)
fn computeMipMap_OptionA(@builtin(global_invocation_id) id: vec3<u32>) {
    let offset = vec2<u32>(0, 1);
    let color = (
        textureLoad(previousMipLevel, 2 * id.xy + offset.xx, 0) +
        textureLoad(previousMipLevel, 2 * id.xy + offset.xy, 0) +
        textureLoad(previousMipLevel, 2 * id.xy + offset.yx, 0) +
        textureLoad(previousMipLevel, 2 * id.xy + offset.yy, 0)
    ) * 0.25;
    textureStore(nextMipLevel, id.xy, color);
}
```

```{important}
The last argument of `textureLoad` is a MIP level **relative to the texture view** that we bound. So in both cases here we look at the first (and only) MIP level available in the view.
```

And this is it! Most of the work was about binding inputs/outputs, the compute shader itself is very simple.

We can inspect the result to check that it matches a [reference](../../images/mipmap-generation/reference.png), downsampled with a regular image editing tool like GIMP or Photoshop:

```{image} /images/mipmap-generation/compare-light.png
:align: center
:class: only-light
```

```{image} /images/mipmap-generation/compare-dark.png
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>Comparison of the output MIP level #1 with a reference. The error map is all black, meaning that this is a perfect match.</em></span>
</p>

### Option B

Let us move on to Option B, which introduces **various problems** we can have when not making a wrong choice about how to organize threads.

```{note}
In the accompanying code, I added in `Application.cpp` a `#define MIPMAP_GEN_OPTION` that is either `A` or `B`. This is a quick but dirty way of adding a parameter to a program, as requires to recompile when switching.
```

This option consists in running **1 thread per texel** of the **input** MIP level.

```C++
uint32_t invocationCountX = m_textureSize.width;
uint32_t invocationCountY = m_textureSize.height;
```

For each texel of the previous MIP level, we accumulate it in the new MIP level:

```rust
@compute @workgroup_size(8, 8)
fn computeMipMap_OptionB(@builtin(global_invocation_id) id: vec3<u32>) {
    let prevCoord = id.xy;
    let nextCoord = id.xy / 2;

    // The value we add to the average
    let prevTexel = textureLoad(previousMipLevel, prevCoord, 0);

    // We load, modify then store the next MIP level to accumulate the average
    var nextTexel = textureLoad(nextMipLevel, nextCoord, 0);
    nextTexel += prevTexel * 0.25;
    textureStore(nextMipLevel, nextCoord, nextTexel);
}
```

This **will not work** as is, because `nextMipLevel` can only be used for **writing**, not for `textureLoad`. We must add an extra binding:

```C++
// In initBindGroupLayout():
#if MIPMAP_GEN_OPTION == B
    bindings.resize(3);
    // Extra binding to access the output in read mode
    bindings[2].binding = 2;
    bindings[2].texture.sampleType = TextureSampleType::Float;
    bindings[2].texture.viewDimension = TextureViewDimension::_2D;
    bindings[2].visibility = ShaderStage::Compute;
#endif

// In initBindGroup():
#if MIPMAP_GEN_OPTION == B
    entries.resize(3);
    entries[2].binding = 2;
    entries[2].textureView = m_outputTextureView;
#endif
```

And we use this new binding in the shader when trying to access the intermediary value of the next MIP level:

```rust
@group(0) @binding(2) var nextMipLevel_readonly: texture_2d<f32>;

// [...]

// Use this read-only binding when reading the already accumulated value:
var nextTexel = textureLoad(nextMipLevel_readonly, nextCoord, 0);
```

Benchmarking
------------

*Resulting code:* [`step210`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step210)
