Image-Based Lighting (🚧WIP)
====================

````{tab} With webgpu.hpp
*Resulting code:* [`step115`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step115-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115-vanilla)
````

```{figure} /images/autumn_park.webp
:align: center
:class: with-shadow
An environment map is a 360° image in high-dynamic range that we use as an omnidirectional light source.
```

```{figure} /images/ibl-coords.png
:align: center
For each camera ray (i.e., each pixel) we compute the direction reflected by the surface's normal to sample the part of the environment map that contributes the most to the lighting.
```

IBL Sampling
------------

TODO

Add the environment map [`autumn_park_4k.jpg`](../../data/autumn_park_4k.jpg) to the list of loaded textures:

```C++
// [...]
if (!initTexture(RESOURCE_DIR "/autumn_park_4k.jpg")) return false;
```

```{note}
You can find plenty more examples of environment maps on [PolyHaven](https://polyhaven.com/hdris) and [ambientCG](https://ambientcg.com/list?type=HDRI). These are CC0 licensed, allowing you to use them in any context!
```

We test on a simpler model than the boat: [`suzanne.obj`](../../data/suzanne.obj).

### Shader

```rust
@group(0) @binding(5) var<uniform> uLighting: LightingUniforms;
//                 ^ // This was a 6
// [...]
@group(0) @binding(4) var environmentTexture: texture_2d<f32>;

// [...]

// Instead of looping over the light sources, we sample the environment map
// in the reflected direction to get the specular shading.
let ibl_direction = -reflect(V, N);
let Pi = 3.14159265359;

// Convert the direction to spherical coordinates
let theta = acos(ibl_direction.z / length(ibl_direction));
let phi = atan2(ibl_direction.y, ibl_direction.x);

// Map spherical coordinates to (0,1) ranges to fit the UV space
let ibl_uv = vec2<f32>(phi / (2.0 * Pi) + 0.5, theta / Pi);

// Sample the texture
let ibl_sample = textureSample(environmentTexture, textureSampler, ibl_uv).rgb;

var diffuse = vec3<f32>(0.0);
let specular = ibl_sample;

// (remove the for loop that was here)
```

```{figure} /images/envmap-ldr.png
:align: center
:class: with-shadow
TODO
```

IBL Prefiltering
----------------

We can give more roughness to the object by sampling a different MIP level:

```rust
// Sample the texture
let ibl_sample = textureSampleLevel(environmentTexture, textureSampler, ibl_uv, 6.0).rgb;
```

```{figure} /images/envmap-ldr-rough.png
:align: center
:class: with-shadow
TODO
```

In fact, instead of letting the GPU guess which MIP level we want as done for a regular texture, we specify manually the level we want depending on the desired roughness of each surface element.

For instance we can create alternating rough and glossy stripes:

```rust
// Sample the texture
let level = mix(1.0, 6.0, step(fract(20.0 * in.uv.y), 0.5));
let ibl_sample = textureSampleLevel(environmentTexture, textureSampler, ibl_uv, level).rgb;
```

```{figure} /images/envmap-ldr-stripes.png
:align: center
:class: with-shadow
TODO
```

Our approach so far has 3 problems:

 - By manually setting the MIP level, we lose the "smart" choice that the GPU is doing based on screen-space gradients to avoid aliasing. To get both manual control and this behavior, we can use  `textureSampleBias`.

 - The MIP levels are generated as if the texture represented a signal regularly sampled along a grid, but the environment map is sampled along directions, which induces distortion that the mip generation should take into account.

 - To be able to represent at the same time the sun and color details in indirectly lit areas, the environment texture usually uses **high-dynamic range** image formats like .hdr or .exr.

Cube Maps
---------

The computation of the `ibl_uv` coordinates at which we sample the lighting is a bit costly, due to the `acos` and `atan2` operations. A more efficient way to store the environment map is as a **cube map**.

TODO

```{figure} /images/cubemap-conv/folded.svg
:align: center
Cube maps are more efficient to sample and hardware accelerated.
```

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
Images appear upside down because the convention was designed by people who use $Y$ as the vertical axis, and in this guide we use $Z$ as the vertical.
```

Conclusion
----------


````{tab} With webgpu.hpp
*Resulting code:* [`step115`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step115-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115-vanilla)
````
