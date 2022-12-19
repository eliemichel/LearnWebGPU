First Color
===========

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)

The goal of this chapter is to draw a solid color all over our window. This will be the occasion to introduce 3 new concepts of WebGPU:

 - Swap Chains
 - Texture Views
 - Render Passes

Swap Chain
----------

To understand the notion of *Swap Chain*, we need to know a little more about how the window's surface is drawn.

<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:960px">
    <source src="../_static/swapchain.mp4" type="video/mp4">
</video>

First, the render pipeline does not draw directly on the texture that is currently displayed, otherwise we would see pixels change all the time. A typical pipeline draws to an off-screen texture, which replaces the currently displayed one only once it is complete. We then say that the texture is **presented** to the surface (what happens once the spinner is fully loaded in the animation above).

Second, drawing takes a different time than the frame rate required by your application, so the GPU may have to wait until the next frame is needed. There might be more than one off-screen texture waiting in the queue to be presented, so that fluctuations in the render time get amortized.

Last, these textures are reused as much as possible. As soon as a new texture is presented, the previous one can be reused as a target for the next frame. This whole texture swapping mechanism is implemented by the **Swap Chain** object.

TODO

```C++
std::cout << "Creating swapchain device..." << std::endl;
WGPUTextureFormat swapChainFormat = wgpuSurfaceGetPreferredFormat(surface, adapter);
WGPUSwapChainDescriptor swapChainDesc = {};
swapChainDesc.usage = WGPUTextureUsage_RenderAttachment;
swapChainDesc.format = swapChainFormat;
swapChainDesc.width = 640;
swapChainDesc.height = 480;
swapChainDesc.presentMode = WGPUPresentMode_Fifo;
WGPUSwapChain swapChain = wgpuDeviceCreateSwapChain(device, surface, &swapChainDesc);
std::cout << "Swapchain: " << device << std::endl;
```

```{note}
The Swap Chain is something that is not exposed in the JavaScript version of the API. Like the notion of *surface* that we have met already, by the way. The web browser takes care of it and does not offer any option.
```

Texture View
------------

TODO

```C++
// In the main loop
WGPUTextureView nextTexture = wgpuSwapChainGetCurrentTextureView(swapChain);
if (!nextTexture) {
    std::cerr << "Cannot acquire next swap chain texture" << std::endl;
    return 1;
}
std::cout << "nextTexture: " << nextTexture << std::endl;

// [...] (Do something with the texture view)

wgpuTextureViewDrop(nextTexture);
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
