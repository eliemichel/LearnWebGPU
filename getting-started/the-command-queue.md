The Command Queue
=================

```{lit-setup}
:tangle-root: 017 - The Command Queue
:parent: 015 - The Device
```

*Resulting code:* [`step017`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017)

We are getting close, but we will still not display anything on our window. We learn in this chapter a key concept of WebGPU (and of most modern graphics APIs as well): the **command queue**.

```{figure} /images/command-queue.png
:align: center
:class: with-shadow
The CPU instructs the GPU what to do by sending commands through a command queue.
```

Different timelines
-------------------

One thing important to keep in mind when doing graphics programming: we have **two processors running simultaneously**. One of them is the CPU, also known as *host*, and the other one is the GPU, or *device*. There are two rules:

 1. **The code we write runs on the CPU**, and some of it triggers operations on the GPU. The only exception are *shaders*, which actually run on GPU.
 2. Processors are "**far away**", meaning that communicating between them takes time.

They are not too far, but for high performance applications like real time graphics, this matters. In advanced pipelines, rendering a frame may involve thousands or tens of thousands of commands running on the GPU.

As a consequence, we cannot afford to send the commands one by one from the CPU and wait for a response after each one. Instead, commands meant to the GPU are batched and fired through a **command queue**. The GPU consumes this queue whenever it is ready, and this way processors minimize the time spend idling for their sibling to respond.

The CPU-side of your program, i.e., the C++ code that you write, lives in the **Content timeline**. The other side of the command queue is the **Queue timeline**, running on the GPU.

```{note}
There is also a **Device timeline** defined in [WebGPU's documentation](https://www.w3.org/TR/webgpu/#programming-model-timelines). It corresponds to the GPU operations for which our code actually waits for an immediate answer (called "synchronous" calls), but unlike the JavaScript API, it is roughly the same as the content timeline in our C++ case.
```

Queue operations
----------------

Our WebGPU device has a single queue, which we can get with `wgpuDeviceGetQueue`.

```{lit} C++, Get Queue
WGPUQueue queue = wgpuDeviceGetQueue(device);
```

```{note}
Other graphics API allow one to build multiple queues per device, and future version of WebGPU might as well. But for now, one queue is already more than enough for us to play with!
```

Looking at `webgpu.h`, we find 3 different ways to submit work to this queue:

 - `wgpuQueueSubmit`
 - `wgpuQueueWriteBuffer`
 - `wgpuQueueWriteTexture`

The first one only sends commands (potentially complicated ones though), and the two other ones send memory from the CPU memory (RAM) to the GPU one (VRAM). This is where the delay of the communication might become particularly critical.

We also find a `wgpuQueueOnSubmittedWorkDone` procedure that we can use to set up a function to be called back once the work is done. Let us do it to make sure things happen as expected:

```{lit} C++, Add queue callback
auto onQueueWorkDone = [](WGPUQueueWorkDoneStatus status, void* /* pUserData */) {
	std::cout << "Queued work finished with status: " << status << std::endl;
};
wgpuQueueOnSubmittedWorkDone(queue, onQueueWorkDone, nullptr /* pUserData */);
```

```{error}
As of now, the `wgpuQueueOnSubmittedWorkDone` is not implemented by our wgpu-native backend. Using it will result in a null pointer exception so do not copy the above code block.
```

```{lit} C++, Add queue callback (replace, hidden)
#ifdef WEBGPU_BACKEND_DAWN
// Add a callback to monitor the moment queued work winished
auto onQueueWorkDone = [](WGPUQueueWorkDoneStatus status, void* /* pUserData */) {
    std::cout << "Queued work finished with status: " << status << std::endl;
};
wgpuQueueOnSubmittedWorkDone(queue, 0 /* non standard argument for Dawn */, onQueueWorkDone, nullptr /* pUserData */);
#endif // WEBGPU_BACKEND_DAWN
```

Submitting commands
-------------------

We submit commands using the following procedure:

```C++
wgpuQueueSubmit(queue, /* number of commands */, /* pointer to the command array */);
```

We see **a typical idiom** here: WebGPU is a C API so whenever it needs to receive an array of things, we first provide the array size then a pointer to the first element.

If we have a single element, it is simply:

```C++
// With a single command:
WGPUCommandBuffer command = /* [...] */;
wgpuQueueSubmit(queue, 1, &command);
```

If we know at compile time ("statically") the number of commands, we may use a C array (although a `std::array` is safer):

```C++
// With a statically know number of commands:
WGPUCommandBuffer commands[3];
commands[0] = /* [...] */;
commands[1] = /* [...] */;
commands[2] = /* [...] */;
wgpuQueueSubmit(queue, 3, commands);

// or, safer and avoid repeating the array size:
std::array<WGPUCommandBuffer, 3> commands;
commands[0] = /* [...] */;
commands[1] = /* [...] */;
commands[2] = /* [...] */;
wgpuQueueSubmit(queue, commands.size(), commands.data());
```

And if we need to dynamically change the size, we use a `std::vector`:

```C++
std::vector<WGPUCommandBuffer> commands;
// [...] (Allocate and fill in command buffers)
wgpuQueueSubmit(queue, commands.size(), commands.data());
```

However, we **cannot manually create** a `WGPUCommandBuffer` object. This buffer uses a special format that is left to the discretion of your driver/hardware. To build this buffer, we use a **command encoder**.

Command encoder
---------------

A command encoder is created following the usual object creation idiom of WebGPU:

```{lit} C++, Create Command Encoder
WGPUCommandEncoderDescriptor encoderDesc = {};
encoderDesc.nextInChain = nullptr;
encoderDesc.label = "My command encoder";
WGPUCommandEncoder encoder = wgpuDeviceCreateCommandEncoder(device, &encoderDesc);
```

We can now use the encoder to write instructions (debug placeholder for now).

```{lit} C++, Add commands
wgpuCommandEncoderInsertDebugMarker(encoder, "Do one thing");
wgpuCommandEncoderInsertDebugMarker(encoder, "Do another thing");
```

And then finally generating the command from the encoder also requires an extra descriptor:

```{lit} C++, Finish encoding and submit
WGPUCommandBufferDescriptor cmdBufferDescriptor = {};
cmdBufferDescriptor.nextInChain = nullptr;
cmdBufferDescriptor.label = "Command buffer";
WGPUCommandBuffer command = wgpuCommandEncoderFinish(encoder, &cmdBufferDescriptor);

// Finally submit the command queue
std::cout << "Submitting command..." << std::endl;
wgpuQueueSubmit(queue, 1, &command);
```

```{note}
The `Finish` operation also destroys the `encoder`, it must not be called afterwards and there is no need to call `wgpuCommandEncoderRelease`. Similarly the `wgpuQueueSubmit` takes care of destroying the command buffer.
```

```{lit} C++, Test command encoding (hidden)
{{Get Queue}}
{{Add queue callback}}
{{Create Command Encoder}}
{{Add commands}}
{{Finish encoding and submit}}
```

```{lit} C++, Create things (append, hidden)
{{Test command encoding}}
```

This should output:

```
Submitting command...
Queued work finished with status: 0
```

```{warning}
Again, on `wgpu-native` you will not see the "finished" line. On Dawn, you need to add an extra non-standard argument set to 0 just after `queue`.
```

At this stage, the code works, but submits a command queue that is almost empty. So it is a bit hard to be thrilled about, let's pump it up with some basic buffer manipulation.

Conclusion
----------

We have seen a few important notions in this chapter:

 - The CPU and GPU live in **different timelines**.
 - Commands are streamed from CPU to GPU through a **command queue**.
 - Queued command buffers must be encoded using a **command encoder**.

This was a bit abstract because we can queue operations but we did not see any yet. In the next chapter we use it to **finally display something** in our window!

We will also see in [*Playing with buffers*](../basic-3d-rendering/input-geometry/playing-with-buffers.md) how to use it for GPU-side buffer manipulation.

*Resulting code:* [`step017`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017)
