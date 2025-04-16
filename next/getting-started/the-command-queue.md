The Command Queue <span class="bullet">🟢</span>
=================

```{lit-setup}
:tangle-root: 015 - The Command Queue - Next
:parent: 010 - The Device - Next
```

Now that we have a `WGPUDevice` object in our hands, we can use it to **sent data and instructions** to the GPU. We learn in this chapter a **key concept** of WebGPU (and of most modern graphics APIs as well), namely **the command queue**.

```{important}
Notice how I use the term ***send*** here: as we will highlight see in this chapter, **our C++ code never runs on the GPU**, all it does is sending bits to the GPU, where programs follow a different logic (and use **a different programming language**) that we will see in the [next chapter](./our-first-shader.md).
```

```{figure} /images/command-queue.png
:align: center
:class: with-shadow
The CPU instructs the GPU what to do by **sending commands** through a command queue.
```

Different timelines
-------------------

One important thing to keep in mind when doing graphics programming: we have **two processors running simultaneously**. One of them is the CPU, also known as *host*, and the other one is the GPU, or *device*. There are two rules:

 1. **The code we write runs on the CPU**, and some of it triggers operations on the GPU. The only exception are *shaders*, which actually run on GPU.
 2. Processors are "**far away**", meaning that communicating between them **takes time**.

They are not too far, but for high performance applications like real time graphics or when manipulating large amounts of data like in machine learning, this matters. For two reasons:

### Bandwidth

Since the GPU is meant for **massive parallel data processing**, its performance can easily be **bound by the memory transfers** rather than the actual computation.

As it turns out, the **memory bandwidth limits** are more often hit within the GPU itself, **between its storage and its compute units**, but the CPU-GPU bandwidth is also limited, which one feels when trying to transfer large textures too often for instance.

```{note}
The connection between the **CPU memory** (RAM) and **GPU memory (vRAM)** depends on the type of GPU. Some GPUs are **integrated** within the same chip as the CPU, so they share the same memory. A **discrete** GPU is typically connected through a PCIe wire. And an **external** GPU would be connected with a Thunderbolt wire for instance. Each has a different bandwidth.
```

### Latency

**Even the smallest bit of information** needs some time for the round trip to and back from the GPU. As a consequence, functions that send instructions to the GPU return almost immediately: they **do not wait for the instruction to have actually been executed** because that would require to wait for the GPU to transfer back the "I'm done" information.

Instead, the commands intended for the GPU are **batched** and fired through a **command queue**. The GPU consumes this queue **whenever it is ready**. This is what we detail in this chapter.

### Timelines

The CPU-side of our program, i.e., the C++ code that we write, lives in the **Content timeline**. The other side of the command queue is in the **Queue timeline**, running on the GPU.

```{note}
There is also a **Device timeline** defined in [WebGPU's documentation](https://www.w3.org/TR/webgpu/#programming-model-timelines). It corresponds to the GPU operations for which our code actually waits for an immediate answer (called "synchronous" calls), but unlike the JavaScript API, it is roughly the same as the content timeline in our C++ case.
```

In the remainder of this chapter:

 - We see **how to manipulate the queue**.
 - We refine our control of **asynchronous operations**.

Manipulating the Queue
----------------------

### Queue operations

Our WebGPU device has **a single queue**, which is used to send both **commands** and **data**. We can get it with `wgpuDeviceGetQueue`.

```{lit} C++, Get Queue
WGPUQueue queue = wgpuDeviceGetQueue(device);
```

Naturally, we must also release the queue once we no longer use it, at the end of the program:

```{lit} C++, Release things (prepend)
// At the end
wgpuQueueRelease(queue);
```

```{note}
**Other graphics API** allow one to build **multiple queues** per device, and future version of WebGPU might as well. But for now, one queue is already more than enough for us to play with!
```

Looking at `webgpu.h`, we find mainly **3 different means** to submit work to this queue:

 - `wgpuQueueSubmit` sends **commands**, i.e., instructions of what to execute on the GPU.
 - `wgpuQueueWriteBuffer` sends **data** from a CPU-side buffer to a **GPU-side buffer**.
 - `wgpuQueueWriteTexture` sends **data** from a CPU-side buffer to a **GPU-side texture**.

We can note that all these functions have a `void` return type: they send instructions/data to the GPU and return immediately **without waiting from an answer from the GPU**.

The only way to **get information back** is through `wgpuQueueOnSubmittedWorkDone`, which is an **asynchronous operation** that gets invoked once the GPU confirms that it has (tried to) execute the commands. We show an example below.

### Submitting commands

We submit commands using the following procedure:

```C++
wgpuQueueSubmit(queue, /* number of commands */, /* pointer to the command array */);
```

We recognize here the typical way of sending arrays (briefly mentioned in [The Device](adapter-and-device/the-adapter.md) chapter). WebGPU is a C API so whenever it needs to receive an array of things, we first provide **the array size** and then **a pointer to the first element**.

#### Array argument

If we have a **single element**, it is simply done like so:

```C++
// With a single command:
WGPUCommandBuffer command = /* [...] */;
wgpuQueueSubmit(queue, 1, &command);
wgpuCommandBufferRelease(command); // release command buffer once submitted
```

If we know at **compile time** ("statically") the number of commands, we may use a C array, or a `std::array` (which is safer):

```C++
// With a statically know number of commands:
WGPUCommandBuffer commands[3];
commands[0] = /* [...] */;
commands[1] = /* [...] */;
commands[2] = /* [...] */;
wgpuQueueSubmit(queue, 3, commands);

// or, safer and avoid repeating the array size:
// (requires to #include <array>)
std::array<WGPUCommandBuffer, 3> commands;
commands[0] = /* [...] */;
commands[1] = /* [...] */;
commands[2] = /* [...] */;
wgpuQueueSubmit(queue, commands.size(), commands.data());
```

Or, if command buffers are **dynamically accumulated**, we use a `std::vector`:

```C++
// With a dynamical number of commands:
// (requires to #include <vector>)
std::vector<WGPUCommandBuffer> commands;
commands.push_back(/* [...] */);
if (someRuntimeCondition) {
	commands.push_back(/* [...] */);
}
wgpuQueueSubmit(queue, commands.size(), commands.data());
```

#### Command buffers

In any case, do not forgot to **release** the command buffers once they have been submitted:

```C++
// Release:
for (auto cmd : commands) {
	wgpuCommandBufferRelease(cmd);
}
```

> 🤔 Hey but what about **creating these buffers**, to begin with?

A command buffer, which has type `WGPUCommandBuffer`, is not a buffer that we directly create! This buffer uses a special format that is left to the discretion of your driver/hardware. To build this buffer, we use a **command encoder**.

### Command encoder

**WIP line**
