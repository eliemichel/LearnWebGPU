Playing with buffers <span class="bullet">🟢</span>
====================

```{lit-setup}
:tangle-root: 031 - Playing with buffers - vanilla
:parent: 030 - Hello Triangle - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 031 - Playing with buffers
:parent: 030 - Hello Triangle
```

````{tab} With webgpu.hpp
*Resulting code:* [`step031`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step031-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step031-vanilla)
````

Before feeding vertex data to the render pipeline, we need to get familiar with the notion of a **buffer**. A buffer is "just" a **chunk of memory** allocated in the **VRAM** (the GPU's memory). Think of it as some kind of `new` or `malloc` for the GPU.

In this chapter, we will see how to **create** (i.e., allocate), **write** from CPU, **copy** from GPU to GPU and **read back** to CPU.

```{note}
Note that textures are a special kind of memory (because of the way we usually sample them) so they live in a different kind of object.
```

Since this is just an experiment, I suggest we temporarily write the whole code of this chapter at the end of the `Initialize()` function. The overall outline of our code is as follows:

```{lit} C++, Playing with buffers (insert in {{Initialize}} after "InitializePipeline()", also for tangle root "Vanilla")
// Experimentation for the "Playing with buffers" chapter
{{Create a first buffer}}
{{Create a second buffer}}

{{Write input data}}

{{Encode and submit the buffer to buffer copy}}

{{Read buffer data back}}

{{Release buffers}}
```

Creating a buffer
-----------------

The overall structure of the buffer creation will surprise no one now: a descriptor, and a call to `createBuffer`.

````{tab} With webgpu.hpp
```{lit} C++, Create a first buffer
BufferDescriptor bufferDesc;
bufferDesc.label = "Some GPU-side data buffer";
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::CopySrc;
bufferDesc.size = 16;
bufferDesc.mappedAtCreation = false;
Buffer buffer1 = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create a first buffer (for tangle root "Vanilla")
WGPUBufferDescriptor bufferDesc = {};
bufferDesc.nextInChain = nullptr;
bufferDesc.label = "Some GPU-side data buffer";
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_CopySrc;
bufferDesc.size = 16;
bufferDesc.mappedAtCreation = false;
WGPUBuffer buffer1 = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

One **notable difference** with a CPU buffer is that we must state some **usage hints**, telling about our use of this memory. For instance, if we are going to use it only to write it from the CPU but never to read it back, we set its `CopyDst` usage flag on but not the `CopySrc` flag. This not fully agnostic memory management **helps the device** figure out the best memory layout.

```{note}
A GPU buffer is **mapped** when it is connected to a specific part of the CPU-side RAM. The driver then automatically synchronizes its content, either for reading or for writing. We do not use this feature for now.
```

For our little exercise, let us **create a second buffer**, called `buffer2`. We will load data in the first buffer, issue a **copy** command so that the GPU copies data from one to another, then **read** the destination buffer back.

We can reuse the descriptor, only changing teh label for now:

````{tab} With webgpu.hpp
```{lit} C++, Create a second buffer
bufferDesc.label = "Output buffer";
Buffer buffer2 = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create a second buffer (for tangle root "Vanilla")
bufferDesc.label = "Output buffer";
WGPUBuffer buffer2 = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

Also, don't forget to **release your buffers** once you no longer use them:

````{tab} With webgpu.hpp
```{lit} C++, Release buffers
// In Terminate()
buffer1.release();
buffer2.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Release buffers (for tangle root "Vanilla")
// In Terminate()
wgpuBufferRelease(buffer1);
wgpuBufferRelease(buffer2);
```
````

`````{note}
Buffers (as well as textures) also provide a **destroy** method:

````{tab} With webgpu.hpp
```C++
buffer1.destroy();
```
````

````{tab} Vanilla webgpu.h
```C++
wgpuBufferDestroy(buffer1);
```
````

This can be used to **force freeing** the GPU memory even if there remains existing references to the buffer.

- **Destroy** frees the GPU memory that was allocated for the buffer, but the buffer object itself, which lives on the driver/backend side, still exists.
 - **Release** frees the driver/backend side object (or rather decreases its reference pointer) and destroys it if nobody else uses it.
`````

Writing to a buffer
-------------------

The device queue provides a `queue.writeBuffer` function (or the C-style `wgpuQueueWriteBuffer`), to which we first give the **GPU buffer** to write into, then a CPU-side **memory address** and **size** from which data is copied:

````{tab} With webgpu.hpp
```{lit} C++, Write input data
// Create some CPU-side data buffer (of size 16 bytes)
std::vector<uint8_t> numbers(16);
for (uint8_t i = 0; i < 16; ++i) numbers[i] = i;
// `numbers` now contains [ 0, 1, 2, ... ]

// Copy this from `numbers` (RAM) to `buffer1` (VRAM)
queue.writeBuffer(buffer1, 0, numbers.data(), numbers.size());
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Write input data (for tangle root "Vanilla")
// Create some CPU-side data buffer (of size 16 bytes)
std::vector<uint8_t> numbers(16);
for (uint8_t i = 0; i < 16; ++i) numbers[i] = i;
// `numbers` now contains [ 0, 1, 2, ... ]

// Copy this from `numbers` (RAM) to `buffer1` (VRAM)
wgpuQueueWriteBuffer(queue, buffer1, 0, numbers.data(), numbers.size());
```
````

```{note}
Uploading data from the CPU-side memory (RAM) to the GPU-side memory (VRAM) **takes time**. When the function `writeBuffer()` returns, data transfer may not have finished yet but what is **guaranteed** is that:

 - You can **free up the memory** from the address you just passed, because the backend maintains its own CPU-side copy of the buffer during transfer (use mapping if you want to avoid that).

 - Commands that are **submitted in the queue after** the `writeBuffer()` operation will not be executed before the data transfer is finished.

And don't forget that commands sent through the **command encoder** are only submitted when calling `queue.submit()` with the encoded command buffer returned by `encoder.finish()`.
```

Copying a buffer
----------------

We can now submit a **buffer-buffer copy** operation to the command queue. This is not directly available from the queue object but rather requires us to **create a command encoder**. Once we have an encoder we may simply add the following:

````{tab} With webgpu.hpp
```{lit} C++, Copy buffer to buffer
// After creating the command encoder
encoder.copyBufferToBuffer(buffer1, 0, buffer2, 0, 16);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Copy buffer to buffer (for tangle root "Vanilla")
// After creating the command encoder
wgpuCommandEncoderCopyBufferToBuffer(encoder, buffer1, 0, buffer2, 0, 16);
```
````

The argment `0` after each buffer is the **byte offset** within the buffer at which the copy must happen. This enables copying **sub-parts** of buffers.

We wrap this in a command encoding process similar to the render pass one:

````{tab} With webgpu.hpp
```{lit} C++, Encode and submit the buffer to buffer copy
CommandEncoder encoder = device.createCommandEncoder(Default);

{{Copy buffer to buffer}}

CommandBuffer command = encoder.finish(Default);
encoder.release();
queue.submit(1, &command);
command.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Encode and submit the buffer to buffer copy (for tangle root "Vanilla")
WGPUCommandEncoder encoder = wgpuDeviceCreateCommandEncoder(device, nullptr);

{{Copy buffer to buffer}}

WGPUCommandBuffer command = wgpuCommandEncoderFinish(encoder, nullptr);
wgpuCommandEncoderRelease(encoder);
wgpuQueueSubmit(queue, 1, &command);
wgpuCommandBufferRelease(command);
```
````

Reading from a buffer
---------------------

The **command queue**, that we used to send data (`writeBuffer`) and instructions (`copyBufferToBuffer`), **only goes in one way**: from CPU host to GPU device. It is thus a "fire and forget" queue: functions do not return a value since they **run on a different timeline**.

So, how do we read data back then? We use an **asynchronous operation**, like we did when using `wgpuQueueOnSubmittedWorkDone` in the [Command Queue](../../getting-started/the-command-queue.md) chapter. Instead of directly getting a value back, we set up a **callback** that gets invoked whenever the requested data is ready. We then **poll the device** to check for incoming events.

**To read data from a buffer**, we use `buffer.mapAsync` (or `wgpuBufferMapAsync`). This operation **maps** the GPU buffer into CPU memory, and then whenever it is ready it executes the callback function it was provided. Once we are done, we can **unmap** the buffer.

```{note}
This **asynchronicity** makes the programming workflow **more complicated** than synchronous operations, but it is very important to minimize wasteful processor idling. It is common to launch a mapping operation, then **do other things while waiting** for the data (which takes a lot of time, compared to running CPU instructions).
```

### Mapping

Let us first change the `usage` of the **second buffer** by adding the `BufferUsage::MapRead` flag, so that the buffer can be mapped for reading:

````{tab} With webgpu.hpp
```{lit} C++, Create a second buffer (replace)
bufferDesc.label = "Output buffer";
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::MapRead;
Buffer buffer2 = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create a second buffer (replace, for tangle root "Vanilla")
bufferDesc.label = "Output buffer";
bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_MapRead;
WGPUBuffer buffer2 = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

```{note}
The `BufferUsage::MapRead` flag is not compatible with `BufferUsage::CopySrc` one, so make sure not to have both at the same time. It is common to create a **buffer dedicated to mapping operations**.
```

We can now call the buffer mapping with a simple callback. The `wgpuBufferMapAsync` procedure takes as argument the **map mode** (read, write or both), the **slice** of buffer data to map, given by an offset (0) and a number of bytes (16), then the **callback** and finally some **"user data"** pointer. We show [below](#mapping-context) what the latter is for.

````{tab} With webgpu.hpp
```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /* pUserData */) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, MapMode::Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```
````

````{tab} Vanilla webgpu.h
```C++
auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* /* pUserData */) {
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};
wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, nullptr /*pUserData*/);
```
````

```{important}
I intentionally use the **C-style procedure** for now, it helps understanding what is happening under the hood when using the simpler API provided by the C++ wrapper.
```

### Asynchronous polling

If you run the program at this point, you might be surprised (and disappointed) to see that the callback is **never executed**! We saw this in the [Device Polling](../../getting-started/the-command-queue.md#device-polling) section of the Command Queue chapter: there is **no hidden process** executed by the WebGPU library to **check that the async operation is ready** so we must do it ourselves.

Unfortunately, this mechanism has no standard solution yet, so we write it differently for Dawn, `wgpu-native` and emscripten, with a little subtlety for the latter:

````{tab} With webgpu.hpp
```{lit} C++, Define the wgpuPollEvents function
// We define a function that hides implementation-specific variants of device polling:
void wgpuPollEvents([[maybe_unused]] Device device, [[maybe_unused]] bool yieldToWebBrowser) {
#if defined(WEBGPU_BACKEND_DAWN)
	device.tick();
#elif defined(WEBGPU_BACKEND_WGPU)
	device.poll(false);
#elif defined(WEBGPU_BACKEND_EMSCRIPTEN)
	if (yieldToWebBrowser) {
		emscripten_sleep(100);
	}
#endif
}
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Define the wgpuPollEvents function (for tangle root "Vanilla")
// We define a function that hides implementation-specific variants of device polling:
void wgpuPollEvents([[maybe_unused]] WGPUDevice device, [[maybe_unused]] bool yieldToWebBrowser) {
#if defined(WEBGPU_BACKEND_DAWN)
	wgpuDeviceTick(device);
#elif defined(WEBGPU_BACKEND_WGPU)
	wgpuDevicePoll(device, false, nullptr);
#elif defined(WEBGPU_BACKEND_EMSCRIPTEN)
	if (yieldToWebBrowser) {
		emscripten_sleep(100);
	}
#endif
}
```
````

```{lit} C++, Global declarations (hidden, append, also for tangle root "Vanilla")
{{Define the wgpuPollEvents function}}
```

```{admonition} Emscripten subtlety
When our C++ code runs in a **Web browser** (after being compiled to WebAssembly through emscripten), there is **no explicit way** to tick/poll the WebGPU device. This is because **the device is managed by the Web browser** itself, which decides at what pace polling should happen. As a result:

 - The device **never ticks** in between two consecutive lines of our WebAssembly module, it can only tick when the execution flow leaves the module.
 - The device **always ticks** between two calls to our `MainLoop()` function, because if you remember the [Emscripten](../../getting-started/opening-a-window.md#emscripten) section of the Opening a Window chapter, we leave the main loop management to the browser and only provide a callback to run at each frame.

Thanks to the second point, we do not need `wgpuPollEvents` to do anything when called at the beginning or end of our main loop (so we set `yieldToWebBrowser` to false).

However, if what we intend is really to **wait until** something happens (e.g., a callback gets invoked), the first point requires us to make sure we **yield back** the execution flow to the Web browser, so that it may tick its device from time to time. We do this thanks to `emscripten_sleep` function, at the cost of effectively sleeping during 100 ms (we're in a case where we want to wait anyways).

Note that using `emscripten_sleep` requires the `-SASYNCIFY` link option to be passed to emscripten, like we added [already](../../getting-started/adapter-and-device/the-adapter.md#waiting-for-the-request-to-end).
```

In our example, we want to wait for read back during an iteration of the main loop, so we specify that we yield back to the browser:

```C++
bool ready = false;

{{Define callback and start mapping buffer}}

while (!ready) {
	wgpuPollEvents(device, true /* yieldToBrowser */);
}
```

You could now see `Buffer 2 mapped with status 1` (1 being the value of `BufferMapAsyncStatus::Success` when using Dawn, it is 0 for WGPU) when running your program. **However**, we never change the `ready` variable to `true`! So the program then **hangs forever**... not great. That is why the next section shows how to pass some context to the callback.

### Mapping context

So, we need the callback to **access and mutate** the `ready` variable. But how can we do this since `onBuffer2Mapped` is a separate function whose signature cannot be changed? We can use the **user pointer**, like we did in [the adapter request](../../getting-started/adapter-and-device/the-adapter.md) or [the device request](../../getting-started/adapter-and-device/the-device.md).

```{note}
When defining `onBuffer2Mapped` as a regular function, it is clear that `ready` is not accessible. When using a lambda expression like we did above, one could be tempted to add `ready` in the **capture list** (the brackets before function arguments). But this **does not work** because a capturing lambda has a **different type**, that cannot be used as a regular callback. We see below that the C++ wrapper fixes this limitation.
```

The **user pointer** is an argument that is provided to `wgpuBufferMapAsync`, when setting up the callback, and that is then fed **as is** to the callback `onBuffer2Mapped` when the map operation is ready. The buffer only forwards this pointer but never uses it: **only you** (the user of the API) interpret it.

````{tab} With webgpu.hpp
```C++
// A first use of the 'pUserData' argument.
bool ready = false;

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	// We know by convention with ourselves that the user data is a pointer to 'ready':
	bool* pReady = reinterpret_cast<bool*>(pUserData);
	// We set ready to 'true'
	*pReady = true;

	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};

wgpuBufferMapAsync(buffer2, MapMode::Read, 0, 16, onBuffer2Mapped, (void*)&ready);
//                                Pass the address of 'ready' here: ^^^^^^^^^^^^
```
````

````{tab} Vanilla webgpu.h
```C++
// A first use of the 'pUserData' argument.
bool ready = false;

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	// We know by convention with ourselves that the user data is a pointer to 'ready':
	bool* pReady = reinterpret_cast<bool*>(pUserData);
	// We set ready to 'true'
	*pReady = true;

	std::cout << "Buffer 2 mapped with status " << status << std::endl;
};

wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, (void*)&ready);
//                                   Pass the address of 'ready' here: ^^^^^^^^^^^^
````

Now, we need to **access to more than a status** when running this callback, since we need to access the buffer's content. But the `onBuffer2Mapped` function cannot have a second user pointer! Not a problem: we can define **a context structure**, that holds **all fields that we want to share** with the callback, then pass the address of an instance of this context.

````{tab} With webgpu.hpp
```{lit} C++, Read buffer data back
// The context shared between this main function and the callback.
struct Context {
	bool ready;
	Buffer buffer;
};

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	Context* context = reinterpret_cast<Context*>(pUserData);
	context->ready = true;
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
	if (status != BufferMapAsyncStatus::Success) return;

	{{Use context->buffer here}}
};

// Create the Context instance
Context context = { false, buffer2 };

wgpuBufferMapAsync(buffer2, MapMode::Read, 0, 16, onBuffer2Mapped, (void*)&context);
//                   Pass the address of the Context instance here: ^^^^^^^^^^^^^^

while (!context.ready) {
	//  ^^^^^^^^^^^^^ Use context.ready here instead of ready
	wgpuPollEvents(device, true /* yieldToBrowser */);
}
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Read buffer data back (for tangle root "Vanilla")
// The context shared between this main function and the callback.
struct Context {
	bool ready;
	WGPUBuffer buffer;
};

auto onBuffer2Mapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	Context* context = reinterpret_cast<Context*>(pUserData);
	context->ready = true;
	std::cout << "Buffer 2 mapped with status " << status << std::endl;
	if (status != WGPUBufferMapAsyncStatus_Success) return;

	{{Use context->buffer here}}
};

// Create the Context instance
Context context = { false, buffer2 };

wgpuBufferMapAsync(buffer2, WGPUMapMode_Read, 0, 16, onBuffer2Mapped, (void*)&context);
//                      Pass the address of the Context instance here: ^^^^^^^^^^^^^^

while (!context.ready) {
	//  ^^^^^^^^^^^^^ Use context.ready here instead of ready
	wgpuPollEvents(device, true /* yieldToBrowser */);
}
```
````

```{tip}
When the whole operation lives in a class like our `Application`, it can be convenient to simply **use `this` as the user pointer**, and thus retrieve the whole application object inside the callback.
```

### Using the mapped buffer

Once the buffer is mapped (either directly within the callback or after the polling loop that makes sure it is ready), we use `Buffer::getConstMappedRange` (a.k.a. `wgpuBufferGetConstMappedRange`) to **get a pointer** to the CPU-side data. Once we are done with this CPU-side data, we must **unmap** the buffer:

````{tab} With webgpu.hpp
```{lit} C++, Use context->buffer here
// Get a pointer to wherever the driver mapped the GPU memory to the RAM
uint8_t* bufferData = (uint8_t*)context->buffer.getConstMappedRange(0, 16);

{{Do stuff with bufferData}}

// Then do not forget to unmap the memory
context->buffer.unmap();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Use context->buffer here (for tangle root "Vanilla")
// Get a pointer to wherever the driver mapped the GPU memory to the RAM
uint8_t* bufferData = (uint8_t*)wgpuBufferGetConstMappedRange(context->buffer, 0, 16);

{{Do stuff with bufferData}}

// Then do not forget to unmap the memory
wgpuBufferUnmap(context->buffer);
```
````

```{note}
When mapping the buffer in **write mode**, use `Buffer::getMappedRange` (a.k.a. `wgpuBufferGetMappedRange`) instead of the "const" version.
```

For instance we can just **display the content** of the buffer and check that it corresponds to our initially fed buffer data:

```{lit} C++, Do stuff with bufferData (also for tangle root "Vanilla")
std::cout << "bufferData = [";
for (int i = 0; i < 16; ++i) {
	if (i > 0) std::cout << ", ";
	std::cout << (int)bufferData[i];
}
std::cout << "]" << std::endl;
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
