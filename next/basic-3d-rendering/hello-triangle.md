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
pipeline = device.createRenderPipeline(pipelineDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Render Pipeline (for tangle root "Vanilla")
WGPURenderPipelineDescriptor pipelineDesc = WGPU_RENDER_PIPELINE_DESCRIPTOR_INIT;
{{Describe render pipeline}}
pipeline = wgpuDeviceCreateRenderPipeline(device, &pipelineDesc);
```
````

`````{note}
Since we will need to **use the pipeline later** on in `MainLoop()`, we need to define the `pipeline` variable as a **class attribute** in `Application.h`:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private:
	wgpu::RenderPipeline pipeline;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private:
	WGPURenderPipeline pipeline;
```
````
`````

If you have a look at its definition in `webpgu.h`, you'll see that the render pipeline descriptor has quite many fields. But don't worry, for this first triangle, we can leave a lot of them to their default values!

**WIP**

````{tab} With webgpu.hpp
```{lit} C++, Describe render pipeline
pipelineDesc.vertex.module = shaderModule;
pipelineDesc.vertex.entryPoint = StringView("vs_main");

FragmentState fragmentState = Default;
fragmentState.module = shaderModule;
fragmentState.entryPoint = StringView("fs_main");
ColorTargetState colorTarget = Default;
colorTarget.format = config.format;
BlendState blendState = Default;
colorTarget.blend = &blendState;
fragmentState.targetCount = 1;
fragmentState.targets = &colorTarget;
pipelineDesc.fragment = &fragmentState;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe render pipeline (for tangle root "Vanilla")
pipelineDesc.vertex.module = shaderModule;
pipelineDesc.vertex.entryPoint = toWgpuStringView("vs_main");

WGPUFragmentState fragmentState = WGPU_FRAGMENT_STATE_INIT;
fragmentState.module = shaderModule;
fragmentState.entryPoint = toWgpuStringView("fs_main");
WGPUColorTargetState colorTarget = WGPU_COLOR_TARGET_STATE_INIT;
colorTarget.format = config.format;
WGPUBlendState blendState = WGPU_BLEND_STATE_INIT;
colorTarget.blend = &blendState;
fragmentState.targetCount = 1;
fragmentState.targets = &colorTarget;
pipelineDesc.fragment = &fragmentState;
```
````

````{tab} With webgpu.hpp
```{lit} C++, Create Shader Module
ShaderSourceWGSL wgslDesc = Default;
wgslDesc.code = StringView(shaderSource);
ShaderModuleDescriptor shaderDesc = Default;
shaderDesc.label = StringView("Shader source from Application.cpp");
shaderDesc.nextInChain = &wgslDesc.chain;
ShaderModule shaderModule = device.createShaderModule(shaderDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Shader Module (for tangle root "Vanilla")
WGPUShaderSourceWGSL wgslDesc = WGPU_SHADER_SOURCE_WGSL_INIT;
wgslDesc.code = toWgpuStringView(shaderSource);
WGPUShaderModuleDescriptor shaderDesc = WGPU_SHADER_MODULE_DESCRIPTOR_INIT;
shaderDesc.label = toWgpuStringView("Shader source from Application.cpp");
shaderDesc.nextInChain = &wgslDesc.chain;
WGPUShaderModule shaderModule = wgpuDeviceCreateShaderModule(device, &shaderDesc);
```
````

````{tab} With webgpu.hpp
```{lit} C++, Initialize (append)
{{Create Shader Module}}
{{Create Render Pipeline}}
shaderModule.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Initialize (append, for tangle root "Vanilla")
{{Create Shader Module}}
{{Create Render Pipeline}}
wgpuShaderModuleRelease(shaderModule);
```
````

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
pipeline.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
wgpuRenderPipelineRelease(pipeline);
```
````

```{lit} C++, Use Render Pass (replace, also for tangle root "Vanilla")
{{Draw a triangle}}
```

```{lit} C++, Shader source (also for tangle root "Vanilla")
const char* shaderSource = R"(
@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> @builtin(position) vec4f {
	var p = vec2f(0.0, 0.0);
	if (in_vertex_index == 0u) {
		p = vec2f(-0.45, 0.5);
	} else if (in_vertex_index == 1u) {
		p = vec2f(0.45, 0.5);
	} else {
		p = vec2f(0.0, -0.5);
	}
	return vec4f(p, 0.0, 1.0);
}

@fragment
fn fs_main() -> @location(0) vec4f {
	return vec4f(0.0, 0.4, 0.7, 1.0);
}
)";
```

```{lit} C++, Application implementation (prepend, also for tangle root "Vanilla")
{{Shader source}}
```

```{figure} /images/hello-triangle/first-triangle.png
:align: center
:class: with-shadow
Our first triangle rendered using WebGPU.
```

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step030-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-next-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next-vanilla)
````
