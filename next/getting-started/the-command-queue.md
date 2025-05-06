The Command Queue <span class="bullet">🟢</span>
=================

```{lit-setup}
:tangle-root: 015 - The Command Queue - Next
:parent: 010 - The Device - Next
```

*Resulting code:* [`step015-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015-next)

Now that we have a `WGPUDevice` object in our hands, we can use it to **sent data and instructions** to the GPU. We learn in this chapter a **key concept** of WebGPU (and of most modern graphics APIs as well), namely **the command queue**.

```{important}
Notice how I use the term ***send*** here: as we will highlight see in this chapter, **our C++ code never runs on the GPU**, all it does is sending bits to the GPU, where programs follow a different logic (and use **a different programming language**) that we will see in the [next chapter](./our-first-shader.md).
```

```{themed-figure} /images/command-queue/queue_{theme}.svg
:align: center

The CPU instructs the GPU what to do by **sending commands** through a command queue.
```

Different timelines
-------------------

One important thing to keep in mind when doing graphics programming: we have **two processors running simultaneously**. One of them is the CPU, also known as *host*, and the other one is the GPU, or *device*. There are two rules:

 1. **The code we write runs on the CPU**, and some of it triggers operations on the GPU. The only exception are *shaders*, which actually run on GPU.
 2. Processors are "**far away**", meaning that communicating between them **takes time**.

They are not too far, but for high performance applications like real time graphics or when manipulating large amounts of data like in machine learning, this matters. For two reasons:

### Bandwidth

```{themed-figure} /images/command-queue/bandwidth_{theme}.svg
:align: center

The bandwidth tells **how much information** can travel at the same time.
```

Since the GPU is meant for **massive parallel data processing**, its performance can easily be **bound by the memory transfers** rather than the actual computation.

As it turns out, the **memory bandwidth limits** are more often hit within the GPU itself, **between its storage and its compute units**, but the CPU-GPU bandwidth is also limited, which one feels when trying to transfer large textures too often for instance.

```{note}
The connection between the **CPU memory** (RAM) and **GPU memory (vRAM)** depends on the type of GPU. Some GPUs are **integrated** within the same chip as the CPU, so they share the same memory. A **discrete** GPU is typically connected through a PCIe wire. And an **external** GPU would be connected with a Thunderbolt wire for instance. Each has a different bandwidth.
```

### Latency

```{themed-figure} /images/command-queue/latency_{theme}.svg
:align: center

The latency is **the time it takes** for each bit to travel.
```

**Even the smallest bit of information** needs some time for the round trip to and back from the GPU (can be as long as 100µs). As a consequence, functions that send instructions to the GPU return almost immediately: they **do not wait for the instruction to have actually been executed** because that would require to wait for the GPU to transfer back the "I'm done" information.

Instead, the commands intended for the GPU are **batched** and fired through a **command queue**. The GPU consumes this queue **whenever it is ready**. This is what we detail in this chapter.

### Timelines

The CPU-side of our program, i.e., the C++ code that we write, lives in the **Content timeline**. The other side of the command queue is in the **Queue timeline**, running on the GPU.

```{themed-figure} /images/command-queue/timelines_{theme}.svg
:align: center

**The order of instructions is conserved**, but they are not executed at the same time as they are sent. This is why any operation that reads back from the GPU is **asynchronous**.
```

```{note}
There is also a **Device timeline** defined in [WebGPU's documentation](https://www.w3.org/TR/webgpu/#programming-model-timelines). It corresponds to the GPU operations for which our code actually waits for an immediate answer (called "synchronous" calls), but unlike the JavaScript API, it is roughly the same as the content timeline in our C++ case.
```

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

Again, we can note that all these functions have a `void` return type: they send instructions/data to the GPU and return immediately **without waiting from an answer from the GPU**.

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

A command encoder is created following **the usual object creation idiom** of WebGPU:

```{lit} C++, Create Command Encoder
WGPUCommandEncoderDescriptor encoderDesc = WGPU_COMMAND_ENCODER_DESCRIPTOR_INIT;
encoderDesc.label = toWgpuStringView("My command encoder");
WGPUCommandEncoder encoder = wgpuDeviceCreateCommandEncoder(device, &encoderDesc);
```

We can now use the encoder to write instructions. Since we do not have any object to manipulate yet we stick with simple **debug placeholder** for now:

```{lit} C++, Add commands
wgpuCommandEncoderInsertDebugMarker(encoder, toWgpuStringView("Do one thing"));
wgpuCommandEncoderInsertDebugMarker(encoder, toWgpuStringView("Do another thing"));
```

And then finally we **generate the command buffer** from the encoder using `wgpuCommandEncoderFinish`. This requires an extra descriptor (because it is a point where there can be extensions):

```{lit} C++, Finish encoding and submit
WGPUCommandBufferDescriptor cmdBufferDescriptor = WGPU_COMMAND_BUFFER_DESCRIPTOR_INIT;
cmdBufferDescriptor.label = toWgpuStringView("Command buffer");
WGPUCommandBuffer command = wgpuCommandEncoderFinish(encoder, &cmdBufferDescriptor);
wgpuCommandEncoderRelease(encoder); // release encoder after it's finished

// Finally submit the command queue
std::cout << "Submitting command..." << std::endl;
wgpuQueueSubmit(queue, 1, &command);
wgpuCommandBufferRelease(command);
std::cout << "Command submitted." << std::endl;
```

```{lit} C++, Test command encoding (hidden)
{{Get Queue}}
{{Create Command Encoder}}
{{Add commands}}
{{Finish encoding and submit}}
{{Wait for completion}}
```

```{lit} C++, Main body (append, hidden)
{{Test command encoding}}
```

Waiting for completion
----------------------

As repeated and illustrated above, instructions that are submitted to the GPU get executed at their own pace. In many cases, it is not a big issue (as long as the instructions are executed in the right order).

Sometimes however, we really want to **have the CPU wait until submitted instructions have been executed**. For that, we may use the function `wgpuQueueOnSubmittedWorkDone`. This creates **an asynchronous operation that does nothing on the GPU side**. Or, more exactly, nothing else than signaling that everything received before has been executed.

Like any asynchronous operation, it takes a **callback info** as argument and returns a `WGPUFuture`. In this case, it only takes one other argument, namely the queue into which we push the operation:

```C++
// Signature of the wgpuQueueOnSubmittedWorkDone function in webgpu.h
WGPUFuture wgpuQueueOnSubmittedWorkDone(
	WGPUQueue queue,
	WGPUQueueWorkDoneCallbackInfo callbackInfo
);
```

As usual, the callback info contains a `nextInChain` pointer for extensions, a `mode`, two `userdata` pointers and a `callback` function pointer. The latter must have the following type:

```C++
// Definition of the WGPUQueueWorkDoneCallback function type in webgpu.h
typedef void (*WGPUQueueWorkDoneCallback)(
	WGPUQueueWorkDoneStatus status,
	void* userdata1,
	void* userdata2
);
```

```{note}
In newer versions of WebGPU, an extra `WGPUStringView message` argument is added after the status.
```

In other words, all it receives besides our potential `userdata` pointers is a status.

````{warning}
The returned status **does not** tell about the success of **other** operations. All it says is whether querying for the moment where submitted work was done did succeed or not. Possible values are:

- `WGPUQueueWorkDoneStatus_Success` when the query operation went well.
- `WGPUQueueWorkDoneStatus_InstanceDropped` when the WebGPU instanced was dropped before previous instructions where executed. This callback is executed nonetheless, but with this special status value.
- `WGPUQueueWorkDoneStatus_Error` when something went wrong in the process (it's probably a bad sign about the overall course of your program).
````

```{note}
In **newer versions** of WebGPU, `InstanceDropped` reason was renamed `CallbackCancelled`.
```

Inspired by what we did when requesting the adapter and device, we can create a callback that takes a boolean as first user pointer and turn it on whenever the callback is invoked:

```{lit} C++, Wait for completion
// Our callback invoked when GPU instructions have been executed
auto onQueuedWorkDone = [](
	WGPUQueueWorkDoneStatus status,
	void* userdata1,
	void* /* userdata2 */
) {
	// Display a warning when status is not success
	if (status != WGPUQueueWorkDoneStatus_Success) {
		std::cout << "Warning: wgpuQueueOnSubmittedWorkDone failed, this is suspicious!" << std::endl;
	}

	// Interpret userdata1 as a pointer to a boolean (and turn it into a
	// mutable reference), then turn it to 'true'
	bool& workDone = *reinterpret_cast<bool*>(userdata1);
	workDone = true;
};

// Create the boolean that will be passed to the callback as userdata1
// and initialize it to 'false'
bool workDone = false;

// Create the callback info
WGPUQueueWorkDoneCallbackInfo callbackInfo = WGPU_QUEUE_WORK_DONE_CALLBACK_INFO_INIT;
callbackInfo.mode = WGPUCallbackMode_AllowProcessEvents;
callbackInfo.callback = onQueuedWorkDone;
callbackInfo.userdata1 = &workDone; // pass the address of workDone

// Add the async operation to the queue
wgpuQueueOnSubmittedWorkDone(queue, callbackInfo);

{{Wait for workDone to be true}}

std::cout << "All queued instructions have been executed!" << std::endl;
```

To wait for the callback to effectively get invoked and thus `workDone` to become `true`, we **reuse the same loop as before**, that calls `wgpuInstanceProcessEvents` interleaved with a small sleep:

```{lit} C++, Wait for workDone to be true
// Hand the execution to the WebGPU instance until onQueuedWorkDone gets invoked
wgpuInstanceProcessEvents(instance);
while (!workDone) {
	sleepForMilliseconds(200);
	wgpuInstanceProcessEvents(instance);
}
```

```{note}
Again, we will see in the [next chapter](playing-with-buffers.md) a more fine-grained method to wait for asynchronous operations, using the `WGPUFuture` handle returned by `wgpuQueueOnSubmittedWorkDone`, but for this case using `wgpuInstanceProcessEvents` works well.
```

You should finally see something like this in your program's output:

```
Submitting command...
Command submitted.
All queued instructions have been executed!
Device 0000009EC06FF4F0 was lost: reason 3 (A valid external Instance reference no longer exists.)
```

````{tip}
It is **normal that our device gets lost** at the end of our program. We can **have the reason change a bit** though by making sure the instance realizes that the device got released before deleting it on its turn. To do so, you may call `wgpuInstanceProcessEvents` between `wgpuDeviceRelease` and `wgpuInstanceRelease`:

```C++
// At the end
wgpuQueueRelease(queue);
wgpuDeviceRelease(device);
// We clean up the WebGPU instance
wgpuInstanceProcessEvents(instance); // <-- add this!
wgpuInstanceRelease(instance);
```

You should now see something like this in your output:

```
Device 000000D266AFEF50 was lost: reason 2 (Device was destroyed.)
```
````

Conclusion
----------

We have seen a few important notions in this chapter:

 - The CPU and GPU live in **different timelines**.
 - Commands are streamed from CPU to GPU through a **command queue**.
 - Queued command buffers must be encoded using a **command encoder**.
 - We can **wait for enqueued commands** to be executed with `wgpuQueueOnSubmittedWorkDone`.

This was a bit abstract because we can queue operations but we did not see any yet. In the next chapter we will start with **simple operations on memory buffers**, followed by **our first shader** to compute things on the GPU!

*Resulting code:* [`step015-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015-next)
