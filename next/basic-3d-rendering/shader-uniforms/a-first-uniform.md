A first uniform <span class="bullet">🟢</span>
===============

```{lit-setup}
:tangle-root: 039 - A first uniform - Next - vanilla
:parent: 037 - Loading from file - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 039 - A first uniform - Next
:parent: 037 - Loading from file - Next
:debug:
```

````{tab} With webgpu.hpp
*Resulting code:* [`step039-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step039-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-vanilla-next)
````

Introduction
------------

### Motivation

If we look at our current shader, we see some **hard-coded** constants:

```rust
let ratio = 640.0 / 480.0;
let offset = vec2f(-0.6875, -0.463);
```

This is **not very satisfying**... what happens when we want to **move the object** during the execution of the application? Or **change the ratio** because the user resized the window?

> ☝️ We could dynamically change the shader code and rebuild a new shader module!

Nice try! It would kinda work, but **building a shader module takes time**. A lot of time, if we compare it to the budget for rendering a single frame (typically a 60th of a second). Imagine if we want to **animate** our scene and thus change the `offset` each frame!

This is why a proper solution is to use a **uniform variable**.

> ☝️ Ok, ok, I have a better idea: we could use a storage buffer to pass the ratio and offset!

We are indeed going to **use a buffer**, but with a **different usage** than `Storage`, one that is optimized for *uniform* access from all threads.

### Definition

A uniform is a global variable in a shader whose value is loaded from a GPU buffer and whose value is **uniform** across the different vertices and fragment of **a given call** to `draw`. It can nonetheless **change from one call to another** by updating the value of the buffer it is *bound* to.

To use a uniform, we need to:

 1. Declare the uniform in the **shader**.
 2. Create the **buffer** it is bound to.
 3. Configure the properties of the **binding** (a.k.a. the binding's **layout**).
 4. Create a **bind group**.

Shader side
-----------

In order to animate our scene, we create a uniform called `uTime` that we update each frame with the current time, expressed in seconds (as provided by `glfwGetTime()`).

```{note}
I usually **prefix** uniform variables with a 'u' so that it is easy to figure out when reading a long shader **when a variable is a uniform** rather than a local variable.
```

As I said, a uniform is a **global variable**, so we can declare it in the first line of our shader. A simple variable declaration in WGSL looks as follows:

```{lit} rust, Declare uniforms (also for tangle root "Vanilla")
// Simple variable declaration
var uTime: f32;
```

The `var` keyword can be labeled with an **address space**, which controls how the variable is stored in the GPU (see [Memory Model](/appendices/memory-model.md)). Here we state that the variable is stored in the *uniform* address space:

```{lit} rust, Declare uniforms (replace, also for tangle root "Vanilla")
// Variable in the *uniform* address space
var<uniform> uTime: f32;
```

Now we need to tell to which **buffer** the uniform is **bound**. Like we did with storage buffers in [*Our first shader*](../../getting-started/our-first-shader.md), this is done by specifying a **bind group** and **binding index** within this group using respectively the `@group(...)` and the `@binding(...)` WGSL attributes.

```{lit} rust, Declare uniforms (replace, also for tangle root "Vanilla")
// The memory location of the uniform is given by a pair of a *bind group* and a *binding*
@group(0) @binding(0)
var<uniform> uTime: f32;
```

```{note}
The line break after attributes is optional, we could write `@group(0) @binding(0) var<uniform> uTime: f32;` on a single line.
```

We are now done with the declaration of the uniform variable, we can use it like any other variable in our shader:

```{lit} rust, Shader prelude (append, also for tangle root "Vanilla")
// We add the declaration of 'uTime' to the shader prelude
{{Declare uniforms}}
```

```{lit} rust, Vertex shader (replace, also for tangle root "Vanilla")
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	let ratio = 640.0 / 480.0;

	// We now move the scene depending on the time!
	var offset = vec2f(-0.6875, -0.463);
	offset += 0.3 * vec2f(cos(uTime), sin(uTime));

	out.position = vec4f(in.position.x + offset.x, (in.position.y + offset.y) * ratio, 0.0, 1.0);
	out.color = in.color;
	return out;
}
```

```{hint}
If you are not familiar with the [trigonometric functions](https://en.wikipedia.org/wiki/Trigonometric_functions) like `cos` and `sin`, be aware that the position $(\cos(a), \sin(a))$ is the point on the circle of radius $1$ at angle $a$ (expressed in radians). Thus, this formula makes the triangles **move along a circle** over time. It is multiplied by $0.3$ in order to decrease the radius of this circle.
```

Uniform buffer
--------------

The uniform buffer is created like any other buffer, except we must specify `BufferUsage::Uniform` in its `usage` field. We only need it to contain 1 float for now, but **buffer size needs to be aligned to 16 bytes**, so we create a buffer of 4 floats (1 float uses 4 bytes).

We first declare our `m_uniformBuffer` in the `Application` class attributes:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // Application attributes
	wgpu::Buffer m_uniformBuffer = nullptr;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // Application attributes
	WGPUBuffer m_uniformBuffer = nullptr;
```
````

We then create the buffer during initialization:

````{tab} With webgpu.hpp
```{lit} C++, Create uniform buffer
// Create uniform buffer (reusing bufferDesc from other buffer creations)
// The buffer will only contain 1 float with the value of uTime
// then 3 floats left empty but needed by alignment constraints
bufferDesc.size = 4 * sizeof(float);

// Make sure to flag the buffer as BufferUsage::Uniform
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;

m_uniformBuffer = m_device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create uniform buffer (for tangle root "Vanilla")
// Create uniform buffer (reusing bufferDesc from other buffer creations)
// The buffer will only contain 1 float with the value of uTime
// then 3 floats left empty but needed by alignment constraints
bufferDesc.size = 4 * sizeof(float);

// Make sure to flag the buffer as BufferUsage::Uniform
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;

m_uniformBuffer = wgpuDeviceCreateBuffer(m_device, &bufferDesc);
```
````

Then use `Queue::writeBuffer` to upload a value in the first float of the buffer:

````{tab} With webgpu.hpp
```{lit} C++, Upload uniform values
float currentTime = 1.0f;
m_queue.writeBuffer(m_uniformBuffer, 0, &currentTime, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Upload uniform values (for tangle root "Vanilla")
float currentTime = 1.0f;
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, 0, &currentTime, sizeof(float));
```
````

To summarize, we put this at the end of `Application::InitializeBuffers()`:

```{lit} C++, InitializeBuffers method (replace, also for tangle root "Vanilla")
bool Application::InitializeBuffers() {
	// 1. Load from disk into CPU-side vectors pointData and indexData
	{{Load geometry data from file}}

	// 2. Create GPU buffers and upload data to them
	{{Create point buffer}}
	{{Create index buffer}}

	// 3. Create and fill uniform buffer <-- HERE
	{{Create uniform buffer}}
	{{Upload uniform values}}
	return true;
}
```

`````{note}
Do not forget to release these buffer in the `Terminate()` method:

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
m_uniformBuffer.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
wgpuBufferRelease(m_uniformBuffer);
```
````
`````

Binding configuration
---------------------

If you try to run your program now, you will hit a device error stating that some bind group referenced in the shader is **incompatible** with the expected bind group layout. What does this mean?

There are two steps in the actual connection of the buffer to the uniform. One is to **declare in the pipeline** that we want a binding, and how exactly. This is the binding **layout**. And the second one is to create the bind group and enable it (see next section).

```{note}
This follows the same spirit than the distinction between the *vertex buffer* and the *vertex buffer layout*.
```

### Pipeline layout

The binding layout is specified through the `PipelineLayout` part of the pipeline descriptor. The pipeline layout describes how all the **resources** used by the render pipeline must be bound.

A resource is either a texture or a buffer, and its layout specifies to which index it is bound to and properties like whether it is accessed as read-only or write-only, etc.

So far, we were **implicitly using an automatic layout** by setting `pipelineDesc.layout`, but from now on we will explicitly declare what resources our pipeline expects:

```{lit} C++, Describe render pipeline (append, also for tangle root "Vanilla")
{{Create pipeline layout}}

// Assign the PipelineLayout to the RenderPipelineDescriptor's layout field
pipelineDesc.layout = m_layout;
```

```{note}
In chapter [*Our first shader*](../../getting-started/our-first-shader.md), we were relying on the automatic layout generation, then used `ComputePipeline::getBindGroupLayout` to retrieve the layout when creating bind groups.

The main drawback of this approach is that **whenever a uniform variable is left unused**, it is then automatically removed from the layout, which requires to also change the bind group creation. By **manually managing layouts**, we can make sure that they do not change when we tweak the shader.
```

When creating a pipeline layout, we may define multiple **bind groups**, and a bind group contains multiple **bindings**:

````{tab} With webgpu.hpp
```{lit} C++, Create pipeline layout
{{Define bindingLayout}}

// Create a bind group layout
BindGroupLayoutDescriptor bindGroupLayoutDesc = Default;
bindGroupLayoutDesc.entryCount = 1;
bindGroupLayoutDesc.entries = &bindingLayout;
m_bindGroupLayout = m_device.createBindGroupLayout(bindGroupLayoutDesc);

// Create the pipeline layout
PipelineLayoutDescriptor layoutDesc = Default;
layoutDesc.bindGroupLayoutCount = 1;
layoutDesc.bindGroupLayouts = (const WGPUBindGroupLayout*)&m_bindGroupLayout;
m_layout = m_device.createPipelineLayout(layoutDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create pipeline layout (for tangle root "Vanilla")
{{Define bindingLayout}}

// Create a bind group layout
WGPUBindGroupLayoutDescriptor bindGroupLayoutDesc = WGPU_BIND_GROUP_LAYOUT_DESCRIPTOR_INIT;
bindGroupLayoutDesc.nextInChain = nullptr;
bindGroupLayoutDesc.entryCount = 1;
bindGroupLayoutDesc.entries = &bindingLayout;
m_bindGroupLayout = wgpuDeviceCreateBindGroupLayout(m_device, &bindGroupLayoutDesc);

// Create the pipeline layout
WGPUPipelineLayoutDescriptor layoutDesc = WGPU_PIPELINE_LAYOUT_DESCRIPTOR_INIT;
layoutDesc.nextInChain = nullptr;
layoutDesc.bindGroupLayoutCount = 1;
layoutDesc.bindGroupLayouts = &m_bindGroupLayout;
m_layout = wgpuDeviceCreatePipelineLayout(m_device, &layoutDesc);
```
````

Importantly, like any object created with a `createSomething` procedure, layouts **must be released** once we no longer use them. Hence we define them as class attributes.

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // Application attributes
	wgpu::PipelineLayout m_layout = nullptr;
	wgpu::BindGroupLayout m_bindGroupLayout = nullptr;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // Application attributes
	WGPUPipelineLayout m_layout = nullptr;
	WGPUBindGroupLayout m_bindGroupLayout = nullptr;
```
````

We can then release them in `Application::Terminate()`:

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
m_layout.release();
m_bindGroupLayout.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
wgpuPipelineLayoutRelease(m_layout);
wgpuBindGroupLayoutRelease(m_bindGroupLayout);
```
````

Retaining `m_bindGroupLayout` is also needed when we create the bind group that goes with it.

### Binding layout

The `BindGroupLayoutEntry` could have been called `BindingLayout`. The first setting is the binding index, as used in the shader's `@binding` attribute. Then the `visibility` field tells which stage requires access to this resource, so that it is not needlessly provided to all stages.

````{tab} With webgpu.hpp
```{lit} C++, Define bindingLayout
// Define binding layout (don't forget to = Default)
BindGroupLayoutEntry bindingLayout = Default;

// The binding index as used in the @binding attribute in the shader
bindingLayout.binding = 0;

// The stage that needs to access this resource
bindingLayout.visibility = ShaderStage::Vertex;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Define bindingLayout (for tangle root "Vanilla")
// Define binding layout
WGPUBindGroupLayoutEntry bindingLayout = WGPU_BIND_GROUP_LAYOUT_ENTRY_INIT;

// The binding index as used in the @binding attribute in the shader
bindingLayout.binding = 0;

// The stage that needs to access this resource
bindingLayout.visibility = WGPUShaderStage_Vertex;
```
````

The remaining of the binding layout depends on the type of resource. We fill either the `buffer` field or the `sampler` and `texture` fields or the `storageTexture` field. In our case it is a buffer:

````{tab} With webgpu.hpp
```{lit} C++, Define bindingLayout (append)
bindingLayout.buffer.type = BufferBindingType::Uniform;
bindingLayout.buffer.minBindingSize = 4 * sizeof(float);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Define bindingLayout (append, for tangle root "Vanilla")
bindingLayout.buffer.type = WGPUBufferBindingType_Uniform;
bindingLayout.buffer.minBindingSize = 4 * sizeof(float);
```
````

```{important}
Notice how I initialized the binding layout object with `= Default` or `WGPU_BIND_GROUP_LAYOUT_ENTRY_INIT` above. It is important because it sets in particular the `buffer`, `sampler`, `texture` and `storageTexture` uses to `BindingNotUsed` so that only the resource type we set up is used.
```

Bind group
----------

### Creation

A bind group contains **the actual bindings**. Indeed, in the layout we told the pipeline that it should expect a uniform, but we did not actually give the uniform buffer object itself.

The structure of a bind group mirrors the bind group layout prescribed in the render pipeline and actually connects it to resources. This way, the **same pipeline** can be reused as is in **multiple draw calls** depending on different variants of the resources.

The bind group is again an object that we want to keep after initialization (we use it in the main loop), so we declare it at the **class level**:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // Application attributes
	wgpu::BindGroup m_bindGroup = nullptr;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // Application attributes
	WGPUBindGroup m_bindGroup = nullptr;
```
````

A bind group must follow the same structure as its layout:

````{tab} With webgpu.hpp
```{lit} C++, Create bind group
// Create a binding
BindGroupEntry binding = Default;
{{Setup binding}}

// A bind group contains one or multiple bindings
BindGroupDescriptor bindGroupDesc = Default;
bindGroupDesc.layout = m_bindGroupLayout;
// There must be as many bindings as declared in the layout!
bindGroupDesc.entryCount = 1;
bindGroupDesc.entries = &binding;
m_bindGroup = m_device.createBindGroup(bindGroupDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create bind group (for tangle root "Vanilla")
// Create a binding
WGPUBindGroupEntry binding = WGPU_BIND_GROUP_ENTRY_INIT;
{{Setup binding}}

// A bind group contains one or multiple bindings
WGPUBindGroupDescriptor bindGroupDesc = WGPU_BIND_GROUP_DESCRIPTOR_INIT;
bindGroupDesc.layout = m_bindGroupLayout;
// There must be as many bindings as declared in the layout!
bindGroupDesc.entryCount = 1;
bindGroupDesc.entries = &binding;
m_bindGroup = wgpuDeviceCreateBindGroup(m_device, &bindGroupDesc);
```
````

And we release the bind group in `Application::Terminate()`:

````{tab} With webgpu.hpp
```{lit} C++, Terminate (prepend)
m_bindGroup.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Terminate (prepend, for tangle root "Vanilla")
wgpuBindGroupRelease(m_bindGroup);
```
````

The content of the binding itself is quite straightforward:

```{lit} C++, Setup binding (also for tangle root "Vanilla")
// The index of the binding (the entries in bindGroupDesc can be in any order)
binding.binding = 0;
// The buffer it is actually bound to
binding.buffer = m_uniformBuffer;
// We can specify an offset within the buffer, so that a single buffer can hold
// multiple uniform blocks.
binding.offset = 0;
// And we specify again the size of the buffer.
binding.size = 4 * sizeof(float);
```

```{note}
The fields `binding.sampler` and `binding.textureView` are only needed when the binding layout uses them.
```

Note that unlike the creation of the bind group **layout**, the creation of the bind group must come **after the creation of the resources** that it binds! I thus suggest we introduce a new initialization method:

```{lit} C++, InitializeBindGroups method (also for tangle root "Vanilla")
void Application::InitializeBindGroups() {
	{{Create bind group}}
}
```

```{lit} C++, Application implementation (append, hidden, also for tangle root "Vanilla")
// Add this in the main file
{{InitializeBindGroups method}}
```

As usual, we declare the method in the application declaration:

```{lit} C++, Private methods (append, also for tangle root "Vanilla")
private: // Application methods
	void InitializeBindGroups();
```

And we initialize the bind group **after** everything else:

```{lit} C++, Initialize (append, also for tangle root "Vanilla")
// At the end of Initialize()
InitializeBindGroups();
```

### Usage

Okay, we are now ready to connect the dots! It is as simple as setting the bind group to use **before the draw call**, in `Application::MainLoop()`:

````{tab} With webgpu.hpp
```{lit} C++, Use Render Pass (replace)
renderPass.setPipeline(m_pipeline);
renderPass.setVertexBuffer(0, m_pointBuffer, 0, m_pointBuffer.getSize());
renderPass.setIndexBuffer(m_indexBuffer, IndexFormat::Uint16, 0, m_indexBuffer.getSize());

// Set binding group here!
renderPass.setBindGroup(0, m_bindGroup, 0, nullptr);

renderPass.drawIndexed(m_indexCount, 1, 0, 0, 0);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Use Render Pass (replace, for tangle root "Vanilla")
wgpuRenderPassEncoderSetPipeline(renderPass, m_pipeline);
wgpuRenderPassEncoderSetVertexBuffer(renderPass, 0, m_pointBuffer, 0, wgpuBufferGetSize(m_pointBuffer));
wgpuRenderPassEncoderSetIndexBuffer(renderPass, m_indexBuffer, WGPUIndexFormat_Uint16, 0, wgpuBufferGetSize(m_indexBuffer));

// Set binding group here!
wgpuRenderPassEncoderSetBindGroup(renderPass, 0, m_bindGroup, 0, nullptr);

wgpuRenderPassEncoderDrawIndexed(renderPass, m_indexCount, 1, 0, 0, 0);
```
````

It should be working already, though not moving because the content of the uniform buffer **does not change yet**. What we need is to update them in the main loop:

We place this for instance at the beginning of `Application::MainLoop()`:

````{tab} With webgpu.hpp
```{lit} C++, Update uniform buffer
// Right after wgpuInstanceProcessEvents():
// Update uniform buffer
float t = static_cast<float>(glfwGetTime()); // glfwGetTime returns a double
m_queue.writeBuffer(m_uniformBuffer, 0, &t, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Update uniform buffer (for tangle root "Vanilla")
// Right after wgpuInstanceProcessEvents():
// Update uniform buffer
float t = static_cast<float>(glfwGetTime()); // glfwGetTime returns a double
wgpuQueueWriteBuffer(m_queue, m_uniformBuffer, 0, &t, sizeof(float));
```
````

```{lit} C++, Main loop content (hidden, prepend, also for tangle root "Vanilla")
{{Update uniform buffer}}
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/turning-webgpu-logo.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Our first dynamic scene!</span></p>
	</figcaption>
</figure>


Device limits
-------------

When using uniforms, two new device limits may be hit:

### Maximum uniform buffers

Limit `maxUniformBuffersPerShaderStage` is the maximum number of buffers that we can use (default: **12**). We will see in the next chapter that it does not really limit the number of variables because we can put a whole `struct` in a uniform binding.

### Maximum uniform buffer size

The maximum byte size of a given uniform buffer is given by the limit `maxUniformBufferBindingSize`. Its default value is **65536 bytes** but I **don't** think you want to **go anywhere near this limit**: if your buffer grows that much, your thread probably don't uniformly access its content, so you may want to switch to a storage buffer.

Conclusion
----------

Congratulation, we have our **first dynamic scene**! And we introduced important concepts a the API:

- **Uniform variables**, which are better cached than storage buffers when all parallel threads of the shader access them uniformly.
- **Pipeline layout**, how to manage them manually for better flexibility.

In the next chapter, we will generalize what we saw here by introducing **a second uniform** (and I guess you'll figure how to generalize further).

````{tab} With webgpu.hpp
*Resulting code:* [`step039-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step039-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step039-vanilla-next)
````
