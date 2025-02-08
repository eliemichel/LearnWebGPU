Cubemap Conversion (<span class="bullet">🟠</span>WIP)
==================

*Resulting code:* [`step220`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step220)

Problem
-------

Remember the cube maps from the [Image-Based Lighting](../../basic-3d-rendering/lighting-and-material/ibl.md) chapter? We can actually build them from the equirectangular environment maps found for instance on [PolyHaven](https://polyhaven.com/hdris) or [ambientCG](https://ambientcg.com/list?type=HDRI).

**Input:**

```{figure} /images/autumn_park.webp
:align: center
:class: with-shadow
An environment map is a 360° image in high-dynamic range that we use as an omnidirectional light source.
```

**Parameterization:**

```{figure} /images/ibl-coords.png
:align: center
The equirectangular map is parameterized with a latitude and longitude graduation, like the Earth.
```

**Output:**

```{figure} /images/cubemap-conv/cubemap.svg
:align: center
A cubemap is made of 6 squared textures, or rather 1 texture with 6 layers. Each layer corresponds to one face of a cube that wraps the scene.
```

Since it is easier to find equirectangular images, but a cubemap is faster to query (because it is accelerated by the hardware), our goal is to convert an equirectangular image to a cubemap.

Implementation
--------------

TODO

```C++
// The output is a square texture with 6 layers, one per face of the cube
textureDesc.size = { (uint32_t)height, (uint32_t)height, 6 };
m_outputTexture = m_device.createTexture(textureDesc);
```

```C++
// We create 1 view per face of the cube (i.e., per layer of the output texture)
// NB: This is only used when drawing the GUI
std::array<wgpu::TextureView, 6> m_outputTextureLayers = {nullptr, nullptr, nullptr, nullptr, nullptr, nullptr};
```

```C++
const char* outputLabels[] = {
	"Output Positive X",
	"Output Negative X",
	"Output Positive Y",
	"Output Negative Y",
	"Output Positive Z",
	"Output Negative Z",
};

for (uint32_t i = 0; i < 6; ++i) {
	textureViewDesc.label = outputLabels[i];
	textureViewDesc.baseArrayLayer = i;
	m_outputTextureLayers[i] = m_outputTexture.createView(textureViewDesc);
}

// We still use the view that covers all layers, because we will draw all of
// them in a single dispatch.
textureViewDesc.baseArrayLayer = 0;
textureViewDesc.arrayLayerCount = 6;
textureViewDesc.dimension = TextureViewDimension::_2DArray;
m_outputTextureView = m_outputTexture.createView(textureViewDesc);
```

In the bind group layout, we switch the texture dimension to `2DArray`:

```C++
bindings[1].storageTexture.viewDimension = TextureViewDimension::_2DArray;
//                                                               ^ This was _2D
```

In the shader, we must change the type or `outputTexture`:

```rust
@group(0) @binding(1) var outputTexture: texture_storage_2d_array<rgba8unorm,write>;
//                                       ^ This was texture_storage_2d
```

The call to `textureStore` then takes a new argument, the layer in which we write:

```rust
let layer = id.z;
textureStore(outputTexture, id.xy, layer, color);
```

We launch `4 * 4 * 6 = 96 = 3 * 32` threads:

```rust
@compute @workgroup_size(4, 4, 6)
```

```C++
uint32_t invocationCountX = m_outputTexture.getWidth();
uint32_t invocationCountY = m_outputTexture.getHeight();
uint32_t workgroupSizePerDim = 4;
```

TODO

Conclusion
----------

*Resulting code:* [`step220`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step220)
