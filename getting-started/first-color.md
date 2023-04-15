First Color
===========

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)

The goal of this chapter is to **draw a solid color** all over our window. This will be the occasion to introduce 3 new concepts of WebGPU:

 - Swap Chains
 - Texture Views
 - Render Passes

Swap Chain
----------

### Drawing process

To understand the notion of **Swap Chain**, we need to know a little more about how the window's surface is drawn.

First, the render pipeline **does not draw directly on the texture that is currently displayed**, otherwise we would see pixels change all the time. A typical pipeline draws to an off-screen texture, which replaces the currently displayed one only once it is complete. We then say that the texture is **presented** to the surface.

Second, drawing takes a **different time** than the frame rate required by your application, so the GPU may have to wait until the next frame is needed. There might be more than one off-screen texture waiting in the queue to be presented, so that fluctuations in the render time get amortized.

Last, **these off-screen textures are reused** as much as possible. As soon as a new texture is presented, the previous one can be reused as a target for the next frame. This whole texture swapping mechanism is implemented by the **Swap Chain** object.

```{note}
Remember that the GPU process runs at its own pace and that our CPU-issued commands are only asynchronously executed. Implementing the swap chain process manually would hence require a lot of boilerplate, so we are glad it is provided by the API!
```

<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:960px">
    <source src="../_static/swapchain.mp4" type="video/mp4">
</video>

*Left: The render process draws on an off-screen texture. Middle: Rendered textures wait in a queue. Right: At a regular frame rate, rendered textures are presented to te window's surface.*

### Creation

As always, we pass swap chain creation option through a descriptor. A first obvious option is the size of all the textures that are manipulated:

```C++
WGPUSwapChainDescriptor swapChainDesc = {};
swapChainDesc.nextInChain = nullptr;
swapChainDesc.width = 640;
swapChainDesc.height = 480;
```

```{warning}
As you can guess, we will have to take care of creating a new swap chain **when the window is resized**. In the meantime, do not try to resize it. You may add `glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);` before creating the window to instruct GLFW to disable resizing.
```

For the swap chain to **allocate textures**, we also need to specify their **format**. The format is a combination of a number of channels (a subset of red, green, blue, alpha), a size per channel (8, 16 or 32 bits) and a channel type (float, integer, signed or not), a compression scheme, a normalization mode, etc.

All available combinations are listed in the `WGPUTextureFormat` enum, but since our swap chain targets an existing surface, we can just use whichever format the surface uses:

```C++
WGPUTextureFormat swapChainFormat = wgpuSurfaceGetPreferredFormat(surface, adapter);
swapChainDesc.format = swapChainFormat;
```

```{admonition} Dawn
When using the Dawn implementation of WebGPU, `wgpuSurfaceGetPreferredFormat` is not implemented yet. Actually, the only texture format it supports is `WGPUTextureFormat_BGRA8Unorm`.
```

Textures are allocated for a **specific usage**, that dictates the way the GPU organizes its memory. In our case, we use the swap chain textures as targets for a *Render Pass* so it needs to be created with the `RenderAttachment` usage flag:

```C++
swapChainDesc.usage = WGPUTextureUsage_RenderAttachment;
```

Finally, we can tell which texture from the waiting queue must be presented at each frame. Possible values are:

 - `Immediate`: No off-screen texture is used, the render process directly draws on the surface, which might lead to artifacts (called *tearing*) but has zero latency.
 - `Mailbox`: There is only one slot in the queue, and when a new frame is rendered, it replaces the one currently waiting (which is discarded without ever being presented).
 - `Fifo`: Stands for "first in, first out", meaning that the presented texture is always the oldest one, like a regular queue. No rendered texture is wasted.

```{tip}
The `Force32` enum values that you can find when reading the source code of `webgpu.h` is not a "legal" value, it is just here to force the underlying enum type to be a 32 bit integer.
```

In our case, we use `Fifo`, as illustrated in the video above.

```C++
swapChainDesc.presentMode = WGPUPresentMode_Fifo;
```

We may now create the swap chain:

```C++
WGPUSwapChain swapChain = wgpuDeviceCreateSwapChain(device, surface, &swapChainDesc);
std::cout << "Swapchain: " << swapChain << std::endl;
```

```{note}
The Swap Chain is something that is not exposed in the JavaScript version of the API. Like the notion of *surface* that we have met already, by the way. The web browser takes care of it and does not offer any option.
```

```{admonition} Troubleshooting
If you get the error `Uncaptured device error: type 3 (Device(OutOfMemory))` when calling `wgpuDeviceCreateSwapChain`, check that you specified the `GLFW_NO_API` value to glfw when creating the window.
```

Texture View
------------

Let's move on to the **main loop** and see how to use the swap chain. As explained above, the swap chain provides us with the texture where to draw the next frame. It is as simple as this:

```C++
// In the main loop
WGPUTextureView nextTexture = wgpuSwapChainGetCurrentTextureView(swapChain);
std::cout << "nextTexture: " << nextTexture << std::endl;
```

Note that this returns a **Texture View**. This gives a restricted access to the actual texture object allocated by the swap chain, so that internally the swap chain can use whatever organization it wants while exposing a view that has the dimensions and format that we expect.

Getting the texture view **may fail**, in particular if the window has been resized and thus the target surface changed, so don't forget to check that it is not null:

```C++
if (!nextTexture) {
    std::cerr << "Cannot acquire next swap chain texture" << std::endl;
    return 1;
}
```

```{important}
*(2022-12-20)* In the `wgpu-native` implementation of WebGPU, we need to *drop* the texture view once we are done using it. This is a non-standard addition not provided in `webgpu.h`, but rather in the extra header `wgpu.h` provided along with it.
```

```C++
// When using the wgpu-native implementation
#include "wgpu.h"

WGPUTextureView nextTexture = wgpuSwapChainGetCurrentTextureView(swapChain);

// [...] (Do something with the texture view)

wgpuTextureViewDrop(nextTexture); // non-standard but required by wgpu-native
```

At the end of the main loop, once the texture is filled in and dropped, we can tell the swap chain to present the next texture (which depends on the `presentMode` of the swap chain):

```C++
wgpuSwapChainPresent(swapChain);
```

Render Pass
-----------

### Render pass encoder

We now hold the texture where to draw to display something in our window. Like any GPU-side operation, we trigger it from the command queue, using a command encoder as described in [the previous chapter](the-command-queue.md). Build a `WGPUCommandEncoder` called `encoder`, then submit it to the queue. In between we will add a command that clears the screen with a uniform color.

If you look in `webgpu.h` at the methods of the encoder (the procedures starting with `wgpuCommandEncoder`), most of them are related to copying buffers and textures around. Except two special ones: `wgpuCommandEncoderBeginComputePass` and `wgpuCommandEncoderBeginRenderPass`. These return specialized encoder objects, namely `WGPUComputePassEncoder` and `WGPURenderPassEncoder`, that give access to commands dedicated to respectively computing and 3D rendering.

In our case, we use a render pass:

```C++
WGPURenderPassDescriptor renderPassDesc = {};
// [...] set up descriptor
WGPURenderPassEncoder renderPass = wgpuCommandEncoderBeginRenderPass(encoder, &renderPassDesc);
wgpuRenderPassEncoderEnd(renderPass);
```

Note that we directly end the pass without issuing any other command. This is because the render pass has a built-in mechanism for clearing the screen when it begins, which we'll set up through the descriptor.

### Color attachment

A render pass leverages the 3D rendering circuits of the GPU to draw content into one or multiple textures. So one important thing to set up is to tell which textures are the target of this process. These are the **attachments** of the render pass.

The number of attachment is variable, so the descriptor gets it through two fields: the number `colorAttachmentCount` of attachments and the address `colorAttachments` of the color attachment array. Since we only use one, the address of the array is just the address of a single `WGPURenderPassColorAttachment` variable.

```C++
WGPURenderPassColorAttachment renderPassColorAttachment = {};
// [...] Set up the attachment

renderPassDesc.colorAttachmentCount = 1;
renderPassDesc.colorAttachments = &renderPassColorAttachment;
```

The first important setting of the attachment is the texture view it must draw in. In our case, the view returned by the swap chain because we directly want to draw on screen, but in a advanced pipelines it is very common to draw on intermediate textures, which are then fed to e.g., post-process passes.

```C++
renderPassColorAttachment.view = nextTexture;
```

There is a second target texture view called `resolveTarget`, but it is not relevant here because we do not use *multi-sampling* (more on this later).

```C++
renderPassColorAttachment.resolveTarget = nullptr;
```

The `loadOp` setting indicates the load operation to perform on view prior to executing the render pass. It can be either read from the view or set to a default uniform color, namely the clear value. When it does not matter, use `WGPULoadOp_Clear` as it is likely more efficient.

The `storeOp` indicates the operation to perform on view after executing the render pass. It can be either stored or discarded (which only makes sense if the render pass has side-effects).

And the `clearValue` is the value to clear the screen with, put anything you want in here! The 4 values are the red, green, blue and alpha channels, on a scale from 0.0 to 1.0.

```C++
renderPassColorAttachment.loadOp = WGPULoadOp_Clear;
renderPassColorAttachment.storeOp = WGPUStoreOp_Store;
renderPassColorAttachment.clearValue = WGPUColor{ 0.9, 0.1, 0.2, 1.0 };
```

```{admonition} Dawn
Unfortunately the `clearValue` field is not taken into account by Dawn.
```

### Misc

There is also one special type of attachment, namely the *depth* and *stencil* attachment (it is a single attachment potentially containing two channels). We'll come back on this later on, for now we do not use it so we set it to null:

```C++
renderPassDesc.depthStencilAttachment = nullptr;
```

When measuring the performance of a render pass, it is not possible to use CPU-side timing functions, since the commands are not executed synchronously. Instead, the render pass can receive a set of timestamp queries. We do not use it in this example.

```C++
renderPassDesc.timestampWriteCount = 0;
renderPassDesc.timestampWrites = nullptr;
```

Lastly, we set `nextInChain` to a null pointer (remember this pointer is an extension mechanism that the standard WebGPU API does not use).

```C++
renderPassDesc.nextInChain = nullptr;
```

Conclusion
----------

At this stage you should be able to get a colored window. This seems simple, but it made us meet a lot of important concepts.

 * Instead of directly drawing to the window's surface, we draw to an off-screen texture and the **swap chain** is responsible for managing the texture turn over.
 * The 3D rendering pipeline of the GPU is leveraged through the **render pass**, which is a special scope of commands accessible through the command encoder.
 * The render pass draws to one or multiple **attachments**, which are texture views.


```{figure} /images/first-color.png
:align: center
:class: with-shadow
Our first color!
```

We are now ready with the basic WebGPU setup, and can dive more deeply in the 3D rendering pipeline.

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)
