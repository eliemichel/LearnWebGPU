A first uniform
===============

````{tab} With webgpu.hpp
*Resulting code:* [`step039`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step039-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-vanilla)
````

Introduction
------------

### Motivation

If we look at our current shader, we see some hard-coded constants:

```rust
let ratio = 640.0 / 480.0;
let offset = vec2<f32>(-0.6875, -0.463);
```

This is not very satisfying, what happens when we want to move the object during the execution of the application? Or change the ratio because the user resized the window?

> ☝️ We could dynamically change the shader code and rebuild a new shader module!

It would work, but **building a shader module takes time**. A lot of time if we compare it to the budget for rendering a single frame (typically a 60th of a second). Imagine we want to **animate** our scene and thus change the `offset` at each frame!

This is why a proper solution is to use a **uniform variable**.

### Definition

A uniform is a global variable in a shader whose value is loaded from a GPU buffer. We say that it is **bound** to the buffer.

Its value is **uniform** across the different vertices and fragment of **a given call** to `draw`, but it change from one call to another one by **updating** the value of the buffer it is *bound* to.

To use a uniform, we need to:

 1. Declare the uniform in the *shader*.
 2. Create the *buffer* it is bound to.
 3. Configure the properties of the *binding* (a.k.a. the binding's *layout*).
 4. Create a *bind group*.

### Device limits

In this chapter, we will require the following limits to be set up for our device:

```C++
// We use at most 1 bind group for now
requiredLimits.limits.maxBindGroups = 1;
// We use at most 1 uniform buffer per stage
requiredLimits.limits.maxUniformBuffersPerShaderStage = 1;
// Uniform structs have a size of maximum 16 float (more than what we need)
requiredLimits.limits.maxUniformBufferBindingSize = 16 * 4;
```

Shader side
-----------

In order to animate our scene, we create a uniform called `uTime` that we update at each frame with the current time, expressed in second (as provided by `glfwGetTime()`).

```{note}
I usually prefix uniform variables with a 'u' so that it is easy to figure out when reading a long shader when a variable is a uniform rather than a local variable.
```

As I said, a uniform is a global variable, so we can declare it in the first line of our shader. A simple variable declaration in WGSL looks as follows:

```rust
// Simple variable declaration
var uTime: f32;
```

The `var` keyword can be labeled with an **address space**, which controls how the variable is stored in the GPU (see [Memory Model](/appendices/memory-model.md)). Here we state that the variable is stored in the *uniform* address space:

```rust
// Variable in the *uniform* address space
var<uniform> uTime: f32;
```

Now we need to tell to which **buffer** the uniform is **bound**. This is done by specifying a **binding index** with the `@binding(...)` WGSL attribute.

```rust
// Specify which binding index the uniform is attached to
@binding(0) var<uniform> uTime: f32;
```

We will then define in the C++ code which buffer is attached to the binding #0. And actually, bindings are organized in **bind groups**, so the binding of a uniform is specified by also providing an `@group(...)` attribute:

```rust
// The memory location of the uniform is given by a pair of a *bind group* and a *binding*
@group(0) @binding(0) var<uniform> uTime: f32;
```

We are now done with the declaration of the uniform variable, we can use it like any other variable in our shader:

```rust
@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	// [...]
	// We move the scene depending on the time
	var offset = vec2<f32>(-0.6875, -0.463);
	offset += 0.3 * vec2<f32>(cos(uTime), sin(uTime));
	// [...]
}
```

```{hint}
If you are not familiar with the [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_functions) like `cos` and `sin`, be aware that the position $(\cos(a), \sin(a))$ is the point on the circle of radius $1$ at angle $a$ (expressed in radians). Thus, this formula makes the triangle move along a circle over time. It is multiplied by $0.3$ in order to decrease the radius of this circle.
```

Uniform buffer
--------------

The uniform buffer is created like any other buffer, except we must specify `BufferUsage::Uniform` in its `usage` field. We only need it to contain 1 float for now.

````{tab} With webgpu.hpp
```C++
// Create uniform buffer
BufferDescriptor bufferDesc{};

// The buffer will only contain 1 float with the value of uTime
bufferDesc.size = sizeof(float);

// Make sure to flag the buffer as BufferUsage::Uniform
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;

bufferDesc.mappedAtCreation = false;
Buffer uniformBuffer = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create uniform buffer
WGPUBufferDescriptor bufferDesc{};
bufferDesc.nextInChain = nullptr;

// The buffer will only contain 1 float with the value of uTime
bufferDesc.size = sizeof(float);

// Make sure to flag the buffer as BufferUsage::Uniform
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;

bufferDesc.mappedAtCreation = false;
WGPUBuffer uniformBuffer = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

Then use `Queue::writeBuffer` to upload a value:

````{tab} With webgpu.hpp
```C++
float currentTime = 1.0f;
queue.writeBuffer(uniformBuffer, 0, &currentTime, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```C++
float currentTime = 1.0f;
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &currentTime, sizeof(float));
```
````

Binding configuration
---------------------

There are two steps in the actual connection of the buffer to the uniform. One is to **declare in the pipeline** that we want a binding, and how exactly. This is the binding layout. And the second one is to create the bind group and enable it (see next section).

```{note}
This follows the same spirit than the distinction between the *vertex buffer* and the *vertex buffer layout*.
```

### Pipeline layout

The binding layout is specified through the `PipelineLayout` part of the pipeline descriptor. The pipeline layout describes how all the **resources** used by the render pipeline must be bound. A resource is either a texture or a buffer, and its layout specifies to which index it is bound to and properties like whether it is accessed as read-only or write-only, etc.

A pipeline layout contains multiple **bind groups**, and a bind group contains multiple **bindings**:

````{tab} With webgpu.hpp
```C++
// [...] Define bindingLayout

// Create a bind group layout
BindGroupLayoutDescriptor bindGroupLayoutDesc{};
bindGroupLayoutDesc.entryCount = 1;
bindGroupLayoutDesc.entries = &bindingLayout;
BindGroupLayout bindGroupLayout = device.createBindGroupLayout(bindGroupLayoutDesc);

// Create the pipeline layout
PipelineLayoutDescriptor layoutDesc{};
layoutDesc.bindGroupLayoutCount = 1;
layoutDesc.bindGroupLayouts = (WGPUBindGroupLayout*)&bindGroupLayout;
PipelineLayout layout = device.createPipelineLayout(layoutDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// [...] Define bindingLayout

// Create a bind group layout
WGPUBindGroupLayoutDescriptor bindGroupLayoutDesc{};
bindGroupLayoutDesc.nextInChain = nullptr;
bindGroupLayoutDesc.entryCount = 1;
bindGroupLayoutDesc.entries = &bindingLayout;
WGPUBindGroupLayout bindGroupLayout = wgpuDeviceCreateBindGroupLayout(device, &bindGroupLayoutDesc);

// Create the pipeline layout
WGPUPipelineLayoutDescriptor layoutDesc{};
layoutDesc.nextInChain = nullptr;
layoutDesc.bindGroupLayoutCount = 1;
layoutDesc.bindGroupLayouts = &bindGroupLayout;
WGPUPipelineLayout layout = wgpuDeviceCreatePipelineLayout(device, &layoutDesc);
```
````

### Binding layout

The `BindGroupLayoutEntry` could have been called `BindingLayout` imho. The first setting is the binding index, as used in the shader's `@binding` attribute. Then the `visibility` field tells which stage requires access to this resource, so that it is not needlessly provided to all stages.

````{tab} With webgpu.hpp
```C++
// Create binding layout (don't forget to = Default)
BindGroupLayoutEntry bindingLayout = Default;

// The binding index as used in the @binding attribute in the shader
bindingLayout.binding = 0;

// The stage that needs to access this resource
bindingLayout.visibility = ShaderStage::Vertex;
```
````

````{tab} Vanilla webgpu.h
```C++
// If you do not use webgpu.hpp, I suggest you create a function to init the
// bindGroup layout entry somewhere.
void setDefault(WGPUBindGroupLayoutEntry &bindingLayout) {
	bindingLayout.buffer.nextInChain = nullptr;
	bindingLayout.buffer.type = WGPUBufferBindingType_Undefined;
	bindingLayout.buffer.hasDynamicOffset = false;

	bindingLayout.sampler.nextInChain = nullptr;
	bindingLayout.sampler.type = WGPUSamplerBindingType_Undefined;

	bindingLayout.storageTexture.nextInChain = nullptr;
	bindingLayout.storageTexture.access = WGPUStorageTextureAccess_Undefined;
	bindingLayout.storageTexture.format = WGPUTextureFormat_Undefined;
	bindingLayout.storageTexture.viewDimension = WGPUTextureViewDimension_Undefined;

	bindingLayout.texture.nextInChain = nullptr;
	bindingLayout.texture.multisampled = false;
	bindingLayout.texture.sampleType = WGPUTextureSampleType_Undefined;
	bindingLayout.texture.viewDimension = WGPUTextureViewDimension_Undefined;
}

// [...]

// Create binding layout
WGPUBindGroupLayoutEntry bindingLayout{};
setDefault(bindingLayout);

// The binding index as used in the @binding attribute in the shader
bindingLayout.binding = 0;

// The stage that needs to access this resource
bindingLayout.visibility = WGPUShaderStage_Vertex;
```
````

The remaining of the binding layout depends on the type of resource. We fill either the `buffer` field or the `sampler` and `texture` fields or the `storageTexture` field. In our case it is a buffer:

````{tab} With webgpu.hpp
```C++
bindingLayout.buffer.type = BufferBindingType::Uniform;
bindingLayout.buffer.minBindingSize = sizeof(float);
```
````

````{tab} Vanilla webgpu.h
```C++
bindingLayout.buffer.type = WGPUBufferBindingType_Uniform;
bindingLayout.buffer.minBindingSize = sizeof(float);
```
````

```{important}
Notice how I initialized the binding layout object with `= Default` above. It is important because it sets in particular the `buffer`, `sampler`, `texture` and `storageTexture` uses to `Undefined` so that only the resource type we set up is used.
```

Bind group
----------

### Creation

A bind group contains the actual bindings. The structure of a bind group mirrors the bind group layout prescribed in the render pipeline and actually connects it to resources. This way, the same pipeline can be reused as is in multiple draw calls depending on different variants of the resources.

````{tab} With webgpu.hpp
```C++
// Create a binding
BindGroupEntry binding{};
// [...] Setup binding

// A bind group contains one or multiple bindings
BindGroupDescriptor bindGroupDesc{};
bindGroupDesc.layout = bindGroupLayout;
// There must be as many bindings as declared in the layout!
bindGroupDesc.entryCount = bindGroupLayoutDesc.entryCount;
bindGroupDesc.entries = &binding;
BindGroup bindGroup = device.createBindGroup(bindGroupDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create a binding
WGPUBindGroupEntry binding{};
binding.nextInChain = nullptr;
// [...] Setup binding

// A bind group contains one or multiple bindings
WGPUBindGroupDescriptor bindGroupDesc{};
bindGroupDesc.nextInChain = nullptr;
bindGroupDesc.layout = bindGroupLayout;
// There must be as many bindings as declared in the layout!
bindGroupDesc.entryCount = bindGroupLayoutDesc.entryCount;
bindGroupDesc.entries = &binding;
WGPUBindGroup bindGroup = wgpuDeviceCreateBindGroup(device, &bindGroupDesc);
```
````

The content of the binding itself is quite straightforward:

```C++
// The index of the binding (the entries in bindGroupDesc can be in any order)
binding.binding = 0;
// The buffer it is actually bound to
binding.buffer = uniformBuffer;
// We can specify an offset within the buffer, so that a single buffer can hold
// multiple uniform blocks.
binding.offset = 0;
// And we specify again the size of the buffer.
binding.size = sizeof(float);
```

```{note}
The fields `binding.sampler` and `binding.textureView` are only needed when the binding layout uses them.
```

### Usage

Okay we are now ready to connect the dots! It is as simple as setting the bind group to use before the draw call:

````{tab} With webgpu.hpp
```C++
// Set binding group
renderPass.setBindGroup(0, bindGroup, 0, nullptr);

renderPass.drawIndexed(indexCount, 1, 0, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```C++
// Set binding group
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, bindGroup, 0, nullptr);

wgpuRenderPassEncoderDrawIndexed(renderPass, indexCount, 1, 0, 0, 0);
```
````

It should be working already, though not moving because the content of the buffer does not change yet. So simply add anywhere in the main loop this:

````{tab} With webgpu.hpp
```C++
// Update uniform buffer
float t = static_cast<float>(glfwGetTime()); // glfwGetTime returns a double
queue.writeBuffer(uniformBuffer, 0, &t, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```C++
// Update uniform buffer
float t = static_cast<float>(glfwGetTime()); // glfwGetTime returns a double
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &t, sizeof(float));
```
````

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/turning-webgpu-logo.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Our first dynamic scene!</span></p>
	</figcaption>
</figure>

````{tab} With webgpu.hpp
*Resulting code:* [`step039`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step039-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-vanilla)
````
