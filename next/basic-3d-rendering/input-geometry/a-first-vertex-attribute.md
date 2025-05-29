A first Vertex Attribute <span class="bullet">🟠</span>
========================

```{lit-setup}
:tangle-root: 032 - A first Vertex Attribute - Next - vanilla
:parent: 030 - Hello Triangle - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 032 - A first Vertex Attribute - Next
:parent: 030 - Hello Triangle - Next
:debug:
```

````{tab} With webgpu.hpp
*Resulting code:* [`step032-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step032-next-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-next-vanilla)
````

In the [Hello Triangle](../hello-triangle.md) chapter, we were **hardcoding** the 3 vertex positions directly in the shader, but this obviously does not scale well. In this chapter, we see the **proper way** to feed vertex attributes as **input to the *vertex shader***.

Multiple options
----------------

Whichever method we adopt to **feed our render pipeline with data**, it goes through the creation of a **buffer** in which we **store vertex data**.

In chapter [*Our first shader*](../../getting-started/our-first-shader.md), we have seen how to bind a **storage buffer** to access a buffer from a shader. This approach **does work** (provided the storage buffer is read-only), using the `@builtin(vertex_index)` to know what part of the buffer to look at to get the position of the current vertex.

You know what? I'll **leave that option as an exercise** because at this stage you already know everything you need!

Instead, we investigate here **a second option**, which relies on the initial **vertex fetch** stage of the render pipeline. This is again a case where specifying more tightly the **usage** of our data helps the GPU better manage the memory, leading to better performance.

```{note}
On modern (higher end) desktop GPUs, there is not much of a performance difference between using a storage buffer and using the pipeline's vertex buffer. However, I strongly invite you to **keep in mind lower end devices** and mobile devices when developing your application ([there are good reasons for that](../../../appendices/keep-in-mind-lower-end-devices.md)).
```

Vertex shader input
-------------------

Remember that we do **not** control the way the `vs_main` function is invoked, the **fixed part** of the render pipeline does. However, we can **request** some input data by labeling the argument of the function with **WGSL attributes**.

```{important}
The term *attribute* is used for two different things. We talk about **WGSL attribute** to mean tokens of the form `@something` in a WGSL code, and about **vertex attribute** to mean an input of the vertex shader.
```

We already use a WGSL attribute in our vertex shader input actually, namely the `@builtin(vertex_index)` attribute:

```rust
@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> /* [...] */ {
	//     ^^^^^^^^^^^^^^^^^^^^^^ This is a WGSL attribute
	// [...]
}
```

This means that the argument `in_vertex_index` must be populated by the vertex fetch stage with the index of the current vertex.

```{note}
Attributes that are **built-in**, like `vertex_index`, are listed in [the WGSL documentation](https://gpuweb.github.io/gpuweb/wgsl/#builtin-values).
```

Instead of using a built-in input, we can **create our own**. For this we need to:

 1. Create a **buffer** to store the value of the input for each vertex; this data must be stored **on the GPU side**, of course.
 2. Tell the render pipeline **how to interpret** the raw buffer data when fetching an entry for each vertex. This is the vertex buffer **layout**.
 3. Set the vertex buffer in the render pass before the draw call.

On the shader side, we replace the vertex index argument with a new one:

```rust
@vertex
fn vs_main(@location(0) in_vertex_position: vec2f) -> /* [...] */ {
	//     ^^^^^^^^^^^^ This is a WGSL attribute
	// [...]
}
```

The `@location(0)` attribute means that this input variable is described by the first (index '0') **vertex attribute** in the `pipelineDesc.vertex.buffers` array. The type `vec2f` must comply with what we will declare in the **layout**. The argument name `in_vertex_position` is up to you, it is only local to the shader code!

The vertex shader becomes really simple in the end:

```{lit} rust, Vertex shader (also for tangle root "Vanilla")
fn vs_main(@location(0) in_vertex_position: vec2f) -> @builtin(position) vec4f {
	return vec4f(in_vertex_position, 0.0, 1.0);
}
```

```{lit} rust, Shader source literal (hidden, replace, also for tangle root "Vanilla")
const char* shaderSource = R"(
@vertex
{{Vertex shader}}

@fragment
{{Fragment shader}}
)";
```

```{lit} rust, Fragment shader (hidden, also for tangle root "Vanilla")
fn fs_main() -> @location(0) vec4f {
	return vec4f(0.0, 0.4, 1.0, 1.0);
}
```

**WIP**

Device capabilities
-------------------

### Checking capabilities

> 🤓 Hey what is the **maximum number** of location attributes?

Glad you asked! The number of vertex attributes available for our device may vary if we do not specify anything. We can check it as follows:

````{tab} With webgpu.hpp
```C++
Limits supportedLimits;

adapter.getLimits(&supportedLimits);
std::cout << "adapter.maxVertexAttributes: " << supportedLimits.maxVertexAttributes << std::endl;

device.getLimits(&supportedLimits);
std::cout << "device.maxVertexAttributes: " << supportedLimits.maxVertexAttributes << std::endl;

// Personally I get:
//   adapter.maxVertexAttributes: 32
//   device.maxVertexAttributes: 16
```
````

````{tab} Vanilla webgpu.h
```C++
WGPULimits supportedLimits{};
supportedLimits.nextInChain = nullptr;

wgpuAdapterGetLimits(adapter, &supportedLimits);
std::cout << "adapter.maxVertexAttributes: " << supportedLimits.maxVertexAttributes << std::endl;

wgpuDeviceGetLimits(device, &supportedLimits);
std::cout << "device.maxVertexAttributes: " << supportedLimits.maxVertexAttributes << std::endl;

// Personally I get:
//   adapter.maxVertexAttributes: 32
//   device.maxVertexAttributes: 16
```
````

The spirit of the [adapter + device](../../getting-started/adapter-and-device/index.md) abstraction provided by WebGPU is to first check on the adapter that it has the capabilities we need, then we **require** the minimal limits we need during the device creation and if the creation succeeds we are **guaranteed** to have the limits we asked for.

And we get nothing more than required, so that if we forget to update the initial check when using more vertex buffers, the program fails. With this **good practice**, we limit the cases of *"it worked for me"* where the program runs correctly on your device but not on somebody else's, which can quickly become a nightmare.

### Requiring capabilities

This initial check is done by specifying a non null `requiredLimits` pointer in the device descriptor. I suggest that we create a method `GetRequiredLimits(Adapter adapter)` dedicated to setting our app requirements:

````{tab} With webgpu.hpp
```{lit} C++, Private methods (append)
// In Application class
private:
	wgpu::Limits GetRequiredLimits(wgpu::Adapter adapter) const;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Private methods (append, for tangle root "Vanilla")
// In Application class
private:
	WGPULimits GetRequiredLimits(WGPUAdapter adapter) const;
```
````

We then call this method while building the **device descriptor**:

````{tab} With webgpu.hpp
```{lit} C++, Build device descriptor TODO
// Before adapter.requestDevice(deviceDesc)
Limits requiredLimits = GetRequiredLimits(adapter);
deviceDesc.requiredLimits = &requiredLimits;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Build device descriptor TODO (for tangle root "Vanilla")
// Before requestDeviceSync(adapter, &deviceDesc)
WGPULimits requiredLimits = GetRequiredLimits(adapter);
deviceDesc.requiredLimits = &requiredLimits;
```
````

The required limits follow the **same structure** than the supported limits, we can customize some of them for our vertex attribute:

````{tab} With webgpu.hpp
```{lit} C++, GetRequiredLimits method
Limits Application::GetRequiredLimits(Adapter adapter) const {
	// Get adapter supported limits, in case we need them
	Limits supportedLimits;
	adapter.getLimits(&supportedLimits);

	// Don't forget to = Default
	Limits requiredLimits = Default;

	// We use at most 1 vertex attribute for now
	requiredLimits.maxVertexAttributes = 1;
	// We should also tell that we use 1 vertex buffers
	requiredLimits.maxVertexBuffers = 1;
	// Maximum size of a buffer is 6 vertices of 2 float each
	requiredLimits.maxBufferSize = 6 * 2 * sizeof(float);
	// Maximum stride between 2 consecutive vertices in the vertex buffer
	requiredLimits.maxVertexBufferArrayStride = 2 * sizeof(float);

	{{Other device limits}}

	return requiredLimits;
}
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, GetRequiredLimits method (for tangle root "Vanilla")
WGPULimits Application::GetRequiredLimits(WGPUAdapter adapter) const {
	// Get adapter supported limits, in case we need them
	WGPULimits supportedLimits;
	supportedLimits.nextInChain = nullptr;
	wgpuAdapterGetLimits(adapter, &supportedLimits);

	WGPULimits requiredLimits = WGPU_LIMITS_INIT;

	// We use at most 1 vertex attribute for now
	requiredLimits.maxVertexAttributes = 1;
	// We should also tell that we use 1 vertex buffers
	requiredLimits.maxVertexBuffers = 1;
	// Maximum size of a buffer is 6 vertices of 2 float each
	requiredLimits.maxBufferSize = 6 * 2 * sizeof(float);
	// Maximum stride between 2 consecutive vertices in the vertex buffer
	requiredLimits.maxVertexBufferArrayStride = 2 * sizeof(float);

	{{Other device limits}}

	return requiredLimits;
}
```
````

```{lit} C++, Application implementation (hidden, append, also for tangle root "Vanilla")
{{GetRequiredLimits method}}
```

```{important}
Notice how I **initialized the required limits** object with `= Default` above. This is a syntactic helper provided by the `webgpu.hpp` wrapper for all structs to prevent us from manually setting default values. In this case it sets all limits to `WGPU_LIMIT_U32_UNDEFINED` or `WGPU_LIMIT_U64_UNDEFINED` to mean that there is no requirement.
```

I now get these more secure supported limits:

```
adapter.maxVertexAttributes: 32
device.maxVertexBuffers: 1
```

I recommend you have a look at all the fields of the `WGPULimits` structure in `webgpu.h` so that you know when to add something to the required limits.

````{note}
There are two limits that may cause issue even if set to `WGPU_LIMIT_U32_UNDEFINED`, namely the one that set **minimums** rather than maximums. The default "undefined" value may not be supported by the adapter, so **in this case only** I suggest we forward values from the **supported limits**:

```{lit} C++, Other device limits (also for tangle root "Vanilla")
// These two limits are different because they are "minimum" limits,
// they are the only ones we are may forward from the adapter's supported
// limits.
requiredLimits.minUniformBufferOffsetAlignment = supportedLimits.minUniformBufferOffsetAlignment;
requiredLimits.minStorageBufferOffsetAlignment = supportedLimits.minStorageBufferOffsetAlignment;
```
````

### Default capabilities

The official default capabilities can be found in [the specification](https://www.w3.org/TR/webgpu/#limit-default). This also mentions that:

> Every adapter is guaranteed to support the default value or better. ([source](https://www.w3.org/TR/webgpu/#limit-default))

**In this guide**, I take care of specifying required capabilities more strictly for two reasons:

 - To make sure we present the capabilities related to the various notions as we are introducing them.
 - Because it is possible to have "**compatibility**" adapters that would not be deemed valid in the web but are still exposed in native mode.

Vertex Buffer
-------------

Back to our vertex position attribute: for now we hard-code the **values of the vertex buffer** in the C++ source:

```{lit} C++, Define vertex data (also for tangle root "Vanilla")
// Vertex buffer data
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

// We will declare vertexCount as a member of the Application class
m_vertexCount = static_cast<uint32_t>(vertexData.size() / 2);
```

The GPU-side vertex buffer is created **like any other buffer**, as introduced in the previous chapter. The main difference is that we must specify `BufferUsage::Vertex` in its `usage` field.

````{tab} With webgpu.hpp
```{lit} C++, Create vertex buffer
// Create vertex buffer
BufferDescriptor bufferDesc;
bufferDesc.size = vertexData.size() * sizeof(float);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex; // Vertex usage here!
bufferDesc.mappedAtCreation = false;
m_vertexBuffer = m_device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
m_queue.writeBuffer(m_vertexBuffer, 0, vertexData.data(), bufferDesc.size);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create vertex buffer (for tangle root "Vanilla")
// Create vertex buffer
WGPUBufferDescriptor bufferDesc{};
bufferDesc.nextInChain = nullptr;
bufferDesc.size = vertexData.size() * sizeof(float);
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Vertex; // Vertex usage here!
bufferDesc.mappedAtCreation = false;
m_vertexBuffer = wgpuDeviceCreateBuffer(m_device, &bufferDesc);

// Upload geometry data to the buffer
wgpuQueueWriteBuffer(m_queue, m_vertexBuffer, 0, vertexData.data(), bufferDesc.size);
```
````

We declare `m_vertexBuffer` and `m_vertexCount` as a members of our `Application` class and place this initialization in a dedicated `InitializeBuffers()` method:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // Application attributes
	wgpu::Buffer m_vertexBuffer;
	uint32_t m_vertexCount;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // Application attributes
	WGPUBuffer m_vertexBuffer;
	uint32_t m_vertexCount;
```
````

```{lit} C++, Private methods (append, also for tangle root "Vanilla")
private: // APplication methods
	void InitializeBuffers();
```

This method define the CPU-side vertex data and then creates the GPU-side buffer as described above:

```{lit} C++, InitializeBuffers method (also for tangle root "Vanilla")
void Application::InitializeBuffers() {
	{{Define vertex data}}
	{{Create vertex buffer}}
}
```

```{lit} C++, Application implementation (hidden, append, also for tangle root "Vanilla")
{{InitializeBuffers method}}
```

````{note}
Do not forget to call this at the end of `Initialize()`:

```{lit} C++, Initialize (append, also for tangle root "Vanilla")
// At the end of Initialize()
InitializeBuffers();
```
````

And of course we release this buffer when the application terminates:

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
// At the beginning of Terminate()
m_vertexBuffer.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
// At the beginning of Terminate()
wgpuBufferRelease(m_vertexBuffer);
```
````

Vertex Buffer Layout
--------------------

For the *vertex fetch* stage to transform this **raw data** from the vertex buffer **into what the vertex shader expects**, we need to specify a `VertexBufferLayout` to `pipelineDesc.vertex.buffers`:

````{tab} With webgpu.hpp
```{lit} C++, Describe vertex buffers
// Vertex fetch
VertexBufferLayout vertexBufferLayout;
{{Describe the vertex buffer layout}}

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe vertex buffers (for tangle root "Vanilla")
// Vertex fetch
WGPUVertexBufferLayout vertexBufferLayout{};
{{Describe the vertex buffer layout}}

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```
````

```{lit} C++, Describe render pipeline (prepend)
{{Describe vertex buffers}}
```

Note that a given render pipeline **may use more than one** vertex buffer. On the other hand, the **same vertex buffer** can contain **multiple vertex attributes**.

```{note}
This is why the `maxVertexAttributes` and `maxVertexBuffers` limits are different concepts.
```

So, within our vertex buffer layout, we specify **how many attributes** it contains and **detail each of them**. In our case, there is only the position attribute:


````{tab} With webgpu.hpp
```{lit} C++, Describe the vertex buffer layout
VertexAttribute positionAttrib;
{{Describe the position attribute}}

vertexBufferLayout.attributeCount = 1;
vertexBufferLayout.attributes = &positionAttrib;

{{Describe buffer stride and step mode}}
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe the vertex buffer layout (for tangle root "Vanilla")
WGPUVertexAttribute positionAttrib;
{{Describe the position attribute}}

vertexBufferLayout.attributeCount = 1;
vertexBufferLayout.attributes = &positionAttrib;

{{Describe buffer stride and step mode}}
```
````

### For each attribute

We can now configure our vertex attribute:

 - The value of `shaderLocation` must be the **same** as what specifies the **WGSL attribute** `@location(...)` in the vertex shader.
 - The **format** `Float32x2` corresponds at the same time to the type `vec2f` in the shader and to the sequence of 2 floats in the vertex buffer data.
 - The **offset** tells where the sequence of position values start in the raw vertex buffer. In our case it starts at the beginning (offset 0). It is **non null** when the same vertex buffer **contains multiple attributes**.

````{tab} With webgpu.hpp
```{lit} C++, Describe the position attribute
// == For each attribute, describe its layout, i.e., how to interpret the raw data ==
// Corresponds to @location(...)
positionAttrib.shaderLocation = 0;
// Means vec2f in the shader
positionAttrib.format = VertexFormat::Float32x2;
// Index of the first element
positionAttrib.offset = 0;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe the position attribute (for tangle root "Vanilla")
// == For each attribute, describe its layout, i.e., how to interpret the raw data ==
// Corresponds to @location(...)
positionAttrib.shaderLocation = 0;
// Means vec2f in the shader
positionAttrib.format = WGPUVertexFormat_Float32x2;
// Index of the first element
positionAttrib.offset = 0;
```
````

### For the whole vertex buffer

Attributes coming from the same vertex buffer **share some properties**:

 - The **stride** is a common concept in buffer manipulation: it designates the number of bytes between two consecutive elements. In our case, the positions are **contiguous** so the stride is equal to the size of a `vec2f`, but this will change when adding more attributes in the same buffer, if attributes are **interleaved**.

 - Finally the `stepMode` is set to `Vertex` to mean that **each value** from the buffer corresponds to a **different vertex**. The step mode is set to `Instance` when each value is **shared by all vertices of the same instance** (i.e., copy) of the shape (we'll see instancing later on).

````{tab} With webgpu.hpp
```{lit} C++, Describe buffer stride and step mode
// == Common to attributes from the same buffer ==
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.stepMode = VertexStepMode::Vertex;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe buffer stride and step mode (for tangle root "Vanilla")
// == Common to attributes from the same buffer ==
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.stepMode = WGPUVertexStepMode_Vertex;
```
````

Render Pass
-----------

The last change we need to apply is to "connect" the vertex buffer to the pipeline's vertex buffer layout when encoding the render pass:

````{tab} With webgpu.hpp
```{lit} C++, Draw a triangle (replace)
renderPass.setPipeline(pipeline);

// Set vertex buffer while encoding the render pass
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexBuffer.getSize());

// We use the `m_vertexCount` variable instead of hard-coding the vertex count
renderPass.draw(m_vertexCount, 1, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Draw a triangle (replace, for tangle root "Vanilla")
wgpuRenderPassEncoderSetPipeline(renderPass, pipeline);

// Set vertex buffer while encoding the render pass
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 0, vertexBuffer, 0, wgpuBufferGetSize(vertexBuffer));

// We use the `m_vertexCount` variable instead of hard-coding the vertex count
wgpuRenderPassEncoderDraw(renderPass, m_vertexCount, 1, 0, 0);
```
````

And we get... exactly the same triangle as before. Except now we can very **easily add some geometry**:

```{lit} C++, Define vertex data (replace, also for tangle root "Vanilla")
// Vertex buffer data
// There are 2 floats per vertex, one for x and one for y.
std::vector<float> vertexData = {
	// Define a first triangle:
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5,

	// Add a second triangle:
	-0.55f, -0.5,
	-0.05f, +0.5,
	-0.55f, +0.5
};
```

Conclusion
----------

```{figure} /images/two-triangles.png
:align: center
:class: with-shadow
Triangles rendered using a vertex attribute
```

We have seen in this chapter how to use **GPU buffers** to feed data as **input** to the vertex shader, and thus to the whole rasterization pipeline. We will refine this in the next chapter by adding **additional attributes**.

````{tab} With webgpu.hpp
*Resulting code:* [`step032-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step032-next-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step032-next-vanilla)
````




