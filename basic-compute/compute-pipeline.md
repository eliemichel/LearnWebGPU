Compute Pipeline (🚧WIP)
================

````{tab} With webgpu.hpp
*Resulting code:* [`step201`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step201-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201-vanilla)
````

Rendering 3D data is the original use of GPUs, but it is far from being the only one nowadays. And even for 3D application, we sometimes use the GPU for non-rendering things, such as simulation, image processing, etc.

When using the GPU for **general purpose** computation (GPGPU), we usually **do not need to call the 3D-specific fixed parts** of the render pipeline, like the rasterization.

This chapter introduces the skeleton for running **compute shaders**, which are shaders ran outside of the fixed-function pipeline.

```{note}
We do not expect you to have read the whole 3D rendering part of the guide, but at least up to the end of the [Shader Uniforms](../basic-3d-rendering/shader-uniforms/index.md) part.
```

Set-up
------

### A simple example

Let us start with a very **simple problem**: we have a GPU-side buffer and want to evaluate a simple function `f` for each element of this buffer:

```rust
// In WGSL
fn f(x: f32) -> f32 {
	return 2.0 * x + 1.0;
}
```

A **naive solution** would be to copy this buffer back to the CPU, evaluate the function here, and upload the result to the GPU again. But this is **very inefficient** for two reasons:

 - The CPU-GPU **copies** are expansive, especially for large buffers.
 - Since `f` is applied independently to each values, the problem is very **parallel**, and the GPU is much better than the CPU at this type of *Single Instruction Multiple Data* (SIMD) parallelism.

So we set up a compute shader that evaluates `f` directly on the GPU, and save the result in a second buffer.

### Architecture

For the sake of the examples throughout this chapter, we create a `onCompute` function that we call once after `onInit`. You may also remove the main loop is `main.cpp` because we won't need the interactive part.

We reuse the same outline as when submitting our render pass on `onFrame`:

```C++
void Application::onCompute() {
	// Initialize a command encoder
	Queue queue = m_device.getQueue();
	CommandEncoderDescriptor encoderDesc = Default;
	CommandEncoder encoder = m_device.createCommandEncoder(encoderDesc);

	// Create and use compute pass here!

	// Encode and submit the GPU commands
	CommandBuffer commands = encoder.finish(CommandBufferDescriptor{});
	queue.submit(commands);

	// Clean up
#if !defined(WEBGPU_BACKEND_WGPU)
	wgpuCommandBufferRelease(commands);
	wgpuCommandEncoderRelease(encoder);
	wgpuQueueRelease(queue);
#endif
}
```

In the initialization method, we mostly keep the initialization of the device and create (private) methods to organize the different steps:

```C++
bool Application::onInit() {
	if (!initDevice()) return false;
	initBindGroupLayout();
	initComputePipeline();
	initBuffers();
	initBindGroup();
	return true;
}
```

Each `initSomething` step comes with a `terminateSomething` that is called at the end in reverse order:

```C++
void Application::onFinish() {
	terminateBindGroup();
	terminateBuffers();
	terminateComputePipeline();
	terminateBindGroupLayout();
	terminateDevice();
}
```

Compute Pass
------------

Remember how we drew [our first color](../getting-started/first-color.md)? We submitted to the command queue a particular render-specific sequence of instructions called a `RenderPass`. The approach to run compute-only shaders is similar, and uses a `ComputePass` instead.

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

// Clean up
#if !defined(WEBGPU_BACKEND_WGPU)
	wgpuComputePassEncoderRelease(computePass);
#endif
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

The compute pipeline first defines the shader to be used:

```C++
// In initComputePipeline():

// Load compute shader
ShaderModule computeShaderModule = ResourceManager::loadShaderModule(RESOURCE_DIR "/compute-shader.wsl", m_device);

// Create compute pipeline
ComputePipelineDescriptor computePipelineDesc = Default;
computePipelineDesc.compute.entryPoint = "computeStuff";
computePipelineDesc.compute.module = computeShaderModule;
ComputePipeline computePipeline = m_device.createComputePipeline(computePipelineDesc);
```

The file `compute-shader.wsl` defines a function named like the entry point `computeStuff` and signal that it is a `@compute`. It must also indicate a **workgroup size**, more or this soon!

```rust
@compute @workgroup_size(32)
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
computePass.dispatchWorkgroups(1, 1, 1);
```

Yey! Except... it does virtually nothing, because without accessing any resource, the compute shader cannot communicate any output.

Resources
---------

For our shader to actually communicate with an input and output buffer, we need to setup a **pipeline layout** that tells how the shader resources should be bound, and a **bind group** that actually connects the resources for a given shader invocation.

### Pipeline layout

We add in the compute shader the two buffer bindings as variables defined in the `storage`address space. It is important to specify the **access mode**, which is `read` for the input and `read_write` for the output (there is no "write only" mode):

```rust
@group(0) @binding(0) var<storage,read> inputBuffer: array<f32,32>;
@group(0) @binding(1) var<storage,read_write> outputBuffer: array<f32,32>;
```

And we create on the C++ side a **bind group layout** that matches these bindings:

```C++
void Application::initBindGroupLayout() {
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
	m_bindGroupLayout = m_device.createBindGroupLayout(bindGroupLayoutDesc);
}
```

In `initComputePipeline()` we simply assigns this to the compute pipeline through the **pipeline layout**:

```C++
// Create compute pipeline layout
PipelineLayoutDescriptor pipelineLayoutDesc;
pipelineLayoutDesc.bindGroupLayoutCount = 1;
pipelineLayoutDesc.bindGroupLayouts = (WGPUBindGroupLayout*)&m_bindGroupLayout;
m_pipelineLayout = m_device.createPipelineLayout(pipelineLayoutDesc);
computePipelineDesc.layout = m_pipelineLayout;
```

```{note}
The objects `m_bindGroupLayout` and `m_pipelineLayout` are attributes of the `Application` class (hence the `m_` prefix) so that they can be used in different methods. Do not forget to destroy them in the terminate functions by the way.
```

### Buffers

Before binding the buffers, we must of course create them (in `initBuffers`):

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

### Bind Group

TODO

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

Invoking the compute shader `1 * 1 * 1 * workgroup_size` times:

```C++
// Use compute pass
computePass.setPipeline(computePipeline);
computePass.setBindGroup(0, bindGroup, 0, nullptr);
computePass.dispatchWorkgroups(1, 1, 1);
```

The invocation id is provided to the `computeStuff` entry point through the `global_invocation_id` built-in input:

```rust
@compute @workgroup_size(32)
fn computeStuff(@builtin(global_invocation_id) id: vec3<u32>) {
    // Compute stuff
    outputBuffer[id.x] = f(inputBuffer[id.x]);
}
```

Read-back
---------

TODO

One of the point of computing things on the GPU is to avoid CPU-GPU copies, but in our example case we still want to check that the computation went well, so we copy the output buffer back to the CPU.

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
auto handle = mapBuffer.mapAsync(MapMode::Read, 0, bufferDesc.size, [&](BufferMapAsyncStatus status) {
	if (status == BufferMapAsyncStatus::Success) {
		const float* output = (const float*)mapBuffer.getConstMappedRange(0, bufferDesc.size);

		for (int i = 0; i < input.size(); ++i) {
			std::cout << "input " << input[i] << " became " << output[i] << std::endl;
		}
		mapBuffer.unmap();
	}
	done = true;
});

while (!done) {
	// Do nothing, this checks for ongoing asynchronous operations and call their callbacks if needed
	wgpuQueueSubmit(queue, 0, nullptr);
}
```

When to use compute shaders?
----------------------------

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step201`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step201-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201-vanilla)
````
