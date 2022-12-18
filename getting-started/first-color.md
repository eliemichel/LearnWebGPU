First Color
===========

*Resulting code:* [`step020`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020)

The goal of this chapter is to draw a solid color all over our window. This will be the occasion to introduce 3 new concepts of WebGPU:

 - Swap Chains
 - Texture Views
 - Render Passes

Swap Chain
----------

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
