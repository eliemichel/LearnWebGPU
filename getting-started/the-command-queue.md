The Command Queue
=================

*Resulting code:* [`step018`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step018)

This is the last off-screen chapter. We will still not display anything on our window, but we'll learn a key concept of WebGPU (and of most modern graphics APIs as well): the *command queue*. And we also later introduce *buffers*, representing GPU-side memory chunks.

Different timelines
-------------------

One thing important to keep in mind when doing graphics programming: we have **two processors running simultaneously**. One of them is the CPU, also known as *host*, and the other one is the GPU, or *device*. There are two rules:

 1. **The code we write runs on the CPU**, and some of it triggers operations on the GPU. The only exception are *shaders*, which actually run on GPU.
 2. Processors are "**far away**", meaning that communicating between them takes time.

They are not too far, but for high performance applications like real time graphics, this matters. In advanced pipelines, rendering frame may involve thousands or tens of thousands of commands running on the GPU.

As a consequence, we cannot afford to send the commands one by one from the CPU and wait for a response after each one. Instead, commands meant to the GPU are batched and fired through a **command queue**. The GPU consumes this queue whenever it is ready, and this way processors minimize the time spend idling for their sibling to respond.

The CPU-side of your program, i.e., the C++ code that you write, lives in the *Content timeline*. The other side of the command queue is the *Queue timeline*, running on the GPU.

```{note}
There is also a *Device timeline* defined in [WebGPU's documentation](https://www.w3.org/TR/webgpu/#programming-model-timelines). It corresponds to the GPU operations for which our code actually waits for an immediate answer (called "synchronous" calls), but unless the JavaScript API, it is roughly the same as the content timeline in our C++ case.
```

Queuing operations
------------------

Our WebGPU device has a single queue, which we can get with `wgpuDeviceGetQueue`.

```C++
WGPUQueue queue = wgpuDeviceGetQueue(device);
```

```{note}
Other graphics API allow one to build multiple queues per device, and future version of WebGPU might as well. But for now, one queue is already more than enough for us to play with!
```

Looking at `webgpu.h`, we find 3 different ways to submit work to this queue:

 - `wgpuQueueSubmit`
 - `wgpuQueueWriteBuffer`
 - `wgpuQueueWriteTexture`

The first one only send commands (potentially complicated ones though), and the two other ones send memory from the CPU memory (RAM) to the GPU one (VRAM). This is where the delay of the communication might become particularly critical. We find also a `wgpuQueueOnSubmittedWorkDone` function that we can use to set up a function to be called once the work is done. Let us do it to make sure things happen as expected:

```C++
auto onQueueWorkDone = [](WGPUQueueWorkDoneStatus status, void* /* pUserData */) {
	std::cout << "Queued work finished with status: " << status << std::endl;
};
wgpuQueueOnSubmittedWorkDone(queue, onQueueWorkDone, nullptr /* pUserData */);
```

```{error}
As of now, the `wgpuQueueOnSubmittedWorkDone` is not implemented by our wgpu-native backend.
```

Submitting commands looks as follow:

```C++
std::vector<WGPUCommandBuffer> commands = {};
// [...] (Allocate and fill in command buffers)
wgpuQueueSubmit(queue, commands.size(), commands.data());

// or, if we only send one command:

WGPUCommandBuffer command = /* [...] */;
wgpuQueueSubmit(queue, 1, &command);
```

However, we cannot manually create a `WGPUCommandBuffer` object. This buffer uses a special format that is left to the discretion of your driver/hardware. To build this buffer, we use a **command encoder**.

Command encoder
---------------

A command encoder is created following the usual object creation idiom of WebGPU:

```C++
WGPUCommandEncoderDescriptor encoderDesc = {};
encoderDesc.nextInChain = nullptr;
encoderDesc.label = "My command encoder";
WGPUCommandEncoder encoder = wgpuDeviceCreateCommandEncoder(device, &encoderDesc);
```

We can now use the encoder to write instructions (debug placeholder for now).

```C++
wgpuCommandEncoderInsertDebugMarker(encoder, "Do one thing");
wgpuCommandEncoderInsertDebugMarker(encoder, "Do another thing");
```

And then finally generating the command from the encoder also requires an extra descriptor:

```C++
WGPUCommandBufferDescriptor cmdBufferDescriptor = {};
cmdBufferDescriptor.nextInChain = nullptr;
cmdBufferDescriptor.label = "Command buffer";
WGPUCommandBuffer command = wgpuCommandEncoderFinish(encoder, &cmdBufferDescriptor);
// then submit queue
```

At this stage, the code works, but submits a command queue that is almost empty. So it is a bit hard to be thrilled about, let's pump it up with some basic buffer manipulation.

```{tip}
You can skip this next part about buffers if you want to quickly get to the next section. We will not use it directly, but this helps understanding the mechanisms of the API.
```

Playing with buffers
--------------------

A buffer is "just" a chunk of memory allocated in the VRAM (the GPU's memory). Think of it as some kind of `new` or `malloc` for the GPU.

One notable difference is that we most state some hint about our use of this memory upon its creation. For instance, if we are going to use it only to write it from the CPU but never to read it back, we set its `CopyDst` flag on but not the `CopySrc` flag. This not fully agnostic memory management helps the device figuring out the best memory layout.

```{note}
Note that textures are a so special kind of memory (because of the way we usually sample them) that they live in a different kind of object.
```

### Creating a buffer

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

### Writing to a buffer

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

### Reading from a buffer

We cannot just use the command queue to read memory back from the GPU, because this is a "fire and forget" queue: functions do not return a value since they are ran on a different timeline.

Instead, we use an asynchronous, namely `wgpuBufferMapAsync`. This operation maps the GPU buffer into CPU memory, and then executes the callback function it was provided. This makes the programming workflow more complicated than synchronous operations, but once again it is important to minimize wasteful processor idling.

Let us first change the `usage` of the second buffer by adding the `WGPUBufferUsage_MapRead` flag, so that the buffer can be mapped for reading:

```C++
bufferDesc2.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_MapRead;
```

```{note}
The `WGPUBufferUsage_MapRead` flag is not compatible with `WGPUBufferUsage_CopySrc` one, make sure not to have both at the same time.
```

We can now call the buffer mapping with a simple callback:

```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /*pUserData*/) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```

#### Asynchronous polling

If you run the program at this point, you might be surprised (and disappointed) to see that the callback is **never executed**! This is because there is no hidden process executed by the WebGPU library to check that the async operation is ready. Instead, the backend checks for ongoing async operations only when we call another operation, so we will add in the main loop a simple operation that does noting:

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

#### Mapping context

You should now see `Buffer 2 mapped with status 0` (0 being the value of `WGPUBufferMapAsyncStatus_Success`) when running your program.

Now, we need to get more than a status when running this callback, we need to access the buffer. We will thus use the `void *userdata` pointer communicated from the original call to `wgpuBufferMapAsync` to the callback, like we did in [the adapter request](the-adapter.md) or [the device request](the-device.md):


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

### Conclusion

Congratulations! We were able to create a GPU-side memory buffer, upload data into it, copy it remotely (operation triggered from the CPU, but executed on the GPU) using the command queue and download data back from the GPU.

We have seen a number of important notions in this chapter:

 - timelines
 - command queue
 - command encoder
 - buffers
 - asynchronous operations

We did not see very exciting operations on buffers though. More interesting ones are defined by *passes*, and in particular by the *render pass* that we will see in the next chapter.

*Resulting code:* [`step018`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step018)
