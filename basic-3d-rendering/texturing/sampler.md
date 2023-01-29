Sampler (WIP)
=======

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````

The `textureLoad` function that we used in our shader accesses the texture data almost as if it was a basic buffer. It **does not benefit** from the interpolation and mip level selection features that the GPU is capable of.

To **sample** values from a texture with all these capabilities, we define another resource called a **sampler**. We set it up to query the texture data in the way we'd like and then use the `textureSample` function in our shader.

Sampler setup
-------------

### Sampler creation

I am going to detail the sampler settings in the second part of this chapter, once everything is wired up, so that we can directly experiment with it.


````{tab} With webgpu.hpp
```C++
// Create a sampler
SamplerDescriptor samplerDesc;
samplerDesc.addressModeU = AddressMode::ClampToEdge;
samplerDesc.addressModeV = AddressMode::ClampToEdge;
samplerDesc.addressModeW = AddressMode::ClampToEdge;
samplerDesc.magFilter = FilterMode::Linear;
samplerDesc.minFilter = FilterMode::Linear;
samplerDesc.mipmapFilter = MipmapFilterMode::Linear;
samplerDesc.lodMinClamp = 0.0f;
samplerDesc.lodMaxClamp = 1.0f;
samplerDesc.compare = CompareFunction::Undefined;
samplerDesc.maxAnisotropy = 0;
Sampler sampler = device.createSampler(samplerDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create a sampler
WGPUSamplerDescriptor samplerDesc;
samplerDesc.addressModeU = WGPUAddressMode_ClampToEdge;
samplerDesc.addressModeV = WGPUAddressMode_ClampToEdge;
samplerDesc.addressModeW = WGPUAddressMode_ClampToEdge;
samplerDesc.magFilter = WGPUFilterMode_Linear;
samplerDesc.minFilter = WGPUFilterMode_Linear;
samplerDesc.mipmapFilter = WGPUMipmapFilterMode_Linear;
samplerDesc.lodMinClamp = 0.0f;
samplerDesc.lodMaxClamp = 1.0f;
samplerDesc.compare = WGPUCompareFunction_Undefined;
samplerDesc.maxAnisotropy = 0;
WGPUSampler sampler = wgpuDeviceCreateSampler(device, samplerDesc);
```
````

We need to raise the following device limits:

```C++
requiredLimits.limits.maxSampledTexturesPerShaderStage = 1;
requiredLimits.limits.maxSamplersPerShaderStage = 1;
```

### Sampler binding

Adding a new binding should feel rather straightforward by now:

````{tab} With webgpu.hpp
```C++
std::vector<BindGroupLayoutEntry> bindingLayoutEntries(3, Default);
//                                                     ^ This was a 2

BindGroupLayoutEntry& samplerBindingLayout = bindingLayoutEntries[2];
samplerBindingLayout.binding = 2;
samplerBindingLayout.visibility = ShaderStage::Fragment;
samplerBindingLayout.sampler.type = SamplerBindingType::Filtering;

// [...]

std::vector<BindGroupEntry> bindings(3);
//                                   ^ This was a 2

bindings[2].binding = 2;
bindings[2].sampler = sampler;
```
````

````{tab} Vanilla webgpu.h
```C++
std::vector<WGPUBindGroupLayoutEntry> bindingLayoutEntries(3, Default);
//                                                     ^ This was a 2

WGPUBindGroupLayoutEntry& samplerBindingLayout = bindingLayoutEntries[2];
samplerBindingLayout.binding = 2;
samplerBindingLayout.visibility = WGPUShaderStage_Fragment;
samplerBindingLayout.sampler.type = WGPUSamplerBindingType_Filtering;

// [...]

std::vector<WGPUBindGroupEntry> bindings(3);
//                                   ^ This was a 2

bindings[2].binding = 2;
bindings[2].sampler = sampler;
```
````

### Sampler usage

The sampler simply uses the `sampler` type. Once bound, we can use `textureSample(t, s, uv)` to sample the texture `t` at UV `uv` using the sampler `s`:

```rust
@group(0) @binding(2) var textureSampler: sampler;

// [...]

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let color = textureSample(gradientTexture, textureSampler, in.uv).rgb;
	// [...]
}
```

```{figure} /images/sampled-cube.png
:align: center
:class: with-shadow
The cube, textured using a filtering sampler.
```

Adressing
---------

The first part of the sampler settings is rather easy to understand. The address mode tells for each axis of the coordinate space (U, V, and W for 3D textures) how to handle values that are **out of the range** $(0,1)$.

To illustrate this, we go back to our plane example and edit the **vertex shader** to scale and offset the UVs.

```rust
out.uv = in.uv * 2.0 - 0.5;
```

```{figure} /images/clamp-to-edge.png
:align: center
:class: with-shadow
With the ClampToEdge mode, UVs out of the $(0,1)$ range are clamped to $0$ or $1$.
```

Note that if we switch back to raw texture loading, out of bounds texels return a null color:

```rust
let texelCoords = vec2<i32>(in.uv * vec2<f32>(textureDimensions(gradientTexture)));
let color = textureLoad(gradientTexture, texelCoords, 0).rgb;
```

```{figure} /images/transformed-uv.png
:align: center
:class: with-shadow
Raw texture loading returns a null color when out of bounds.
```

Back to a sampled texture, let us now try a different value for the U address mode:

```C++
samplerDesc.addressModeU = AddressMode::Repeat;
```

```{figure} /images/repeat-u.png
:align: center
:class: with-shadow
The Repeat mode set on U repeats the texture infinitly.
```

The last address mode, which we can try on the V axis, repeats with a mirroring effect:

```C++
samplerDesc.addressModeV = AddressMode::MirrorRepeat;
```

```{figure} /images/mirror-v.png
:align: center
:class: with-shadow
The Repeat mode set on V repeats the texture with mirroring.
```

Filtering
---------

The next sampler settings are about **filtering**. There are two types of filtering.

### Magnifying filtering

Magnifying filtering consists in interpolating (i.e., mixing) the value of two neighboring pixels when a fragment samples a location that falls **between two round texel coordinates**.

We can compare the two possible filters:

```C++
samplerDesc.magFilter = FilterMode::Nearest;
// versus
samplerDesc.magFilter = FilterMode::Linear;
```

```{image} /images/mag-filter-light.svg
:align: center
:class: only-light
```

```{image} /images/mag-filter-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>Different magnifying filters.</em></span>
</p>

The `Nearest` mode corresponds to rounding to the closest integer texel coordinate, which corresponds roughly to what we had with raw texel loading (not exactly because we were truncating coordinates rather than rounding).

The `Linear` mode, commonly used, corresponds to mixing coordinates from `floor(u * width)` and `floor((u + 1) * width)` with factor `fract(u * width)`.

### Minifying filtering

#### Aliasing

Since we only have 1 mip level count, it is deactivated and I highlight the issue it addresses by moving the camera over the plane:

```C++
samplerDesc.addressModeU = AddressMode::Repeat;
samplerDesc.addressModeV = AddressMode::Repeat;

// [...]

// In the main loop
float viewZ = glm::mix(0.0f, 0.25f, cos(2 * PI * uniforms.time / 4) * 0.5 + 0.5);
uniforms.viewMatrix = glm::lookAt(vec3(-0.5f, -1.5f, viewZ + 0.25f), vec3(0.0f), vec3(0, 0, 1));
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, viewMatrix), &uniforms.viewMatrix, sizeof(MyUniforms::viewMatrix));
```

```rust
// Repeat the texture 6 times along each axis
out.uv = in.uv * 6.0;
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/aliasing.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">When texels become smaller than pixels, a lot of <strong>aliasing</strong> artifacts emerges.</span></p>
	</figcaption>
</figure>

```{image} /images/min-filter-light.svg
:align: center
:class: only-light
```

```{image} /images/min-filter-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>The aliasing occurs when the <strong>footprint</strong> of a pixel covers multiple texels.</em></span>
</p>


#### Mip-mapping

The minifying filtering is more commonly called **mip-mapping**.

TODO

```C++
samplerDesc.minFilter = FilterMode::Linear;
samplerDesc.mipmapFilter = MipmapFilterMode::Linear;
samplerDesc.lodMinClamp = 0.0f;
samplerDesc.lodMaxClamp = 1.0f;
```

Let us now do some experiment by zomming in and out to better grasp the different settings of the sampler.

```C++
bool success = loadGeometryFromObj(RESOURCE_DIR "/plane.obj", vertexData);

// [...]

// In the main loop
float viewZ = glm::mix(0.5f, 8.0f, cos(uniforms.time) * 0.5 + 0.5);
uniforms.viewMatrix = glm::lookAt(vec3(0.0f, -0.5f, viewZ), vec3(0.0f), vec3(0, 0, 1));
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, viewMatrix), &uniforms.viewMatrix, sizeof(MyUniforms::viewMatrix));
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/texture-zoom.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Raw texture loading.</span></p>
	</figcaption>
</figure>

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/sampler-zoom.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Using a sampler.</span></p>
	</figcaption>
</figure>

**Address mode and filtering**

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````
