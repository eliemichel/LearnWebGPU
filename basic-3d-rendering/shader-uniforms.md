Shader Uniforms
===============

````{tab} With webgpu.hpp
*Resulting code:* [`step035`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step035-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035-vanilla)
````

TODO Let's animate our triangle!

Layout
------

![Binding Layout Figure](/images/binding-layout.png)

TODO

````{tab} With webgpu.hpp
```C++
// Create bind group layout
BindGroupLayoutEntry bindGroupLayoutEntry = Default;
bindGroupLayoutEntry.binding = 0;
bindGroupLayoutEntry.visibility = ShaderStage::Vertex;
bindGroupLayoutEntry.buffer.type = BufferBindingType::Uniform;
bindGroupLayoutEntry.buffer.minBindingSize = 4; // 1 f32 = 4 bytes
```
````

````{tab} Vanilla webgpu.h
```C++
// If you do not use webgpu.hpp, I suggest you create a function to init the
// bindGroup layout entry somewhere.
void initBindGroupLayoutEntry(WGPUBindGroupLayoutEntry &bindGroupLayoutEntry) {
	bindGroupLayoutEntry.buffer.nextInChain = nullptr;
	bindGroupLayoutEntry.buffer.type = WGPUBufferBindingType_Undefined;
	bindGroupLayoutEntry.buffer.hasDynamicOffset = false;

	bindGroupLayoutEntry.sampler.nextInChain = nullptr;
	bindGroupLayoutEntry.sampler.type = WGPUSamplerBindingType_Undefined;

	bindGroupLayoutEntry.storageTexture.nextInChain = nullptr;
	bindGroupLayoutEntry.storageTexture.access = WGPUStorageTextureAccess_Undefined;
	bindGroupLayoutEntry.storageTexture.format = WGPUTextureFormat_Undefined;
	bindGroupLayoutEntry.storageTexture.viewDimension = WGPUTextureViewDimension_Undefined;

	bindGroupLayoutEntry.texture.nextInChain = nullptr;
	bindGroupLayoutEntry.texture.multisampled = false;
	bindGroupLayoutEntry.texture.sampleType = WGPUTextureSampleType_Undefined;
	bindGroupLayoutEntry.texture.viewDimension = WGPUTextureViewDimension_Undefined;
}

// [...]

// Create bind group layout
WGPUBindGroupLayoutEntry bindGroupLayoutEntry{};
initBindGroupLayoutEntry(bindGroupLayoutEntry);
bindGroupLayoutEntry.binding = 0;
bindGroupLayoutEntry.visibility = ShaderStage::Vertex;
bindGroupLayoutEntry.buffer.type = WGPUBufferBindingType_Uniform;
bindGroupLayoutEntry.buffer.minBindingSize = 4; // 1 f32 = 4 bytes
```
````

```C++
BindGroupLayoutDescriptor bindGroupLayoutDesc{};
bindGroupLayoutDesc.entryCount = 1;
bindGroupLayoutDesc.entries = &bindGroupLayoutEntry;
BindGroupLayout bindGroupLayout = device.createBindGroupLayout(bindGroupLayoutDesc);

PipelineLayoutDescriptor layoutDesc{};
layoutDesc.bindGroupLayoutCount = 1;
layoutDesc.bindGroupLayouts = &(WGPUBindGroupLayout)bindGroupLayout;
PipelineLayout layout = device.createPipelineLayout(layoutDesc);
pipelineDesc.layout = layout;
```

Device capabilities
-------------------

TODO

Bind Group
----------

TODO

```C++
// Create buffer
BufferDescriptor bufferDesc{};
bufferDesc.size = 4;
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;
bufferDesc.mappedAtCreation = false;
Buffer buffer = device.createBuffer(bufferDesc);

float currentTime = 1.0f;
queue.writeBuffer(buffer, 0, &currentTime, 4);
```

```C++
// Create bind group
BindGroupEntry bindGroupEntry{};
bindGroupEntry.binding = 0;
bindGroupEntry.buffer = buffer;
bindGroupEntry.offset = 0;
bindGroupEntry.sampler = nullptr;
bindGroupEntry.size = 4;
bindGroupEntry.textureView = nullptr;

BindGroupDescriptor bindGroupDesc{};
bindGroupDesc.layout = bindGroupLayout;
bindGroupDesc.entryCount = bindGroupLayoutDesc.entryCount;
bindGroupDesc.entries = &bindGroupEntry;
BindGroup bindGroup = device.createBindGroup(bindGroupDesc);
```

Uniforms
--------

TODO

```C++
renderPass.setPipeline(pipeline);

// Set binding group
renderPass.setBindGroup(0, bindGroup, 0, nullptr);

renderPass.draw(3, 1, 0, 0);
```

```rust
// Declare the uniform variable as being tight to the binding #0 in bind group #0
@group(0) @binding(0) var<uniform> uTime: f32;

@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> @builtin(position) vec4<f32> {
	// [...]

	// We move the object depending on the time
	p += 0.3 * vec2<f32>(cos(uTime), sin(uTime));

	return vec4<f32>(p, 0.0, 1.0);
}
```

```C++
// Update uniform buffer
float t = static_cast<float>(glfwGetTime());
queue.writeBuffer(buffer, 0, &t, 4);
```

Conclusion
----------

TODO

![Animated triangle](/images/shader-uniforms.png)

````{tab} With webgpu.hpp
*Resulting code:* [`step035`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step035-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035-vanilla)
````
