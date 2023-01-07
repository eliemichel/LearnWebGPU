Dynamic uniforms (WIP)
================

````{tab} With webgpu.hpp
*Resulting code:* [`step044`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla)
````

Imagine we want to issue two calls to the `draw` method of our render pipeline with different values of the uniforms, in order to draw two WebGPU logos with different colors. Naively we could try this:

```C++
// THIS WON'T WORK!

// A first color
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));

// First draw call
renderPass.drawIndexed(indexCount, 1, 0, 0, 0);

// Different location and different color for another draw call
uniforms.time += 1.0;
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Second draw call
renderPass.drawIndexed(indexCount, 1, 0, 0, 0);
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

````{tab} With webgpu.hpp
*Resulting code:* [`step044`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla)
````
