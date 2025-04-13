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

They are not too far, but for high performance applications like real time graphics or when manipulating large amounts of data like in machine learning, this matters.

### Latency

**Even the smallest bit of information** needs some time for the round trip to and back from the GPU. As a consequence, functions that send instructions to the GPU return almost immediately: they **do not wait for the instruction to have actually been executed** because that would require to wait for the GPU to transfer back the "I'm done" information.

Instead, the commands intended for the GPU are **batched** and fired through a **command queue**. The GPU consumes this queue **whenever it is ready**.

The CPU-side of our program, i.e., the C++ code that we write, lives in the **Content timeline**. The other side of the command queue is in the **Queue timeline**, running on the GPU.

```{note}
There is also a **Device timeline** defined in [WebGPU's documentation](https://www.w3.org/TR/webgpu/#programming-model-timelines). It corresponds to the GPU operations for which our code actually waits for an immediate answer (called "synchronous" calls), but unlike the JavaScript API, it is roughly the same as the content timeline in our C++ case.
```

### Bandwidth

Since the GPU is meant for **massive parallel data processing**, its performance can easily be **bound by the memory transfers** rather than the actual computation.

As it turns out, the **memory bandwidth limits** are more often hit within the GPU itself, **between its storage and its compute units**, but the CPU-GPU bandwidth is also limited, which one feels when trying to transfer large textures too often for instance.

```{note}
The connection between the CPU memory (RAM) and GPU memory (vRAM) depends on the type of GPU. Some GPUs are *integrated* within the same chip as the CPU, so they share the same memory. A *discrete* GPU is typically connected through a PCIe wire. And an *external* GPU would be connected with a Thunderbolt wire for instance. Each has a different bandwidth.
```

Queue operations
----------------

**WIP line**

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
