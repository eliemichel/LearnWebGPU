First Color <span class="bullet">🟢</span>
===========

```{lit-setup}
:tangle-root: 025 - First Color - Next
:parent: 020 - Opening a window - Next
```

*Resulting code:* [`step025-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step025-next)

The goal of this chapter is to **draw a solid color** all over our window. To do so, we add the following steps:

 1. We must first **configure** the *surface* of our window.
 2. We then get at each frame the **Surface Texture** to draw onto.
 3. And finally we create a **Render Pass** to effectively draw something.

Surface configuration
---------------------

At the end of the previous chapter, we introduced the **surface** object as the link between the OS window (managed by GLFW) and the WebGPU instance.

However, this surface needs to be **configured** before we can draw on it. To understand why, we need to know a little more about how the window's surface is drawn.

### Drawing process

First, the render pipeline **does not draw directly on the texture that is currently displayed**, otherwise we would see pixels change all the time. A typical pipeline draws to an **off-screen texture**, which replaces the currently displayed one only once it is complete. We then say that the texture is **presented** to the surface.

Second, drawing takes a **different time** than the frame rate required by your application, so the GPU may have to wait until the next frame is needed. There might be more than one off-screen texture waiting in the queue to be presented, so that fluctuations in the render time get amortized.

Last, **these off-screen textures are reused** as much as possible. As soon as a new texture is presented, the previous one can be reused as a target for the next frame. This whole mechanism is called a **Swap Chain** and is handled under the hood by the **Surface** object.

```{note}
Remember that the GPU process runs at its own pace and that our CPU-issued commands are only asynchronously executed. Implementing the swap chain process manually would hence require a lot of boilerplate, so we are glad it is provided by the API!
```

<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:960px">
    <source src="/_static/swapchain.mp4" type="video/mp4">
</video>

<p class="align-center">
    <span class="caption-text"><em><strong>Left:</strong> The render process draws on an off-screen texture. <strong>Middle:</strong> Rendered textures wait in a queue. <strong>Right:</strong> At a regular frame rate, rendered textures are presented to the window's surface.</em></span>
</p>

### Configuration

The process that we just described has a couple of parameters that we set through the `wgpuSurfaceConfigure` function. It works a bit like an object creation:

```{lit} C++, Surface Configuration
WGPUSurfaceConfiguration config = WGPU_SURFACE_CONFIGURATION_INIT;

{{Describe the surface configuration}}

wgpuSurfaceConfigure(m_surface, &config);
```

This must be done **at the end of the initialization**. And at the end of the program, we can *unconfigure* the surface (to release the swap chain):

```{lit} C++, Terminate (prepend)
wgpuSurfaceUnconfigure(m_surface);
```

#### Texture parameters

Lastly, the surface needs to know the device to use to create the swap chain textures:

We must first specify the parameters used to **allocate the textures** for the underlying swap chain. This includes of course a **size** (which we set to the window size), but also the device to use to create theses textures, and a **format**.

```{lit} C++, Describe the surface configuration
// Configuration of the textures created for the underlying swap chain
config.width = 640;
config.height = 480;
config.device = m_device;
{{Describe surface format}}
```

```{warning}
As you can guess, we will have to take care of re-configuring the surface **when the window is resized**. In the meantime, **do not try** to resize it. This is why in the previous chapter we have added `glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);` before creating the window.
```

The **format** is a combination of a **number of channels** (a subset of red, green, blue, alpha), a **size per channel** (8, 16 or 32 bits) and a **channel type** (float, integer, signed or not), a compression scheme, a normalization mode, etc.

All available combinations are listed in the `WGPUTextureFormat` enum, but since our swap chain targets an existing surface, it is advised to use the **the format preferred by the surface** (to avoid unnecessary conversions).

To do so, we use the `wgpuSurfaceGetCapabilities` function, which not only tells us what a given adapter can do with a given surface, but also return these capabilities **by order of preference**. Because the `WGPUSurfaceCapabilities` structure contains **dynamically allocated arrays**, we need to check that the get worked, and call `wgpuSurfaceCapabilitiesFreeMembers` afterwards to release these arrays:

```{lit} C++, Describe surface format
// We initialize an empty capability struct:
WGPUSurfaceCapabilities capabilities = WGPU_SURFACE_CAPABILITIES_INIT;

// We get the capabilities for a pair of (surface, adapter).
// If it works, this populates the `capabilities` structure
WGPUStatus status = wgpuSurfaceGetCapabilities(m_surface, adapter, &capabilities);
if (status != WGPUStatus_Success) {
    return false;
}

// From the capabilities, we get the preferred format: it is always the first one!
// (NB: There is always at least 1 format if the GetCapabilities was successful)
config.format = capabilities.formats[0];

// We no longer need to access the capabilities, so we release their memory.
wgpuSurfaceCapabilitiesFreeMembers(capabilities);
```

````{warning}
Make sure to place the call to `wgpuAdapterRelease` **after** the call to `wgpuSurfaceGetCapabilities`, since the latter uses our `adapter` handle.

```{lit} C++, Initialize (hidden, replace)
{{Open window and get adapter}}

{{Request device}}

m_queue = wgpuDeviceGetQueue(m_device);

{{Surface Configuration}}

// We no longer need to access the adapter
wgpuAdapterRelease(adapter);
```
````

#### Presentation parameters

```{note}
What we do in this section corresponds to what is **already set by default**. You can thus **skip this** if you are not interested in the details about alternatives!
```

After telling how to allocate textures, we can tell which texture from the waiting queue must be presented at each frame. Possible values are found in the `WGPUPresentMode` enum:

 - `Immediate`: No off-screen texture is used, the render process directly draws on the surface, which might lead to artifacts (called *tearing*) but has zero latency.
 - `Mailbox`: There is only one slot in the queue, and when a new frame is rendered, it replaces the one currently waiting (which is discarded without ever being presented).
 - `Fifo`: Stands for "first in, first out", meaning that the presented texture is always the oldest one, like a regular queue. No rendered texture is wasted.

```{tip}
The `Force32` enum values that you can find when reading the source code of `webgpu.h` is not a "legal" value, it is just here to force the underlying enum type to be a 32 bit integer.
```

In our case, we use `Fifo`, as illustrated in the video above.

```{lit} C++, Describe the surface configuration (append)
config.presentMode = WGPUPresentMode_Fifo;
```

Finally, we may specify how the textures will be composited onto the OS window, which may be used to create **transparent** windows. We can also simply leave it to the auto mode:

```{lit} C++, Describe the surface configuration (append)
config.alphaMode = WGPUCompositeAlphaMode_Auto;
```

```{admonition} Troubleshooting
If you get the error `Uncaptured device error: type 3 (Device(OutOfMemory))` when calling `wgpuSurfaceConfigure`, check that you specified the `GLFW_NO_API` value to glfw when creating the window.
```

Surface Texture
---------------

Now that our surface is configured, we can ask it **at each frame** for the **next available texture** in the swap chain, i.e., the texture onto which we must draw. Overall, the content of our main loop is as follows:

```{lit} C++, Main loop content (replace)
// In Application::MainLoop()
{{Get the next target texture view}}
{{Draw things}}
{{Present the surface onto the window}}
```

For the first step, we create a dedicated method `GetNextSurfaceView()` in our application class, which returns a **texture view** onto which the render pass will draw.

```{lit} C++, GetNextSurfaceView method
WGPUTextureView Application::GetNextSurfaceView() {
    {{Get the next surface texture}}
    {{Create surface texture view}}
    {{Release the texture}}
    return targetView;
}
```

```{lit} C++, Application implementation (append, hidden)
{{GetNextSurfaceView method}}
```

We then simply call this function at the beginning of the main loop and check that it returns a valid view:

```{lit} C++, Get the next target texture view
// Get the next target texture view
WGPUTextureView targetView = GetNextSurfaceView();
if (!targetView) return; // no surface texture, we skip this frame
```

````{note}
Do not forget to **declare the method** in the `Application` class declaration. This is an internal gear of our app so we make this method **private**:

```{lit} C++, Private methods (insert in {{Application class}} after "bool IsRunning();")
private:
    WGPUTextureView GetNextSurfaceView();
```
````

### Getting the next target texture

To get the texture to draw onto, we use `wgpuSurfaceGetCurrentTexture`. The "surface texture" is not really an object but rather a **container** for the **multiple things that this function returns**. It is thus up to us to create the `WGPUSurfaceTexture` container, which we pass to the function to write into it:

```{lit} C++, Get the next surface texture
WGPUSurfaceTexture surfaceTexture = WGPU_SURFACE_TEXTURE_INIT;
wgpuSurfaceGetCurrentTexture(m_surface, &surfaceTexture);
```

We then have access to the following information:

 - `surfaceTexture.texture` is the **texture** that we must draw on **during this frame**.
 - `surfaceTexture.status` tells us whether the operation was **successful**, and if not gives some hint about why.

```{note}
There are two slightly different cases of **success status**, namely `SuccessOptimal` and `SuccessSuboptimal`. The latter may arise when the window is being resized, and should be considered as "almost a failure", that we fix by reconfiguring the surface.
```

If the status is not a success we do not even create a view and just skip the frame:

```{lit} C++, Get the next surface texture (append)
if (
    surfaceTexture.status != WGPUSurfaceGetCurrentTextureStatus_SuccessOptimal &&
    surfaceTexture.status != WGPUSurfaceGetCurrentTextureStatus_SuccessSuboptimal
) {
    return nullptr;
}
```

### Texture view

What we will need in the next section is not directly the surface texture, but a **texture view**, which may represent a sub-part of the texture, or expose it using a different format.

We will come back on texture views in the [Texturing](/basic-3d-rendering/texturing/index.md) section of this guide, for now we can leave **almost every field** of the descriptor to their **default value**:

```{lit} C++, Create surface texture view
WGPUTextureViewDescriptor viewDescriptor = WGPU_TEXTURE_VIEW_DESCRIPTOR_INIT;
viewDescriptor.label = toWgpuStringView("Surface texture view");
viewDescriptor.dimension = WGPUTextureViewDimension_2D; // not to confuse with 2DArray
WGPUTextureView targetView = wgpuTextureCreateView(surfaceTexture.texture, &viewDescriptor);
```

As soon as we have this view, we can **release the texture**. The view indeed **holds a reference** to its parent texture, so as long as the view lives, the texture does as well.

```{lit} C++, Release the texture
// We no longer need the texture, only its view,
// so we release it at the end of GetNextSurfaceViewData
wgpuTextureRelease(surfaceTexture.texture);
```

The texture view is returned by `GetNextSurfaceViewData`, and we release it once we no longer need it, **after submitting the render pass** (which we introduce below):

```{lit} C++, Present the surface onto the window
// At the end of the frame
wgpuTextureViewRelease(targetView);
```

### Presenting

Finally, once the texture is filled in and released, we can tell the surface to **present** the next texture of its swap chain (which may or may not be the texture we just drew onto, depending on the `presentMode`):

```{lit} C++, Present the surface onto the window (append)
wgpuSurfacePresent(m_surface);
```

````{admonition} Building for the Web
In the context of a **Web browser**, we do **not** present the surface texture ourselves. We rather rely on `emscripten_set_main_loop_arg` (a.k.a. `requestAnimationFrame` in JavaScript) to call our `MainLoop()` function right before presenting.

As a consequence, we **must not** call `wgpuSurfacePresent()` when building with emcripten:

```{lit} C++, Present the surface onto the window (replace)
// At the end of the frame
wgpuTextureViewRelease(targetView);
#ifndef __EMSCRIPTEN__
wgpuSurfacePresent(m_surface);
#endif
```
````

Render Pass
-----------

### Render pass encoder

We now hold the texture where to draw to display something in our window. Like any GPU-side operation, we trigger drawing operations from the **command queue**, using a command encoder as described in the [Command Queue](the-command-queue.md).

We build a `WGPUCommandEncoder` called `encoder`, then submit it to the queue. In between we will add a command that clears the screen with a uniform color.

```{lit} C++, Draw things
{{Create Command Encoder}}
{{Encode Render Pass}}
{{Finish encoding and submit}}
```

````{note}
Do not forget to rename `device` into `m_device` and `queue` into `m_queue` when reusing the encoder related code from earlier chapters.

```{lit} C++, Create Command Encoder (replace, hidden)
WGPUCommandEncoderDescriptor encoderDesc = WGPU_COMMAND_ENCODER_DESCRIPTOR_INIT;
encoderDesc.label = toWgpuStringView("My command encoder");
WGPUCommandEncoder encoder = wgpuDeviceCreateCommandEncoder(m_device, &encoderDesc);
```

```{lit} C++, Finish encoding and submit (replace, hidden)
WGPUCommandBufferDescriptor cmdBufferDescriptor = WGPU_COMMAND_BUFFER_DESCRIPTOR_INIT;
cmdBufferDescriptor.label = toWgpuStringView("Command buffer");
WGPUCommandBuffer command = wgpuCommandEncoderFinish(encoder, &cmdBufferDescriptor);
wgpuCommandEncoderRelease(encoder); // release encoder after it's finished

// Finally submit the command queue
std::cout << "Submitting command..." << std::endl;
wgpuQueueSubmit(m_queue, 1, &command);
wgpuCommandBufferRelease(command);
std::cout << "Command submitted." << std::endl;
```
````

In chapter [*Our first shader*](our-first-shader.md), we introduced the concept of **pass**, and played with the most simple one, namely the compute pass. This time, we play with the **render pass**, using the `wgpuCommandEncoderBeginRenderPass` function:

```{lit} C++, Encode Render Pass
WGPURenderPassDescriptor renderPassDesc = WGPU_RENDER_PASS_DESCRIPTOR_INIT;
{{Describe Render Pass}}

WGPURenderPassEncoder renderPass = wgpuCommandEncoderBeginRenderPass(encoder, &renderPassDesc);
{{Use Render Pass}}
wgpuRenderPassEncoderEnd(renderPass);
wgpuRenderPassEncoderRelease(renderPass);
```

In general, we would need to set a specific **render pipeline** to run, but actually for this simple example we directly end the pass **without issuing** any other command: the render pass has a built-in mechanism for **clearing the screen** when it begins, which we will set up through the descriptor.

```{lit} C++, Use Render Pass (hidden)
// Use the render pass here (we do nothing with the render pass for now)
```

### Color attachment

A render pass leverages the 3D rendering circuits of the GPU to draw content into one or multiple textures. So one important thing to set up is to tell **which textures are the target** of this process. These are the **attachments** of the render pass.

The number of attachment is variable, so the descriptor gets it through two fields: the number `colorAttachmentCount` of attachments and the address `colorAttachments` of the color attachment array. Since we **only use one** here, the address of the array is just the address of a single `WGPURenderPassColorAttachment` variable.

```{lit} C++, Describe Render Pass
WGPURenderPassColorAttachment colorAttachment = WGPU_RENDER_PASS_COLOR_ATTACHMENT_INIT;

{{Describe the attachment}}

renderPassDesc.colorAttachmentCount = 1;
renderPassDesc.colorAttachments = &colorAttachment;
```

The first important setting of the attachment is the **texture view** it must draw in.

In our case, this is simply the `targetView` that we got from the surface, because we want to **directly draw on screen**, but in advanced pipelines it is very common to draw on **intermediate textures**, which are then fed to post-processing passes for instance.

```{lit} C++, Describe the attachment
colorAttachment.view = targetView;
```

The `loadOp` setting indicates the load operation to perform on the view **prior to executing** the render pass. It can be either read from the view or set to a default uniform color, namely the clear value. **When it does not matter**, use `WGPULoadOp_Clear` as it is likely more efficient.

The `storeOp` indicates the operation to perform on view **after executing** the render pass. It can be either stored or discarded (the latter only makes sense if the render pass has side-effects).

And the `clearValue` is the value to **clear the screen** with, put anything you want in here! The 4 values are the **red**, **green**, **blue** and **alpha** channels, on a scale **from 0.0 to 1.0**.

```{lit} C++, Describe the attachment (append)
colorAttachment.loadOp = WGPULoadOp_Clear;
colorAttachment.storeOp = WGPUStoreOp_Store;
colorAttachment.clearValue = WGPUColor{ 1.0, 0.8, 0.55, 1.0 };
```

Conclusion
----------

At this stage you should be able to get a colored window. This seems simple, but it made us meet a lot of important concepts.

 * Instead of directly drawing to the window's surface, we draw to an off-screen texture and the **swap chain** is responsible for managing the texture turn over.
 * The 3D rendering pipeline of the GPU is leveraged through the **render pass**, which is a special scope of commands accessible through the command encoder.
 * The render pass draws to one or multiple **attachments**, which are texture views.


```{figure} /images/first-color/first-color.png
:align: center
:class: with-shadow
Our first color!
```

We are now **ready with the basic WebGPU setup**, and can dive more deeply in the 3D rendering pipeline! The next chapter is a **bonus** that introduces a **more comfortable API** that benefits from C++ idioms.

*Resulting code:* [`step025-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step025-next)
