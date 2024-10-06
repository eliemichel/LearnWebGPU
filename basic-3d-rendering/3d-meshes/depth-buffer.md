Depth buffer <span class="bullet">🟡</span>
============

````{tab} With webgpu.hpp
*Resulting code:* [`step052`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla)
````

```{figure} /images/pyramid-zissue.png
:align: center
:class: with-shadow
There is something wrong with the depth.
```

The Z-Buffer algorithm
----------------------

The issue we are facing with this basic example comes from the problem of **visibility**. As easy to conceive as it is, the question "does this point see that one" (i.e., does the line between them intersect any geometry) is hard to answer efficiently.

In particular, when producing a **fragment**, we must figure out whether the 3D point it corresponds to is seen by the view point in order decide whether it must be blended into the output texture.

The **Z-Buffer algorithm** is what the GPU's render pipeline uses to solve the visibility problem:

 1. **For each pixel**, it stores the depth of the last fragment that has been blended into this pixel, or a default value (that represents the furthest depth possible).
 2. Each time a new fragment is produced, its **depth is compared** to this value. If the fragment depth is larger than the currently stored depth, it is **discarded** without being blended. Otherwise, it is blended normally and the stored value is updated to the depth of this new closest fragment.

As a result, only the fragment with the lowest depth is visible in the resulting image. The depth value for each pixel is stored in a special **texture** called the **Z-buffer**. This is the only memory overhead required by the Z-buffer algorithm, making it a good fit for real time rendering.

```{topic} About transparency
The fact that only the fragment with the lowest depth is visible is **not guaranteed** when fragments have **opacity values that are neither 0 or 1** (and alpha-blending is used). Even worse; the order in which fragments are emitted has an impact on the result (because blending a fragment **A** and then a fragment **B** is different than blending **B** then **A**).

Long story short: **transparent objects are always a bit tricky** to handle in a Z-buffer pipeline. A simple solution is to limit the number of transparent objects, and dynamically sort them wrt. their distance to the view point. More advanced schemes exist such as [Order-independent transparency](https://en.wikipedia.org/wiki/Order-independent_transparency) techniques.
```

Pipeline State
--------------

Since this Z-Buffer algorithm is a critical step of the 3D rasterization pipeline, it is implemented as a **fixed-function** stage. We configure it through the `pipelineDesc.depthStencil` field, which we had left null so far.

````{tab} With webgpu.hpp
```C++
DepthStencilState depthStencilState = Default;
// Setup depth state
pipelineDesc.depthStencil = &depthStencilState;
```
````

````{tab} Vanilla webgpu.h
```C++
void setDefault(WGPUStencilFaceState &stencilFaceState); {
	stencilFaceState.compare = WGPUCompareFunction_Always;
	stencilFaceState.failOp = WGPUStencilOperation_Keep;
	stencilFaceState.depthFailOp = WGPUStencilOperation_Keep;
	stencilFaceState.passOp = WGPUStencilOperation_Keep;
}

void setDefault(WGPUDepthStencilState &depthStencilState); {
	depthStencilState.format = WGPUTextureFormat_Undefined;
	depthStencilState.depthWriteEnabled = false;
	depthStencilState.depthCompare = WGPUCompareFunction_Always;
	depthStencilState.stencilReadMask = 0xFFFFFFFF;
	depthStencilState.stencilWriteMask = 0xFFFFFFFF;
	depthStencilState.depthBias = 0;
	depthStencilState.depthBiasSlopeScale = 0;
	depthStencilState.depthBiasClamp = 0;
	setDefault(depthStencilState.stencilFront);
	setDefault(depthStencilState.stencilBack);
}

// [...]

WGPUDepthStencilState depthStencilState;
setDefault(depthStencilState);
// Setup depth state
pipelineDesc.depthStencil = &depthStencilState;
```
````

The first aspect of the Z-Buffer algorithm that we can configure is the **comparison function** that is used to decide whether we should keep a new fragment or not. It defaults to `Always`, which basically deactivate the depth testing (the fragment is always blended).

**The most common choice** is to set it to `Less` to mean that a fragment is blended only if its depth is **less** than the current value of the Z-Buffer.

````{tab} With webgpu.hpp
```C++
depthStencilState.depthCompare = CompareFunction::Less;
```
````

````{tab} Vanilla webgpu.h
```C++
depthStencilState.depthCompare = WGPUCompareFunction_Less;
```
````

The second option we have is whether or not we want to **update the value** of the Z-Buffer once a fragment passes the test. It can be useful to deactivate this, when rendering user interface elements for instance, or when dealing with transparent objects, but **for a regular use case**, we indeed want to write the new depth each time a fragment is blended.

```C++
depthStencilState.depthWriteEnabled = true;
```

Lastly, we must tell the pipeline how the depth values of the Z-Buffer are **encoded** in memory:

````{tab} With webgpu.hpp
```C++
// Store the format in a variable as later parts of the code depend on it
TextureFormat depthTextureFormat = TextureFormat::Depth24Plus;
depthStencilState.format = depthTextureFormat;
```
````

````{tab} Vanilla webgpu.h
```C++
// Store the format in a variable as later parts of the code depend on it
WGPUTextureFormat depthTextureFormat = WGPUTextureFormat_Depth24Plus;
depthStencilState.format = depthTextureFormat;
```
````

```{important}
Depth textures **do not use the same formats** as color textures, they have their own set of possible values (all starting with `Depth`). The same texture is used to represent both the depth and the *stencil* value, when enabled, and the total budget is 32 bits per pixel, so it is common to use a depth encoded on 24 bits and leave the last 8 bits to a potential stencil buffer.
```

Lastly, **we deactivate the stencil** by telling that it should neither read nor write any of the bytes of the stencil buffer.

```C++
// Deactivate the stencil alltogether
depthStencilState.stencilReadMask = 0;
depthStencilState.stencilWriteMask = 0;
```

Depth texture
-------------

We must allocate the texture where the GPU stores the Z-buffer ourselves. I'm going to be quick on this part, as **we will come back on textures later on**.

We first create a texture that has the size of our swap chain texture, with a usage of `RenderAttachment` and a format that matches the one declared in `depthStencilState.format`.

````{tab} With webgpu.hpp
```C++
// Create the depth texture
TextureDescriptor depthTextureDesc;
depthTextureDesc.dimension = TextureDimension::_2D;
depthTextureDesc.format = depthTextureFormat;
depthTextureDesc.mipLevelCount = 1;
depthTextureDesc.sampleCount = 1;
depthTextureDesc.size = {640, 480, 1};
depthTextureDesc.usage = TextureUsage::RenderAttachment;
depthTextureDesc.viewFormatCount = 1;
depthTextureDesc.viewFormats = (WGPUTextureFormat*)&depthTextureFormat;
Texture depthTexture = device.createTexture(depthTextureDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create the depth texture
WGPUTextureDescriptor depthTextureDesc;
depthTextureDesc.dimension = WGPUTextureDimension_2D;
depthTextureDesc.format = depthTextureFormat;
depthTextureDesc.mipLevelCount = 1;
depthTextureDesc.sampleCount = 1;
depthTextureDesc.size = {640, 480, 1};
depthTextureDesc.usage = WGPUTextureUsage_RenderAttachment;
depthTextureDesc.viewFormatCount = 1;
depthTextureDesc.viewFormats = &depthTextureFormat;
Texture depthTexture = wgpuDeviceCreateTexture(device, depthTextureDesc);
```
````

We also create a **texture view**, which is what the render pipeline expects. In general a texture view represents a sub-part of a texture, potentially exposed as a different format, but here we have a simple texture and the view mostly represents the whole texture. Only the `aspect` set to `DepthOnly` limits the scope of the view.

````{tab} With webgpu.hpp
```C++
// Create the view of the depth texture manipulated by the rasterizer
TextureViewDescriptor depthTextureViewDesc;
depthTextureViewDesc.aspect = TextureAspect::DepthOnly;
depthTextureViewDesc.baseArrayLayer = 0;
depthTextureViewDesc.arrayLayerCount = 1;
depthTextureViewDesc.baseMipLevel = 0;
depthTextureViewDesc.mipLevelCount = 1;
depthTextureViewDesc.dimension = TextureViewDimension::_2D;
depthTextureViewDesc.format = depthTextureFormat;
TextureView depthTextureView = depthTexture.createView(depthTextureViewDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create the view of the depth texture manipulated by the rasterizer
WGPUTextureViewDescriptor depthTextureViewDesc;
depthTextureViewDesc.aspect = WGPUTextureAspect_DepthOnly;
depthTextureViewDesc.baseArrayLayer = 0;
depthTextureViewDesc.arrayLayerCount = 1;
depthTextureViewDesc.baseMipLevel = 0;
depthTextureViewDesc.mipLevelCount = 1;
depthTextureViewDesc.dimension = WGPUTextureViewDimension_2D;
depthTextureViewDesc.format = depthTextureFormat;
WGPUTextureView depthTextureView = wgpuTextureCreateView(depthTexture, depthTextureViewDesc);
```
````

Like buffers, textures must be destroyed after use, and both views and textures must be released:

````{tab} With webgpu.hpp
```C++
// Destroy the depth texture and its view
depthTextureView.release();
depthTexture.destroy();
depthTexture.release();
```
````

````{tab} Vanilla webgpu.h
```C++
// Destroy the depth texture and its view
wgpuTextureViewRelease(depthTextureView);
wgpuTextureDestroy(depthTexture);
wgpuTextureRelease(depthTexture);
```
````

Lastly, we need to update the required limits to state the maximum texture size:

```C++
// For the depth buffer, we enable textures (up to the size of the window):
requiredLimits.limits.maxTextureDimension1D = 480;
requiredLimits.limits.maxTextureDimension2D = 640;
requiredLimits.limits.maxTextureArrayLayers = 1;
```

```{note}
Again, more on textures and texture views later!
```

Depth attachment
----------------

Like when attaching a color target or binding a uniform buffer, we define an object to "connect" our depth texture to the render pipeline. This is the `RenderPassDepthStencilAttachment`:

````{tab} With webgpu.hpp
```C++
// We already had a color attachment:
renderPassDesc.colorAttachments = &colorAttachment;

// We now add a depth/stencil attachment:
RenderPassDepthStencilAttachment depthStencilAttachment;
// [...] // Setup depth/stencil attachment
renderPassDesc.depthStencilAttachment = &depthStencilAttachment;
```
````

````{tab} Vanilla webgpu.h
```C++
// We already had a color attachment:
renderPassDesc.colorAttachments = &colorAttachment;

// We now add a depth/stencil attachment:
WGPURenderPassDepthStencilAttachment depthStencilAttachment;
// [...] // Setup depth/stencil attachment
renderPassDesc.depthStencilAttachment = &depthStencilAttachment;
```
````

We must set up clear/store operations for the stencil part as well even if we do not use it:

````{tab} With webgpu.hpp
```C++
// Setup depth/stencil attachment

// The view of the depth texture
depthStencilAttachment.view = depthTextureView;

// The initial value of the depth buffer, meaning "far"
depthStencilAttachment.depthClearValue = 1.0f;
// Operation settings comparable to the color attachment
depthStencilAttachment.depthLoadOp = LoadOp::Clear;
depthStencilAttachment.depthStoreOp = StoreOp::Store;
// we could turn off writing to the depth buffer globally here
depthStencilAttachment.depthReadOnly = false;

// Stencil setup, mandatory but unused
depthStencilAttachment.stencilClearValue = 0;
depthStencilAttachment.stencilLoadOp = LoadOp::Clear;
depthStencilAttachment.stencilStoreOp = StoreOp::Store;
depthStencilAttachment.stencilReadOnly = true;
```
````

````{tab} Vanilla webgpu.h
```C++
// Setup depth/stencil attachment

// The view of the depth texture
depthStencilAttachment.view = depthTextureView;

// The initial value of the depth buffer, meaning "far"
depthStencilAttachment.depthClearValue = 1.0f;
// Operation settings comparable to the color attachment
depthStencilAttachment.depthLoadOp = WGPULoadOp_Clear;
depthStencilAttachment.depthStoreOp = WGPUStoreOp_Store;
// we could turn off writing to the depth buffer globally here
depthStencilAttachment.depthReadOnly = false;

// Stencil setup, mandatory but unused
depthStencilAttachment.stencilClearValue = 0;
depthStencilAttachment.stencilLoadOp = WGPULoadOp_Clear;
depthStencilAttachment.stencilStoreOp = WGPUStoreOp_Store;
depthStencilAttachment.stencilReadOnly = true;
```
````

````{admonition} Dawn
When using the Dawn implementation of WebGPU, `stencilLoadOp` and `stencilStoreOp` must be set to respectively `LoadOp::Undefined` and `StoreOp::Undefined` instead.

Furthermore, a `clearDepth` attribute of `depthStencilAttachment` must be turned to NaN (it's a backward compatibility thing):

```C++
constexpr auto NaNf = std::numeric_limits<float>::quiet_NaN();
depthStencilAttachment.clearDepth = NaNf;
```
````

Shader
------

The last thing we need to do is to set up a depth for each fragment, which we can do through the **vertex shader** (and the rasterizer will interpolate it for each fragment):

```rust
out.position = vec4f(position.x, position.y * ratio, /* set the depth here */ 1.0);
```

The depth value must be in the range $(0,1)$. We will build a proper way to define it in the next chapter but for now let use simply remap our `position.z` from its range $(-1,1)$ to $(0,1)$:

```rust
out.position = vec4f(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
```

Conclusion
----------

We now fixed the depth issue, and setup an important part of the 3D rendering pipeline that we won't have to edit so much.

```{figure} /images/pyramid-zissue-fixed.png
:align: center
:class: with-shadow
The depth ordering issue is gone!
```

````{tab} With webgpu.hpp
*Resulting code:* [`step052`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla)
````
