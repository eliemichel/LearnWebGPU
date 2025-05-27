Hello Triangle <span class="bullet">🔴</span>
==============

```{lit-setup}
:tangle-root: 030 - Hello Triangle - Next - vanilla
:parent: 025 - First Color - Next
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 030 - Hello Triangle - Next
:parent: 028 - C++ Wrapper - Next
:debug:
```

````{tab} With webgpu.hpp
*Resulting code:* [`step030-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-next-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next-vanilla)
````

In this chapter, we finally see how to **draw something** on the screen! And by **something**, I mean triangles, because... all the GPU can draw is triangles. Rest assured, we can do **a lot** with triangles.

In its overall outline, **drawing a triangle** is as simple as this:

````{tab} With webgpu.hpp
```{lit} C++, Draw a triangle
// Select which render pipeline to use
renderPass.setPipeline(pipeline);
// Draw 1 instance of a 3-vertices shape
renderPass.draw(3, 1, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Draw a triangle (for tangle root "Vanilla")
// Select which render pipeline to use
wgpuRenderPassEncoderSetPipeline(renderPass, pipeline);
// Draw 1 instance of a 3-vertices shape
wgpuRenderPassEncoderDraw(renderPass, 3, 1, 0, 0);
```
````

What is a bit verbose is the configuration of the **render pipeline**, and the creation of **shaders**. Luckily, we already introduced a lot of key concepts in chapter [*Our first shader*](../getting-started/our-first-shader.md), the main new element here is the render pipeline.

```{note}
In case you start reading the guide from here, and just because it cannot hurt, I will repeat some of the most important points about shaders here as well.
```

Render Pipeline
---------------

In order to achieve high performance real-time 3D rendering, the GPU processes shapes through a predefined pipeline. The pipeline itself is **always the same** (it is generally built into the physical architecture of the hardware), but we can **configure** it in many ways. To do so, WebGPU provides a *Render Pipeline* object.

```{note}
If you are familiar with OpenGL, you can see WebGPU's render pipeline as a memorized value for all the stateful functions that configure the rendering pipeline.
```

The figure below illustrates the sequence of data processing **stages** executed by the render pipeline. Most of them are **fixed-function** stages, meaning we can only customize some variables, but the most powerful ones are the **programmable stages**.

In these programmable stages, a true program, called a **shader**, is executed in a massively parallel way (across input **vertices**, or across rasterized **fragments**).

```{themed-figure} /images/render-pipeline-{theme}.svg
:align: center

The Render Pipeline abstraction used by WebGPU, detailed in subsections below. On the left is the succession of **stages**, and on the right is a visualization of of the data it processes, from individual **vertices** to triangles rasterized into pixel-size **fragments**.
```

```{note}
Other graphics APIs provide access to more programmable stages (geometry shader, mesh shader, task shader). These are not part of the Web standard. They might be available in the future or as native-only extensions, but in a lot of cases one can use general purpose [compute shaders](../basic-compute/index.md) to mimic their behavior.
```

As always, we build a descriptor in order to create the render pipeline:

````{tab} With webgpu.hpp
```{lit} C++, Create Render Pipeline
RenderPipelineDescriptor pipelineDesc = Default;
{{Describe render pipeline}}
RenderPipeline pipeline = device.createRenderPipeline(pipelineDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Render Pipeline (for tangle root "Vanilla")
WGPURenderPipelineDescriptor pipelineDesc = WGPU_RENDER_PIPELINE_DESCRIPTOR_INIT;
{{Describe render pipeline}}
WGPURenderPipeline pipeline = wgpuDeviceCreateRenderPipeline(device, &pipelineDesc);
```
````

If you have a look at its definition in `webpgu.h`, you'll see that the render pipeline descriptor has quite many fields. But don't worry, for this first triangle, we can leave a lot of them to their default values!

**WIP**

````{tab} With webgpu.hpp
```{lit} C++, Describe render pipeline
// TODO
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe render pipeline (for tangle root "Vanilla")
// TODO
```
````

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step030-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-next-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next-vanilla)
````
