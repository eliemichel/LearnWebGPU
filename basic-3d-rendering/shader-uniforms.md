Shader Uniforms
===============

````{tab} With webgpu.hpp
*Resulting code:* [`step037`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step037-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-vanilla)
````

Let us now animate our triangle! For this, we use a **uniform** variable in the shader.

A first uniform
---------------

### Definition

A uniform is a global variable whose value is loaded from a GPU buffer. We say that it is **bound** to the buffer.

Its value is **uniform** across the different vertices and fragment of **a given call** to `draw`, but it change from one call to another one by **updating** the value of the buffer it is *bound* to.

To use a uniform, we need to:

 1. Declare the uniform in the *shader*.
 2. Create the *buffer* it is bound to.
 3. Configure the properties of the *binding* (a.k.a. the binding's *layout*).
 4. Create a *bind group*.

### Shader side

In order to animate our triangle, we create a uniform called `uTime` that we update at each frame with the current time, expressed in second (as provided by `glfwGetTime()`).

```{note}
I usually prefix uniform variables with a 'u' so that it is easy to figure out when reading a long shader when a variable is a uniform rather than a local variable.
```

As I said, a uniform is a global variable, so we can declare it in the first line of our shader. A simple variable declaration in WGSL looks as follows:

```rust
// Simple variable declaration
var uTime: f32;
```

The `var` keyword can be labeled with an **address space**, which controls how the variable is stored in the GPU (see [Memory Model](../appendices/memory-model.md)). Here we state that the variable is stored in the *uniform* address space:

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
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> @builtin(position) vec4<f32> {
	// [...]

	// We move the object depending on the time
	p += 0.3 * vec2<f32>(cos(uTime), sin(uTime));

	return vec4<f32>(p, 0.0, 1.0);
}
```

```{hint}
If you are not familiar with the [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_functions) like `cos` and `sin`, be aware that the position $(\cos(a), \sin(a))$ is the point on the circle of radius $1$ at angle $a$ (expressed in radians). Thus, this formula makes the triangle move along a circle over time. It is multiplied by $0.3$ in order to decrease the radius of this circle.
```

### Uniform buffer

The uniform buffer is created like any other buffer, as introduced in chapter [*The Command Queue*](../getting-started/the-command-queue.md). The main difference is that we must specify `BufferUsage::Uniform` in its `usage` field.

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

### Binding configuration

There are two steps in the actual connection of the buffer to the uniform. One is to **declare in the pipeline** that we want a binding, and how exactly. This is the binding layout. And the second one is to create the bind group and enable it (see next section).

#### Pipeline layout

In the previous chapter we had to create a `PipelineLayout` but we left it empty. The pipeline layout describes how all the **resources** used by the render pipeline must be bound. A resource is either a texture or a buffer, and its layout specifies to which index it is bound to and properties like whether it is accessed as read-only or write-only, etc.

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
layoutDesc.bindGroupLayouts = &(WGPUBindGroupLayout)bindGroupLayout;
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

#### Binding layout

The `BindGroupLayoutEntry` could have been called `BindingLayout` imho. The first setting is the binding index, as used in the shader's `@binding` attribute. Then the `visibility` field tells which stage requires access to this resource, so that it is not needlessly provided to all stages.

````{tab} With webgpu.hpp
```C++
// Create binding layout
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
Notice how I initialized the binding layout object with `= Default` above. This is a syntactic helper provided by the `webgpu.hpp` wrapper to prevent us from manually setting default values. In particular it sets the `buffer`, `sampler`, `texture` and `storageTexture` uses to `Undefined` so that only the resource type we set up is used.
```

### Bind group

#### Creation

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

#### Usage

Okey we are now ready to connect the dots! It is as simple as setting the bind group to use before the draw call:

````{tab} With webgpu.hpp
```C++
renderPass.setPipeline(pipeline);

// Set binding group
renderPass.setBindGroup(0, bindGroup, 0, nullptr);

renderPass.draw(3, 1, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuRenderPassEncoderSetPipeline(renderPass, pipeline);

// Set binding group
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, bindGroup, 0, nullptr);

wgpuRenderPassEncoderDraw(renderPass, 3, 1, 0, 0);
```
````

It should be working already, though not moving yet because the content of the buffer does not change yet. So simply add anywhere in the main loop this:

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

Device capabilities
-------------------

### Good practice

The number of bind groups available for our device may vary if we do not specify anything. We can check it as follows:

````{tab} With webgpu.hpp
```C++
SupportedLimits supportedLimits;

adapter.getLimits(&supportedLimits);
std::cout << "adapter.maxBindGroups: " << supportedLimits.limits.maxBindGroups << std::endl;

device.getLimits(&supportedLimits);
std::cout << "device.maxBindGroups: " << supportedLimits.limits.maxBindGroups << std::endl;

// Personally I get:
//   adapter.maxBindGroups: 8
//   device.maxBindGroups: 4
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUSupportedLimits supportedLimits;

wgpuAdapterGetLimits(adapter, &supportedLimits);
std::cout << "adapter.maxBindGroups: " << supportedLimits.limits.maxBindGroups << std::endl;

wgpuDeviceGetLimits(device, &supportedLimits);
std::cout << "device.maxBindGroups: " << supportedLimits.limits.maxBindGroups << std::endl;

// Personally I get:
//   adapter.maxBindGroups: 8
//   device.maxBindGroups: 4
```
````

The spirit of the adapter + device abstraction provided by WebGPU is to first check on the adapter that it has the capabilities we need, then we **require** the minimal limits we need during the device creation and if the creation succeeds we are **guarantied** to have the limits we asked for.

And we get nothing more than required, so that if we forget to update the initial check when using more bind groups, the program fails. With this **good practice**, we limit the cases of "it worked for me" where the program runs correctly on your device but not on somebody else's, which can quickly become a nightmare.

This initial check is done by specifying a non null `requiredLimits` pointer in the device descriptor:

````{tab} With webgpu.hpp
```C++
// Don't forget to = Default
RequiredLimits requiredLimits = Default;

// We use at most 1 bind group for now
requiredLimits.limits.maxBindGroups = 1;
// We use at most 1 uniform buffer per stage
requiredLimits.limits.maxUniformBuffersPerShaderStage = 1;
// Uniform structs have a size of maximum 16 float
requiredLimits.limits.maxUniformBufferBindingSize = 16 * 4;

DeviceDescriptor deviceDesc{};
// [...]
// We specify required limits here
deviceDesc.requiredLimits = &requiredLimits;

Device device = adapter.requestDevice(deviceDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// If you do not use webgpu.hpp, I suggest you create a function to init the
// WGPULimits structure somewhere.
void setDefault(WGPULimits &limits) {
	limits.maxTextureDimension1D = 0;
	limits.maxTextureDimension2D = 0;
	limits.maxTextureDimension3D = 0;
	// [...] Set everything to 0 to mean "no limit"
}

// [...]

WGPURequiredLimits requiredLimits{};
setDefault(requiredLimits.limits);

// We use at most 1 bind group for now
requiredLimits.limits.maxBindGroups = 1;
// We use at most 1 uniform buffer per stage
requiredLimits.limits.maxUniformBuffersPerShaderStage = 1;
// Uniform structs have a size of maximum 16 float
requiredLimits.limits.maxUniformBufferBindingSize = 16 * 4;

DeviceDescriptor deviceDesc{};
// [...]
// We specify required limits here
deviceDesc.requiredLimits = &requiredLimits;

Device device = adapter.requestDevice(deviceDesc);
```
````

I now get these more secure supported limits:

```
adapter.maxBindGroups: 8
device.maxBindGroups: 1
```

I recommend you have a look at all the fields of the `WGPUlimits` structure in `webgpu.h` so that you know when to add something to the required limits.

### Intermediate resulting code

<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
    <source src="../_static/animated-triangle.mp4" type="video/mp4">
</video>

Before going further, you can check the code of this first part against this branch:

````{tab} With webgpu.hpp
*Intermediate resulting code:* [`step035`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035)
````

````{tab} Vanilla webgpu.h
*Intermediate resulting code:* [`step035-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step035-vanilla)
````

More uniforms
-------------

In order to illustrate the flexibility of the uniform binding process, let us add a second uniform variable, this time controlling the color of the triangle.

There are multiple ways to add a second uniform:

 - In a different bind group.
 - In the same bind group but different binding.
 - In the same binding, by replacing the type of the uniform with a custom struct.

The interest of using different bindings is to set a different `visibility` depending on the binding. In our case, the time is only used in the Vertex shader, while the color is only needed by the Fragment shader, so this could be beneficial. However, we may decide to use the time in the Fragment shader eventually, so we'll use the same binding.

```{note}
Another reason is that different bindings should either point to different buffers, or point in the same buffer at **an offset that is at least** `deviceLimits.minUniformBufferOffsetAlignment`. By default, this value is set to 256 bytes for me, and the minimum supported by my adapter is 64. This would be a bit of a waste to add that much padding.
```

### Shader side

Let us replace the `f32` uniform with a struct:

```rust
/**
 * A structure holding the value of our uniforms
 */
struct MyUniforms {
	time: f32,
	color: vec4<f32>,
};

// Instead of the simple uTime variable, our uniform variable is a struct
@group(0) @binding(0) var<uniform> uMyUniforms: MyUniforms;

@vertex
// [...] (Replace uTime with uMyUniforms.time in here)

@fragment
fn fs_main() -> @location(0) vec4<f32> {
	// Return this uniform instead of the color that was previously hard-coded
	return uMyUniforms.color;
}
```

Of course depending on your use case you will find a name more relevant than "MyUniforms", but let's stick to this for now.

### Buffer

On the CPU side, we define the very same struct:

```C++
/**
 * The same structure as in the shader, replicated in C++
 */
struct MyUniforms {
	float time;
	Color color; // We use the color type provided by WebGPU
};
```

The initial buffer upload thus becomes:

```C++
// Upload the initial value of the uniforms
MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```

More generally, you should replace all instances of `sizeof(float)` by `sizeof(MyUniforms)`.

Updating the value of the buffer now looks like this:

```C++
// Update uniform buffer
uniforms.time = static_cast<float>(glfwGetTime());
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```

And actually we can be more subtle:

```C++
// Only update the 1-st float of the buffer
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(float));
```

Similarly we can update only the color bytes:

```C++
// Update uniform buffer
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, sizeof(float), &uniforms.color, sizeof(Color));
//                               ^^^^^^^^^^^^^ offset of `color` in the uniform struct
```

Better yet, if we forget the offset, or want to be flexible to the addition of new fields, we can use the `offsetof` macro:

```C++
// Upload only the time, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, time), &uniforms.time, sizeof(MyUniforms::time));
// Upload only the color, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));
```

### Binding layout

The only thing to change in the binding layout is the visibility:

```C++
bindingLayout.visibility = ShaderStage::Vertex | ShaderStage::Fragment;
```

### Memory Layout Constraints

#### Alignment

There is one thing I have omitted until now: the architecture of the GPU imposes some constraints on the way we can organize fields in a uniform buffer.

If we look at [the uniform layout constraints](https://gpuweb.github.io/gpuweb/wgsl/#address-space-layout-constraints), we can see that **the offset** (as returned by `offsetof`) of a field of type `vec4<f32>` **must be a multiple** of the size of `vec4<f32>`, namely 16 bytes. We say that the field is **aligned** to 16 bytes.

In our current `MyUniforms` struct, this property is **not verified** because `color` as an offset of 4 bytes (`sizeof(float)`), which is obviously not a multiple of 16 bytes! An easy fix is simply to swap the `color` and `time` fields:

```C++
// Don't
struct MyUniforms {
	// offset = 0 * sizeof(f32) -> OK
	float time;

	// offset = 4 -> WRONG, not a multiple of sizeof(vec4<f32>)
	std::array<float,4> color;
};

// Do
struct MyUniforms {
	// offset = 0 * sizeof(vec4<f32>) -> OK
	std::array<float,4> color;

	// offset = 16 = 4 * sizeof(f32) -> OK
	float time;
};
```

And **don't forget** to apply the same change to the struct defined in the shader code!

#### Padding

Another constraint on uniform types is that they must be [host-shareable](https://gpuweb.github.io/gpuweb/wgsl/#host-shareable), which comes with [a constraint on the total structure size](https://gpuweb.github.io/gpuweb/wgsl/#alignment-and-size).

Basically, the total size must be **a multiple of the alignment size of its largest field**. In our case, this means it must be a multiple of 16 bytes (the size of `vec4<f32>`).

Thus we add **padding** to our structure, namely an unused attribute at the end that fills in extra bytes:

```C++
struct MyUniforms {
	std::array<float,4> color;
	float time;
	float _pad[3];
};
// Have the compiler check byte alignment
static_assert(sizeof(MyUniforms) % 16 == 0);
```

Okey, the result is not so impressive but we now are more familiar with uniforms:

![Orange triangle](/images/orange-triangle.png)

Dynamic uniforms
----------------

Imagine we want to issue two calls to the `draw` method of our render pipeline with different values of the uniforms, in order to draw two triangles with different colors. Naively we could try this:

```C++
// THIS WON'T WORK!

// A first color
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));

// First draw call
renderPass.draw(3, 1, 0, 0);

// Different location and different color for another draw call
uniforms.time += 1.0;
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Second draw call
renderPass.draw(3, 1, 0, 0);
```

It is legal, but will not do what you expect. Remember that commands are executed **asynchronously**! When we call methods of the `renderPass` object, we do not really trigger operations, we rather build a command buffer, that is sent all at once at the end. So the calls to `writeBuffer` **do not** get interleaved between the draw calls as we would like.

Instead, we need to use **dynamic uniform buffers**.

TODO

```C++
// Extra limit requirement
requiredLimits.limits.maxDynamicUniformBuffersPerPipelineLayout = 1;
```

```C++
// Create binding layouts
BindGroupLayoutEntry bindingLayout = Default;
// [...]
// Make this binding dynamic so we can offset it between draw calls
bindingLayout.buffer.hasDynamicOffset = true;
```

```C++
// Subtility
uint32_t uniformStride = std::max(
	(uint32_t)sizeof(MyUniforms),
	(uint32_t)deviceLimits.minStorageBufferOffsetAlignment
);
// The buffer will contain 2 values for the uniforms
bufferDesc.size = 2 * uniformStride;

// [...]

MyUniforms uniforms;

// Upload first value
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Upload second value
uniforms.time = -1.0f;
uniforms.color = { 1.0f, 0.5f, 0.0f, 0.7f };
queue.writeBuffer(uniformBuffer, uniformStride, &uniforms, sizeof(MyUniforms));
//                               ^^^^^^^^^^^^^ beware of the non-null offset!
```

```C++
renderPass.setPipeline(pipeline);

uint32_t dynamicOffset = 0;

// Set binding group
dynamicOffset = 0 * uniformStride;
renderPass.setBindGroup(0, bindGroup, 1, &dynamicOffset);
renderPass.draw(3, 1, 0, 0);

// Set binding group with a different uniform offset
dynamicOffset = 1 * uniformStride;
renderPass.setBindGroup(0, bindGroup, 1, &dynamicOffset);
renderPass.draw(3, 1, 0, 0);

renderPass.end();
```

Conclusion
----------

TODO This was quite of a chapter.

![Two triangles](/images/two-triangles-uniforms.png)

````{tab} With webgpu.hpp
*Resulting code:* [`step036`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step036)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step036-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step036-vanilla)
````
