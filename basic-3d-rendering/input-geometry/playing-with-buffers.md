Playing with buffers
====================

*Resulting code:* [`step018`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step018)

Before feeding vertex data to the render pipeline, we need to get familiar with the notion of **buffer**. A buffer is "just" a chunk of memory allocated in the VRAM (the GPU's memory). Think of it as some kind of `new` or `malloc` for the GPU.

One notable difference is that we must state some hint about our use of this memory upon its creation. For instance, if we are going to use it only to write it from the CPU but never to read it back, we set its `CopyDst` flag on but not the `CopySrc` flag. This not fully agnostic memory management helps the device figure out the best memory layout.

```{note}
Note that textures are a special kind of memory (because of the way we usually sample them) that they live in a different kind of object.
```

Creating a buffer
-----------------

The overall structure of the buffer creation will surprise no one now:

```C++
WGPUBufferDescriptor bufferDesc = {};
bufferDesc.nextInChain = nullptr;
bufferDesc.label = "Some GPU-side data buffer";
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_CopySrc;
bufferDesc.size = 16;
bufferDesc.mappedAtCreation = false;
WGPUBuffer buffer1 = wgpuDeviceCreateBuffer(device, &bufferDesc);
```

```{note}
A GPU buffer is *mapped* when it is connected to a specific part of the CPU-side RAM. The driver then automatically synchronizes its content, either for reading or for writing. We will not use it here.
```

For our little exercise, create a second buffer, called `buffer2`. We will load data in the first buffer, issue a copy command so that the GPU copies data from one to another, then read the destination buffer back.

Also, don't forget to free your buffers once you no longer use them:

```C++
wgpuBufferDestroy(buffer1);
wgpuBufferDestroy(buffer2);
```

Writing to a buffer
-------------------

Let us simply use the `wgpuQueueWriteBuffer` function that we noticed earlier:

```C++
// Create some CPU-side data buffer (of size 16 bytes)
std::vector<unsigned char> numbers(16);
for (unsigned char i = 0; i < 16; ++i) numbers[i] = i;

// Copy this from `numbers` (RAM) to `buffer1` (VRAM)
wgpuQueueWriteBuffer(queue, buffer1, 0, numbers.data(), numbers.size());
```

Do this before submitting the command queue, in which you can add a `wgpuCommandEncoderCopyBufferToBuffer` command:

```C++
wgpuCommandEncoderCopyBufferToBuffer(encoder, buffer1, 0, buffer2, 0, 16);
```

```{important}
Make sure that command encoding operations are called before `wgpuCommandEncoderFinish`!
```

Reading from a buffer
---------------------

We cannot just use the command queue to read memory back from the GPU, because this is a "fire and forget" queue: functions do not return a value since they are run on a different timeline.

Instead, we use an asynchronous operation, namely `wgpuBufferMapAsync`. This operation maps the GPU buffer into CPU memory, and then executes the callback function it was provided. This makes the programming workflow more complicated than synchronous operations, but once again it is important to minimize wasteful processor idling.

Let us first change the `usage` of the second buffer by adding the `WGPUBufferUsage_MapRead` flag, so that the buffer can be mapped for reading:

```C++
bufferDesc2.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_MapRead;
```

```{note}
The `WGPUBufferUsage_MapRead` flag is not compatible with `WGPUBufferUsage_CopySrc` one, so make sure not to have both at the same time.
```

We can now call the buffer mapping with a simple callback:

```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /*pUserData*/) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```

### Asynchronous polling

If you run the program at this point, you might be surprised (and disappointed) to see that the callback is **never executed**! This is because there is no hidden process executed by the WebGPU library to check that the async operation is ready. Instead, the backend checks for ongoing async operations only when we call another operation, so we will add in the main loop a simple operation that does nothing:

```C++
while (!glfwWindowShouldClose(window)) {
	// Do nothing, this checks for ongoing asynchronous operations and call their callbacks if needed
	wgpuQueueSubmit(queue, 0, nullptr);
	// (This is the same idea, for the GLFW library callbacks)
	glfwPollEvents();
}
```

```{note}
Our wgpu-native backend provides a more explicit but non-standard `wgpuDevicePoll(device)` to do "nothing but check on async jobs" operation. This kind of extension is provided in the `wgpu.h` header.
```

```{warning}
Make sure the calls to `wgpuBufferDestroy` are issued *after* the main loop, otherwise the callback will be called with status `WGPUBufferMapAsyncStatus_DestroyedBeforeCallback`.
```

### Mapping context

You should now see `Buffer 2 mapped with status 0` (0 being the value of `WGPUBufferMapAsyncStatus_Success`) when running your program.

Now, we need to get more than a status when running this callback, we need to access the buffer. We will thus use the `void *userdata` pointer communicated from the original call to `wgpuBufferMapAsync` to the callback, like we did in [the adapter request](../../getting-started/the-adapter.md) or [the device request](../../getting-started/the-device.md):


```C++
// The context shared between this main function and the callback.
struct Context {
	WGPUBuffer buffer;
};

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	Context* context = reinterpret_cast<Context*>(pUserData);
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
	if (status != WGPUBufferMapAsyncStatus_Success) return;

	// Get a pointer to wherever the driver mapped the GPU memory to the RAM
	unsigned char* bufferData = (unsigned char*)wgpuBufferGetMappedRange(context->buffer, 0, 16);

	// [...] (Do stuff with bufferData)

	// Then do not forget to unmap the memory
	wgpuBufferUnmap(context->buffer);
};

Context context = { buffer2 };
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, (void*)&context);
```

For instance we can just display the content of the buffer and check that it corresponds to our initially fed buffer data:

```C++
std::cout << "bufferData = [";
for (unsigned char i = 0; i < 16; ++i) {
	if (i > 0) std::cout << ", ";
	std::cout << bufferData[i];
}
std::cout << "]" << std::endl;
```

```{note}
In such a simple example, we could spare ourselves the need to define a `Context struct` and just pass the address of the `buffer` object as the value of `pUserData` (or even the `buffer` object itself, as it is a pointer already).
```

Conclusion
----------

Congratulations! We were able to create a GPU-side memory buffer, upload data into it, copy it remotely (operation triggered from the CPU, but executed on the GPU) using the command queue and download data back from the GPU.

We have seen a number of important notions in this chapter:

 - timelines
 - command queue
 - command encoder
 - buffers
 - asynchronous operations

We can now use a buffer to specify vertex attributes, in particular vertex positions!

*Resulting code:* [`step018`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step018)
