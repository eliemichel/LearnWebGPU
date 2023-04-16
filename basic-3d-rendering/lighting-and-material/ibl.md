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

(TODO: Use cubemap instead of envmap?)

```{figure} /images/ibl-coords.png
:align: center
:class: with-shadow
TODO
```

IBL Sampling
------------

TODO

Add the environment map [`autumn_park_4k.jpg`](../../data/autumn_park_4k.jpg) to the list of loaded textures:

```C++
// [...]
if (!initTexture(RESOURCE_DIR "/autumn_park_4k.jpg")) return false;
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

Conclusion
----------

You can find plenty more environment maps on [PolyHaven](https://polyhaven.com/hdris) and [ambientCG](https://ambientcg.com/list?type=HDRI).

````{tab} With webgpu.hpp
*Resulting code:* [`step115`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step115-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step115-vanilla)
````
