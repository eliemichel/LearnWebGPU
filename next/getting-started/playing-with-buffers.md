Playing with buffers <span class="bullet">🟠</span>
====================

```{lit-setup}
:tangle-root: 017 - Playing with buffers - Next
:parent: 015 - The Command Queue - Next
:debug:
```

*Resulting code:* [`step017-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017-next)

We have seen how to send **instructions** to the GPU, and we now see how to send **data**.

In this chapter:

 - We see **how to allocate data buffers on the GPU**.
 - We see our first useful GPU command to **copy buffers**.
 - We refine our control of **asynchronous operations** to retrieve data from the GPU.

Memory allocation
-----------------

Allocating memory on the GPU (in the VRAM) is slightly more complex than allocating memory on the CPU (in the RAM).

### Recall about CPU-side allocation

When we talk about (dynamic) memory allocation on CPU, we may think of something like this:

```C++
// Allocation in RAM
char* buffer = (char*)malloc(256); // C
char* buffer = new char[256]; // C++
auto buffer = std::vector<char>(256); // C++ using STL
```

The `malloc` function, and everything that is built on top of is like the C++ `new[]` operator or the **default allocator** from the *standard template library* (STL), is seen as a low-level black box that **asks the OS for some contiguous memory buffer**.

In most cases, the level of abstraction of these is enough, and we do not need control about where/how this memory is allocated.

It is nonetheless possible to go **lower level** and for instance implement a custom [`std::allocator`](https://en.cppreference.com/w/cpp/memory/allocator) so that we can inform the runtime about our intended **usage** of this memory, which it can use to **find a more appropriate place** in its memory.

We will **not** do custom allocation on the C++ side, but I mention all this to help justifying how things work on the GPU side.

```{note}
We talk here about **dynamic allocation**, where the allocation may depend on runtime inputs. This is opposed to static allocation, like when declaring `char buffer[256];`, which is known at **compile time** and thus handled differently.

In case of GPU memory, static allocation happens when compiling shaders (see next chapter), but our C++ code can only interact with dynamically allocated data.
```

### GPU-side allocation

Because GPU programs are highly parallel, they process **a lot of data**, to a point where **data transfers** within the GPU (between computing units and VRAM) is often the **limiting bottleneck** of our programs.

For this reason, we **always specify an intended usage** when allocating data on the GPU!

Let us get practical: to allocate data, we create a `WGPUBuffer` object, which follows the usual object creation idiom:

```{lit} C++, Create buffer A
// 1. We build a descriptor (called 'A' because we will have multiple buffers)
WGPUBufferDescriptor bufferDescA = WGPU_BUFFER_DESCRIPTOR_INIT;
{{Fill in buffer descriptor A}}

// 2. We create the buffer from its descriptor
WGPUBuffer bufferA = wgpuDeviceCreateBuffer(device, &bufferDescA);
```

First of all, we of course need to specify the **size of the buffer**, like we do when calling `malloc`:

```{lit} C++, Fill in buffer descriptor A
bufferDescA.size = 256;
```

Then, as described above, we tell the device **how we intend to use this buffer**. The usage is given as a **bitmask**, i.e., an integer where each bit is a flag, that we can **combine** with others. The following bits are defined (comments are mine):

```C++
// Definition of WGPUBufferUsage bit flags values in webgpu.h

// The buffer can be *mapped* to be *read* on the CPU side
static const WGPUBufferUsage WGPUBufferUsage_MapRead = 0x0000000000000001;

// The buffer can be *mapped* to be *written* on the CPU side
static const WGPUBufferUsage WGPUBufferUsage_MapWrite = 0x0000000000000002;

// The buffer can be used as the *source* of a GPU-side copy operation
static const WGPUBufferUsage WGPUBufferUsage_CopySrc = 0x0000000000000004;

// The buffer can be used as the *destination* of a GPU-side copy operation
static const WGPUBufferUsage WGPUBufferUsage_CopyDst = 0x0000000000000008;

// The buffer can be used as an Index buffer when doing indexed drawing in a render pipeline
static const WGPUBufferUsage WGPUBufferUsage_Index = 0x0000000000000010;

// The buffer can be used as an Vertex buffer when using a render pipeline
static const WGPUBufferUsage WGPUBufferUsage_Vertex = 0x0000000000000020;

// The buffer can be bound to a shader as a uniform buffer
static const WGPUBufferUsage WGPUBufferUsage_Uniform = 0x0000000000000040;

// The buffer can be bound to a shader as a storage buffer
static const WGPUBufferUsage WGPUBufferUsage_Storage = 0x0000000000000080;

// The buffer can store arguments for an indirect draw call
static const WGPUBufferUsage WGPUBufferUsage_Indirect = 0x0000000000000100;

// The buffer can store the result of a timestamp or occlusion query
static const WGPUBufferUsage WGPUBufferUsage_QueryResolve = 0x0000000000000200;
```

```{note}
**Only the first usages** make sens to us for now, we will progressively discover what the others mean in later chapters.
```

The **rule of thumb** is simple: **only specify the flags you really need**. If you miss one, WebGPU will complain with a message that should hint you about the missing usage flag.

At this point, we need a little scenario for our example, so that we can determine a usage.

Simple example
--------------

Let us say we want to **create 2 buffers**, **write** data in the first one (`bufferA`), **copy** it into the second one (`bufferB`) on the GPU-side, and finally **read** `bufferB` back on the CPU.

So, we create a second buffer, with a second descriptor:

```{lit} C++, Create buffer B
// We build a second buffer, called B
WGPUBufferDescriptor bufferDescB = WGPU_BUFFER_DESCRIPTOR_INIT;
{{Fill in buffer descriptor B}}
WGPUBuffer bufferB = wgpuDeviceCreateBuffer(device, &bufferDescB);
```

````{note}
We create buffers **before the command encoding test** from previous chapter:

```{lit} C++, Create things (append)
// Before encoding commands:
{{Create buffer A}}
{{Create buffer B}}
{{Write initial value in Buffer A}}
```
````

To makes things **slightly more interesting**, I will make buffer B shorter than buffer A, so that **we only copy a slice** of buffer A into buffer B.

```{lit} C++, Fill in buffer descriptor B
// buffer B is shorter than buffer A in this example
bufferDescB.size = 32;
```

```{note}
We could also **reuse** the same `WGPUBufferDescriptor` struct for both buffer creations, but using a separate one is clearer for the context of this guide.
```

### Usage

Back to the question of usage, we now know what to specify:

```{lit} C++, Fill in buffer descriptor A (append)
// Buffer A is *written* on CPU, and used as *source* of a GPU-side copy
bufferDescA.usage = WGPUBufferUsage_MapWrite | WGPUBufferUsage_CopySrc;
```

```{lit} C++, Fill in buffer descriptor B (append)
// Buffer B is *read* on CPU, and used as *destination* of a GPU-side copy
bufferDescB.usage = WGPUBufferUsage_MapRead | WGPUBufferUsage_CopyDst;
```

Note how the **pipe operator** (`|`, also called *bitwise OR*) is used to combine the usage flags together.

### Labels

We could stop here with descriptors: specifying a **byte size** and a **usage** is all the device requires to allocate a buffer.

It is however **good practice** to take benefit from the possibility to **name** our objects, especially now that we have 2 objects of the same nature (2 buffers). This greatly **helps understanding error messages**.

```{lit} C++, Fill in buffer descriptor A (append)
bufferDescA.label = toWgpuStringView("Buffer A");
```

```{lit} C++, Fill in buffer descriptor B (append)
bufferDescB.label = toWgpuStringView("Buffer B");
```

### Initial mapping state

There is one **last field** in the buffer descriptor which tells whether the buffer is *mapped* to the CPU side upon its creation. **Mapping a buffer** means to make it temporarily available on the CPU side, although it is a GPU buffer.

The `mappedAtCreation` field is of course only relevant for buffers that have declared a **mapping usage** (`MapWrite` or `MapRead`), and is only really useful for the `MapWrite` case.

In order to write the initial value of our `bufferA`, we are interested in having it mapped at creation:

```{lit} C++, Fill in buffer descriptor A (append)
bufferDescA.mappedAtCreation = true;
```

```{note}
Technically, the field `mappedAtCreation` has type `WGPUBool`, which is actually a `uint32_t` and not a `bool`. The **boolean** type is not a built-in type of C and it sometimes induces special behaviors in C++ (e.g., `std::vector<bool>` is something special) so it is usually not used in C APIs. Use `1` instead of `true` if you compiler complains.

In newer versions of WebGPU, macros `WGPU_TRUE` and `WGPU_FALSE` are defined to clarify this.
```

### Freeing memory

If you ever played with manual allocation using `malloc` or `new`, you must know that **we must always free our dynamically allocated memory**.

In the case of `WGPUBuffer`, its associated memory in VRAM is freed as soon as all references to it are released. We thus simply release our buffers:

```{lit} C++, Release things (prepend)
wgpuBufferRelease(bufferA);
wgpuBufferRelease(bufferB);
```

Sometimes, we want to **force freeing VRAM memory** even if there may **remain references** to our buffers somewhere else in our program (for instance through a **bind group**, an object that we will discover later). For this, we may call `wgpuBufferDestroy(buffer)`. Other references to the buffer are then no longer usable.

Copying buffers
---------------

Our GPU buffers are allocated in VRAM, we can now proceed with the GPU-side copy operation.

### Initial value

Before copying, we need something to copy, so we will **set the initial value of `bufferA`**. Given that we had it **mapped at creation**, we can get **the address in RAM** where it is mapped and simply write in there!

To get this address, we use the following function:

```C++
// The signature of the wgpuBufferGetMappedRange function as it is in webgpu.h
void * wgpuBufferGetMappedRange(WGPUBuffer buffer, size_t offset, size_t size);
```

As you can see, this can be used to map only a sub range of the buffer, but in our case we want to **map the whole buffer**, so we can use the special sentinel value `WGPU_WHOLE_MAP_SIZE` to mean exactly that:

```{lit} C++, Write initial value in Buffer A
uint8_t* bufferDataA = (uint8_t*)wgpuBufferGetMappedRange(bufferA, 0, WGPU_WHOLE_MAP_SIZE);
```

Note that I also **cast** the returned `void*` pointer into something we can actually write to, e.g., a `uint8_t` in this example. We can now simply write whatever we want:

```{lit} C++, Write initial value in Buffer A (append)
// Write 0, 1, 2, 3, ... in bufferA
for (int i = 0 ; i < 256 ; ++i) {
	bufferDataA[i] = static_cast<uint8_t>(i);
}
```

```{caution}
In this simple example, we write elements of type `uint8_t` whose **byte size is exactly 1** (and can have values up to 255). If we would use a **larger type** we would need to adapt the byte size of the buffer. For instance, we should allocate `256 * sizeof(int)` bytes if we want our buffer to store 256 integers.
```

**Importantly**, we must **unmap** the buffer once we no longer need it on the CPU side, **before doing anything else** with it!

```{lit} C++, Write initial value in Buffer A (append)
wgpuBufferUnmap(bufferA);
// Do NOT use bufferDataA beyond this point!
```

```{note}
There are **other ways** to set the initial value of a buffer. If you want to **copy from another CPU buffer**, you can use [`wgpuBufferWriteMappedRange`](https://webgpu-native.github.io/webgpu-headers/group__WGPUBufferMethods.html#ga77b3a18397655692488536b0e4186de7) when the buffer is mapped, or even [`wgpuQueueWriteBuffer`](https://webgpu-native.github.io/webgpu-headers/group__WGPUQueueMethods.html#gaaa2dfc15dc7497ea8e9011f940f4dcf0), which only requires usage `CopyDst`.
```

### Copy operation

**WIP** *In this version of the guide, this chapter moves back in the "getting started" section, between command queue and the first (compute) shader.*

```C++
void wgpuCommandEncoderCopyBufferToBuffer(
	WGPUCommandEncoder commandEncoder,
	WGPUBuffer source,
	uint64_t sourceOffset,
	WGPUBuffer destination,
	uint64_t destinationOffset,
	uint64_t size
);
```

```{lit} C++, Add commands (replace)
wgpuCommandEncoderCopyBufferToBuffer(
	encoder,
	bufferA,
	16,
	bufferB,
	0,
	bufferDescB.size
);
```

TODO: FIGURE!

TODO: LIMITS!

Troubleshooting
---------------

In this section, we intentionally create errors and see what error message it gives. This is a good practice when learning an API, so that we can then more easily recognize these messages later on, when they occur in more complex scenarios.

Asynchronous operations
-----------------------

##### The good way

**To keep track of ongoing asynchronous operations**, each function that starts such an operation **returns a `WGPUFuture`**, which is some sort of internal ID that **identifies the operation**:

```C++
WGPUFuture adapterRequest = wgpuInstanceRequestAdapter(instance, &options, callbackInfo);
```

```{note}
Although it is technically just an integer value, the `WGPUFuture` should be treated as an **opaque handle**, i.e., one should not try to deduce anything from the very value of this ID.
```

This *future* can then be passed to `wgpuInstanceWaitAny` to mean "wait until this asynchronous operation completes"! Here is the signature of `wgpuInstanceWaitAny`:

```C++
WGPUWaitStatus wgpuInstanceWaitAny(WGPUInstance instance, size_t futureCount, WGPUFutureWaitInfo * futures, uint64_t timeoutNS);
```

```C++
uint64_t timeoutNS = 200 * 1000; // 200 ms
WGPUWaitStatus status = wgpuInstanceWaitAny(instance, 1, &adapterRequest, timeoutNS);
```

*Resulting code:* [`step017-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017-next)
