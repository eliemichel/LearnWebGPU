First Color
===========

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)

The goal of this chapter is to draw a solid color all over our window. This will be the occasion to introduce 3 new concepts of WebGPU:

 - Swap Chains
 - Texture Views
 - Render Passes

Swap Chain
----------

### Drawing process

To understand the notion of *Swap Chain*, we need to know a little more about how the window's surface is drawn.

First, the render pipeline does not draw directly on the texture that is currently displayed, otherwise we would see pixels change all the time. A typical pipeline draws to an off-screen texture, which replaces the currently displayed one only once it is complete. We then say that the texture is **presented** to the surface.

Second, drawing takes a different time than the frame rate required by your application, so the GPU may have to wait until the next frame is needed. There might be more than one off-screen texture waiting in the queue to be presented, so that fluctuations in the render time get amortized.

Last, these textures are reused as much as possible. As soon as a new texture is presented, the previous one can be reused as a target for the next frame. This whole texture swapping mechanism is implemented by the **Swap Chain** object.

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
swapChainDesc.width = 640;
swapChainDesc.height = 480;
```

```{warning}
As you can guess, we will have to take care of creating a new swap chain when the window is resized. In the meantime, do not try to resize it.
```

For the swap chain to allocate textures, we also need to specify their *format*. The format is a combination of a number of channels (a subset of red, green, blue, alpha), a size per channel (8, 16 or 32 bits) and a channel type (float, integer, signed or not), a compression scheme, a normalization mode, etc.

All available combinations are listed in the `WGPUTextureFormat` enum, but since our swap chain targets an existing surface, we can just use whichever format the surface uses:

```C++
WGPUTextureFormat swapChainFormat = wgpuSurfaceGetPreferredFormat(surface, adapter);
swapChainDesc.format = swapChainFormat;
```

Like buffers, textures are allocated for a specific usage. In our case, we will use them as the target of a Render Pass so it needs to be created with the `RenderAttachment` usage flag:

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

In our case, we use a Fifo, as illustrated in the video above.

```C++
swapChainDesc.presentMode = WGPUPresentMode_Fifo;
```

We may now create the swap chain:

```C++
WGPUSwapChain swapChain = wgpuDeviceCreateSwapChain(device, surface, &swapChainDesc);
std::cout << "Swapchain: " << device << std::endl;
```

```{note}
The Swap Chain is something that is not exposed in the JavaScript version of the API. Like the notion of *surface* that we have met already, by the way. The web browser takes care of it and does not offer any option.
```

Texture View
------------

Let's move on to the main loop. As explained above, the swap chain provides us with the texture where to draw the next frame. It is as simple as this:

```C++
// In the main loop
WGPUTextureView nextTexture = wgpuSwapChainGetCurrentTextureView(swapChain);
std::cout << "nextTexture: " << nextTexture << std::endl;
```

Note that this returns a *Texture View*. This gives a restricted access to the actual texture object allocated by the swap chain, so that internally the swap chain can use whatever organization it wants while exposing a view that has the dimensions and format that we expect.

Getting the texture may fail, in particular if the window has been resized and thus the target surface changed, so don't forget to check that it is not null:

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

Render Pass
-----------

TODO

```C++
WGPURenderPassDescriptor renderPassDesc = {};
renderPassDesc.nextInChain = nullptr;
renderPassDesc.colorAttachmentCount = 1;
WGPURenderPassColorAttachment renderPassColorAttachment = {};
renderPassColorAttachment.view = nextTexture;
renderPassColorAttachment.resolveTarget = 0;
renderPassColorAttachment.loadOp = WGPULoadOp_Clear;
renderPassColorAttachment.storeOp = WGPUStoreOp_Store;
renderPassColorAttachment.clearValue = WGPUColor{ 0.9, 0.1, 0.2, 1.0 };
renderPassDesc.colorAttachments = &renderPassColorAttachment;
renderPassDesc.depthStencilAttachment = nullptr;
renderPassDesc.timestampWriteCount = 0;
WGPURenderPassEncoder renderPass = wgpuCommandEncoderBeginRenderPass(encoder, &renderPassDesc);
wgpuRenderPassEncoderEnd(renderPass);
```

Conclusion
----------

![First colored window](/images/first-color.png)

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)
