Our first shader <span class="bullet">🟢</span>
================

```{lit-setup}
:tangle-root: 019 - Our first shader - Next
:parent: 017 - Playing with buffers - Next
```

*Resulting code:* [`step019-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step019-next)

We have introduced how to **allocate GPU memory** in chapter [*Playing with buffers*](playing-with-buffers.md), and we now see how to **run a custom program on the GPU**.

In this chapter, we create a **very simple shader** that takes an input buffer, **multiplies all its values by 2** and stores the result in an output buffer. Not a ground-breaking operation, but the occasion to introduce **many important concepts**!

GPU Pipelines
-------------

There are **similarities and differences** between the way programs run on a CPU and on a GPU.

Like a CPU, **a GPU can be programmed**. The program is written in a human language, then compiled into a binary representation. Traditionally, a GPU program is called a **shader program**.

The **programming languages** used to program a GPU **are different** from the ones used to program a CPU. This is because the **computing models** are quite different. For instance, **a GPU cannot allocate/free memory for itself**. We can cite for example GPU languages like GLSL, HLSL, MSL, Slang, etc. and the one we'll be using: **WGSL** ("SL" stands for *Shader Language*).

GPU programs are **fundamentally parallel**, following a _**Single Instruction/Multiple Data**_ model: the **execution pointer** (address of the currently executed instruction) **is shared** among neighbor threads, only they fetch and process slightly different data. This enables the hardware to **mutualize some operations** like memory access, which is key to data-intensive applications.

Besides programmable stages, a GPU also features **fixed-function** stages. It typically contains hardware circuits **dedicated to some performance critical operations**. A canonical example of such stage is the **rasterization**, which projects 3D triangles onto the pixels of a texture. Fixed-function stages can be **configured** through some options, but are not programmable.

```{themed-figure} /images/our-first-shader/pipelines_{theme}.svg
:align: center

What we call a **pipeline** is a series of fixed-function stages with a specific configuration and programmable stages with a given shader.
```

WebGPU gives access to **two types of pipelines**, namely **compute** pipelines and **render** pipelines.

In this chapter, we **start with a compute pipeline** because it is **much simpler**: there is only 1 programmable stage, and no fixed-function stage.

```{note}
Everything we see for this compute pipeline will be **useful once we get to render pipelines**!
```

In the remainder of this chapter, we introduce **3 key objects** related to pipelines:

- The `WGPUComputePipeline` object, that represents **a compute pipeline** as a whole.
- The `WGPUShaderModule` object, which represents a **GPU program**, written in WGSL, that we can use for the programmable stages of a pipeline.
- The `WGPUBindGroup` object, that is how we **give a pipeline access to GPU resources**, like buffers and textures.

We also introduce `WGPUPipelineLayout` and `WGPUBindGroupLayout` objects, which ensure that a bind group is **compatible** with a pipeline.

Pipeline creation
-----------------

You may have guessed that creating a pipeline goes through the device, with a **descriptor** and a **create** function:

```{lit} C++, Create compute pipeline
WGPUComputePipelineDescriptor pipelineDesc = WGPU_COMPUTE_PIPELINE_DESCRIPTOR_INIT;
{{Describe compute pipeline}}

WGPUComputePipeline pipeline = wgpuDeviceCreateComputePipeline(device, &pipelineDesc);
```

The compute pipeline has **a single stage**, which is configured through `pipelineDesc.compute`. The only fields that are required are:

- `module`: The shader module, i.e., the **GPU program** that we want to run.
- `entryPoint`: The **name of the function** to run in that program (the equivalent of `main` in a C++ program, if you will).

```{lit} C++, Describe compute pipeline
// Description of our pipeline
pipelineDesc.label = toWgpuStringView("Our simple pipeline");
pipelineDesc.compute.module = shaderModule;
pipelineDesc.compute.entryPoint = toWgpuStringView("computeStuff");
```

Shader module
-------------

A shader module is kind of a dynamic library (like a .dll, .so or .dylib file), except that it talks the **binary language of your GPU** rather than your CPU's.

Like any compiled program, the shader is first written in a **human-writable programming language**, then **compiled** into low-level machine code. However, the low-level code is highly hardware-dependent, and often not publicly documented. So the application is distributed with the **source code** of the shaders, which is **compiled on the fly** when initializing the application.

### Shader language

The shader language officially used by WebGPU is called [WGSL](https://gpuweb.github.io/gpuweb/wgsl/), namely the *WebGPU Shading Language*. Any implementation of WebGPU must support it, and the JavaScript version of the API only supports WGSL, but the native header `webgpu.h` also offers the possibility to provide shaders written in [SPIR-V](https://www.khronos.org/spir) or [GLSL](https://www.khronos.org/opengl/wiki/Core_Language_(GLSL)) (`wgpu-native` only).

```{tip}
**SPIR-V** is more of an intermediate representation, i.e., a **bytecode**, than something that one would write manually. It is the shader language used by the Vulkan API and a lot of tools exist to **cross-compile** code from other common shader languages (HLSL, GLSL) so it is an interesting choice when one needs to reuse **existing shader code bases**.
```

```{note}
Also note that WGSL was originally designed to be a human-editable version of SPIR-V programming model, so **transpilation** from SPIR-V to WGSL is in theory efficient and lossless (use [Naga](https://github.com/gfx-rs/naga) or [Tint](https://dawn.googlesource.com/tint) for this).
```

In this guide, we will only use WGSL. Its syntax may seem a bit unfamiliar if you are used to C/C++ so let us start with a very simple function and its equivalent in C++:

```rust
// In WGSL
fn my_addition(x: f32, y: f32) -> f32 {
	let z = x + y;
	return z;
}
```

```C++
// In C++
float my_addition(float x, float y) {
	auto z = x + y;
	return z;
}
```

Notice how the **types** are specified **after** instead of **before** the argument names. The type of `z` is automatically inferred, though we could have forced it using `let z: f32 = ...`. The return type is specified after the arguments, using the arrow `->`.

```{note}
The keyword `let` defines a *value*, which is sort of a variable but that cannot be reassigned. A regular variable is defined using the `var` keyword. **Prefer using `let`** where possible to help the compiler optimize your shader.
```

We will **progressively introduce** the WGSL syntax and features throughout this guide.

### Concurrent threads

Besides the different syntax, a shader follows a **different programming model**. In particular, its **entry point** (the sort of "main" function) is **called multiple times in parallel**! This is how we benefit from the parallel architecture of the GPU.

When we **dispatch** our compute pipeline (i.e., we invoke it), **we specify a number of threads** to run, each of which starts at the entry point. And instead of providing a single number of threads, we express this number as a **grid of** $x \times y \times z$ **workgroups**.

```{themed-figure} /images/our-first-shader/workgroup_{theme}.svg
:align: center

The **parallel threads** of the GPU are organized in a **3D grid** and dispatched by fixed-size **workgroups**.
```

We will give more details about this grid in chapters that focus on computer shaders. **For now we only use the first dimension of the grid.**

### Attributes

Let us start writing the **entry point** function that we want to call from our pipeline (which we called "computeStuff" in the pipeline descriptor):

```rust
@compute @workgroup_size(32)
fn computeStuff(@builtin(global_invocation_id) threadId: vec3u) {
    // [...]
}
```

```{note}
Shader languages natively support **vector and matrix types** up to size 4. The type `vec3u` of the argument `threadId` is a vector of 3 unsigned integers, and an **alias** for the *templated* type `vec3<u32>`. As another example, the type `vec4<f32>` is a vector of 4 floats and has alias `vec4f`.
```

What are these tokens that start with an `@`? They are called [**attributes**](https://www.w3.org/TR/WGSL/#attributes) and **decorate the object that comes afterward** with various information.

#### Entry point attributes

Here we **mark the function** `computeStuff` with `@compute` to tell the WGSL compiler that this function **might be used as an entry point of a compute shader**. Similarly, we will see `@vertex` and `@fragment` attributes when we write render shaders.

The entry point of a compute shader **must** also be marked with the `@workgroup_size` attribute, which tells the size of the atomic groups of threads that constitute the **compute shader grid** described above.

```{note}
The `@workgroup_size` attribute can take **up to 3 arguments**, for the 3 dimensions of the compute grid. Their default value is 1, so our example above is equivalent to `@workgroup_size(32, 1, 1)`.
```

#### Built-in inputs

We also **decorate the argument of our entry point** (`threadId: vec3u`) with the `@builtin` attribute. This tells WebGPU that when invoking this entry point, its argument `threadId` must receive the value of the **special built-in value** `global_invocation_id`.

The [`@builtin` inputs/outputs specification](https://www.w3.org/TR/WGSL/#builtin-inputs-outputs) tell us that this code name corresponds to the **position of the thread in the compute shader grid**. This is how each thread can make a slightly different job while they all follow the very same source code.

```{note}
The argument `threadId` could have any other name: as long as it is decorated with the **same built-in attribute**, it has the **same semantics**.
```

### Binding resources

Thanks to the thread ID, we are able to **tell each thread to take care of a different index** of the buffer:

```{lit} rust, The compute shader entry point
@compute @workgroup_size(32)
fn computeStuff(@builtin(global_invocation_id) threadId: vec3u) {
	// Core behavior of our shader: multiply input by 2 and store result
	// in output buffer:
    outputBuffer[threadId.x] = 2.0 * inputBuffer[threadId.x];
}
```

Since this runs for various thread indices, we end up applying the multiplication for the whole buffer.

> 🤔 But where do the `inputBuffer` and `outputBuffer` variables come from?

Resources are **not** inputs argument of the entry point: they are provided as **global variables** of the shader module which are **decorated with a `@group` and a a `@binding` attribute**:

```{lit} rust, Shader global declarations
// Declaration of the inputBuffer resource,
// attached to binding #0 of bind group #0
@group(0) @binding(0)
var<storage,read> inputBuffer: array<f32>;

// Declaration of the outputBuffer resource,
// attached to binding #1 of bind group #0
@group(0) @binding(1)
var<storage,read_write> outputBuffer: array<f32>;
```

**Three new things** here, namely the group/binding attributes, the arguments after the `var` keyword and the `array` type.

#### Binding attributes

The pair group/binding given by `@group(0) @binding(0)` is how we will **identify the resource on the C++ side**, when saying things like "*bind that `WGPUBuffer` object to the binding #0 of the compute pipeline*".

````{note}
The **order** in which functions and global variables are declared **does not matter to the compiler**. It is however recommended to write binding declarations at the beginning for **better readability**:

```{lit} rust, The WGSL shader source code
// Bindings are declared for instance at the beginning of the shader
{{Shader global declarations}}

// Then we write our entry point
{{The compute shader entry point}}
```
````

#### Memory space and access mode

The `inputBuffer` and `outputBuffer` variables are declared with the `var` keyword because they correspond to **an actual memory location** (as opposed to `let`-declared values), and here we specify **options** between the **angle brackets** (`<` and `>`) that follow:

```rust
var<storage,read> inputBuffer
```

The `storage` option indicates that the variables `inputBuffer` and `outputBuffer` are **storage buffers**, as opposed to uniform buffers which we will see later on. Remember how we specified a **usage** when creating a buffer? This is again related to the fact that the best memory space for some data depends on how we use this data.

Storage buffers are **read-only by default**, so we could have skipped the `read` option when declaring `inputBuffer`. For `oututBuffer` however we need to explicitly ask for its **access mode** to be `read_write` (write-only does not exist) so that our shader is **allowed to modify it**.

#### Array type

Lastly, we declare `inputBuffer` and `outputBuffer` with the type `array<f32>`. The `array` type corresponds to the C/C++ array, where a given type is repeated multiple times in memory. Like in C++, we use angle brackets to specify the type of array elements, so `array<f32>` contains 32-bits float values.

We use here a **runtime-sized array**, where the size will be determined from the `WGPUBuffer` object that we bind. We could also have provided a specific size as a second template argument, e.g. `array<f32,64>` for a fixed-size array of 64 floats.

### Loading the module

Okey, **our shader code is ready**! All we need now is to load it on the C++ side, into a `WGPUShaderModule` object.

For more flexibility, the shader code should be loaded from a file, but for now **we simply write it in a multi-line string literal** at the beginning of our `main.cpp`:

```{lit} C++, Shader source literal
// Before main()
const char* shaderSource = R"(
{{The WGSL shader source code}}
)";
```

```{lit} C++, file: main.cpp (replace, hidden)
{{Includes}}

{{Utility functions in main.cpp}}

{{Shader source literal}}

int main() {
	{{Create things}}

	{{Main body}}

	{{Release things}}

	return 0;
}
```

Now the shader module object can be **created by the device**:

```{lit} C++, Create shader module
WGPUShaderModuleDescriptor moduleDesc = WGPU_SHADER_MODULE_DESCRIPTOR_INIT;
{{Describe shader module}}

WGPUShaderModule shaderModule = wgpuDeviceCreateShaderModule(device, &moduleDesc);
```

**At first glance**, the descriptor type seems to only contain a label...

```C++
// The WGPUShaderModuleDescriptor structure as defined in webgpu.h
struct WGPUShaderModuleDescriptor {
    WGPUChainedStruct * nextInChain;
    WGPUStringView label;
};
```

So, **where do we set the source code**? We see here our first case of **extension**, which uses the `nextInChain` field that many structures contain.

```{themed-figure} /images/our-first-shader/chained-struct_{theme}.svg
:align: center

Descriptors can be **extended** through the `nextInChain` pointer. Each extension starts with a `WGPUChainedStruct` header that may point to yet another extension, and provides a **structure type** `sType` to tell how to **interpret** the remaining fields.
```

There exists a `WGPUShaderSourceWGSL` struct, which is a **chained structure** that can be chained to a `WGPUShaderModuleDescriptor` to provide WGSL source code. The **first field** of a chained structure is always `WGPUChainedStruct chain` and is what `nextInChain` can point to:

```{lit} C++, Describe shader module
// We create a chained descriptor dedicated to the WGSL source:
WGPUShaderSourceWGSL wgslSourceDesc = WGPU_SHADER_SOURCE_WGSL_INIT;
{{Describe WGSL source}}

// And we connect it to the shader module descriptor through the nextInChain pointer:
moduleDesc.nextInChain = &wgslSourceDesc.chain;
```

```{important}
Make sure to initialize `wgslSourceDesc` with the macro `WGPU_SHADER_SOURCE_WGSL_INIT`, or to manually set `wgslSourceDesc.chain.sType` to `WGPUSType_ShaderSourceWGSL`. This "*SType*" is **the way WebGPU understand** what chained structure is connected.
```

All we have left is to fill in the content of `wgslSourceDesc` with our WGSL source code:

```{lit} C++, Describe WGSL source
// The only payload of WGPUShaderSourceWGSL is the `code` field:
wgslSourceDesc.code = toWgpuStringView(shaderSource);
```

```{note}
The reason why the shader source code is provided through an extension is that **other extensions may be used instead**. For instance, `WGPUShaderSourceSPIRV` can be used to provide a SPIR-V shader. However, **only WGSL is available when building for the Web**.
```

Optionally, it is also advised to **name our module**, to better track error messages:

```{lit} C++, Describe shader module (prepend)
moduleDesc.label = toWgpuStringView("Our first compute shader");
```

```{tip}
Once we will load shader module from file, it is convenient to **label the module after the name of the file** it was loaded from.
```

Binding resources
-----------------

### Recap

Let us summarize what we have done so far in this chapter:

- We created a **compute pipeline**.
- To configure the programmable **stage** of this pipeline, we needed to create a **shader module**.
- We wrote the **source code** of this shader module in **WGSL**.

The **shader module** is only used to build the pipeline, and **can be released** right after that:

```{lit} C++, Create things (append)
// At the beginning of our program:
{{Create shader module}}
{{Create compute pipeline}}

// Once the compute pipeline is ready, we no longer need the shader module:
wgpuShaderModuleRelease(shaderModule);
```

The computer pipeline must also be released of course, but this must wait for the end of the program:

```{lit} C++, Release things (prepend)
// At the end of our program, we release the pipeline.
wgpuComputePipelineRelease(pipeline);
```

What we see now is:

- How to set up our buffers and their **usage**.
- How to **bind buffers** to the compute pipeline.
- How we run the pipeline, i.e., how we **dispatch** compute jobs.

### Buffers

When binding a buffer as a `storage` variable of a shader, it must have the `Storage` usage. A problem we quickly face is that **the `Storage` usage is incompatible with the `MapRead` usage**.

We thus need to create **a third buffer** dedicated to retrieving data. We commonly call it **staging buffer**, or **map buffer**.

We create these buffers, this time with a size that can **contain 64 float elements**:

```{lit} C++, Create buffers (replace)
// Number of floats in the buffers
size_t elementCount = 64;

WGPUBufferDescriptor inputBufferDesc = WGPU_BUFFER_DESCRIPTOR_INIT;
inputBufferDesc.label = toWgpuStringView("Input Buffer");
inputBufferDesc.size = elementCount * sizeof(float);
inputBufferDesc.usage = WGPUBufferUsage_Storage;
inputBufferDesc.mappedAtCreation = true;
WGPUBuffer inputBuffer = wgpuDeviceCreateBuffer(device, &inputBufferDesc);

WGPUBufferDescriptor outputBufferDesc = WGPU_BUFFER_DESCRIPTOR_INIT;
outputBufferDesc.label = toWgpuStringView("Output Buffer");
outputBufferDesc.size = elementCount * sizeof(float);
outputBufferDesc.usage = WGPUBufferUsage_Storage | WGPUBufferUsage_CopySrc;
WGPUBuffer outputBuffer = wgpuDeviceCreateBuffer(device, &outputBufferDesc);

WGPUBufferDescriptor stagingBufferDesc = WGPU_BUFFER_DESCRIPTOR_INIT;
stagingBufferDesc.label = toWgpuStringView("Staging Buffer");
stagingBufferDesc.size = elementCount * sizeof(float);
stagingBufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_MapRead;
WGPUBuffer stagingBuffer = wgpuDeviceCreateBuffer(device, &stagingBufferDesc);

{{Initialize input buffer data}}
```

````{note}
This replaces the buffers `bufferA` and `bufferB` used previously.
````

And we release the buffers at the end of the program:

```{lit} C++, Release buffers (replace)
wgpuBufferRelease(inputBuffer);
wgpuBufferRelease(outputBuffer);
wgpuBufferRelease(stagingBuffer);
```

When initializing the **input data**, we take care to **cast the mapped buffer as `float*`**:

```{lit} C++, Initialize input buffer data
float* inputBufferData = static_cast<float*>(
	wgpuBufferGetMappedRange(inputBuffer, 0, WGPU_WHOLE_MAP_SIZE)
);
// Write 0.0, 0.1, 0.2, 0.3, ... in inputBuffer
for (size_t i = 0 ; i < elementCount ; ++i) {
	inputBufferData[i] = static_cast<float>(i) * 0.1f;
}
wgpuBufferUnmap(inputBuffer);
```

And finally we change the way we **display the result** by interpreting bits as float values:

```{lit} C++, Map and display buffer B in main (replace)
fetchBufferDataSync(instance, stagingBuffer, [&](const void* data) {
	const float* floatData = static_cast<const float*>(data);	
	std::cout << "Result: [";
	for (size_t i = 0 ; i < elementCount ; ++i) {
		if (i > 0) std::cout << ", ";
		std::cout << floatData[i];
	}
	std::cout << "]" << std::endl;
});
```

### Bind group

We have our buffers `inputBuffer` and `outputBuffer` as **C++ variable**, and we now want to **bind** them to the similarly named **WGSL variables** in our compute pipeline.

```{important}
The **variable names** have **no impact** on binding. They can have very different names on the C++ side and the WGSL side, and using similar names will not automate anything.
```

We specify the variable assignment through **bind group entries**, which we use below to create a bind group object. This should be self-explanatory:

```{lit} C++, Define bind group entries
std::vector<WGPUBindGroupEntry> bindGroupEntries(2, WGPU_BIND_GROUP_ENTRY_INIT);
bindGroupEntries[0].binding = 0;
bindGroupEntries[0].buffer = inputBuffer;
bindGroupEntries[1].binding = 1;
bindGroupEntries[1].buffer = outputBuffer;
```

```{note}
Here again, we use an `INIT` macro to **initialize the entries**, even if they are contained in a `std::vector`.
```

We now use these entries in the **bind group descriptor**. **Array values** in descriptors are always specified through the combination of **a pointer** (`entries`) and **a number of elements** (`entryCount`), which directly map to the `data()` and `size()` methods of a `std::vector` or `std::array`:

```{lit} C++, Create bind group
{{Define bind group entries}}

WGPUBindGroupDescriptor bindGroupDesc = WGPU_BIND_GROUP_DESCRIPTOR_INIT;
bindGroupDesc.entries = bindGroupEntries.data();
bindGroupDesc.entryCount = bindGroupEntries.size();
{{Continue describing bind group}}

WGPUBindGroup bindGroup = wgpuDeviceCreateBindGroup(device, &bindGroupDesc);
```

```{lit} C++, Create things (append, hidden)
{{Create bind group}}
```

There is one extra **important** thing to specify when we build a bind group, namely its **bind group layout**, which makes sure that the entries are compatible with the pipeline. We can retrieve the layout expected by the pipeline using `wgpuComputePipelineGetBindGroupLayout`:

```{lit} C++, Continue describing bind group
bindGroupDesc.layout = wgpuComputePipelineGetBindGroupLayout(pipeline, 0);
```

````{caution}
The layout is a **WebGPU object**, and getting it from the pipeline increases its internal reference count. We must thus **explicitly release** it once we no longer use it, namely right after `bindGroup` was created:

```{lit} C++, Create bind group (append)
wgpuBindGroupLayoutRelease(bindGroupDesc.layout);
```
````

```{note}
In this first shader example, we rely on the **automatic layout generation**. Since **we did not explicitly specify a layout** in the **pipeline descriptor**, WebGPU generated one for us. We will see later how to specify it ourselves to increase flexibility.
```

We now have our pipeline, our buffers and the bind group to connect them. We are **finally ready to invoke our shader**!

Invocation
----------

Like all GPU-side operation, running a shader is **invoked through the command queue**.

```{note}
You can remove the commands that we had so far between the creation of the `encoder` and its submission into the command queue.
```

If you look in `webgpu.h` at the methods of the encoder (the procedures starting with `wgpuCommandEncoder`), most of them are related to copying buffers and textures around. Except **two special ones**: `wgpuCommandEncoderBeginComputePass` and `wgpuCommandEncoderBeginRenderPass`. These return **specialized encoder objects**, namely `WGPUComputePassEncoder` and `WGPURenderPassEncoder`, that give access to commands dedicated to respectively **computing** and **3D rendering**.

In our case, we use a **compute pass**. We **begin** the pass, encode compute-specific commands, then **end** the pass. A soon as the pass ended, we can **release** it:

```{lit} C++, Add commands (replace)
WGPUComputePassEncoder computePass = wgpuCommandEncoderBeginComputePass(encoder, nullptr);
{{Add commands to compute pass}}
wgpuComputePassEncoderEnd(computePass);
wgpuComputePassEncoderRelease(computePass);
```

```{note}
The "end" procedure does not automatically release the pass object, because higher level WebGPU wrappers usually need to handle the release process in a specific way.
```

We first need to tell our compute pass **which compute pipeline** to use using its `setPipeline` method, and we also specify our **bind group** with `setBindGroup`:

```{lit} C++, Add commands to compute pass
wgpuComputePassEncoderSetPipeline(computePass, pipeline);
wgpuComputePassEncoderSetBindGroup(computePass, 0, bindGroup, 0, nullptr);
```

```{note}
As you can see, the same pipeline can easily run on different bind groups.
```

We can now instruct the GPU to run our pipeline by **dispatching a workgroups**. If you remember our discussion from the [*Concurrent threads*](#concurrent-threads) section above, a workgroup corresponds to **multiple threads** ($32 \times 1 \times 1$ in our case) and the number of workgroups is given by 3 values $x \times y \times z$. Since we want **one thread per element** in the buffer, we need to divide:

```{lit} C++, Add commands to compute pass (append)
uint32_t workgroupSizeX = 32; // the value specified in @workgroup_size(...)
uint32_t workgroupCountX = divideAndCeil((uint32_t)elementCount, workgroupSizeX);
wgpuComputePassEncoderDispatchWorkgroups(computePass, workgroupCountX, 1, 1);
```

The `divideAndCeil` function divides its arguments and ceils the result to the next integer value, to make sure that we have **at least** `elementCount` threads. We can define it as follows:

```{lit} C++, file: webgpu-utils.cpp (append)
uint32_t divideAndCeil(uint32_t p, uint32_t q) {
	return (p + q - 1) / q;
}
```

```{lit} C++, file: webgpu-utils.h (append, hidden)
/**
 * Divides p / q and ceil up to the next integer value
 */
uint32_t divideAndCeil(uint32_t p, uint32_t q);
```

Our pipeline finally runs! But remember that **we do not directly map the output buffer** back on the CPU, but rather a **staging buffer**. We must then **copy** our result to the staging buffer **after the end of the compute pass**:

```{lit} C++, Add commands (append)
// After the end of the compute pass, we copy the whole output buffer into the staging buffer
wgpuCommandEncoderCopyBufferToBuffer(encoder, outputBuffer, 0, stagingBuffer, 0, stagingBufferDesc.size);
```

And here we are, the result of our first shader is not so impressive, but we can congratulate ourselves!

```
Result: [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3,
3.2, 3.4, 3.6, 3.8, 4, 4.2, 4.4, 4.6, 4.8, 5, 5.2, 5.4, 5.6, 5.8, 6, 6.2, 6.4,
6.6, 6.8, 7, 7.2, 7.4, 7.6, 7.8, 8, 8.2, 8.4, 8.6, 8.8, 9, 9.2, 9.4, 9.6, 9.8,
10, 10.2, 10.4, 10.6, 10.8, 11, 11.2, 11.4, 11.6, 11.8, 12, 12.2, 12.4, 12.6]
```

Conclusion
----------

We learned here important concepts, including the **compute shader grid**, the **WGSL** language and the notion of **binding**. We can actually **do a lot** already with this compute pipeline, but I am sure you would also like to see some **graphics things**, so in the next chapters we will **open a window** and fill it with our **first color**.

*Resulting code:* [`step019-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step019-next)
