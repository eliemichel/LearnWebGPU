Playing with buffers <span class="bullet">🟢</span>
====================

```{lit-setup}
:tangle-root: 017 - Playing with buffers - Next
:parent: 015 - The Command Queue - Next
```

*Resulting code:* [`step017-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017-next)

We have seen how to send **instructions** to the GPU, and we now see how to send **data**.

In this chapter:

 - We see **how to allocate data buffers on the GPU**.
 - We see our first useful GPU command to **copy buffers**.

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

```{themed-figure} /images/playing-with-buffers/scenario_{theme}.svg
:align: center

In our simple **example scenario**, we copy a slice of Buffer A into Buffer B.
```

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
{{Create buffers}}
```

```{lit} C++, Create buffers
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
// Map Buffer A at creation in order to upload its initial value
bufferDescA.mappedAtCreation = true;
```

```{note}
Technically, the field `mappedAtCreation` has type `WGPUBool`, which is actually a `uint32_t` and not a `bool`. The **boolean** type is not a built-in type of C and it sometimes induces special behaviors in C++ (e.g., `std::vector<bool>` is something special) so it is usually not used in C APIs. Use `1` instead of `true` if you compiler complains.

In newer versions of WebGPU, macros `WGPU_TRUE` and `WGPU_FALSE` are defined to clarify this.
```

```{admonition} TODO
It is not required to specify usage `WGPUBufferUsage_MapWrite` to use `mappedAtCreation` actually!
```

### Freeing memory

If you ever played with manual allocation using `malloc` or `new`, you must know that **we always free our dynamically allocated memory**.

In the case of `WGPUBuffer`, its associated memory in VRAM is freed as soon as all references to it are released. We thus simply release our buffers:

```{lit} C++, Release buffers
// At the end of the program:
wgpuBufferRelease(bufferA);
wgpuBufferRelease(bufferB);
```

```{lit} C++, Release things (prepend, hidden)
{{Release buffers}}
```

Sometimes, we want to **force freeing VRAM memory** even if there may **remain references** to our buffers somewhere else in our program (for instance through a **bind group**, an object that we will discover later). For this, we may call `wgpuBufferDestroy(buffer)`. Other references to the buffer are then no longer usable.

Copying buffers
---------------

Our GPU buffers are allocated in VRAM, we can now populate Buffer A and proceed with the GPU-side copy operation.

### Initial value

Before copying, we need something to copy, so we will **set the initial value of `bufferA`**. Given that we had it **mapped at creation**, we can get **the address in (CPU-side) RAM** where it is mapped and simply write in there!

To get this address, we use the following function:

```C++
// The signature of the wgpuBufferGetMappedRange function as it is in webgpu.h
void * wgpuBufferGetMappedRange(WGPUBuffer buffer, size_t offset, size_t size);
```

As you can see, this can be used to map only a sub range of the buffer, but in our case we want to **map the whole buffer**, so we can use the special sentinel value `WGPU_WHOLE_MAP_SIZE` to mean exactly that:

```{lit} C++, Write initial value in Buffer A
// Get a pointer to the entire mapped buffer and interpret it as 8-bit unsigned integers
uint8_t* bufferDataA = static_cast<uint8_t*>(
	wgpuBufferGetMappedRange(bufferA, 0, WGPU_WHOLE_MAP_SIZE)
);
```

Note that I also **cast** the returned `void*` pointer into something we can actually write to, e.g., a `uint8_t` in this example. We can now simply **write whatever we want**:

```{lit} C++, Write initial value in Buffer A (append)
// Write 0, 1, 2, 3, ... in bufferA
for (size_t i = 0 ; i < 256 ; ++i) {
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

Okey, we have two buffers `bufferA` and `bufferB`, the former contains some values, and we want to **copy a slice** of it into the latter.

Copying buffers is done using `wgpuCommandEncoderCopyBufferToBuffer`. From the name of this function, we know that **this instruction is sent through the command encoder** object that we created in the previous chapter.

```{note}
This will **replace the calls** to `wgpuCommandEncoderInsertDebugMarker` that we used previously to mock instructions.
```

The full buffer copy command defines a **source** and a **destination buffer**, but also **the offset at which the copy starts** in both source and offset, and the overall **number of bytes to copy**:

```C++
// The signature of the wgpuCommandEncoderCopyBufferToBuffer function as it is in webgpu.h
void wgpuCommandEncoderCopyBufferToBuffer(
	WGPUCommandEncoder commandEncoder,
	WGPUBuffer source,
	uint64_t sourceOffset,
	WGPUBuffer destination,
	uint64_t destinationOffset,
	uint64_t size
);
```

```{themed-figure} /images/playing-with-buffers/copy_{theme}.svg
:align: center

The command copies `size` bytes from byte `sourceOffset` of buffer `source` into the bytes starting at `destinationOffset` in `destination`.
```

In our case, we copy `bufferDescB.size` bytes (because buffer B is smaller than buffer A), and let us say we start at an offset of 16 in the source:

```{lit} C++, Add commands (replace)
wgpuCommandEncoderCopyBufferToBuffer(
	encoder,
	bufferA,
	16, // sourceOffset
	bufferB,
	0, // destinationOffset
	bufferDescB.size
);
```

Did this work? The only way to know is to **read back the content of buffer B** and check that it contains $(16, 17, \dots, 47)$!

Reading back
------------

As you may have expected, **the only way** to read data back from the GPU is through an **asynchronous operation**. This is by design, because reading may take a lot of time (relatively to simple CPU operations).

### Asynchronous mapping

Reading from a buffer is done by **mapping it onto the CPU**. This is similar to the way we filled in our input buffer A above, except that this time **buffer B is not mapped by default**, so we need to ask for this with the following asynchronous operation:

```C++
// The signature of the wgpuBufferMapAsync function as it is in webgpu.h
WGPUFuture wgpuBufferMapAsync(
	WGPUBuffer buffer,
	WGPUMapMode mode, // can be WGPUMapMode_Read or WGPUMapMode_Write
	size_t offset,
	size_t size,
	WGPUBufferMapCallbackInfo callbackInfo
);
```

We first introduced asynchronous operations in chapter [*The Adapter*](adapter-and-device/the-adapter.md#asynchronous-function), so you should already guess how to use this and in particular the `callbackInfo`.

### Launching the operation

We call `wgpuBufferMapAsync` for our buffer B, with a map mode of `WGPUMapMode_Read` (read-only). Like we did above, we can use `WGPU_WHOLE_MAP_SIZE` to mean that we want to map the entire buffer:

```{lit} C++, Map buffer B
{{Define callback handling the mapped buffer B}}

{{Build callback info for mapping buffer B}}

// And finally we launch the asynchronous operation
wgpuBufferMapAsync(
	bufferB,
	WGPUMapMode_Read,
	0, // offset
	WGPU_WHOLE_MAP_SIZE,
	callbackInfo
);
```

What should we do in the callback? We can **check that the mapping is successful** and anyways let the rest of the program know that the operation ended:

```{lit} C++, Define callback handling the mapped buffer B
// Context passed to `onBufferBMapped` through theuserdata pointer:
struct OnBufferBMappedContext {
	bool operationEnded = false; // Turned true as soon as the callback is invoked
	bool mappingIsSuccessful = false; // Turned true only if mapping succeeded
};

// This function has the type WGPUBufferMapCallback as defined in webgpu.h
auto onBufferBMapped = [](
	WGPUMapAsyncStatus status,
	struct WGPUStringView message,
	void* userdata1,
	void* /* userdata2 */
) {
	OnBufferBMappedContext& context = *reinterpret_cast<OnBufferBMappedContext*>(userdata1);
	context.operationEnded = true;
	if (status == WGPUMapAsyncStatus_Success) {
		context.mappingIsSuccessful = true;
	} else {
		std::cout << "Could not map buffer B! Status: " << status << ", message: " << toStdStringView(message) << std::endl;
	}
};
```

````{note}
Instead of remembering the status of the map operation, we could **retrieve this information later** with `wgpuBufferGetMapState()`, e.g.:

```C++
if (wgpuBufferGetMapState(bufferB) == WGPUBufferMapState_Mapped) {
	// [...]
}
```
````

```{lit} C++, Build callback info for mapping buffer B
// We create an instance of the context shared with `onBufferBMapped`
OnBufferBMappedContext context;

// And we build the callback info:
WGPUBufferMapCallbackInfo callbackInfo = WGPU_BUFFER_MAP_CALLBACK_INFO_INIT;
callbackInfo.mode = WGPUCallbackMode_AllowProcessEvents;
callbackInfo.callback = onBufferBMapped;
callbackInfo.userdata1 = &context;
```

### Waiting for mapping

We can follow the same pattern than before, using `wgpuInstanceProcessEvents`.

```{note}
We could also use the approach proposed in the [*Futures and asynchronous operations*](../../appendices/futures-and-asynchronous-operations.md) appendix by using the `WGPUFuture` object returned by `wgpuBufferMapAsync()`.
```

```{lit} C++, Wait for mapping of buffer B
// Process events until the map operation ended
wgpuInstanceProcessEvents(instance);
while (!context.operationEnded) {
	sleepForMilliseconds(200);
	wgpuInstanceProcessEvents(instance);
}
```

Once the operation ended, and if it was successful, we can read and display our output buffer B on the CPU. **To recap**, here is the outline of our read back process:

```{lit} C++, Map and display buffer B
{{Map buffer B}}

{{Wait for mapping of buffer B}}

if (context.mappingIsSuccessful) {
	{{Display buffer B}}
}
```

````{note}
We add the mapping **at the end of the main body**, right before releasing things. Note that this **replaces** the "Wait for completion" of the previous chapter, since the mapping will always happen **after the previously submitted commands**.

```{lit} C++, Main body (append, hidden)
{{Map and display buffer B in main}}
```

```{lit} C++, Map and display buffer B in main (hidden)
{{Map and display buffer B}}
```

```{lit} C++, Wait for completion (replace, hidden)
// Removed
```
````

### Displaying output buffer

Now that the buffer B is mapped, we can **get its CPU-side address** like we did to fill in the input buffer A.

The **only difference** is that instead of `wgpuBufferGetMappedRange` we use `wgpuBufferGetConstMappedRange`, which returns a `const` pointer, because the buffer is mapped in **read-only** mode.

```{lit} C++, Display buffer B
// Get a (read-only) pointer to the buffer content
const uint8_t* bufferDataB = static_cast<const uint8_t*>(
	wgpuBufferGetConstMappedRange(bufferB, 0, WGPU_WHOLE_MAP_SIZE)
);
```

With this pointer in hand, we can simply **print its content**:

```{lit} C++, Display buffer B (append)
// Display
std::cout << "Buffer B: [";
for (size_t i = 0 ; i < bufferDescB.size ; ++i) {
	if (i > 0) std::cout << ", ";
	std::cout << static_cast<int>(bufferDataB[i]); // cast to display as int rather than char
}
std::cout << "]" << std::endl;
```

And finally we **unmap the buffer** once we no longer need it:

```{lit} C++, Display buffer B (append)
// Unmap
wgpuBufferUnmap(bufferB);
// Do NOT use bufferDataB beyond this point!
```

Finally, **you should see the following output**:

```
Buffer B: [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
```

Like we expected, the values from index 16 to 47 (= offset 16 + size 32 - 1) were copied from buffer A to buffer B, **congrats**!

Utility function
----------------

As we just saw, WebGPU provides a **very flexible API** to retrieve buffer data, but this comes at the cost of **some verbosity**. Since fetching data back from GPU buffers to CPU code is something that we will **commonly need**, I suggest we introduce a **dedicated utility function**.

We call this function `fetchBufferDataSync`, with the ending "Sync" meaning that this function **blocks the execution of our program** until it finishes its job (as opposed to "Async" functions).

```{note}
Such **synchronous functions** are convenient for debugging but can lead to performance limitations, which is why I suggest we **explicitly** write "Sync" in its name, to remember about it.
```

We declare this utility function in `webgpu-utils.h`, and take **3 arguments**:

```{lit} C++, file: webgpu-utils.h (append)
#include <functional>

/**
 * Fetch data from a GPU buffer back to the CPU.
 * This function blocks until the data is available on CPU, then calls the
 * `processBufferData` callback, and finally unmap the buffer.
 */
void fetchBufferDataSync(
	WGPUInstance instance,
	WGPUBuffer buffer,
	std::function<void(const void*)> processBufferData
);
```

The `buffer` is obviously the GPU resource that we want to fetch data from. The `instance` is needed to **wait for completion**, and the `processBufferData` is a C++ **callback** that `fetchBufferDataSync` calls when data is ready. This makes the function **flexible** by letting the caller tell what to do with the mapped data.

In our case, we use it in the main function to **display the content of buffer B**, which is now as **simple** as calling `fetchBufferDataSync`:

```{lit} C++, Map and display buffer B in main (replace)
// In main()
fetchBufferDataSync(instance, bufferB, [&](const void* data) {
	auto* bufferDataB = static_cast<const char*>(data);
	std::cout << "Buffer B: [";
	for (size_t i = 0 ; i < bufferDescB.size ; ++i) {
		if (i > 0) std::cout << ", ";
		std::cout << static_cast<int>(bufferDataB[i]); // cast to display as int rather than char
	}
	std::cout << "]" << std::endl;
});
```

```{note}
In order to access `bufferDescB` from inside the callback, we need to **capture** it. With `[&]`, we capture (by reference) everything that is in the local scope where `fetchBufferDataSync` is called.

This is something we **cannot** do when manipulating the raw C callbacks expected by the WebGPU API. Capturing functions are a mechanism that C++ provides to automate what C callbacks do with "userdata" pointers.
```

As for the implementation of `fetchBufferDataSync` in `webgpu-utils.cpp`, we simply copy what we wrote in the previous [*Reading back*](#reading-back) section above:

```{lit} C++, file: webgpu-utils.cpp (append)
void fetchBufferDataSync(
	WGPUInstance instance,
	WGPUBuffer bufferB,
	std::function<void(const void*)> processBufferData
) {
	// We copy here what used to be in main():
	{{Map and display buffer B}}
}
```

```{caution}
In order to "just copy-paste" the body of this function, the second argument of `fetchBufferDataSync` is called `bufferB` instead of `buffer`. You may alternatively rename all occurrences of `bufferB` into `buffer` to make things cleaner.
```

There is **one thing to change** though, which is the moment we displayed the mapped buffer. Instead, for this utility function, we just call the `processBufferData` function that was provided:

```{lit} C++, Display buffer B (replace)
const void* bufferData = wgpuBufferGetConstMappedRange(bufferB, 0, WGPU_WHOLE_MAP_SIZE);
processBufferData(bufferData);
```

You can try running your program again: it should not change anything, but we now have this convenient `fetchBufferDataSync()` in our toolbox!

Conclusion
----------

We know how to **allocate**, **populate**, **copy* and **read back** values from **GPU-side buffers**. This is an important base because it allows us to **transfer significant information** back and forth with the GPU.

Note that buffers are **not the only type of memory** object on the GPU: there are also **textures**, which we will see later on. Think of textures as a chunk of memory with even **more detailed information about its intended usage**, which enables the use of dedicated circuits in the hardware.

Buffer are nonetheless enough to start **running operations on the GPU**, which we will do in [*Our first shader*](our-first-shader.md). But one last chapter before that: let us learn to **deal with errors**!

*Resulting code:* [`step017-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017-next)
