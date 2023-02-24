Compute Pipeline (WIP)
================

````{tab} With webgpu.hpp
*Resulting code:* [`step200`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step200)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step200-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step200-vanilla)
````

Rendering 3D data is the original use of GPUs, but it is far from being the only one nowadays. And even for 3D application, we sometimes use the GPU for non-rendering things, such as simulation, image processing, etc.

When using the GPU for **general purpose** computation (GPGPU), we usually **do not need to call the 3D-specific fixed parts** of the render pipeline, like the rasterization.

This chapter introduces the skeleton for running **compute shaders**, which are shaders ran outside of the fixed-function pipeline.

Compute Pass
------------

Remember how we drew [our first color](../getting-started/first-color.md), we submitted to the command queue a particular render-specific sequence of instructions called a `RenderPass`. The approach to run compute-only shaders is similar, and uses a `ComputePass` instead.

For the sake of the examples throughout this chapter, we create a `computeStuff` function that we call once at the end of `onInit`. You may also remove the main loop is `main.cpp` because we won't need the interactive part.

We reuse the same outline as when submitting our render pass on `onFrame`:

```C++
void Application::computeStuff() {
	// Initialize a command encoder
	Queue queue = m_device.getQueue();
	CommandEncoderDescriptor encoderDesc = Default;
	CommandEncoder encoder = m_device.createCommandEncoder(encoderDesc);

	// Create and use compute pass here!

	// Encode and submit the GPU commands
	CommandBuffer commands = encoder.finish(CommandBufferDescriptor{});
	queue.submit(commands);
}
```

The creation of the compute pass is **much simpler** than the one of the render pass, because since we do **not use any fixed-function stage**, there is almost nothing to configure! The only option if the timestamp writes that will be described in the benchmarking chapter.

```C++
// Create compute pass
ComputePassDescriptor computePassDesc;
computePassDesc.timestampWriteCount = 0;
computePassDesc.timestampWrites = nullptr;
ComputePassEncoder computePass = encoder.beginComputePass(computePassDesc);

// Use compute pass

// Finalize compute pass
computePass.end();
```

Compute pipeline
----------------

Once created, the use of the compute pass looks a lot like the use of the render pass. The main difference is that `draw` is replaced by `dispatchWorkgroups`, which calls our compute shader, and there is no such thing as a vertex buffer.

```C++
// Use compute pass
computePass.setPipeline(computePipeline);
computePass.setBindGroup(/* ... */);
computePass.dispatchWorkgroups(/* ... */);
```

The compute pipeline mainly defines the shader to be used. It also defines a layout for bind groups, but let us start simple:

```C++
// Load compute shader
ShaderModule computeShaderModule = ResourceManager::loadShaderModule(RESOURCE_DIR "/compute-shader.wsl", m_device);

// Create compute pipeline
ComputePipelineDescriptor computePipelineDesc;
computePipelineDesc.compute.constantCount = 0;
computePipelineDesc.compute.constants = nullptr;
computePipelineDesc.compute.entryPoint = "computeStuff";
computePipelineDesc.compute.module = computeShaderModule;
computePipelineDesc.layout = nullptr;
ComputePipeline computePipeline = m_device.createComputePipeline(computePipelineDesc);
```

The file `compute-shader.wsl` defines a function named like the entry point `computeStuff` and signal that it is a `@compute`. It must also indicate a **workgroup size**, more or this soon!

```rust
@compute @workgroup_size(64)
fn computeStuff() {
	// Compute stuff
}
```

```{note}
We can totally use the same shader module and file as for the other shaders, I just avoid mixing unrelated parts of code.
```

At this point, it is possible to invoke our shader as long as we have no bind group:

```C++
// Use compute pass
computePass.setPipeline(computePipeline);
//computePass.setBindGroup(/* ... */);
computePass.dispatchWorkgroups(1, 0, 0);
```

Yey! Except... it does virtually nothing, because without accessing any resource, the compute shader cannot communicate any output.

Resources
---------

Again, binding resources is similar to what we have done with the render pipeline. We define a **pipeline layout** that tells how the resources should be bound, and set a **bind group** that actually connects the resources for a given shader invocation.

For our first example, we create two buffers, one used as input and the other one as output.

```C++
// Create input/output buffers
BufferDescriptor bufferDesc;
bufferDesc.mappedAtCreation = false;
bufferDesc.size = 32 * sizeof(float);
bufferDesc.usage = BufferUsage::Storage | BufferUsage::CopyDst;
Buffer inputBuffer = m_device.createBuffer(bufferDesc);
bufferDesc.usage = BufferUsage::Storage | BufferUsage::MapRead;
Buffer outputBuffer = m_device.createBuffer(bufferDesc);

// Fill in input buffer
std::vector<float> input(32);
for (int i = 0; i < input.size(); ++i) {
	input[i] = 0.1f * i;
}
queue.writeBuffer(inputBuffer, 0, input.data(), input.size() * sizeof(float));
```

TODO

```C++
// Create bind group layout
std::vector<BindGroupLayoutEntry> bindings(2, Default);
// Input buffer
bindings[0].binding = 0;
bindings[0].buffer.type = BufferBindingType::ReadOnlyStorage;
bindings[0].visibility = ShaderStage::Compute;
// Output buffer
bindings[1].binding = 1;
bindings[1].buffer.type = BufferBindingType::Storage;
bindings[1].visibility = ShaderStage::Compute;

BindGroupLayoutDescriptor bindGroupLayoutDesc;
bindGroupLayoutDesc.entryCount = (uint32_t)bindings.size();
bindGroupLayoutDesc.entries = bindings.data();
BindGroupLayout bindGroupLayout = m_device.createBindGroupLayout(bindGroupLayoutDesc);

// Create compute pipeline layout
PipelineLayoutDescriptor pipelineLayoutDesc;
pipelineLayoutDesc.bindGroupLayoutCount = 1;
pipelineLayoutDesc.bindGroupLayouts = (WGPUBindGroupLayout*)&bindGroupLayout;
PipelineLayout pipelineLayout = m_device.createPipelineLayout(pipelineLayoutDesc);
```

```C++
// Create compute bind group
std::vector<BindGroupEntry> entries(2, Default);
// Input buffer
entries[0].binding = 0;
entries[0].buffer = inputBuffer;
entries[0].offset = 0;
entries[0].size = bufferDesc.size;
// Output buffer
entries[1].binding = 1;
entries[1].buffer = outputBuffer;
entries[1].offset = 0;
entries[1].size = bufferDesc.size;

BindGroupDescriptor bindGroupDesc;
bindGroupDesc.layout = bindGroupLayout;
bindGroupDesc.entryCount = (uint32_t)entries.size();
bindGroupDesc.entries = (WGPUBindGroupEntry*)entries.data();
BindGroup bindGroup = m_device.createBindGroup(bindGroupDesc);
```

```C++
// Use compute pass
computePass.setPipeline(computePipeline);
computePass.setBindGroup(0, bindGroup, {});
computePass.dispatchWorkgroups(1, 0, 0);
```

To get the result back, we need to add an extra buffer. This is because the same buffer cannot be used both as a storage and for mapping.

```C++
// Create an intermediary buffer to which we copy the output and that can be
// used for reading into the CPU memory.
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::MapRead;
Buffer mapBuffer = m_device.createBuffer(bufferDesc);

// [...]

// Before encoder.finish
encoder.copyBufferToBuffer(outputBuffer, 0, mapBuffer, 0, bufferDesc.size);

// [...]

// Print output
bool done = false;
auto handle = outputBuffer.mapAsync(MapMode::Read, 0, bufferDesc.size, [&](BufferMapAsyncStatus status) {
	if (status == BufferMapAsyncStatus::Success) {
		float* output = (float*)outputBuffer.getMappedRange(0, bufferDesc.size);
		for (int i = 0; i < input.size(); ++i) {
			std::cout << "input " << input[i] << " became " << output[i] << std::endl;
		}
		outputBuffer.unmap();
	}
	done = true;
});

while (!done) {
	// Do nothing, this checks for ongoing asynchronous operations and call their callbacks if needed
	wgpuQueueSubmit(queue, 0, nullptr);
}
```

```rust

```

When to use compute shaders?
----------------------------

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step200`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step200)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step200-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step200-vanilla)
````
