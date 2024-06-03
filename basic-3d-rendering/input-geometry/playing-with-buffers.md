Playing with buffers
====================

```{admonition} 🚧 WIP
From this chapter on, the guide uses a previous version of the accompanying code (in particular, it does not define an `Application` class but rather puts everything in a monolithic `main` function). **I am currently refreshing it** chapter by chapter and this is **where I am currently working**!
```

````{tab} With webgpu.hpp
*Resulting code:* [`step031`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step031-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031-vanilla)
````

Before feeding vertex data to the render pipeline, we need to get familiar with the notion of **buffer**. A buffer is "just" a chunk of memory allocated in the VRAM (the GPU's memory). Think of it as some kind of `new` or `malloc` for the GPU.

One notable difference is that we must state some hint about our use of this memory upon its creation. For instance, if we are going to use it only to write it from the CPU but never to read it back, we set its `CopyDst` flag on but not the `CopySrc` flag. This not fully agnostic memory management helps the device figure out the best memory layout.

```{note}
Note that textures are a special kind of memory (because of the way we usually sample them) that they live in a different kind of object.
```

Creating a buffer
-----------------

The overall structure of the buffer creation will surprise no one now:

````{tab} With webgpu.hpp
```C++
BufferDescriptor bufferDesc;
bufferDesc.label = "Some GPU-side data buffer";
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::CopySrc;
bufferDesc.size = 16;
bufferDesc.mappedAtCreation = false;
Buffer buffer1 = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUBufferDescriptor bufferDesc = {};
bufferDesc.nextInChain = nullptr;
bufferDesc.label = "Some GPU-side data buffer";
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_CopySrc;
bufferDesc.size = 16;
bufferDesc.mappedAtCreation = false;
WGPUBuffer buffer1 = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

```{note}
A GPU buffer is *mapped* when it is connected to a specific part of the CPU-side RAM. The driver then automatically synchronizes its content, either for reading or for writing. We will not use it here.
```

For our little exercise, create a second buffer, called `buffer2`. We will load data in the first buffer, issue a copy command so that the GPU copies data from one to another, then read the destination buffer back.

Also, don't forget to free your buffers once you no longer use them:

````{tab} With webgpu.hpp
```C++
buffer1.destroy();
buffer2.destroy();

buffer1.release();
buffer2.release();
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuBufferDestroy(buffer1);
wgpuBufferDestroy(buffer2);

wgpuBufferRelease(buffer1);
wgpuBufferRelease(buffer2);
```
````

Note that there are two different operations here:

 - **Destroy** frees the GPU memory that was allocated for the buffer, but the buffer object itself, which lives on the driver/backend side, still exists.
 - **Release** frees the driver/backend side object (or rather decreases its reference pointer and frees it if nobody else uses it).

Writing to a buffer
-------------------

Let us simply use the `queue.writeBuffer` function (or the C-style `wgpuQueueWriteBuffer`), to which we give a memory address and size from which data is copied:

````{tab} With webgpu.hpp
```C++
// Create some CPU-side data buffer (of size 16 bytes)
std::vector<uint8_t> numbers(16);
for (uint8_t i = 0; i < 16; ++i) numbers[i] = i;

// Copy this from `numbers` (RAM) to `buffer1` (VRAM)
queue.writeBuffer(buffer1, 0, numbers.data(), numbers.size());
```
````

````{tab} Vanilla webgpu.h
```C++
// Create some CPU-side data buffer (of size 16 bytes)
std::vector<uint8_t> numbers(16);
for (uint8_t i = 0; i < 16; ++i) numbers[i] = i;

// Copy this from `numbers` (RAM) to `buffer1` (VRAM)
wgpuQueueWriteBuffer(queue, buffer1, 0, numbers.data(), numbers.size());
```
````

```{note}
Uploading data from the CPU-side memory (RAM) to the GPU-side memory (VRAM) **takes time**. When the function `writeBuffer()` returns, data transfer may not have finished yet but it is **guaranteed** that:

 - You can **free up the memory** from the address you just passed, because the backend maintains its own CPU-side copy of the buffer during transfer.

 - Commands that are **submitted in the queue after** the `writeBuffer()` operation will not be executed before the data transfer is finished.

And don't forget that commands sent through the **command encoder** are only submitted when calling `queue.submit()` with the encoded command buffer returned by `encoder.finish()`.
```

We can thus submit a buffer-buffer copy operation to the command queue, after having created a command encoder:

````{tab} With webgpu.hpp
```C++
encoder.copyBufferToBuffer(buffer1, 0, buffer2, 0, 16);
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuCommandEncoderCopyBufferToBuffer(encoder, buffer1, 0, buffer2, 0, 16);
```
````

```{important}
Make sure that command encoding operations are called before `encoder.finish()` or `wgpuCommandEncoderFinish()`!
```

Reading from a buffer
---------------------

We cannot just use the command queue to read memory back from the GPU, because this is a "fire and forget" queue: functions do not return a value since they are run on a different timeline.

Instead, we use an **asynchronous operation**, namely `buffer.mapAsync` (or `wgpuBufferMapAsync`). This operation maps the GPU buffer into CPU memory, and then whenever it is ready it executes the callback function it was provided.

This asynchronicity makes the programming workflow more complicated than synchronous operations, but once again it is important to minimize wasteful processor idling.

### Mapping

Let us first change the `usage` of the second buffer by adding the `BufferUsage::MapRead` flag, so that the buffer can be mapped for reading:

````{tab} With webgpu.hpp
```C++
bufferDesc2.usage = BufferUsage::CopyDst | BufferUsage::MapRead;
```
````

````{tab} Vanilla webgpu.h
```C++
bufferDesc2.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_MapRead;
```
````

```{note}
The `BufferUsage::MapRead` flag is not compatible with `BufferUsage::CopySrc` one, so make sure not to have both at the same time.
```

We can now call the buffer mapping with a simple callback.

```{important}
I intentionally use the C-style procedure for now, it helps understanding what is happening under the hood when using the simpler API provided by the C++ wrapper.
```

````{tab} With webgpu.hpp
```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /*pUserData*/) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, MapMode::Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```
````

````{tab} Vanilla webgpu.h
```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /*pUserData*/) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```
````

````{note}
The function `onBuffer2Mapped` is defined here as a [lambda expression](https://en.cppreference.com/w/cpp/language/lambda) but it could also be a regular function declared before `main()`, provided it has the same signature:

```C++
void onBuffer2Mapped(WGPUBufferMapAsyncStatus status, void* /*pUserData*/) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
}
```
````

### Asynchronous polling

If you run the program at this point, you might be surprised (and disappointed) to see that the callback is **never executed**!

This is because there is no hidden process executed by the WebGPU library to check that the async operation is ready. Instead, the backend checks for ongoing async operations only when we call another operation, so we will add in the main loop a simple operation that does nothing.

Unfortunately, this mechanism has no standard solution, so we write it differently for Dawn and `wgpu-native`:

````{tab} With webgpu.hpp
```C++
while (!glfwWindowShouldClose(window)) {
	// Do nothing, this checks for ongoing asynchronous operations and call their callbacks
#ifdef WEBGPU_BACKEND_WGPU
	// Non-standardized behavior: submit empty queue to flush callbacks
	// (wgpu-native also has a device.poll but its API is more complex)
	queue.submit(0, nullptr);
#else
	// Non-standard Dawn way
	device.tick();
#endif

	// (This is the same idea, for the GLFW library callbacks)
	glfwPollEvents();
}
```
````

````{tab} Vanilla webgpu.h
```C++
while (!glfwWindowShouldClose(window)) {
	// Do nothing, this checks for ongoing asynchronous operations and call their callbacks
#ifdef WEBGPU_BACKEND_WGPU
	// Non-standardized behavior: submit empty queue to flush callbacks
	// (wgpu-native also has a wgpuDevicePoll but its API is more complex)
	wgpuQueueSubmit(queue, 0, nullptr);
#else
	// Non-standard Dawn way
	wgpuDeviceTick(device);
#endif

	// (This is the same idea, for the GLFW library callbacks)
	glfwPollEvents();
}
```
````

```{warning}
Make sure the calls to `buffer.destroy` are issued *after* the main loop, otherwise the callback will be called with status `BufferMapAsyncStatus::DestroyedBeforeCallback`.
```

You should now see `Buffer 2 mapped with status 0` (0 being the value of `BufferMapAsyncStatus::Success`) when running your program.

### Mapping context

Now, we need to get more than a status when running this callback, we need to access the buffer's content. But the `onBuffer2Mapped` function cannot access the `buffer2` variable so far.

```{note}
When using a regular function, it is clear that `buffer2` is not accessible. When using a lambda expression, one could be tempted to add `buffer2` in the **capture list** (the brackets before function arguments). But this **does not work** because capturing lambdas have a different type, that cannot be used as a regular callback. The C++ wrapper fixes this.
```

We thus use the `void *userdata` pointer communicated from the original call to `wgpuBufferMapAsync` to the callback, like we did in [the adapter request](../../getting-started/the-adapter.md) or [the device request](../../getting-started/the-device.md):


````{tab} With webgpu.hpp
```C++
// The context shared between this main function and the callback.
struct Context {
	Buffer buffer;
};

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	Context* context = reinterpret_cast<Context*>(pUserData);
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
	if (status != BufferMapAsyncStatus::Success) return;

	// Get a pointer to wherever the driver mapped the GPU memory to the RAM
	uint8_t* bufferData = (uint8_t*)context->buffer.getConstMappedRange(0, 16);

	// [...] (Do stuff with bufferData)

	// Then do not forget to unmap the memory
	context->buffer.unmap();
};

Context context = { buffer2 };
wgpuBufferMapAsync(buffer2, MapMode::Read, 0, 16, onBuffer2Mapped, (void*)&context);
```
````

````{tab} Vanilla webgpu.h
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
	uint8_t* bufferData = (uint8_t*)wgpuBufferGetConstMappedRange(context->buffer, 0, 16);

	// [...] (Do stuff with bufferData)

	// Then do not forget to unmap the memory
	wgpuBufferUnmap(context->buffer);
};

Context context = { buffer2 };
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, (void*)&context);
```
````

For instance we can just display the content of the buffer and check that it corresponds to our initially fed buffer data:

```C++
std::cout << "bufferData = [";
for (int i = 0; i < 16; ++i) {
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

Congratulations! We were able to create a GPU-side memory buffer, upload data into it, copy it remotely (operation triggered from the CPU, but executed on the GPU) using the command queue and download data back from the GPU. We can now use a buffer to specify vertex attributes, in particular vertex positions!

````{tab} With webgpu.hpp
*Resulting code:* [`step031`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step031-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031-vanilla)
````
