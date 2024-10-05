Cube Maps (<span class="bullet">🟠</span>WIP)
=========

````{tab} With webgpu.hpp
*Resulting code:* [`step117`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step117)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step117-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step117-vanilla)
````

The computation of the `ibl_uv` coordinates at which we sampled the environment lighting in the previous chapter is a bit costly, due to the `acos` and `atan2` operations. A more efficient way to store the environment map is as a **cube map**.

TODO

```{figure} /images/cubemap-conv/folded.svg
:align: center
Cube maps are more efficient to sample and hardware accelerated.
```

Multi-layer textures
--------------------

We will see in the [Cubemap Conversion](../../basic-compute/image-processing/cubemap-conversion.md) chapter how to convert an equirectangular environment map into a cubemap and vice versa.

All we need to know for now is that **a cubemap is a special type of texture**. It is stored as a **2D array texture** with **6 layers**, which means that when creating the texture, with specify a dimension of `2D` but the `size` has 3 dimensions:

```C++
TextureDescriptor textureDesc;
textureDesc.dimension = TextureDimension::_2D;
textureDesc.size = { size, size, 6 };
// [...]
```

**By convention**, the face of the cube are stored in the following **order**:

| Layer | Cube Map Face |  S   |  T   |
| :---: | :-----------: | :--: | :--: |
|   0   | `Positive X`  | `-Z` | `-Y` |
|   1   | `Negative X`  | `+Z` | `-Y` |
|   2   | `Positive Y`  | `+X` | `+Z` |
|   3   | `Negative Y`  | `+X` | `-Z` |
|   4   | `Positive Z`  | `+X` | `-Y` |
|   5   | `Negative Z`  | `-X` | `-Y` |

As you can see, the convention also specifies the world-space direction to which the local texture axes `S` and `T` correspond.

```{image} /images/cubemap-conv/stacked-light.svg
:align: center
:class: only-light
```

```{image} /images/cubemap-conv/stacked-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>CubeMaps are represented as 2D array textures.</em></span>
</p>

In practice, we **load the faces one by one**, from individual files. The computations of **MIP levels** is also done face by face. The texture sampler will take care of mixing faces together appropriately.

```C++
Extent3D singleLayerSize = { size, size, 1 };
for (uint32_t layer = 0; layer < 6; ++layer) {
    destination.origin = { 0, 0, layer };
    m_queue.writeTexture(destination, pixelData[layer], (size_t)(4 * size * size), source, singleLayerSize);
}
```

```{image} /images/cubemap-conv/faces-light.svg
:align: center
:class: only-light
```

```{image} /images/cubemap-conv/faces-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>Each face of a cube map is loaded from a different image file.</em></span>
</p>

```{note}
Images appear upside down because the convention was designed by people who use $Y$ as the vertical axis, and in this guide we use $Z$ as the vertical. Anyways even when using $Y$-up it is better to stick to the convention table above than to try to intuitively guess the correct S and T texture axes.
```

TODO

Implementation
--------------

TODO

Unzip [`autumn_park_4k.zip`](../../data/autumn_park_4k.zip) in your `resource` directory.

```C++
// In Application.h
bool initTexture(const std::filesystem::path& path, bool isCubemap = false);

// In onInit()
if (!initTexture(RESOURCE_DIR "/autumn_park_4k"), true /* isCubemap */) return false;

// In Application.cpp
bool Application::initTexture(const std::filesystem::path& path, bool isCubemap) {
    TextureView textureView = nullptr;
    Texture texture =
        isCubemap
        ? ResourceManager::loadCubemapTexture(path, m_device, &textureView)
        : ResourceManager::loadTexture(path, m_device, &textureView);

    // [...]

    bindingLayout.texture.viewDimension =
        isCubemap
        ? TextureViewDimension::Cube
        : TextureViewDimension::_2D;

    // [...]
}
```

```C++
// In ResourceManager.h
static wgpu::Texture loadCubemapTexture(const path& path, wgpu::Device device, wgpu::TextureView* pTextureView = nullptr);

// In ResourceManager.cpp
Texture ResourceManager::loadCubemapTexture(const path& path, Device device, TextureView* pTextureView) {
    const char* cubemapPaths[] = {
        "cubemap-posX.png",
        "cubemap-negX.png",
        "cubemap-posY.png",
        "cubemap-negY.png",
        "cubemap-posZ.png",
        "cubemap-negZ.png",
    };

    // Load image data for each of the 6 layers
    Extent3D cubemapSize = { 0, 0, 6 };
    std::array<uint8_t*, 6> pixelData;
    for (uint32_t layer = 0; layer < 6; ++layer) {
        int width, height, channels;
        auto p = path / cubemapPaths[layer];
        pixelData[layer] = stbi_load(p.string().c_str(), &width, &height, &channels, 4 /* force 4 channels */);
        if (nullptr == pixelData[layer]) throw std::runtime_error("Could not load input texture!");
        if (layer == 0) {
            cubemapSize.width = (uint32_t)width;
            cubemapSize.height = (uint32_t)height;
        }
        else {
            if (cubemapSize.width != (uint32_t)width || cubemapSize.height != (uint32_t)height)
                throw std::runtime_error("All cubemap faces must have the same size!");
        }
    }

    // [...]
    textureDesc.size = cubemapSize;

    // [...]
    Extent3D cubemapLayerSize = { cubemapSize.width , cubemapSize.height , 1 };
    for (uint32_t layer = 0; layer < 6; ++layer) {
        Extent3D origin = { 0, 0, layer };

        writeMipMaps(device, texture, cubemapLayerSize, textureDesc.mipLevelCount, pixelData[layer], origin);

        // Free CPU-side data
        stbi_image_free(pixelData[layer]);
    }

    // [...]
    textureViewDesc.arrayLayerCount = 6;
    //                                ^ This was 1
    textureViewDesc.dimension = TextureViewDimension::Cube;
    //                                                ^ This was 2D
```

Note that we also add a new extra argument to `writeMipMaps` to specify which layer to upload to:

```C++
template<typename component_t>
static void writeMipMaps(
    /* [...] */
    Origin3D origin = { 0, 0, 0 }
) {
    // [...]
    destination.origin = origin;
    // ^                 ^ This was { 0, 0, 0 }
```

```rust
// In shader
@group(0) @binding(4) var cubemapTexture: texture_cube<f32>;

// [...]

let ibl_sample = textureSample(cubemapTexture, textureSampler, ibl_direction).rgb;
//                                                             ^ This was ibl_uv
```

TODO

Conclusion
----------


````{tab} With webgpu.hpp
*Resulting code:* [`step117`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step117)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step117-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step117-vanilla)
````
