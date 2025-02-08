A first texture <span class="bullet">🟡</span>
===============

````{tab} With webgpu.hpp
*Resulting code:* [`step060`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step060)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step060-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step060-vanilla)
````

Textures play **a very important role** in a rendering pipeline, both for 2D or 3D graphics.

**Theoretically**, a GPU buffer could be used to store the texture data, and the shader would compute at which offset within this buffer a given pixel belongs. But this would be **inefficient** (and maybe not even supported on some devices). Texture access is actually handled by **dedicated fixed units** of the GPU.

This is why although all types of **resources** live in the VRAM, **buffers**, **textures** and **storage textures** are different objects in the WebGPU API (as well as in all other graphics APIs).

Texture creation
----------------

Let us get back to the texture that we had to create for the depth buffer, and **copy it** to create a new texture in the initialization of the app:

````{tab} With webgpu.hpp
```C++
TextureDescriptor textureDesc;
// [...] setup descriptor
Texture texture = device.createTexture(textureDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUTextureDescriptor textureDesc;
textureDesc.nextInChain = nullptr;
// [...] setup descriptor
WGPUTexture texture = wgpuDeviceCreateTexture(device, &textureDesc);
```
````

And add right away the texture destruction at the end of the app:

````{tab} With webgpu.hpp
```C++
texture.destroy();
texture.release();
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuTextureDestroy(texture);
wgpuTextureRelease(texture);
```
````

### Size

A simple setting is the size of the texture (which I arbitrarily set to a power of 2 because it usually helps the GPU in aligning memory):

````{tab} With webgpu.hpp
```C++
textureDesc.dimension = TextureDimension::_2D;
textureDesc.size = { 256, 256, 1 };
//                             ^ ignored because it is a 2D texture
```
````

````{tab} Vanilla webgpu.h
```C++
textureDesc.dimension = WGPUTextureDimension_2D;
textureDesc.size = { 256, 256, 1 };
//                             ^ ignored because it is a 2D texture
```
````

A texture can have $1$, $2$ or $3$ dimensions. Meaning it is either a 1D color gradient, a 2D image of a 3D grid of voxels.

> 🤔 When should I use a 1D texture rather than a simple buffer?

A texture allows to **sample** values **continuously**. For instance even if your 1D texture has only 10 texels (a **texel** is a pixel of a texture), you may sample its value at a **non-integer coordinate** $4.5 / 10$ and you would automatically get a mix of texels 4 and 5.

Another powerful feature of textures is the possibility to sample the **average** value over a neighborhood of a texel, thanks to **mip-maps**. These make a texture **contain multiple images** (also called *subresources*). So the texture size is not only the `size` field but also the number of mip-maps given by `mipLevelCount`.

We'll get to why this is useful **later on**, for now we set the mip level count to the minimum value $1$ to deactivate this feature:

```C++
textureDesc.mipLevelCount = 1;
```

Textures are also able to store **more than one color per texel**, thanks to **multisampling**. This is typically used for handling anti-aliasing ([MSAA](https://en.wikipedia.org/wiki/Multisample_anti-aliasing)). Again, we do not use this for our texture:

```C++
textureDesc.sampleCount = 1;
```

Both the mip level count and the sample count have an **impact on the memory size** of the texture, so when not using these features, setting them to $1$ (the minimum) saves memory.

### Format

The texture format indicates at the same time the **number of channels** in the texture (R, RG, RGB, RGBA), **their order** (RGBA, BGRA, etc.), and **the way each channel is encoded**, including the number of bits and the scale.

For instance, `RGBA8Unorm` means 4 channels (RGBA), with 8 bits per channel which represent unsigned values (U) normalized (norm) so that they are manipulated as real numbers in the range $(0,1)$ (instead of integers in $(0,255)$ for instance).

````{tab} With webgpu.hpp
```C++
textureDesc.format = TextureFormat::RGBA8Unorm;
```
````

````{tab} Vanilla webgpu.h
```C++
textureDesc.format = WGPUTextureFormat_RGBA8Unorm;
```
````

### Misc

Like buffers, textures must **declare their intended usage**, so that they can be placed in more appropriate parts of the memory by the GPU's memory allocator.

In order to be able to **copy pixel data from C++**, the texture needs the `CopyDst` usage. And we will then use the texture by **sampling it from a shader**, so it must be declared with the `TextureBinding` usage:

````{tab} With webgpu.hpp
```C++
textureDesc.usage = TextureUsage::TextureBinding | TextureUsage::CopyDst;
```
````

````{tab} Vanilla webgpu.h
```C++
textureDesc.usage = WGPUTextureUsage_TextureBinding | WGPUTextureUsage_CopyDst;
```
````

Lastly, we initialize the texture view settings to 0 (more on this later):

```C++
textureDesc.viewFormatCount = 0;
textureDesc.viewFormats = nullptr;
```

Uploading texture data
----------------------

We created a texture, which allocated memory in VRAM (i.e. on the GPU). But this remains an **uninitialized chunk of memory**, to which we must set data. This is typically done by **uploading** it from the CPU.

### Test data

Our first texture will be **a simple gradient**, which we can define in our C++ code as follows:

```C++
// Create image data
std::vector<uint8_t> pixels(4 * textureDesc.size.width * textureDesc.size.height);
for (uint32_t i = 0; i < textureDesc.size.width; ++i) {
	for (uint32_t j = 0; j < textureDesc.size.height; ++j) {
		uint8_t *p = &pixels[4 * (j * textureDesc.size.width + i)];
		p[0] = (uint8_t)i; // r
		p[1] = (uint8_t)j; // g
		p[2] = 128; // b
		p[3] = 255; // a
	}
}
```

```{figure} /images/gradient-texture.png
:align: center
:class: with-shadow
The test texture that we generate in our C++ code.
```

### Write texture

Uploading this pixel data to the texture uses `Queue::writeTexture`, to be called once both the texture and its data are created. But a call to `Queue::writeTexture` is a bit more complicated than `Queue::writeBuffer`: since write texture has a lot of arguments, they are grouped in substructures:

````{tab} With webgpu.hpp
```C++
// Arguments telling which part of the texture we upload to
// (together with the last argument of writeTexture)
ImageCopyTexture destination;
// [...]

// Arguments telling how the C++ side pixel memory is laid out
TextureDataLayout source;
// [...]

queue.writeTexture(destination, pixels.data(), pixels.size(), source, textureDesc.size);
```
````

````{tab} Vanilla webgpu.h
```C++
// Arguments telling which part of the texture we upload to
// (together with the last argument of writeTexture)
WGPUImageCopyTexture destination;
// [...]

// Arguments telling how the C++ side pixel memory is laid out
WGPUTextureDataLayout source;
// [...]

wgpuQueueWriteTexture(queue, destination, pixels.data(), pixels.size(), source, textureDesc.size);
```
````

### Destination

The `writeTexture` procedure writes **only one image** (subresource of the texture) at a time. The argument `destination.mipLevel` tells which one we target, and in our case we have only **one mip level**.

The `destination.origin` is the equivalent of the **offset** argument of `Queue::writeBuffer`. Together with the `writeSize` argument, it tells **which part of the image** gets updated, so that we may update only a small part of it. Finally, the aspect is not relevant for color textures.

````{tab} With webgpu.hpp
```C++
destination.texture = texture;
destination.mipLevel = 0;
destination.origin = { 0, 0, 0 }; // equivalent of the offset argument of Queue::writeBuffer
destination.aspect = TextureAspect::All; // only relevant for depth/Stencil textures
```
````

````{tab} Vanilla webgpu.h
```C++
destination.texture = texture;
destination.mipLevel = 0;
destination.origin = { 0, 0, 0 }; // equivalent of the offset argument of Queue::writeBuffer
destination.aspect = WGPUTextureAspect_All; // only relevant for depth/Stencil textures
```
````

### Source

The `source` layout tells how to read from the buffer. The `offset` tells where the data starts after the CPU data pointer we provide in `writeTexture`.

The `bytesPerRow` tells the stride, i.e. the number of bytes between two consecutive rows in the CPU data.

And the `rowsPerImage` is the height of an image, it is important when uploading multiple images at once (only possible when uploading a *texture array*, which we do not use here).

In our case, the data is contiguous, so we set this as follows:

```C++
source.offset = 0;
source.bytesPerRow = 4 * textureDesc.size.width;
source.rowsPerImage = textureDesc.size.height;
```

```{note}
When loading data from an image file, rows might be aligned to a round number of bytes, hence `source.bytesPerRow` would be slightly bigger than `4 * textureDesc.size.width`. This is also needed when uploading very small images because there is **a minimum value** for `bytesPerRow` that is set to 256 by the API.
```

Texture drawing
---------------

Great, we have loaded a texture to the GPU memory... But what can we do with it? How can we check that it was correctly uploaded?

Unfortunately, there is no quick way to copy a texture to the texture view `nextTexture` returned by the swap chain. Instead, we **bind our texture to the render pipeline** and sample it from our shader.

### Binding layout

This binding is close to the uniform buffer binding. We first need to add it to the bind group **layout**. We also slightly reorganize our code to handle multiple bindings:

````{tab} With webgpu.hpp
```C++
// Create binding layouts

// Since we now have 2 bindings, we use a vector to store them
std::vector<BindGroupLayoutEntry> bindingLayoutEntries(2, Default);

// The uniform buffer binding that we already had
BindGroupLayoutEntry& bindingLayout = bindingLayoutEntries[0];
bindingLayout.binding = 0;
bindingLayout.visibility = ShaderStage::Vertex | ShaderStage::Fragment;
bindingLayout.buffer.type = BufferBindingType::Uniform;
bindingLayout.buffer.minBindingSize = sizeof(MyUniforms);

// The texture binding
BindGroupLayoutEntry& textureBindingLayout = bindingLayoutEntries[1];
// [...] Setup texture binding

// Create a bind group layout
BindGroupLayoutDescriptor bindGroupLayoutDesc{};
bindGroupLayoutDesc.entryCount = (uint32_t)bindingLayoutEntries.size();
bindGroupLayoutDesc.entries = bindingLayoutEntries.data();
BindGroupLayout bindGroupLayout = device.createBindGroupLayout(bindGroupLayoutDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create binding layouts

// Since we now have 2 bindings, we use a vector to store them
std::vector<WGPUBindGroupLayoutEntry> bindingLayoutEntries(2);

// The uniform buffer binding that we already had
WGPUBindGroupLayoutEntry& bindingLayout = bindingLayoutEntries[0];
setDefaults(bindingLayout);
bindingLayout.binding = 0;
bindingLayout.visibility = WGPUShaderStage_Vertex | WGPUShaderStage_Fragment;
bindingLayout.buffer.type = WGPUBufferBindingType_Uniform;
bindingLayout.buffer.minBindingSize = sizeof(MyUniforms);

// The texture binding
WGPUBindGroupLayoutEntry& textureBindingLayout = bindingLayoutEntries[1];
setDefaults(textureBindingLayout);
// [...] Setup texture binding

// Create a bind group layout
WGPUBindGroupLayoutDescriptor bindGroupLayoutDesc{};
bindGroupLayoutDesc.nextInChain = nullptr;
bindGroupLayoutDesc.entryCount = (uint32_t)bindingLayoutEntries.size();
bindGroupLayoutDesc.entries = bindingLayoutEntries.data();
WGPUBindGroupLayout bindGroupLayout = wgpuDeviceCreateBindGroupLayout(device, bindGroupLayoutDesc);
```
````

We can now specifically setup our texture binding layout:

````{tab} With webgpu.hpp
```C++
// Setup texture binding
textureBindingLayout.binding = 1;
textureBindingLayout.visibility = ShaderStage::Fragment;
textureBindingLayout.texture.sampleType = TextureSampleType::Float;
textureBindingLayout.texture.viewDimension = TextureViewDimension::_2D;
```
````

````{tab} Vanilla webgpu.h
```C++
// Setup texture binding
textureBindingLayout.binding = 1;
textureBindingLayout.visibility = WGPUShaderStage_Fragment;
textureBindingLayout.texture.sampleType = WGPUTextureSampleType_Float;
textureBindingLayout.texture.viewDimension = WGPUTextureViewDimension_2D;
```
````

The visibility is set to the **fragment shader only**, we will not sample this texture in the vertex shader.

The texture **sample type** tells which variable type will be returned in the shader code when sampling the texture. Since our texture uses a normalized format (`RGBAUnorm`), its values are represented as floats.

### Binding

Once both the pipeline layout and the texture itself are created, we can alter the bind group to add the texture binding (and again slightly reorganize):

````{tab} With webgpu.hpp
```C++
// Create a binding
std::vector<BindGroupEntry> bindings(2);

bindings[0].binding = 0;
bindings[0].buffer = uniformBuffer;
bindings[0].offset = 0;
bindings[0].size = sizeof(MyUniforms);

bindings[1].binding = 1;
bindings[1].textureView = ???;

BindGroupDescriptor bindGroupDesc;
bindGroupDesc.layout = bindGroupLayout;
bindGroupDesc.entryCount = (uint32_t)bindings.size();
bindGroupDesc.entries = bindings.data();
BindGroup bindGroup = device.createBindGroup(bindGroupDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create a binding
std::vector<WGPUBindGroupEntry> bindings(2);

bindings[0].binding = 0;
bindings[0].buffer = uniformBuffer;
bindings[0].offset = 0;
bindings[0].size = sizeof(MyUniforms);

bindings[1].binding = 1;
bindings[1].textureView = ???;

WGPUBindGroupDescriptor bindGroupDesc{};
bindGroupDesc.nextInChain = nullptr;
bindGroupDesc.layout = bindGroupLayout;
bindGroupDesc.entryCount = (uint32_t)bindings.size();
bindGroupDesc.entries = bindings.data();
WGPUBindGroup bindGroup = wgpuDeviceCreateBindGroup(device, bindGroupDesc);
```
````

As you can see, we are not allowed to directly pass a texture to the binding, we rather need to create a **texture view**. Create it right after the creation of the texture itself:

````{tab} With webgpu.hpp
```C++
TextureViewDescriptor textureViewDesc;
textureViewDesc.aspect = TextureAspect::All;
textureViewDesc.baseArrayLayer = 0;
textureViewDesc.arrayLayerCount = 1;
textureViewDesc.baseMipLevel = 0;
textureViewDesc.mipLevelCount = 1;
textureViewDesc.dimension = TextureViewDimension::_2D;
textureViewDesc.format = textureDesc.format;
TextureView textureView = texture.createView(textureViewDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
TextureViewDescriptor textureViewDesc;
textureViewDesc.aspect = WGPUTextureAspect_All;
textureViewDesc.baseArrayLayer = 0;
textureViewDesc.arrayLayerCount = 1;
textureViewDesc.baseMipLevel = 0;
textureViewDesc.mipLevelCount = 1;
textureViewDesc.dimension = WGPUTextureViewDimension_2D;
textureViewDesc.format = textureDesc.format;
TextureView textureView = texture.createView(textureViewDesc);
```
````

### Shader

We can now declare a global variable of type `texture_2d<f32>` in our shader, attached to binding 1 in bind group 0. The function `textureLoad` returns the raw texel value at a given coordinate, and the `@builtin(position)` input of the frament shader is the pixel screen coordinate:

```rust
@group(0) @binding(1) var gradientTexture: texture_2d<f32>;

fn fs_main(in: VertexOutput) -> @location(0) vec4f {
	let color = textureLoad(gradientTexture, vec2i(in.position.xy), 0).rgb;
	// ...
}
```

Sampling from a texture in a shader requires to set a new device limit, to be increased each time you add a texture:

```C++
// Add the possibility to sample a texture in a shader
requiredLimits.limits.maxSampledTexturesPerShaderStage = 1;
```

In order to better see the result, we make sure that there is a fragment for each pixel by drawing a plane that covers the whole screen. Load the file [plane.obj](../../data/plane.obj) and set your matrices to:

```C++
bool success = loadGeometryFromObj(RESOURCE_DIR "/plane.obj", vertexData);

// [...]

uniforms.modelMatrix = mat4x4(1.0);
uniforms.viewMatrix = glm::scale(mat4x4(1.0), vec3(1.0f));
uniforms.projectionMatrix = glm::ortho(-1, 1, -1, 1, -1, 1);
```

```{figure} /images/gradient-texture-window.png
:align: center
:class: with-shadow
Our first texture displayed by drawing a full-screen quad.
```

Feel free to play with other formulas to create the texture data:

```C++
// Create image data
std::vector<uint8_t> pixels(4 * textureDesc.size.width * textureDesc.size.height);
for (uint32_t i = 0; i < textureDesc.size.width; ++i) {
	for (uint32_t j = 0; j < textureDesc.size.height; ++j) {
		uint8_t *p = &pixels[4 * (j * textureDesc.size.width + i)];
		p[0] = (i / 16) % 2 == (j / 16) % 2 ? 255 : 0; // r
		p[1] = ((i - j) / 16) % 2 == 0 ? 255 : 0; // g
		p[2] = ((i + j) / 16) % 2 == 0 ? 255 : 0; // b
		p[3] = 255; // a
	}
}
```

```{figure} /images/other-texture-window.png
:align: center
:class: with-shadow
Changing the pixel array indeed changes the displayed image.
```

Conclusion
----------

We have seen **how to create** a texture and **how to access** its pixels from a shader. In the next chapter we will see **how to map a texture onto a 3D mesh**. And we will realize that we miss a very important ingredient: to fully benefit from the power of a texture, it must be accessed through a **sampler**.

````{tab} With webgpu.hpp
*Resulting code:* [`step060`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step060)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step060-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step060-vanilla)
````
