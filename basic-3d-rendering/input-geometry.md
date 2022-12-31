Input Geometry
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step040`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step040-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040-vanilla)
````

Vertex Attribute Buffers
------------------------

Instead of hard-coding the position of vertices in the shader, we fetch them from a buffer.

TODO

```C++
std::vector<VertexAttribute> vertexAttribs(1);
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = VertexFormat::Float32x2;
vertexAttribs[0].offset = 0;

VertexBufferLayout vertexBufferLayout;
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.attributeCount = static_cast<uint32_t>(vertexAttribs.size());
vertexBufferLayout.attributes = vertexAttribs.data();
vertexBufferLayout.stepMode = VertexStepMode::Vertex;

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```

```C++
// Define geometry
std::vector<float> vertexData = {
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5
};
int vertexCount = static_cast<int>(vertexData.size());

// Create vertex buffer
bufferDesc.size = vertexCount * 2 * sizeof(float);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex;
bufferDesc.mappedAtCreation = false;
Buffer vertexBuffer = device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
queue.writeBuffer(vertexBuffer, 0, vertexData, bufferDesc.size);
```

```C++
renderPass.setPipeline(pipeline);

// Set vertex buffer while encoding the render pass
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexCount * 2 * sizeof(float));

renderPass.setBindGroup(0, bindGroup, 0, nullptr);
renderPass.draw(vertexCount, 1, 0, 0);
```

```rust
@vertex
fn vs_main(@location(0) in_position: vec2<f32>) -> @builtin(position) vec4<f32> {
	var p = in_position + 0.3 * vec2<f32>(cos(uTime), sin(uTime));
	return vec4<f32>(p, 0.0, 1.0);
}
```

Let's change the input geometry:

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

Loading from file
-----------------

TODO

Conclusion
----------

TODO

![Two triangles](/images/two-triangles.png)

````{tab} With webgpu.hpp
*Resulting code:* [`step040`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step040-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040-vanilla)
````


