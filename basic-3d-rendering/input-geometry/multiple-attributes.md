Multiple Attributes
===================

````{tab} With webgpu.hpp
*Resulting code:* [`step033`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step033)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step033-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step033-vanilla)
````

Vertices can contain more than just a position. A typical example is to **add a color attribute** to each vertex. This will also show us how the rasterizer automatically interpolate vertex attributes across triangles.

Shader
------

You may have guessed that we can simply add a second argument to the vertex shader entry point `vs_main`, with a different `@location` WGSL attribute:

```rust
@vertex
fn vs_main(@location(0) in_position: vec2<f32>, @location(1) in_color: vec3<f32>) -> /* ... */ {
	// [...]
}
```

This works, but you might prefer when the number of input attribute grows to instead take a single argument whose type is a custom struct labeled with locations:

```rust
/**
 * A structure with fields labeled with vertex attribute locations can be used
 * as input to the entry point of a shader.
 */
struct VertexInput {
	@location(0) position: vec2<f32>,
	@location(1) color: vec3<f32>,
};

@vertex
fn vs_main(in: VertexInput) -> /* ... */ {
	// [...]
}
```

> 😐 But I don't need the color in the vertex shader, I want it in the fragment shader, can I do `fn fs_main(@location(1) color: vec3<f32>)`?

Nope. The vertex attributes are only provided to the vertex shader. However, **the fragment shader can receive what the vertex shader returns!** This is where the structure-based approach becomes handy:

```rust
struct VertexInput {
	@location(0) position: vec2<f32>,
	@location(1) color: vec3<f32>,
};

/**
 * A structure with fields labeled with builtins and locations can also be used
 * as *output* of the vertex shader, which is also the input of the fragment
 * shader.
 */
struct VertexOutput {
	@builtin(position) position: vec4<f32>,
	// The location here does not refer to a vertex attribute, it just means
	// that this field must be handled by the rasterizer.
	// (It can also refer to another field of another struct that would be used
	// as input to the fragment shader.)
	@location(0) color: vec3<f32>,
};

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	out.position = vec4<f32>(in.position, 0.0, 1.0);
	out.color = in.color; // forward to the fragment shader
	return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	return vec4<f32>(in.color, 1.0);
}
```

Vertex Buffer Layout
--------------------

There are different ways of feeding multiple attributes to the vertex fetch stage. The choice usually depends on the way your input data is organized, which varies with the context, so I am going to present two different ways.

### Option A: Interleaved attributes

Before anything, do not forget to increase the vertex attribute limit of your device:

```C++
requiredLimits.limits.maxVertexAttributes = 2;
```

Interleaved attributes means that we put in a single buffer the values for all the attributes of the first vertex, then all values for the second vertex, etc:

```C++
std::vector<float> vertexData = {
	// x0,  y0,  r0,  g0,  b0
	-0.5, -0.5, 1.0, 0.0, 0.0,

	// x1,  y1,  r1,  g1,  b1
	+0.5, -0.5, 0.0, 1.0, 0.0,

	// ...
	+0.0,   +0.5, 0.0, 0.0, 1.0,
	-0.55f, -0.5, 1.0, 1.0, 0.0,
	-0.05f, +0.5, 1.0, 0.0, 1.0,
	-0.55f, +0.5, 0.0, 1.0, 1.0
};
// We now divide the vector size by 5 fields.
int vertexCount = static_cast<int>(vertexData.size() / 5);
```

The first thing we can remark is that now the **stride** of our position attribute has changed from `2 * sizeof(float)` to `5 * sizeof(float)`:

```C++
// The new stride
vertexBufferLayout.arrayStride = 5 * sizeof(float);
```

This stride is the same for both attributes, so it is not a problem that the stride is set at the level of the while buffer layout. The main difference between our two attributes actually is the offset at which they start in the buffer: the color starts after 2 floats.

We now need to provide 2 elements in the `vertexBufferLayout.attributes` array. So instead of passing the address `&vertexAttrib` of a single entry, we use a `std::vector`:

````{tab} With webgpu.hpp
```C++
// We now have 2 attributes
std::vector<VertexAttribute> vertexAttribs(2);

// Position attribute
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = VertexFormat::Float32x2;
vertexAttribs[0].offset = 0;

// Color attribute
vertexAttribs[1].shaderLocation = 1;
vertexAttribs[1].format = VertexFormat::Float32x3; // different type!
vertexAttribs[1].offset = 2 * sizeof(float); // non null offset!

vertexBufferLayout.attributeCount = static_cast<uint32_t>(vertexAttribs.size());
vertexBufferLayout.attributes = vertexAttribs.data();
```
````

````{tab} Vanilla webgpu.h
```C++
// We now have 2 attributes
std::vector<WGPUVertexAttribute> vertexAttribs(2);

// Position attribute
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = WGPUVertexFormat_Float32x2;
vertexAttribs[0].offset = 0;

// Color attribute
vertexAttribs[1].shaderLocation = 1;
vertexAttribs[1].format = WGPUVertexFormat_Float32x3; // different type!
vertexAttribs[1].offset = 2 * sizeof(float); // non null offset!

vertexBufferLayout.attributeCount = static_cast<uint32_t>(vertexAttribs.size());
vertexBufferLayout.attributes = vertexAttribs.data();
```
````

### Option B: Multiple buffers

Another possible data layout is to have two different buffers for the two attributes. Make sure to change the device limit to support this:

```C++
requiredLimits.limits.maxVertexAttributes = 2;
requiredLimits.limits.maxVertexBuffers = 2;
```

We thus have 2 input vectors:

```C++
// x0, y0, x1, y1, ...
std::vector<float> positionData = {
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5,
	-0.55f, -0.5,
	-0.05f, +0.5,
	-0.55f, +0.5
};

// r0,  g0,  b0, r1,  g1,  b1, ...
std::vector<float> colorData = {
	1.0, 0.0, 0.0,
	0.0, 1.0, 0.0,
	0.0, 0.0, 1.0,
	1.0, 1.0, 0.0,
	1.0, 0.0, 1.0,
	0.0, 1.0, 1.0
};

int vertexCount = static_cast<int>(positionData.size() / 2);
assert(vertexCount == static_cast<int>(colorData.size() / 3));
```

Which lead to two GPU buffers:

````{tab} With webgpu.hpp
```C++
// Create vertex buffers
BufferDescriptor bufferDesc;
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex;
bufferDesc.mappedAtCreation = false;

bufferDesc.size = positionData.size() * sizeof(float);
Buffer positionBuffer = device.createBuffer(bufferDesc);
queue.writeBuffer(positionBuffer, 0, positionData.data(), bufferDesc.size);

bufferDesc.size = colorData.size() * sizeof(float);
Buffer colorBuffer = device.createBuffer(bufferDesc);
queue.writeBuffer(colorBuffer, 0, colorData.data(), bufferDesc.size);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create vertex buffers
WGPUBufferDescriptor bufferDesc;
bufferDesc.nextInChain = nullptr;
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Vertex;
bufferDesc.mappedAtCreation = false;

bufferDesc.size = positionData.size() * sizeof(float);
WGPUBuffer positionBuffer = wgpuDeviceCreateBuffer(device, &bufferDesc);
wgpuQueueWriteBuffer(queue, positionBuffer, 0, positionData.data(), bufferDesc.size);

bufferDesc.size = colorData.size() * sizeof(float);
WGPUBuffer colorBuffer = wgpuDeviceCreateBuffer(device, &bufferDesc);
wgpuQueueWriteBuffer(queue, colorBuffer, 0, colorData.data(), bufferDesc.size);
```
````

This time it is not the `VertexAttribute` struct but the `VertexBufferLayout` that is replaced with a vector:

````{tab} With webgpu.hpp
```C++
// We now have 2 attributes
std::vector<VertexBufferLayout> vertexBufferLayouts(2);

// Position attribute remains untouched
VertexAttribute positionAttrib;
positionAttrib.shaderLocation = 0;
positionAttrib.format = VertexFormat::Float32x2; // size of position
positionAttrib.offset = 0;

vertexBufferLayouts[0].attributeCount = 1;
vertexBufferLayouts[0].attributes = &positionAttrib;
vertexBufferLayouts[0].arrayStride = 2 * sizeof(float); // stride = size of position
vertexBufferLayouts[0].stepMode = VertexStepMode::Vertex;

// Position attribute
VertexAttribute colorAttrib;
colorAttrib.shaderLocation = 1;
colorAttrib.format = VertexFormat::Float32x3; // size of color
colorAttrib.offset = 0;

vertexBufferLayouts[1].attributeCount = 1;
vertexBufferLayouts[1].attributes = &colorAttrib;
vertexBufferLayouts[1].arrayStride = 3 * sizeof(float); // stride = size of color
vertexBufferLayouts[1].stepMode = VertexStepMode::Vertex;

pipelineDesc.vertex.bufferCount = static_cast<uint32_t>(vertexBufferLayouts.size());
pipelineDesc.vertex.buffers = vertexBufferLayouts.data();
```
````

````{tab} Vanilla webgpu.h
```C++
// We now have 2 attributes
std::vector<WGPUVertexBufferLayout> vertexBufferLayouts(2);

// Position attribute remains untouched
WGPUVertexAttribute positionAttrib;
positionAttrib.shaderLocation = 0;
positionAttrib.format = WGPUVertexFormat_Float32x2; // size of position
positionAttrib.offset = 0;

vertexBufferLayouts[0].attributeCount = 1;
vertexBufferLayouts[0].attributes = &positionAttrib;
vertexBufferLayouts[0].arrayStride = 2 * sizeof(float); // stride = size of position
vertexBufferLayouts[0].stepMode = WGPUVertexStepMode_Vertex;

// Position attribute
VertexAttribute colorAttrib;
colorAttrib.shaderLocation = 1;
colorAttrib.format = WGPUVertexFormat_Float32x3; // size of color
colorAttrib.offset = 0;

vertexBufferLayouts[1].attributeCount = 1;
vertexBufferLayouts[1].attributes = &colorAttrib;
vertexBufferLayouts[1].arrayStride = 3 * sizeof(float); // stride = size of color
vertexBufferLayouts[1].stepMode = WGPUVertexStepMode_Vertex;

pipelineDesc.vertex.bufferCount = static_cast<uint32_t>(vertexBufferLayouts.size());
pipelineDesc.vertex.buffers = vertexBufferLayouts.data();
```
````

And finally we also have 2 calls to `renderPass.setVertexBuffer`. The first argument (`slot`) corresponds to the index of the buffer layout in the `pipelineDesc.vertex.buffers` array.

````{tab} With webgpu.hpp
```C++
// Set vertex buffers while encoding the render pass
renderPass.setVertexBuffer(0, positionBuffer, 0, positionData.size() * sizeof(float));
renderPass.setVertexBuffer(1, colorBuffer, 0, colorData.size() * sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```C++
// Set vertex buffers while encoding the render pass
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 0, positionBuffer, 0, positionData.size() * sizeof(float));
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 1, colorBuffer, 0, colorData.size() * sizeof(float));
```
````

Conclusion
----------

```{figure} /images/color-attribute.png
:align: center
:class: with-shadow
Triangles with a color attribute (same result for both options).
```

```{tip}
I changed the background color (`clearValue`) to `Color{ 0.05, 0.05, 0.05, 1.0 }` to better appreciate the colors of the triangles.
```

````{tab} With webgpu.hpp
*Resulting code:* [`step033`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step033)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step033-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step033-vanilla)
````


