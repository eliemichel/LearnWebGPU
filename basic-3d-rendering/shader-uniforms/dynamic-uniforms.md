Dynamic uniforms <span class="bullet">🟡</span>
================

```{admonition} 🚧 WIP
From this chapter on, the guide uses a previous version of the accompanying code (in particular, it does not define an `Application` class but rather puts everything in a monolithic `main` function). **I am currently refreshing it** chapter by chapter and this is **where I am currently working**!
```

````{tab} With webgpu.hpp
*Resulting code:* [`step044`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla)
````

Imagine we want to issue **two calls** to the `draw` method of our render pipeline **with different values** of the uniforms, in order to draw two WebGPU logos with different colors. Naively we could try this:

````{tab} With webgpu.hpp
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
````

````{tab} Vanilla webgpu.h
```C++
// THIS WON'T WORK!

// A first color
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));

// First draw call
wgpuRenderPassEncoderDrawIndexed(renderPass, indexCount, 1, 0, 0, 0);

// Different location and different color for another draw call
uniforms.time += 1.0;
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Second draw call
wgpuRenderPassEncoderDrawIndexed(renderPass, indexCount, 1, 0, 0, 0);
```
````

It is legal, but **will not do** what you expect. Remember that commands are executed **asynchronously**! When we call methods of the `renderPass` object, we do not really trigger operations, we rather build a command buffer, that **is sent all at once** at the end. So the calls to `writeBuffer` **do not** get interleaved between the draw calls as we would like.

Instead, we need to use **dynamic uniform buffers**. This is a simple option to turn on in the binding layout, but requires to be careful with the buffer's **stride** (see below).

Device limits
-------------

As always, we checkout first that the features we use are somewhere in the `WGPULimits` struct and add our requirements to the device creation code:

```C++
// Extra limit requirement
requiredLimits.limits.maxDynamicUniformBuffersPerPipelineLayout = 1;
```

Another related limit is `minUniformBufferOffsetAlignment`, which we already set as the minimum value supported by the adapter (see below).

Binding layout
--------------

When declaring the bind group layout, we can **set the buffer as dynamically offset**:

````{tab} With webgpu.hpp
```C++
// Create binding layouts
BindGroupLayoutEntry bindingLayout = Default;
// [...]
// Make this binding dynamic so we can offset it between draw calls
bindingLayout.buffer.hasDynamicOffset = true;
```
````

````{tab} Vanilla webgpu.h
```C++
// Create binding layouts
WGPUBindGroupLayoutEntry bindingLayout;
setDefault(bindingLayout);
// [...]
// Make this binding dynamic so we can offset it between draw calls
bindingLayout.buffer.hasDynamicOffset = true;
```
````

The value of this dynamic offset will be later passed to `renderPass.setBindGroup`.

Buffer data
-----------

The basic idea is to have a buffer that is **twice the size** of `MyUniforms`. For the first draw call, we set the dynamic offset to 0 so that it uses the first set of values, then we issue a second draw call with an offset of `sizeof(MyUniforms)` to point to the second half of the buffer.

There is **one thing to keep in mind** though: the value of the offset is constrained to be **a multiple of** the `minUniformBufferOffsetAlignment` limit of the device.

```
  ---------------------------------     ---------------------------------
 | r | g | b | a | t | _ | _ | _ |  ...  | r | g | b | a | t | _ | _ | _ |
  ---------------------------------     ---------------------------------
                                         ^^^^^^ second instance of the MyUniform struct
 ^^^^^^ first instance of the MyUniform struct
```

This means that the **stride** of the uniform buffer, i.e., the number of bytes between the first `r` and the second `r` above, must be rounded up to the closest multiple of `minUniformBufferOffsetAlignment`:

````{tab} With webgpu.hpp
```C++
SupportedLimits supportedLimits;
device.getLimits(&supportedLimits);
Limits deviceLimits = supportedLimits.limits;
//[...]

// Subtlety
uint32_t uniformStride = ceilToNextMultiple(
	(uint32_t)sizeof(MyUniforms),
	(uint32_t)deviceLimits.minUniformBufferOffsetAlignment
);
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUSupportedLimits supportedLimits;
wgpuDeviceGetLimits(device, &supportedLimits);
WGPULimits deviceLimits = supportedLimits.limits;
//[...]

// Subtlety
uint32_t uniformStride = ceilToNextMultiple(
	(uint32_t)sizeof(MyUniforms),
	(uint32_t)deviceLimits.minUniformBufferOffsetAlignment
);
```
````

Where the utility function is given by:

```C++
/**
 * Round 'value' up to the next multiplier of 'step'.
 */
uint32_t ceilToNextMultiple(uint32_t value, uint32_t step) {
	uint32_t divide_and_ceil = value / step + (value % step == 0 ? 0 : 1);
	return step * divide_and_ceil;
}
```

We can now create the buffer and upload 2 different set of values:

````{tab} With webgpu.hpp
```C++
// The buffer will contain 2 values for the uniforms plus the space in between
// (NB: stride = sizeof(MyUniforms) + spacing)
bufferDesc.size = uniformStride + sizeof(MyUniforms);

// [...]

MyUniforms uniforms;

// Upload first value
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Upload second value
uniforms.time = -1.0f;
uniforms.color = { 1.0f, 1.0f, 1.0f, 0.7f };
queue.writeBuffer(uniformBuffer, uniformStride, &uniforms, sizeof(MyUniforms));
//                               ^^^^^^^^^^^^^ beware of the non-null offset!
```
````

````{tab} Vanilla webgpu.h
```C++
// The buffer will contain 2 values for the uniforms plus the space in between
// (NB: stride = sizeof(MyUniforms) + spacing)
bufferDesc.size = uniformStride + sizeof(MyUniforms);

// [...]

MyUniforms uniforms;

// Upload first value
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));

// Upload second value
uniforms.time = -1.0f;
uniforms.color = { 1.0f, 1.0f, 1.0f, 0.7f };
wgpuQueueWriteBuffer(queue, uniformBuffer, uniformStride, &uniforms, sizeof(MyUniforms));
//                                         ^^^^^^^^^^^^^ beware of the non-null offset!
```
````

Drawing
-------

In the previous chapters we did not use the last two arguments of `renderPass.setBindGroup`, namely `dynamicOffsetCount` and `dynamicOffsets` array. They are the way to provide an offset that is different for different calls. To change the offset, we re-bind the bind group only with a different offset.

If we would have multiple dynamic uniforms, we would need to point to an array, but since we only have one, we can just give the address of a `dynamicOffset` variable:

````{tab} With webgpu.hpp
```C++
renderPass.setPipeline(pipeline);

uint32_t dynamicOffset = 0;

// Set binding group
dynamicOffset = 0 * uniformStride;
renderPass.setBindGroup(0, bindGroup, 1, &dynamicOffset);
renderPass.drawIndexed(indexCount, 1, 0, 0, 0);

// Set binding group with a different uniform offset
dynamicOffset = 1 * uniformStride;
renderPass.setBindGroup(0, bindGroup, 1, &dynamicOffset);
renderPass.drawIndexed(indexCount, 1, 0, 0, 0);

renderPass.end();
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuRenderPassEncoderSetPipeline(renderPass, pipeline);

uint32_t dynamicOffset = 0;

// Set binding group
dynamicOffset = 0 * uniformStride;
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, bindGroup, 1, &dynamicOffset);
wgpuRenderPassEncoderDrawIndexed(renderPass, indexCount, 1, 0, 0, 0);

// Set binding group with a different uniform offset
dynamicOffset = 1 * uniformStride;
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, bindGroup, 1, &dynamicOffset);
wgpuRenderPassEncoderDrawIndexed(renderPass, indexCount, 1, 0, 0, 0);

wgpuRenderPassEncoderEnd(renderPass);
```
````

```{note}
Another solution could have been to create 2 different bind groups, pointing to 2 different buffers. But the dynamic offset approach **scales better** when issuing a large number of draw calls with varying uniforms.
```

Conclusion
----------

We are now quite comfortable with uniforms, we are ready to move on to actual 3D shapes!

```{figure} /images/webgpu-logo-double.png
:align: center
:class: with-shadow
We draw the scene twice with different values of the **dynamic uniforms**.
```

````{tab} With webgpu.hpp
*Resulting code:* [`step044`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla)
````
