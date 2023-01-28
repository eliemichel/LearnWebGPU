Sampler (WIP)
=======

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````

The `textureLoad` function that we used in our shader accesses the texture data almost as if it was a basic buffer. It does not benefit from the interpolation and mip level selection features that the GPU is capable of.

To **sample** values from a texture with all these capabilities, we define another resource called a **sampler**. We set it up to query the texture data in the way we'd like and then use the `textureSample` function in our shader.

Sampler creation
----------------

TODO

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

```C++
requiredLimits.limits.maxSampledTexturesPerShaderStage = 1;
requiredLimits.limits.maxSamplersPerShaderStage = 1;
```

Sampler binding
---------------

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

Sampler usage
-------------

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

Filtering
---------

Let's do some experiment by zomming in and out.

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````
