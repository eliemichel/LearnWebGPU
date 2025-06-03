Hello Triangle <span class="bullet">🟢</span>
==============

```{lit-setup}
:tangle-root: 030 - Hello Triangle - Next - vanilla
:parent: 025 - First Color - Next
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 030 - Hello Triangle - Next
:parent: 028 - C++ Wrapper - Next
```

````{tab} With webgpu.hpp
*Resulting code:* [`step030-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-vanilla-next)
````

In this chapter, we finally see how to **draw something** on the screen! And by **something**, I mean triangles, because... all the GPU can draw is triangles. Rest assured, we can do **a lot** with triangles.

In its core, **drawing a triangle** is as simple as this:

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

But of course there is some configuration to set up around this. We see in this chapter a very minimal example of **render pipeline**. This is more complex than the basic compute pipeline that we have introduced in chapter [*Our first shader*](../getting-started/our-first-shader.md) because it has **more stages**, but also shares some mechanisms like the creation of the creation of **shaders**.

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
m_pipeline = m_device.createRenderPipeline(pipelineDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Render Pipeline (for tangle root "Vanilla")
WGPURenderPipelineDescriptor pipelineDesc = WGPU_RENDER_PIPELINE_DESCRIPTOR_INIT;
{{Describe render pipeline}}
m_pipeline = wgpuDeviceCreateRenderPipeline(m_device, &pipelineDesc);
```
````

`````{note}
Since we will need to **use the pipeline later** on in `MainLoop()`, we need to define the `m_pipeline` variable as a **class attribute** in `Application.h` (hence the `m_` prefix):

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private:
	wgpu::RenderPipeline m_pipeline = nullptr;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private:
	WGPURenderPipeline m_pipeline = nullptr;
```
````

And we release this in the `Terminate()` function:

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
m_pipeline.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
wgpuRenderPipelineRelease(m_pipeline);
```
````
`````

If you have a look at definition of `WGPURenderPipelineDescriptor` in `webpgu.h`, you'll see that the render pipeline descriptor has quite **many fields**. But don't worry! For this first triangle, we can **leave a lot of them to their default values**.

In fact, we only need to configure the **vertex** and the **fragment** stages. Since both of these use a **shader module** to specify their **programmable** part, we start with that.

Shader module
-------------

Since the render pipeline descriptor needs the shader module, we **create this shader module** before:

````{tab} With webgpu.hpp
```{lit} C++, Initialize pipeline
// In Initialize() or in a dedicated InitializePipeline()
{{Create Shader Module}}
{{Create Render Pipeline}}
shaderModule.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Initialize pipeline (for tangle root "Vanilla")
// In Initialize() or in a dedicated InitializePipeline()
{{Create Shader Module}}
{{Create Render Pipeline}}
wgpuShaderModuleRelease(shaderModule);
```
````

```{note}
As you can see, we **release the shader module** as soon as the pipeline is created. We will no longer need it and the pipeline object retains whatever it needs from this module.
```

Similarly to what we did in chapter [*Our first shader*](../getting-started/our-first-shader.md), we place our **shader source** in a literal at the beginning of `Application.cpp`:

```{lit} C++, Shader source literal (also for tangle root "Vanilla")
const char* shaderSource = R"(
{{The WGSL shader source code}}
)";
```

```{lit} C++, Application implementation (prepend, hidden, also for tangle root "Vanilla")
{{Shader source literal}}
```

We then **create the shader module**, providing this WGSL source code through the `WGPUShaderSourceWGSL` **chained extension** of the `WGPUShaderModuleDescriptor`:

````{tab} With webgpu.hpp
```{lit} C++, Create Shader Module
ShaderSourceWGSL wgslDesc = Default;
wgslDesc.code = StringView(shaderSource);
ShaderModuleDescriptor shaderDesc = Default;
shaderDesc.nextInChain = &wgslDesc.chain; // connect the chained extension
shaderDesc.label = StringView("Shader source from Application.cpp");
ShaderModule shaderModule = m_device.createShaderModule(shaderDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Shader Module (for tangle root "Vanilla")
WGPUShaderSourceWGSL wgslDesc = WGPU_SHADER_SOURCE_WGSL_INIT;
wgslDesc.code = toWgpuStringView(shaderSource);
WGPUShaderModuleDescriptor shaderDesc = WGPU_SHADER_MODULE_DESCRIPTOR_INIT;
shaderDesc.nextInChain = &wgslDesc.chain; // connect the chained extension
shaderDesc.label = toWgpuStringView("Shader source from Application.cpp");
WGPUShaderModule shaderModule = wgpuDeviceCreateShaderModule(m_device, &shaderDesc);
```
````

Vertex stage
------------

### Vertex state descriptor

The vertex stage is configured through the **vertex state** structure, accessible at `pipelineDesc.vertex`. The only thing we need to provide here is the **vertex shader**, which is given by a pair of:

1. A **shader module**, which contains the actual code of the shader.
2. An **entry point**, which is the name of the function in the shader module that must be called for each vertex. This enables a given shader module to include entry points for multiple render pipeline configurations at the same time. In particular, we use the **same module** for the **vertex and fragment** shaders.

````{tab} With webgpu.hpp
```{lit} C++, Describe render pipeline
pipelineDesc.vertex.module = shaderModule;
pipelineDesc.vertex.entryPoint = StringView("vs_main");
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe render pipeline (for tangle root "Vanilla")
pipelineDesc.vertex.module = shaderModule;
pipelineDesc.vertex.entryPoint = toWgpuStringView("vs_main");
```
````

### Vertex shader

As a reminder, the shader is written in a dedicated programming language, namely [WGSL](https://gpuweb.github.io/gpuweb/wgsl/).

The content of our first **vertex shader** consists in defining a function `vs_main`, which we advertised above as the name of our **entry point**:

```{lit} rust, The WGSL shader source code (also for tangle root "Vanilla")
@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> @builtin(position) vec4f {
	if (in_vertex_index == 0u) {
		return vec4f(-0.45, 0.5, 0.0, 1.0);
	} else if (in_vertex_index == 1u) {
		return vec4f(0.45, 0.5, 0.0, 1.0);
	} else {
		return vec4f(0.0, -0.5, 0.0, 1.0);
	}
}
```

To be used as an entry point of the vertex shader, a function must be marked with **the `@vertex` attribute**.

```{note}
Contrary to the compute shader, the choice of the **workgroup size is left up to the pipeline**. No need for a `@workgroup_size` attribute like when we used `@compute`.
```

We also use again the `@builtin` attribute, but the **available [builtin inputs/outputs](https://www.w3.org/TR/WGSL/#builtin-inputs-outputs) depend on the stage**.

For instance, `@builtin(vertex_index)` tells that the argument `in_vertex_index` will be populated by the **built-in** input vertex attribute that is the **vertex index**.

```{tip}
The argument `in_vertex_index` could have had any other name: as long as it is decorated with the same built-in attribute, it has the same **semantics**.
```

We use this **vertex index** to set the output value of the shader. This output is labelled with the `@builtin(position)` attribute to mean that it must be **interpreted by the rasterizer** as the vertex position.

The `position` builtin output of the vertex shader **must be** a `vec4f` value. The $x$ and $y$ components correspond to the **screen position** in range $(-1, 1)$. The $z$ component tells the **depth** of the vertex (in range $(0, 1)$) and is used to **resolve overlaps** when a depth buffer is set up. And the fourth $w$ component is used to encode projections, but we leave it to to $1$ for now.

Rasterization
-------------

The **rasterization** is the very heart ❤️ of the 3D rendering algorithm implemented by a GPU. It transforms a **primitive** (a point, a line or a triangle) into a series of **fragments**, that correspond to the pixels covered by the primitive. It **interpolates** any extra attribute output by the vertex shader, such that each fragment receives a value for all attributes.

We **leave its configuration to the default**, but I still think that it is worth having a look at some of its configuration options, which lie in `pipelineDesc.primitive`:

````{tab} With webgpu.hpp
```{lit} C++, Describe primitive pipeline state
// NB: This is optional, it corresponds to the default values

// Each sequence of 3 vertices is considered as a triangle
pipelineDesc.primitive.topology = PrimitiveTopology::TriangleList;

// We'll see later how to specify the order in which vertices should be
// connected. When not specified, vertices are considered sequentially.
pipelineDesc.primitive.stripIndexFormat = IndexFormat::Undefined;

// The face orientation is defined by assuming that when looking
// from the front of the face, its corner vertices are enumerated
// in the counter-clockwise (CCW) order.
pipelineDesc.primitive.frontFace = FrontFace::CCW;

// But the face orientation does not matter much because we do not
// cull (i.e. "hide") the faces pointing away from us (which is often
// used for optimization).
pipelineDesc.primitive.cullMode = CullMode::None;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe primitive pipeline state (for tangle root "Vanilla")
// NB: This is optional, it corresponds to the default values

// Each sequence of 3 vertices is considered as a triangle
pipelineDesc.primitive.topology = WGPUPrimitiveTopology_TriangleList;

// We'll see later how to specify the order in which vertices should be
// connected. When not specified, vertices are considered sequentially.
pipelineDesc.primitive.stripIndexFormat = WGPUIndexFormat_Undefined;

// The face orientation is defined by assuming that when looking
// from the front of the face, its corner vertices are enumerated
// in the counter-clockwise (CCW) order.
pipelineDesc.primitive.frontFace = WGPUFrontFace_CCW;

// But the face orientation does not matter much because we do not
// cull (i.e. "hide") the faces pointing away from us (which is often
// used for optimization).
pipelineDesc.primitive.cullMode = WGPUCullMode_None;
```
````

```{note}
It is common to set the **cull mode** to `Front` to avoid wasting resources in rendering the inside of objects. But for beginners it **can be very frustrating** to see nothing on screen for hours only to discover that the triangle was just facing in the wrong direction, so I advise you to leave it to `None` when **developing**.
```

Fragment stage
--------------

After the rasterization stage, we are left with many **fragments** (as many fragments as there are overlapping pairs of pixels and triangle). The pipeline does 2 things with these fragments:

1. It runs a **programmable fragment shader**.
2. It **blends** the resulting fragment colors into the **render target**.

```{note}
Fragments might also be **discarded** by the stencil and depth test mechanisms, which we will introduce later on.
```

### Fragment shader

The main responsibility of the fragment shader is to tell **what color** it has, given input information coming from the vertex stage through the rasterizer. We will do very simple here, with just a **solid color**:

```{lit} rust, The WGSL shader source code (append, also for tangle root "Vanilla")
// Add this in the same shaderSource literal than the vertex entry point
@fragment
fn fs_main() -> @location(0) vec4f {
	return vec4f(0.0, 0.4, 0.7, 1.0);
}
```

This time, we specify the `@fragment` attribute to mean that this is a fragment shader entry point, and we introduce a **new attribute**, namely `@location`.

This `@location` attribute is used for the input/output of the render pipeline, and here it simply means that the returned color (`vec4f` for red, green, blue, alpha) must be written into the **first color attachment** of the render pass (see chapter [First Color](../getting-started/first-color.md)).

### Fragment state descriptor

The fragment stage is **optional** (although very common), so its state is provided to the pipeline descriptor through a nullable pointer:

````{tab} With webgpu.hpp
```{lit} C++, Describe render pipeline (append)
FragmentState fragmentState = Default;
{{Describe fragment state}}
pipelineDesc.fragment = &fragmentState;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe render pipeline (append, for tangle root "Vanilla")
WGPUFragmentState fragmentState = WGPU_FRAGMENT_STATE_INIT;
{{Describe fragment state}}
pipelineDesc.fragment = &fragmentState;
```
````

The first things that we can set up is the **shader module and entry point**:

````{tab} With webgpu.hpp
```{lit} C++, Describe fragment state
fragmentState.module = shaderModule;
fragmentState.entryPoint = StringView("fs_main");
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe fragment state (for tangle root "Vanilla")
fragmentState.module = shaderModule;
fragmentState.entryPoint = toWgpuStringView("fs_main");
```
````

Then comes the configuration of **blending** into **color targets**, which is a fixed-function part of the pipeline. We must describe a **target** for each **attachment** of the **render pass** (i.e., each texture written by the pipeline).

Again, in our case we only have one target, but there could be more, hence the pair `targets`/`targetCount` to pass an **array of targets**:

````{tab} With webgpu.hpp
```{lit} C++, Describe fragment state (append)
ColorTargetState colorTarget = Default;
{{Describe color target state}}
fragmentState.targetCount = 1;
fragmentState.targets = &colorTarget;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe fragment state (append, for tangle root "Vanilla")
WGPUColorTargetState colorTarget = WGPU_COLOR_TARGET_STATE_INIT;
{{Describe color target state}}
fragmentState.targetCount = 1;
fragmentState.targets = &colorTarget;
```
````

We need to specify 2 aspects of the color target state:

**1.** The expected **texture format** of the render pass attachment. For this, we store the `config.format` from the **surface configuration** into an attribute `m_surfaceFormat` and reuse it here:

```{lit} C++, Describe color target state (also for tangle root "Vanilla")
colorTarget.format = m_surfaceFormat;
```

`````{admonition} Details about the surface format attribute
:class: foldable

We add the `m_surfaceFormat` class attribute:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // In Application.h
	wgpu::TextureFormat m_surfaceFormat = wgpu::TextureFormat::Undefined;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // In Application.h
	WGPUTextureFormat m_surfaceFormat = WGPUTextureFormat_Undefined;
```
````

And after building the surface configuration, we store its format:

```{lit} C++, Surface Configuration (append, also for tangle root "Vanilla")
m_surfaceFormat = config.format;
```
`````

**2.** We must enable fragment blending through the nullable `colorTarget.blend`:

````{tab} With webgpu.hpp
```{lit} C++, Describe color target state (append)
BlendState blendState = Default;
colorTarget.blend = &blendState;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe color target state (append, for tangle root "Vanilla")
WGPUBlendState blendState = WGPU_BLEND_STATE_INIT;
colorTarget.blend = &blendState;
```
````

The `WGPUBlendState` describes the **formula** that blends the **fragment color** with the **existing texture** color. Its **default value** is fine, but we still need to specify one because blending is **disabled by default**.

Wrapping up
-----------

### Dedicated method

We could place everything in the `Initialize()` function, but it would end up being very long. Instead, I suggest we create a dedicated `InitializePipeline()` method, which we simply call in `Initialize()`:

```{lit} C++, Initialize (append, also for tangle root "Vanilla")
// At the end of Initialize()
if (!InitializePipeline()) return false;
```

```{note}
I will have all initialization methods **return a boolean status** so that they can **signal initialization failure**. We could also use **C++ exceptions** for this, or use a more complex object than a boolean to carry extra information about the failure.
```

We then declare this method in `Application.h`:

```{lit} C++, Private methods (append, also for tangle root "Vanilla")
// In Application.h
private:
    bool InitializePipeline();
```

And implement it in `Application.cpp`:

```{lit} C++, InitializePipeline method (also for tangle root "Vanilla")
bool Application::InitializePipeline() {
    {{Initialize pipeline}}
    return true;
}
```

```{lit} C++, Application implementation (append, hidden, also for tangle root "Vanilla")
{{InitializePipeline method}}
```

### Drawing the triangle

We are almost there! All we have to do is run our render pipeline in the `MainLoop()`, within the **render pass** that we have left empty in chapter [First Color](../getting-started/first-color.md):

````{tab} With webgpu.hpp
```{lit} C++, Draw a triangle (replace)
// [...] Begin render pass
// Select which render pipeline to use
renderPass.setPipeline(m_pipeline);
// Draw 1 instance of a 3-vertices shape
renderPass.draw(3, 1, 0, 0);
// [...] End render pass
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Draw a triangle (replace, for tangle root "Vanilla")
// [...] Begin render pass
// Select which render pipeline to use
wgpuRenderPassEncoderSetPipeline(renderPass, m_pipeline);
// Draw 1 instance of a 3-vertices shape
wgpuRenderPassEncoderDraw(renderPass, 3, 1, 0, 0);
// [...] End render pass
```
````

```{lit} C++, Use Render Pass (replace, hidden, also for tangle root "Vanilla")
{{Draw a triangle}}
```

```{note}
Only pay attention to the **first argument** of `renderPass.draw`/`wgpuRenderPassEncoderDraw` for now. This argument is the **number of vertices** that we want to draw.
```

And tadaam! You should finally see **a triangle**!

```{figure} /images/hello-triangle/first-triangle.png
:align: center
:class: with-shadow
Our first triangle rendered using WebGPU.
```

Conclusion
----------

This chapter introduced the **core skeleton** for rendering triangle-based shapes on the GPU. For now these are 2D graphics, but once everything will be in place, switching to 3D will be straightforward. We have seen two very important concepts:

 - The **render pipeline**, which is based on the way the hardware actually works, with some parts fixed, for the sake of efficiency, and some parts are programmable.
 - The **shaders**, which are the GPU-side programs driving the programmable stages of the pipeline.

### What's next?

The key algorithms and techniques of computer graphics used for 3D rendering are for a large part implemented in the shaders code. What we still miss at this point though is ways to **communicate** between the C++ code (CPU) and the shaders (GPU).

The next two chapters focus on two ways to **feed input** to this render pipeline: **vertex** attributes, where there is one value per vertex, and **uniforms**, which define variable that are common to all vertices and fragments for a given call.

We then take a break away from pipeline things with the switch to **3D meshes**, which is in the end less about code and more about math. We also introduce a bit of **interaction** with a basic **camera controller**. We then introduce a 3rd way to provide input resource, namely **textures**, and how to map them onto meshes.

Storage textures, which are used the other way around, to get data out of the render pipeline, will be presented only in advanced chapters. Instead, the last chapter of this section is fully dedicated to the computer graphics matter of **lighting** and **material modeling**.

````{tab} With webgpu.hpp
*Resulting code:* [`step030-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-vanilla-next)
````
