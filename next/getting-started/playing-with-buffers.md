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
 - We try breaking things to **get familiar with error messages**.

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

### Freeing memory

If you ever played with manual allocation using `malloc` or `new`, you must know that **we always free our dynamically allocated memory**.

In the case of `WGPUBuffer`, its associated memory in VRAM is freed as soon as all references to it are released. We thus simply release our buffers:

```{lit} C++, Release things (prepend)
wgpuBufferRelease(bufferA);
wgpuBufferRelease(bufferB);
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

Asynchronous read back
----------------------

As you may have expected, **the only way** to read data back from the GPU is through an **asynchronous operation**. This is by design, because reading may take a lot of time (relatively to simple CPU operations).

### Mapping

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

At this stage, **you should see the following output**:

```
Buffer B: [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
```

Like we expected, the values from index 16 to 47 (= offset 16 + size 32 - 1) were copied from buffer A to buffer B, **congrats**!

Troubleshooting
---------------

> 😃 **I did not have any trouble**, I followed the wonderful instructions above and it **just worked**!

Congrats, and thank you! **But** as you'll gradually want to **experiment by yourselves**, it is import to **get familiar with the cases of error** that can happen when playing with buffers.

In this section, **we intentionally create errors** and see what error message it gives. This is a good practice when learning an API, so that we can then **more easily recognize these messages later on**, when they occur in more complex scenarios.

### Wrong usage

A very typical issue is to **forget about one of the usages** of a buffer. Let us introduce an error by **forgetting the `CopySrc` usage**:

```C++
//bufferDescA.usage = WGPUBufferUsage_MapWrite | WGPUBufferUsage_CopySrc; // GOOD
bufferDescA.usage = WGPUBufferUsage_MapWrite; // BAD
```

If we run our program now, the **uncaptured error callback** that we have defined in [*The Device*](adapter-and-device/the-device.md) gets invoked twice:

```
Uncaptured error in device 00000058E3F3F1A0: type 2 ([Buffer "Buffer A"] usage (BufferUsage::MapWrite) doesn't include BufferUsage::CopySrc.
 - While validating source [Buffer "Buffer A"] usage.
 - While encoding [CommandEncoder "My command encoder"].CopyBufferToBuffer([Buffer "Buffer A"], 16, [Buffer "Buffer B"], 0, 32).
 - While finishing [CommandEncoder "My command encoder"].
)
Submitting command...
Uncaptured error in device 00000058E3F3F190: type 2 ([Invalid CommandBuffer "Command buffer" from CommandEncoder "My command encoder"] is invalid.
 - While calling [Queue "The Default Queue"].Submit([[Invalid CommandBuffer "Command buffer" from CommandEncoder "My command encoder"]])
)
```

```{note}
The very format of error message **varies with the implementation**. Here I report what I get using Dawn.
```

### Reading error messages

In general, always **investigate the first error first**. In all likelihood, the other errors are consequences of the first one. Let's focus on that first one then, and let me recall **the content of our error callback**:

```C++
// Content of our error callback:
std::cout
	<< "Uncaptured error in device " << device << ": type " << type
	<< " (" << toStdStringView(message) << ")"
	<< std::endl;
```

The first thing that comes is the **device pointer** `00000058E3F3F1A0`. We only have a single device anyways, so it is not that useful in our case.

Then comes the **error type**, which is just "2". Not very informative, until we inspect the definition of the `WGPUErrorType` enum in `webgpu.h`:

```C++
// The enum WGPUErrorType as defined in webgpu.h
enum WGPUErrorType {
    WGPUErrorType_NoError = 0x00000001,
    WGPUErrorType_Validation = 0x00000002,
    WGPUErrorType_OutOfMemory = 0x00000003,
    WGPUErrorType_Internal = 0x00000004,
    WGPUErrorType_Unknown = 0x00000005,
    WGPUErrorType_Force32 = 0x7FFFFFFF
};
```

```{note}
You may want to write a utility function that **maps each value to a string name** of the error type. Later in this guide I introduce [`magic_enum`](https://github.com/Neargye/magic_enum) which does that automatically for any enum.
```

Here we have a **validation** error (2). This means that what we are trying to do is **not the correct use** of the API, and this is something that **the WebGPU implementation** (Dawn, wgpu-native, etc.) checks to prevent you the trouble of the cascade of unintended consequences that it could have in lower level layers.

Lastly, and this is the most helpful part, we have the **error message**. In Dawn, the error message **reads top down** to go **from the specific issue to the broader context** in which the error occurred. The first lines (the specific one) is already quite helpful:

```
[Buffer "Buffer A"] usage (BufferUsage::MapWrite) doesn't include BufferUsage::CopySrc.
```

```{note}
The name `"Buffer A"` here comes directly from us, it is **the label we have assigned** to the buffer that is causing trouble. **Always label your objects**, it will save you a lot of time!
```

The message is quite clear: the usage we declared, namely `(BufferUsage::MapWrite)`, does not include `CopySrc`. Why does this matter? The **context lines** bellow tell us why!

The error happens because we WebGPU tries to validate the usage of the buffer that **we use as the source** of a `CopyBufferToBuffer` operation:

```
- While validating source [Buffer "Buffer A"] usage.
- While encoding [CommandEncoder "My command encoder"].CopyBufferToBuffer([Buffer "Buffer A"], 16, [Buffer "Buffer B"], 0, 32).
- While finishing [CommandEncoder "My command encoder"].
```

Nice and helpful! And again, naming things really helps.

> 🤔 But **I don't remember** where I call this `CopyBufferToBuffer`. Or maybe this **happens multiple times** in my program and **I don't know which one is causing the issue**...

There is a solution to that, let's go further with debugging then!

### Investigating the call stack

The error handler is a function that we wrote ourselves and that lives in our code. The good thing about this is that we can then use **breakpoints** to get **insights about the execution of our program** at the time of the error.

```{tip}
I strongly encourage you to always **set up a breakpoint** in your device's *uncaptured error callback*.
```

In a visual IDE, adding a breakpoint is typically done by **clicking in the margin** of the source code view (see screenshot below). You can also use **command line debuggers** (e.g., [`gdb`](https://sourceware.org/gdb/)), in which case you must type in the file name and line number where to break.

```{figure} /images/playing-with-buffers/ide-breakpoint.jpg
:align: center
:class: with-shadow
Once **debugging symbols** are enabled (1), we can use **breakpoints** (2) to **inspect our program's state** whenever there is an error.
```

```{note}
The screenshots used here demonstrate debugging with **Visual Studio**, but **all major C++ IDEs and debugger** provide the same concept of **breakpoint** and **call stack**. Refer to your IDE's documentation for more details.

To **enable debugging** symbols with build tools that **do not support multiple Debug/Release configuration** (e.g., make, ninja), you must configure your build with the `-DCMAKE_BUILD_TYPE=Debug` option **when invoking CMake**.
```

Once you have a breakpoint, run your program as usual, and it should **automatically pause** when the execution process reaches the line with a breakpoint. Once this is the case, you can **inspect the call stack** that gives information about the context of the error:

```{figure} /images/playing-with-buffers/ide-callstack.jpg
:align: center
:class: with-shadow
Our first triangle rendered using WebGPU.
```

```{admonition} Visual Studio
If you do not find the *Call Stack* panel in Visual studio, go to "Debug > Windows > Call Stack".
```

Here again, the stack **reads top-down** to go from specific to generic. The top-most row is the very line of your breakpoint, the next one tells you **what function call led you here**, and what parent call led you to that call, and so on.

**In my screenshot above**, we see that the breakpoint is located inside **a lambda function** (the `onDeviceError` lambda we passed to the device descriptor), which is **called by some `[External Code]`** (namely internal bits of the WebGPU implementation, which was built without debug symbols so it's just called "external code"), which is in turned **called by line 181 in my `main()` function**.

Going to that line (**double clicking** on the row in the call stack may quickly take you there), we finally **locate the guilty line of code**!

```{figure} /images/playing-with-buffers/ide-line181.jpg
:align: center
:class: with-shadow
We found **the very line of code** that triggered the error!
```

As you can see, the error that triggered the failed buffer usage verification is a call to `wgpuCommandEncoderFinish()`. This **exactly matches the bottom-most line of the WebGPU error message**! Overall, if we **glue together** the WebGPU error and the IDE call stack, we have a **full view of the chain of events** that led to our error.

### Accessing a buffer that is not mapped

Okey, let is try a new intentional error: what if we **forget to map the buffer A at creation**, but still try to write into its content?

```C++
//bufferDescA.mappedAtCreation = true; // GOOD
bufferDescA.mappedAtCreation = false; // BAD
```

This time, **no invocation of the uncaptured error callback**. But no result neither: **our program crashes**! More specifically, it raises a **segmentation fault** with a message that may look like "*Access violation writing location 0x0000000000000000*".

If you use a debugger or if you print in the console the content of your variables, you will realize that `bufferDataA` is a **null pointer**! Indeed, this is the way `wgpuBufferGetMappedRange` **reports that it could not map** the requested buffer (see [documentation](https://webgpu-native.github.io/webgpu-headers/BufferMapping.html#MappedRangeBehavior)).

In this case, the error is **not as clear as previously**, so that is why we are doing this exercise of intentionally triggering errors. Remember that when `wgpuBufferGetMappedRange` returns a null pointer, **you probably forgot to map it** (or already unmapped it).

### Wrong buffer bounds

Another example? Try messing up with the arguments of `wgpuCommandEncoderCopyBufferToBuffer`!

For instance, if I set a size that exceeds the length of the destination buffer (e.g., replace `bufferDescB.size` with `bufferDescB.size + 10` as the last argument), my **error callback** gets invoked with the following message:

```
Copy range (offset: 0, size: 42) does not fit in [Buffer "Buffer B"] size (32).
 - While validating destination [Buffer "Buffer B"] copy size.
 - While encoding [CommandEncoder "My command encoder"].CopyBufferToBuffer([Buffer "Buffer A"], 16, [Buffer "Buffer B"], 0, 42).
 - While finishing [CommandEncoder "My command encoder"].
```

The error is clear since we **correctly labeled our objects**: the range we are trying to copy does not fit in the destination buffer B. And we know how to precisely locate the location of the error now, so we can easily fix it!

### Failing to unmap a buffer

What if we forget to unmap buffer A before the copy?

```C++
//wgpuBufferUnmap(bufferA);
```

We get a clear error message:

```
[Buffer "Buffer A"] used in submit while mapped.
 - While calling [Queue "The Default Queue"].Submit([[CommandBuffer "Command buffer" from CommandEncoder "My command encoder"]])
```

Note that the error occurs **while submitting the command buffer**. It is totally possible to build this command buffer (using the command encoder) while the buffer is still mapped, what matters is that it is no longer mapped **when the instructions are actually sent** to the device.

### Limits

**WIP** TODO And maybe move the whole troubleshooting section to a dedicated chapter.

```{note}
To **learn more about error handling in WebGPU**, you can consult [the dedicated article](https://webgpu-native.github.io/webgpu-headers/Errors.html) in the official documentation of the WebGPU C API.
```

Conclusion
----------

NB: Buffers are not the only type of memory, there are also textures

*Resulting code:* [`step017-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017-next)
