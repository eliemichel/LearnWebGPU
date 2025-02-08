Compute Pipeline <span class="bullet">🟡</span>
================

*Resulting code:* [`step201`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201)

Rendering 3D data is the original use of GPUs, but it is far from being the only one nowadays. And even for 3D application, we sometimes use the GPU for non-rendering things, such as simulation, image processing, etc.

When using the GPU for **general purpose** computation (GPGPU), we usually **do not need to call the 3D-specific fixed parts** of the render pipeline, like the rasterization.

This chapter introduces the skeleton for running **compute shaders**, which are shaders run outside of the fixed-function pipeline.

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

 - The CPU-GPU **copies** are expensive, especially for large buffers.
 - Since `f` is applied independently to each value, the problem is very **parallel**, and the GPU is much better than the CPU at this type of *Single Instruction Multiple Data* (SIMD) parallelism.

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

The creation of the compute pass is **much simpler** than the one of the render pass, because since we do **not use any fixed-function stage**, there is almost nothing to configure! The only option is the timestamp writes that will be described in the benchmarking chapter.

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

The file `compute-shader.wsl` defines a function named like the entry point `computeStuff` and signal that it is a `@compute`. It must also indicate a **workgroup size**, more on this soon!

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
@group(0) @binding(0) var<storage,read> inputBuffer: array<f32,64>;
@group(0) @binding(1) var<storage,read_write> outputBuffer: array<f32,64>;
```

```{note}
The [`array`](https://gpuweb.github.io/gpuweb/wgsl/#array-types) type of WGSL is very similar to the [`std::array`](https://en.cppreference.com/w/cpp/container/array) type of C++.
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

In `initComputePipeline()` we simply assign this to the compute pipeline through the **pipeline layout**:

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

Before binding the buffers, we must of course create them (in `initBuffers`). An important point is to mark their usage with the `Storage` flag, so that we can read/write them from shaders:

```C++
// We save this size in an attribute, it will be useful later on
m_bufferSize = 64 * sizeof(float);

// Create input buffers
BufferDescriptor bufferDesc;
bufferDesc.mappedAtCreation = false;
bufferDesc.size = m_bufferSize;
bufferDesc.usage = BufferUsage::Storage | BufferUsage::CopyDst;
Buffer inputBuffer = m_device.createBuffer(bufferDesc);


// Create output buffer: the only difference is the usage
bufferDesc.usage = BufferUsage::Storage;
Buffer outputBuffer = m_device.createBuffer(bufferDesc);
```

Buffers that have the `Storage` usage are confronted to specific device limits:

```C++
// We bind an input, and an output buffers:
requiredLimits.limits.maxStorageBuffersPerShaderStage = 2;

// Each buffer has (at most) the size m_bufferSize (which definition should be
// moved to the constructor so that it is known in initDevice):
requiredLimits.limits.maxStorageBufferBindingSize = m_bufferSize;
```

We can already fill in the input buffer with some values:

```C++
// Fill in input buffer
std::vector<float> input(m_bufferSize / sizeof(float));
for (int i = 0; i < input.size(); ++i) {
	input[i] = 0.1f * i;
}
queue.writeBuffer(inputBuffer, 0, input.data(), m_bufferSize);
```

### Bind Group

Remember: the bind group **layout** was telling *how* to bind resources to the shader. Once we effectively have created these resources (the buffers), we can define a **bind group** to tell *what* to bind:

```C++
void Application::initBindGroup() {
	// Create compute bind group
	std::vector<BindGroupEntry> entries(2, Default);

	// Input buffer
	entries[0].binding = 0;
	entries[0].buffer = m_inputBuffer;
	entries[0].offset = 0;
	entries[0].size = m_bufferSize;

	// Output buffer
	entries[1].binding = 1;
	entries[1].buffer = m_outputBuffer;
	entries[1].offset = 0;
	entries[1].size = m_bufferSize;

	BindGroupDescriptor bindGroupDesc;
	bindGroupDesc.layout = m_bindGroupLayout;
	bindGroupDesc.entryCount = (uint32_t)entries.size();
	bindGroupDesc.entries = (WGPUBindGroupEntry*)entries.data();
	m_bindGroup = m_device.createBindGroup(bindGroupDesc);
}
```

Once the bind group is created, it can be bound to the pipeline in `onCompute()`:

```C++
computePass.setPipeline(computePipeline);
// Set the bind group:
computePass.setBindGroup(0, m_bindGroup, 0, nullptr);
computePass.dispatchWorkgroups(1, 1, 1);
```

Invocation
----------

### Concurrent calls

Now that the `dispatchWorkgroups` call actually does something, let us explain a little more what it does.

A compute shader (and more generally a GPU) is **good at doing the same thing multiple times in parallel**, so built in this *dispatch* operation is the possibility to call the shader's entry point multiple times.

Instead of providing a single number of concurrent calls, we express this number as a **grid** (a.k.a. **dispatch**) of $x \times y \times z$ **workgroups**:

```C++
computePass.dispatchWorkgroups(x, y, z);
```

Beware that this launches $x \times y \times z$ **workgroups**, i.e., groups of calls. Each workgroup is itself a little block of $w \times h \times d$ **threads**, each of which runs the entry point. The workgroup size is set by the shader's entry point:

```rust
@compute
@workgroup_size(w, d, h)
fn computeStuff() {
	// [...]
}
```

```{note}
The workgroup sizes must be constant expressions.
```

### Workgroup size vs count

> 😟 Okay, that makes a lot of variables just to set a number of jobs that is just the product of them in the end, doesn't it?

The thing is: **all combinations are not equivalent**, even if they multiply to the same number of threads.

The jobs are **not really all launched at once**: under the hood a scheduler organizes the execution of individual workgroups. What we can know is that the jobs from the **same workgroup** are launched together, but two **different workgroups** might get executed at significantly different times.

The appropriate size for a workgroup **depends a lot on the task** that threads run. Here are some rules of thumb about the **workgroup size versus workgroup count**:

 - The number $w \times h \times d$ of threads per workgroup should be a multiple of 32, because within a workgroup threads are launched by **warps** of (usually a multiple of) 32 threads.

 - The total resource usage of a workgroup should be kept to a **minimum**, so that the scheduler has more freedom in organizing things.

 - When threads **share memory** with each others, it is cheaper if they are in the same workgroup (and even cheaper if they are in the same warp).

 - Group threads that are likely to have the **same branching path**. Threads from the same warp share the same instruction pointer, so threads are idling when one of their neighbors follows a different branch of an `if` or loop condition.

 - Try to have workgroup sizes be powers of two.

```{note}
These rules are somehow contradictory. Only a benchmark on your specific use case can tell you what the best trade-off is.
```

### Workgroup dimensions

> 😟 Okay, I see better now, but what about the different axes $w$, $h$ and $d$? Is a workgroup size of $2 \times 2 \times 4$ different from $16 \times 1 \times 1$?

It is different indeed, because this size **gives hints to the hardware** about the potential **consistency of memory access** across threads.

Both the CPU and the GPU try in general to guess patterns in the way consecutive and/or concurrent operations use memory, in order for instance to [prefetch](https://en.wikipedia.org/wiki/Cache_prefetching) memory in caches or to group (a.k.a. "coalesce") concurrent read/writes into a single memory access.

Since a very common task of the GPU is to process **data organized as a 2D or 3D grid**, a graphics API provides grid-based data storage (**textures**) and grid-based concurrency model. When neighbor threads access neighbor pixels/voxels in a similar way, the hardware can better anticipate what is happening.

So the main rule of thumb here is that although the $x$, $y$ and $z$ axes are at first glance abstract values that are "just" multiplied together, you should really use them as the $x$, $y$ and $z$ axes of your data grid.

### Example

In our simple example, we process data laid out in 1D buffers, so our dispatch is also a one dimensional series of workgroups: $(x, y, z) = (x, 1, 1)$ and $(w, h, d) = (w, 1, 1)$.

The workgroup size $w$ should be at least 32, and there is no apparent reason for it to be more than that. So in the end, we dispatch workgroups of `32 * 1 * 1` threads:

```rust
@compute @workgroup_size(32, 1, 1) // or just @workgroup_size(32)
fn computeStuff() {
    // [...]
}
```

And we infer the number of workgroups from the expected invocation calls:

```C++
uint32_t invocationCount = m_bufferSize / sizeof(float);
uint32_t workgroupSize = 32;
// This ceils invocationCount / workgroupSize
uint32_t workgroupCount = (invocationCount + workgroupSize - 1) / workgroupSize;
computePass.dispatchWorkgroups(workgroupCount, 1, 1);
```

```{note}
Be careful about ceiling the `invocationCount / workgroupSize` division instead of flooring it, otherwise when `workgroupSize` does not exactly divide `invocationCount` the last threads will be missing.
```

All we need now is to know in which thread of which workgroup we are, to figure out which index of the buffer we need to process. This is given by [built-in shader inputs](https://gpuweb.github.io/gpuweb/wgsl/#built-in-values-global_invocation_id), and in particular the **invocation id** provided as the `global_invocation_id` built-in:

```rust
@compute @workgroup_size(32)
fn computeStuff(@builtin(global_invocation_id) id: vec3<u32>) {
    // Apply the function f to the buffer element at index id.x:
    outputBuffer[id.x] = f(inputBuffer[id.x]);
}
```

### Device limits

There are a bunch of device limits associated to the choice of workgroup size/count:

```C++
// The maximum value for respectively w, h and d
requiredLimits.limits.maxComputeWorkgroupSizeX = 32;
requiredLimits.limits.maxComputeWorkgroupSizeY = 1;
requiredLimits.limits.maxComputeWorkgroupSizeZ = 1;

// The maximum value of the product w * h * d
requiredLimits.limits.maxComputeInvocationsPerWorkgroup = 32;

// And the maximum value of max(x, y, z)
// (It is 2 because workgroupCount = 64 / 32 = 2)
requiredLimits.limits.maxComputeWorkgroupsPerDimension = 2;
```

Read-back
---------

After dispatching all parallel compute threads, the output buffer is populated with the result. So naturally now we want to **read this output buffer** back.

```{note}
One of the point of computing things on the GPU is to avoid CPU-GPU copies, because maybe the output buffer is only used in a subsequent operation on the GPU. But in our example case we still want to check that the computation went well.
```

### Map Buffer

We have seen already how to use the Buffer's `mapAsync` method to read a buffer back, but this won't work directly:

```C++
// DON'T
m_outputBuffer.mapAsync(MapMode::Read, /* ... */);
```

Why not? This requires the output buffer to be created with the `MapRead` usage flag. But unfortunately **this flag is incompatible** with `Storage`, that is needed for the shader to be allowed to write in the output.

The solution is to **create a 3rd buffer**, responsible for the transport back on CPU. In the `initBuffers()` method we create this new "map buffer" and add the `CopySrc` usage to the output:

```C++
// Add the CopySrc usage here, so that we can copy to the map buffer
bufferDesc.usage = BufferUsage::Storage | BufferUsage::CopySrc;
m_outputBuffer = m_device.createBuffer(bufferDesc);

// Create an intermediary buffer to which we copy the output and that can be
// used for reading into the CPU memory.
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::MapRead;
m_mapBuffer = m_device.createBuffer(bufferDesc);
```

After the `computePass.end()`, and before `encoder.finish(...)`, we add a copy command:

```C++
// Copy the memory from the output buffer that lies in the storage part of the
// memory to the map buffer, which is in the "mappable" part of the memory.
encoder.copyBufferToBuffer(m_outputBuffer, 0, m_mapBuffer, 0, m_bufferSize);
```

### Callback

We are now ready to read from the map buffer on the CPU, through a callback provided to `mapAsync`:

```C++
// Print output
bool done = false;
auto handle = m_mapBuffer.mapAsync(MapMode::Read, 0, m_bufferSize, [&](BufferMapAsyncStatus status) {
	if (status == BufferMapAsyncStatus::Success) {
		const float* output = (const float*)m_mapBuffer.getConstMappedRange(0, m_bufferSize);
		for (int i = 0; i < input.size(); ++i) {
			std::cout << "input " << input[i] << " became " << output[i] << std::endl;
		}
		m_mapBuffer.unmap();
	}
	done = true;
});
```

Do not forget to call `Instance::processEvents` in the loop that waits that the map is done afterwards:

```C++
while (!done) {
	// Checks for ongoing asynchronous operations and call their callbacks if needed
	m_instance.processEvents();
}
```

````{caution}
As of April 23, 2023, `wgpu-native` does not implement `processEvent` yet, but its behavior can be mimicked by submitting an empty queue:

```C++
#ifdef WEBGPU_BACKEND_WGPU
		queue.submit(0, nullptr);
#else
		m_instance.processEvents();
#endif
```
````

And you should finally see something like this in the output console:

```
input 0 became 1
input 0.1 became 1.2
input 0.2 became 1.4
input 0.3 became 1.6
input 0.4 became 1.8
[...]
```

Conclusion
----------

Some parts of this chapter were reminders of what has been done with the render pass, the **most important novelty** here is the dispatch/workgroup/thread hierarchy. Make sure to come back to the list of rules regularly to check that the choice of workgroup size is relevant (and benchmark whenever possible).

We are now ready to focus on the content of the compute shader itself, and the different ways it can manipulate resources and memory!

*Resulting code:* [`step201`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step201)
