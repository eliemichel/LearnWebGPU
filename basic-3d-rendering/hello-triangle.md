Hello Triangle
==============

*Resulting code:* [`step030`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030)

In its overall outline, drawing a triangle is as simple as this:

```C++
// Configure the render pipeline
renderPass.setPipeline(pipeline);
// Draw 1 instance of a 3-vertices shape
renderPass.draw(3, 1, 0, 0);
```

What is a bit verbose is the configuration of the pipeline, and the creation of *shaders*.

Render Pipeline
---------------

TODO *Fixed pipeline* Configured through states and shaders

This is the *Render Pipeline* abstraction used by WebGPU:

![The Render Pipeline abstraction used by WebGPU](/images/render-pipeline.png)

```C++
RenderPipelineDescriptor pipelineDesc{};
// [...] Describe render pipeline
RenderPipeline pipeline = device.createRenderPipeline(pipelineDesc);
```

```{note}
If you are familiar with OpenGL, you can see WebGPU's render pipeline as a memorized value for all the stateful functions used to configure the rasterization pipeline.
```

```C++
PipelineLayoutDescriptor layoutDesc{};
layoutDesc.bindGroupLayoutCount = 0;
layoutDesc.bindGroupLayouts = nullptr;
PipelineLayout layout = device.createPipelineLayout(layoutDesc);

pipelineDesc.layout = layout;
```

### Vertex pipeline state

TODO **Fetch**

```C++
pipelineDesc.vertex.bufferCount = 0;
pipelineDesc.vertex.buffers = nullptr;
```

TODO **Shader**

```C++
pipelineDesc.vertex.module = shaderModule;
pipelineDesc.vertex.entryPoint = "vs_main";
pipelineDesc.vertex.constantCount = 0;
pipelineDesc.vertex.constants = nullptr;
```

The `shaderModule` will be defined in the next section.

### Primitive pipeline state

TODO assembly and rasterization

```C++
pipelineDesc.primitive.topology = PrimitiveTopology::TriangleList;
pipelineDesc.primitive.stripIndexFormat = IndexFormat::Undefined;
pipelineDesc.primitive.frontFace = FrontFace::CCW;
pipelineDesc.primitive.cullMode = CullMode::None;
```

```{note}
Usually we set the cull mode to `Front` to avoid wasting resources in rendering the inside of objects. But for beginners it can be very frustrating to see nothing on screen for hours only to discover that the triangle was just facing in the wrong direction, so I advise you to set it to `None` when developing.
```

### Fragment shader

```C++
FragmentState fragmentState{};
fragmentState.module = shaderModule;
fragmentState.entryPoint = "fs_main";
fragmentState.constantCount = 0;
fragmentState.constants = nullptr;

pipelineDesc.fragment = &fragmentState;
```

### Stencil/Depth state

```C++
pipelineDesc.depthStencil = nullptr;
```

### Blending

```C++
BlendState blendState{};
blendState.color.srcFactor = BlendFactor::One;
blendState.color.dstFactor = BlendFactor::Zero;
blendState.color.operation = BlendOperation::Add;
blendState.alpha.srcFactor = BlendFactor::SrcAlpha;
blendState.alpha.dstFactor = BlendFactor::OneMinusSrcAlpha;
blendState.alpha.operation = BlendOperation::Add;
ColorTargetState colorTarget{};
colorTarget.format = swapChainFormat;
colorTarget.blend = &blendState;
colorTarget.writeMask = ColorWriteMask::All;

fragmentState.targetCount = 1;
fragmentState.targets = &colorTarget;
```

```C++
pipelineDesc.multisample.count = 1;
pipelineDesc.multisample.mask = ~0u; // meaning "all bits on"
pipelineDesc.multisample.alphaToCoverageEnabled = false;
```

Shaders
-------

TODO As always:

```C++
ShaderModuleDescriptor shaderDesc{};
// [...] Describe shader module
ShaderModule shaderModule = device.createShaderModule(shaderDesc);
```

TODO For once, we use the `nextInChain` extension mechanism.

```C++
ShaderModuleWGSLDescriptor shaderCodeDesc{};
shaderCodeDesc.chain.next = nullptr;
shaderCodeDesc.chain.sType = SType::ShaderModuleWGSLDescriptor;
shaderCodeDesc.code = shaderSource;
shaderDesc.nextInChain = reinterpret_cast<ChainedStruct*>(&shaderCodeDesc);
```

```C++
shaderDesc.hintCount = 0;
shaderDesc.hints = nullptr;
```

```C++
const char* shaderSource = R"(
[...] The WGSL shader source code
)";
```

TODO ![WGSL](https://gpuweb.github.io/gpuweb/wgsl/), the WebGPU Shading Language.

```wgsl
@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> @builtin(position) vec4<f32> {
	if (in_vertex_index == 0u) {
		return vec4<f32>(-0.5, -0.5, 0.0, 1.0);
	} else if (in_vertex_index == 1u) {
		return vec4<f32>(0.5, -0.5, 0.0, 1.0);
	} else {
		return vec4<f32>(0.0, 0.5, 0.0, 1.0);
	}
}

@fragment
fn fs_main() -> @location(0) vec4<f32> {
    return vec4<f32>(0.0, 0.4, 1.0, 1.0);
}
```

Conclusion
----------

![First rendered triangle](/images/hello-triangle.png)

*Resulting code:* [`step030`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030)
