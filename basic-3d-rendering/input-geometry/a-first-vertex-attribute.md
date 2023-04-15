A first Vertex Attribute
========================

````{tab} With webgpu.hpp
*Resulting code:* [`step032`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step032-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-vanilla)
````

This chapter presents a proper way to feed data as **input to the *vertex shader***.

Shader
------

Remember that we do **not** control the way the `vs_main` function is invoked, the fixed part of the render pipeline does. However, we can **request** some input data by labeling the argument of the function with **WGSL attributes**.

Actually we do this already, with the `@builtin(vertex_index)` attribute:

```rust
@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> /* [...] */ {
	// [...]
}
```

This means that the argument `in_vertex_index` must be populated by the vertex fetch stage with the index of the current vertex.

```{note}
Attributes that are built-in can be found in [the WGSL documentation](https://gpuweb.github.io/gpuweb/wgsl/#builtin-values).
```

Instead of using a built-in input, we can create our own. For this we need to:

 1. Create a **buffer** to store the value of the input for each vertex; this data must be stored on the GPU side of course.
 2. Tell the render pipeline how to interpret the raw buffer data when fetching an entry for each vertex. This is the vertex buffer **layout**.
 3. Set vertex buffer in the render pass before the draw call.

On the shader side, we replace the vertex index argument with a new one:

```rust
@vertex
fn vs_main(@location(0) in_vertex_position: vec2<f32>) -> /* [...] */ {
	// [...]
}
```

The `@location(0)` attribute means that this input variable is described by the vertex attribute in the `pipelineDesc.vertex.buffers` array. The type `vec2<f32>` must comply with what we will declare in the layout. The argument name `in_vertex_position` is up to you, it is only internal to the shader code!

```{note}
The term *attribute* is used for two different things. We talk about **WGSL attribute** to mean tokens of the form `@something` in a WGSL code, and about **vertex attribute** to mean an input of the vertex shader.
```

The vertex shader becomes really simple in the end:

```rust
fn vs_main(@location(0) in_vertex_position: vec2<f32>) -> @builtin(position) vec4<f32> {
	return vec4<f32>(in_vertex_position, 0.0, 1.0);
}
```

Device capabilities
-------------------

> 🤓 Hey what is the maximum number of location attributes?

Glad you asked! The number of vertex attributes available for our device may vary if we do not specify anything. We can check it as follows:

````{tab} With webgpu.hpp
```C++
SupportedLimits supportedLimits;

adapter.getLimits(&supportedLimits);
std::cout << "adapter.maxVertexAttributes: " << supportedLimits.limits.maxVertexAttributes << std::endl;

device.getLimits(&supportedLimits);
std::cout << "device.maxVertexAttributes: " << supportedLimits.limits.maxVertexAttributes << std::endl;

// Personally I get:
//   adapter.maxVertexAttributes: 32
//   device.maxVertexAttributes: 16
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUSupportedLimits supportedLimits;

wgpuAdapterGetLimits(adapter, &supportedLimits);
std::cout << "adapter.maxVertexAttributes: " << supportedLimits.limits.maxVertexAttributes << std::endl;

wgpuDeviceGetLimits(device, &supportedLimits);
std::cout << "device.maxVertexAttributes: " << supportedLimits.limits.maxVertexAttributes << std::endl;

// Personally I get:
//   adapter.maxVertexAttributes: 32
//   device.maxVertexAttributes: 16
```
````

The spirit of the adapter + device abstraction provided by WebGPU is to first check on the adapter that it has the capabilities we need, then we **require** the minimal limits we need during the device creation and if the creation succeeds we are **guarantied** to have the limits we asked for.

And we get nothing more than required, so that if we forget to update the initial check when using more vertex buffers, the program fails. With this **good practice**, we limit the cases of *"it worked for me"* where the program runs correctly on your device but not on somebody else's, which can quickly become a nightmare.

This initial check is done by specifying a non null `requiredLimits` pointer in the device descriptor:

````{tab} With webgpu.hpp
```C++
// Don't forget to = Default
RequiredLimits requiredLimits = Default;
// We use at most 1 vertex attribute for now
requiredLimits.limits.maxVertexAttributes = 1;
// We should also tell that we use 1 vertex buffers
requiredLimits.limits.maxVertexBuffers = 1;

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
// We use at most 1 vertex attribute for now
requiredLimits.limits.maxVertexAttributes = 1;
// We should also tell that we use 1 vertex buffers
requiredLimits.limits.maxVertexBuffers = 1;

DeviceDescriptor deviceDesc{};
// [...]
// We specify required limits here
deviceDesc.requiredLimits = &requiredLimits;
Device device = adapter.requestDevice(deviceDesc);
```
````

```{important}
Notice how I initialized the required limits object with `= Default` above. This is a syntactic helper provided by the `webgpu.hpp` wrapper for all structs to prevent us from manually setting default values. In this case it sets all limits to 0 to mean that there is no requirement.
```

I now get these more secure supported limits:

```
adapter.maxVertexAttributes: 32
device.maxVertexBuffers: 1
```

I recommend you have a look at all the fields of the `WGPULimits` structure in `webgpu.h` so that you know when to add something to the required limits.

Vertex Buffer
-------------

For now we hard-code the value of the vertex buffer in the C++ source:

```C++
// Vertex buffer
// There are 2 floats per vertex, one for x and one for y.
// But in the end this is just a bunch of floats to the eyes of the GPU,
// the *layout* will tell how to interpret this.
std::vector<float> vertexData = {
	// x0, y0
	-0.5, -0.5,

	// x1, y1
	+0.5, -0.5,

	// x2, y2
	+0.0, +0.5
};
int vertexCount = static_cast<int>(vertexData.size() / 2);
```

The GPU-side vertex buffer is created like any other buffer, as introduced in the previous chapter. The main difference is that we must specify `BufferUsage::Vertex` in its `usage` field.

````{tab} With webgpu.hpp
```C++
// Create vertex buffer
BufferDescriptor bufferDesc;
bufferDesc.size = vertexData.size() * sizeof(float);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex;
bufferDesc.mappedAtCreation = false;
Buffer vertexBuffer = device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
queue.writeBuffer(vertexBuffer, 0, vertexData.data(), bufferDesc.size);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create vertex buffer
WGPUBufferDescriptor bufferDesc{};
bufferDesc.nextInChain = nullptr;
bufferDesc.size = vertexData.size() * sizeof(float);
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Vertex;
bufferDesc.mappedAtCreation = false;
WGPUBuffer vertexBuffer = wgpuDeviceCreateBuffer(device, &bufferDesc);

// Upload geometry data to the buffer
wgpuQueueWriteBuffer(queue, vertexBuffer, 0, vertexData.data(), bufferDesc.size);
```
````

Vertex Buffer Layout
--------------------

For the *vertex fetch* stage to provide data from the vertex buffer to our vertex shader, we need to add a `VertexBufferLayout` to `pipelineDesc.vertex.buffers`:

````{tab} With webgpu.hpp
```C++
// Vertex fetch
VertexBufferLayout vertexBufferLayout;
// [...] Build vertex buffer layout

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```
````

````{tab} Vanilla webgpu.h
```C++
// Vertex fetch
WGPUVertexBufferLayout vertexBufferLayout{};
vertexBufferLayout.nextInChain = nullptr;
// [...] Build vertex buffer layout

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```
````

It is important to note that **the same vertex buffer** can contain **multiple vertex attributes**. This is why the `maxVertexAttributes` and `maxVertexBuffers` limits are different concepts. So there is yet another array pointer:

```C++
VertexAttribute vertexAttrib;
// [...]

vertexBufferLayout.attributeCount = 1;
vertexBufferLayout.attributes = &vertexAttrib;
```

We can now configure our vertex attribute. The value of `shaderLocation` must be the same than what specifies the WGSL attribute `@location(...)` in the vertex shader. The format `Float32x2` corresponds at the same time to the type `vec2<f32>` in the shader and to the sequence of 2 floats in the vertex buffer data.

````{tab} With webgpu.hpp
```C++
// == Per attribute ==
// Corresponds to @location(...)
vertexAttrib.shaderLocation = 0;
// Means vec2<f32> in the shader
vertexAttrib.format = VertexFormat::Float32x2;
// Index of the first element
vertexAttrib.offset = 0;
```
````

````{tab} Vanilla webgpu.h
```C++
// == Per attribute ==
// Corresponds to @location(...)
vertexAttrib.shaderLocation = 0;
// Means vec2<f32> in the shader
vertexAttrib.format = WGPUVertexFormat_Float32x2;
// Index of the first element
vertexAttrib.offset = 0;
```
````

The **stride** is a common concept in buffer manipulation: it designates the number of bytes between two consecutive elements. In our case, the positions are **contiguous** so the stride is equal to the size of a `vec2<f32>`, but this will change when adding more attributes in the same buffer.

Finally the `stepMode` is set to `Vertex` to mean that each vertex corresponds to a different value from the buffer. The step mode is set to `Instance` when each value is shared by all vertices of the same instance (i.e., copy) of the shape.

````{tab} With webgpu.hpp
```C++
// == Common to attributes from the same buffer ==
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.stepMode = VertexStepMode::Vertex;
```
````

````{tab} Vanilla webgpu.h
```C++
// == Common to attributes from the same buffer ==
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.stepMode = WGPUVertexStepMode_Vertex;
```
````

Render Pass
-----------

The last change we need to apply is to "connect" the vertex buffer to the pipeline's vertex buffer layout when encoding the render pass:

````{tab} With webgpu.hpp
```C++
renderPass.setPipeline(pipeline);

// Set vertex buffer while encoding the render pass
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexData.size() * sizeof(float));

// We use the `vertexCount` variable instead of hard-coding the vertex count
renderPass.draw(vertexCount, 1, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuRenderPassEncoderSetPipeline(renderPass, pipeline);

// Set vertex buffer while encoding the render pass
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 0, vertexBuffer, 0, vertexData.size() * sizeof(float));

// We use the `vertexCount` variable instead of hard-coding the vertex count
wgpuRenderPassEncoderDraw(renderPass, vertexCount, 1, 0, 0);
```
````

And we get... exactly the same triangle as before. Except now we can very easily add some geometry:

```C++
std::vector<float> vertexData = {
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5,

	-0.55f, -0.5,
	-0.05f, +0.5,
	-0.55f, +0.5
};
```

Conclusion
----------

TODO

```{figure} /images/two-triangles.png
:align: center
:class: with-shadow
Triangles rendered using a vertex attribute
```

````{tab} With webgpu.hpp
*Resulting code:* [`step032`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step032-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-vanilla)
````


