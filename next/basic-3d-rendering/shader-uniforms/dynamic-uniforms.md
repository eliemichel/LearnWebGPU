Dynamic uniforms <span class="bullet">🟢</span>
================

```{lit-setup}
:tangle-root: 044 - Dynamic uniforms - Next - vanilla
:parent: 043 - More uniforms - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 044 - Dynamic uniforms - Next
:parent: 043 - More uniforms - Next
:debug:
```

````{tab} With webgpu.hpp
*Resulting code:* [`step044-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla-next)
````

Imagine we want to issue **two calls** to the `draw` method of our render pipeline **with different values** of the uniforms, in order to draw two WebGPU logos with different colors. Naively we could try this:

````{tab} With webgpu.hpp
```C++
// THIS WON'T WORK!

// A first color
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
m_queue.writeBuffer(m_uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(uniforms.color));

// First draw call
renderPass.drawIndexed(m_indexCount, 1, 0, 0, 0);

// Different location and different color for another draw call
uniforms.time += 1.0;
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
m_queue.writeBuffer(m_uniformBuffer, 0, &uniforms, sizeof(uniforms));

// Second draw call
renderPass.drawIndexed(m_indexCount, 1, 0, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```C++
// THIS WON'T WORK!

// A first color
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(uniforms.color));

// First draw call
wgpuRenderPassEncoderDrawIndexed(renderPass, m_indexCount, 1, 0, 0, 0);

// Different location and different color for another draw call
uniforms.time += 1.0;
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, 0, &uniforms, sizeof(uniforms));

// Second draw call
wgpuRenderPassEncoderDrawIndexed(renderPass, m_indexCount, 1, 0, 0, 0);
```
````

It is legal, but **will not do** what you expect. Remember that commands are **batched**! When we call methods of the `renderPass` object, we do not really trigger operations, we rather build a command buffer, that **is sent all at once** at the end. So the calls to `writeBuffer` **do not** get interleaved between the draw calls as we would like.

```{themed-figure} /images/dynamic-uniforms/timelines_{theme}.svg
:align: center

The draw calls are **batched into a command buffer** and submitted all at once, so both buffer writes happen **before the first draw call** is executed.
```

We could adopt multiple strategies to avoid this:

- **Option A:** Submit two **different render passes**, and build two command buffers, etc. This is ok if we don't have too many draw calls, but if you want scale up to draw 100 objects the overhead will be significant.
- **Option B:** Create two **different uniform buffers**, and two bind groups, and call `renderPass.setBindGroup()` in between draw calls. Works as well, but maybe you don't want to maintain 1000 buffers if you have that many objects to draw.
- **Option C:** Use a single buffer that contains a concatenation of all variations of the uniforms, and **dynamically change the offset** at which uniforms are read.

In this chapter, we explore this last option, i.e., we use **dynamic uniform buffers**. This is a simple option to turn on in the binding layout, but requires to be careful with the buffer's **stride**.

```{note}
You already know everything you need to implement options A and B.
```

Drawing
-------

In the previous chapters we did not use the last two arguments of `renderPass.setBindGroup`, namely `dynamicOffsetCount` and `dynamicOffsets` array. They are the way to **provide an offset** that is different for different calls. To change the offset, we re-bind the same bind group, only with a different offset.

If we would have multiple dynamic uniforms, we would need to point to an array, but since we only have one, we can just give the address of a `dynamicOffset` variable. Here is how we can use it:

````{tab} With webgpu.hpp
```{lit} C++, Use Render Pass (replace)
renderPass.setPipeline(m_pipeline);
renderPass.setVertexBuffer(0, m_pointBuffer, 0, m_pointBuffer.getSize());
renderPass.setIndexBuffer(m_indexBuffer, IndexFormat::Uint16, 0, m_indexBuffer.getSize());

uint32_t dynamicOffset = 0;

// Set binding group
dynamicOffset = 0 * m_uniformStride;
renderPass.setBindGroup(0, m_bindGroup, 1, &dynamicOffset);
renderPass.drawIndexed(m_indexCount, 1, 0, 0, 0);

// Set binding group with a different uniform offset
dynamicOffset = 1 * m_uniformStride;
renderPass.setBindGroup(0, m_bindGroup, 1, &dynamicOffset);
renderPass.drawIndexed(m_indexCount, 1, 0, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Use Render Pass (replace, for tangle root "Vanilla")
wgpuRenderPassEncoderSetPipeline(renderPass, m_pipeline);
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 0, m_pointBuffer, 0, wgpuBufferGetSize(m_pointBuffer));
wgpuRenderPassEncoderSetIndexBuffer(renderPass, m_indexBuffer, WGPUIndexFormat_Uint16, 0, wgpuBufferGetSize(m_indexBuffer));

uint32_t dynamicOffset = 0;

// Set binding group
dynamicOffset = 0 * m_uniformStride;
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, m_bindGroup, 1, &dynamicOffset);
wgpuRenderPassEncoderDrawIndexed(renderPass, m_indexCount, 1, 0, 0, 0);

// Set binding group with a different uniform offset
dynamicOffset = 1 * m_uniformStride;
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, m_bindGroup, 1, &dynamicOffset);
wgpuRenderPassEncoderDrawIndexed(renderPass, m_indexCount, 1, 0, 0, 0);
```
````

Here the `m_uniformStride` gives the **byte distance** between the beginning of two versions of the uniform buffer values, similarly to the notion of stride we used with vertex buffers. We declare it at the class level:

```{lit} C++, Application attributes (append, also for tangle root "Vanilla")
private: // In Application.h
	uint32_t m_uniformStride = 0;
```

What we need now is to **adapt the size of the buffer** to contain multiple versions of the values.

Buffer data
-----------

The basic idea is to have a buffer that is **twice the size** of `MyUniforms`. For the **first draw call**, we set the dynamic offset to 0 so that it uses the first set of values, then we issue a **second draw call** with an offset of `sizeof(MyUniforms)` to point to the second half of the buffer.

There is **one thing to keep in mind** though: the value of the offset is constrained to be **a multiple of** the `minUniformBufferOffsetAlignment` limit of the device.


```{themed-figure} /images/dynamic-uniforms/stride_{theme}.svg
:align: center

There is a **minimum allowed byte stride** in between two occurrences of the uniform values.
```

The **stride** of the uniform buffer, i.e., the number of bytes between the first `r` and the second `r` above, must be **rounded up to the closest multiple** of `minUniformBufferOffsetAlignment`:

````{tab} With webgpu.hpp
```{lit} C++, Compute uniform stride
Limits deviceLimits = Default;
m_device.getLimits(&deviceLimits);

// Subtlety
m_uniformStride = ceilToNextMultiple(
	(uint32_t)sizeof(MyUniforms),
	(uint32_t)deviceLimits.minUniformBufferOffsetAlignment
);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Compute uniform stride (for tangle root "Vanilla")
WGPULimits deviceLimits = WGPU_LIMITS_INIT;
wgpuDeviceGetLimits(m_device, &deviceLimits);

// Subtlety
m_uniformStride = ceilToNextMultiple(
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

```{lit} C++, file: webgpu-utils.h (append, hidden, also for tangle root "Vanilla")
/**
 * Round 'value' up to the next multiplier of 'step'.
 */
uint32_t ceilToNextMultiple(uint32_t value, uint32_t step);
```

```{lit} C++, Utility functions (append, hidden, also for tangle root "Vanilla")
uint32_t ceilToNextMultiple(uint32_t value, uint32_t step) {
	uint32_t divide_and_ceil = value / step + (value % step == 0 ? 0 : 1);
	return step * divide_and_ceil;
}
```

We can now use it when creating the uniform buffer:

````{tab} With webgpu.hpp
```{lit} C++, Create uniform buffer (replace)
{{Compute uniform stride}}

// The buffer now contains 2 values for the uniforms plus the space in between:
// (NB: stride = sizeof(MyUniforms) + spacing)
bufferDesc.size = m_uniformStride + sizeof(MyUniforms);
	
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;
m_uniformBuffer = m_device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create uniform buffer (replace, for tangle root "Vanilla")
{{Compute uniform stride}}

// The buffer now contains 2 values for the uniforms plus the space in between:
// (NB: stride = sizeof(MyUniforms) + spacing)
bufferDesc.size = m_uniformStride + sizeof(MyUniforms);
	
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;
m_uniformBuffer = wgpuDeviceCreateBuffer(m_device, &bufferDesc);
```
````

And we upload 2 different set of uniform values:

````{tab} With webgpu.hpp
```{lit} C++, Upload uniform values (replace)
MyUniforms uniforms;

// Upload first value
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
m_queue.writeBuffer(m_uniformBuffer, 0, &uniforms, sizeof(uniforms));

// Upload second value
uniforms.time = -1.0f;
uniforms.color = { 1.0f, 1.0f, 1.0f, 0.7f };
m_queue.writeBuffer(m_uniformBuffer, m_uniformStride, &uniforms, sizeof(uniforms));
//                                   ^^^^^^^^^^^^^^^ beware of the non-null offset!
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Upload uniform values (replace, for tangle root "Vanilla")
MyUniforms uniforms;

// Upload first value
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, 0, &uniforms, sizeof(uniforms));

// Upload second value
uniforms.time = -1.0f;
uniforms.color = { 1.0f, 1.0f, 1.0f, 0.7f };
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, m_uniformStride, &uniforms, sizeof(uniforms));
//                                             ^^^^^^^^^^^^^^^ beware of the non-null offset!
```
````

Binding layout
--------------

One last thing before we can run our code: we need to **declare in the bind group layout** that the buffer uses a **dynamically offset**:

```{lit} C++, Define bindingLayout (append, also for tangle root "Vanilla")
// After declaring the uniform's `bindingLayout` in InitializePipeline():

// Make this binding dynamic so we can offset it between draw calls
bindingLayout.buffer.hasDynamicOffset = true;
```

And here we are, with our two different draw calls!

```{figure} /images/webgpu-logo-double.png
:align: center
:class: with-shadow

We draw the scene twice with different values of the **dynamic uniforms**.
```

Device limits
-------------

Here comes the usual point about device limits! We saw already that we need to pay attention to `minUniformBufferOffsetAlignment` when using dynamic uniform buffers. The other related limit is `maxDynamicUniformBuffersPerPipelineLayout`, which simply sets a maximum on the number of such dynamic uniform buffer. It defaults to **8**.

Conclusion
----------

We are now quite comfortable with uniforms, we are ready to move on to actual **3D shapes**!

````{tab} With webgpu.hpp
*Resulting code:* [`step044-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step044-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step044-vanilla-next)
````
