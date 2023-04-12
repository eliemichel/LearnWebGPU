The Command Queue
=================

*Resulting code:* [`step017`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017)

We are getting close, but we will still not display anything on our window. We learn in this chapter a key concept of WebGPU (and of most modern graphics APIs as well): the *command queue*.

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
As of now, the `wgpuQueueOnSubmittedWorkDone` is not implemented by our wgpu-native backend. Using it will result in a null pointer exception so do not copy the above code block.
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

Conclusion
----------

We have seen a few important notions in this chapter:

 - timelines
 - command queue
 - command encoder

This was a bit abstract though, because we can queue operations but we did not see any yet. The next chapter shows how to use it to manipulate **buffers**, but you may also skip it to go right away to your [first color](/getting-started/first-color.md) and come back to it later on.

*Resulting code:* [`step017`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step017)
