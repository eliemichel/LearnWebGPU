Depth buffer <span class="bullet">🟢</span>
============

```{lit-setup}
:tangle-root: 052 - Depth buffer - Next - vanilla
:parent: 050 - A simple example - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 052 - Depth buffer - Next
:parent: 050 - A simple example - Next
```

````{tab} With webgpu.hpp
*Resulting code:* [`step052-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla-next)
````

```{figure} /images/pyramid-zissue.png
:align: center
:class: with-shadow
There is something wrong with the depth.
```

The Z-Buffer algorithm
----------------------

The issue we are facing with this basic example comes from the problem of **visibility**. As easy to conceive as it is, the question "does this point see that one" (i.e., does the line between them intersect any geometry) is hard to answer efficiently.

In particular, when producing a **fragment**, we must figure out whether the 3D point it corresponds to is seen by the viewpoint in order decide whether it must be blended into the output texture.

The **Z-Buffer algorithm** is what the GPU's render pipeline uses to solve the visibility problem:

 1. **For each pixel**, it stores the depth of the last fragment that has been blended into this pixel, or a default value (that represents the furthest depth possible).
 2. Each time a new fragment is produced, its **depth is compared** to this value. If the fragment depth is larger than the currently stored depth, it is **discarded** without being blended. Otherwise, it is blended normally and the stored value is updated to the depth of this new closest fragment.

As a result, **only the fragment with the lowest depth is visible** in the resulting image. The depth value for each pixel is stored in a special **texture** called the **Z-buffer**. This is the only memory overhead required by the Z-buffer algorithm, making it a good fit for real time rendering.

```{topic} About transparency
The fact that only the fragment with the lowest depth is visible is **not guaranteed** when fragments have **opacity values that are neither 0 or 1** (and alpha-blending is used). Even worse; the order in which fragments are emitted has an impact on the result (because blending a fragment **A** and then a fragment **B** is different than blending **B** then **A**).

Long story short: **transparent objects are always a bit tricky** to handle in a Z-buffer pipeline. A simple solution is to limit the number of transparent objects, and dynamically sort them wrt. their distance to the viewpoint (this is what [Gaussian Splatting](https://en.wikipedia.org/wiki/Gaussian_splatting) does for instance. More advanced schemes exist such as [Order-independent transparency](https://en.wikipedia.org/wiki/Order-independent_transparency) techniques.
```

Pipeline State
--------------

Since this Z-Buffer algorithm is a **critical step** of the 3D rasterization pipeline, it is implemented as a **fixed-function** stage. We configure it through the `pipelineDesc.depthStencil` field, which we had left null so far.

````{tab} With webgpu.hpp
```{lit} C++, Describe render pipeline (append)
DepthStencilState depthStencilState = Default;
{{Describe depth/stencil state}}
pipelineDesc.depthStencil = &depthStencilState;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe render pipeline (append, for tangle root "Vanilla")
WGPUDepthStencilState depthStencilState = WGPU_DEPTH_STENCIL_STATE_INIT;
{{Describe depth/stencil state}}
pipelineDesc.depthStencil = &depthStencilState;
```
````

### Comparison function

The first aspect of the Z-Buffer algorithm that we can configure is the **comparison function** that is used to decide whether we should keep a new fragment or not.

**The most common choice** is to set it to `Less` to mean that a fragment is blended only if its depth is **less** than the current value of the Z-Buffer (i.e., it is closer to the viewpoint).

````{tab} With webgpu.hpp
```{lit} C++, Describe depth/stencil state
depthStencilState.depthCompare = CompareFunction::Less;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe depth/stencil state (for tangle root "Vanilla")
depthStencilState.depthCompare = WGPUCompareFunction_Less;
```
````

### Depth write

The second option we have is whether or not we want to **update the value** of the Z-Buffer once a fragment passes the test. It can be useful to deactivate this, when rendering user interface elements for instance, or when dealing with transparent objects, but **for a regular use case**, we indeed want to write the new depth each time a fragment is blended.

````{tab} With webgpu.hpp
```{lit} C++, Describe depth/stencil state (append)
depthStencilState.depthWriteEnabled = OptionalBool::True;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe depth/stencil state (append, for tangle root "Vanilla")
depthStencilState.depthWriteEnabled = WGPUOptionalBool_True;
```
````

```{note}
This field uses the special type `WGPUOptionalBool`, which may be either `True`, `False` or `Undefined` because it is supposed to remain undefined when the depth/stencil state only contains a stencil and no depth buffer. 
```

### Texture format

Lastly, we must tell the pipeline how the depth values of the Z-Buffer are **encoded** in memory. We define for this a `m_depthTextureFormat` class attribute because we need it in both `InitializePipeline()` and when configuring the surface in `Initialize()`:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // In Application.h
	wgpu::TextureFormat m_depthTextureFormat = wgpu::TextureFormat::Depth24Plus;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // In Application.h
	WGPUTextureFormat m_depthTextureFormat = WGPUTextureFormat_Depth24Plus;
```
````

We then use it when describing the depth state:

```{lit} C++, Describe depth/stencil state (append, also for tangle root "Vanilla")
depthStencilState.format = m_depthTextureFormat;
```

```{important}
Depth textures **do not use the same formats** as color textures, they have their own set of possible values (all starting with `Depth`). The same texture is used to represent both the depth and the *stencil* value, when enabled. It is common to use a depth encoded on **24 bits** and leave the last 8 bits to a potential stencil buffer, so that it sums it to 32, which is a nice size for byte alignment.
```

Depth texture
-------------

We must allocate the texture where the GPU stores the Z-buffer ourselves. I'm going to be quick on this part, as **we will come back on textures later on**.

We first create a texture that has the size of our swap chain texture, with a usage of `RenderAttachment` and a format that matches the one declared in `depthStencilState.format`.

````{note}
We create this texture next to the surface configuration (in `Initialize()`), because when we will start resizing the window, we will also want to resize the depth buffer:

```{lit} C++, Create the depth texture and view (insert in {{Initialize}} after "{{Surface Configuration}}", also for tangle root "Vanilla")
// Create the depth texture after surface configuration 
```
````

````{tab} With webgpu.hpp
```{lit} C++, Create the depth texture and view (append)
// Create the depth texture
TextureDescriptor depthTextureDesc = Default;
depthTextureDesc.label = StringView("Z Buffer");
depthTextureDesc.usage = TextureUsage::RenderAttachment;
depthTextureDesc.size = { 640, 480, 1 };
depthTextureDesc.format = m_depthTextureFormat;
Texture depthTexture = m_device.createTexture(depthTextureDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create the depth texture and view (append, for tangle root "Vanilla")
// Create the depth texture
WGPUTextureDescriptor depthTextureDesc = WGPU_TEXTURE_DESCRIPTOR_INIT;
depthTextureDesc.label = toWgpuStringView("Z Buffer");
depthTextureDesc.usage = WGPUTextureUsage_RenderAttachment;
depthTextureDesc.size = { 640, 480, 1 };
depthTextureDesc.format = m_depthTextureFormat;
WGPUTexture depthTexture = wgpuDeviceCreateTexture(m_device, &depthTextureDesc);
```
````

We also create a **texture view**, which is what the render pipeline expects (like we did in chapter [*First color*](../../getting-started/first-color.md)). The default view descriptor is all we need here, so we are even allowed not to specify a descriptor:

````{tab} With webgpu.hpp
```{lit} C++, Create the depth texture and view (append)
// Create the view of the depth texture manipulated by the rasterizer
m_depthTextureView = depthTexture.createView();

// We can now release the texture and only hold to the view
depthTexture.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create the depth texture and view (append, for tangle root "Vanilla")
// Create the view of the depth texture manipulated by the rasterizer
m_depthTextureView = wgpuTextureCreateView(depthTexture, nullptr);

// We can now release the texture and only hold to the view
wgpuTextureRelease(depthTexture);
```
````

The view will only be released at the end of the program, which is why we define it at the class level:

````{tab} With webgpu.hpp
```{lit} C++, Application attributes (append)
private: // In Application.h
	wgpu::TextureView m_depthTextureView = nullptr;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Application attributes (append, for tangle root "Vanilla")
private: // In Application.h
	WGPUTextureView m_depthTextureView = nullptr;
```
````

And in `Application::Terimnate()`:

```{lit} C++, Terminate (hidden, prepend, also for tangle root "Vanilla")
{{Release the depth texture view}}
```

````{tab} With webgpu.hpp
```{lit} C++, Release the depth texture view
// Release the depth texture view
m_depthTextureView.release();
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Release the depth texture view (for tangle root "Vanilla")
// Release the depth texture view
wgpuTextureViewRelease(m_depthTextureView);
```
````

Depth attachment
----------------

Like when attaching a color target or binding a uniform buffer, we define an object to "connect" our depth texture to the render pipeline. This is the `RenderPassDepthStencilAttachment`:

````{tab} With webgpu.hpp
```{lit} C++, Describe Render Pass (append)
// We already had a color attachment
// e.g., renderPassDesc.colorAttachments = &colorAttachment;

// We now add a depth/stencil attachment:
RenderPassDepthStencilAttachment depthStencilAttachment = Default;
{{Describe depth/stencil attachment}}
renderPassDesc.depthStencilAttachment = &depthStencilAttachment;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe Render Pass (append, for tangle root "Vanilla")
// We already had a color attachment
// e.g., renderPassDesc.colorAttachments = &colorAttachment;

// We now add a depth/stencil attachment:
WGPURenderPassDepthStencilAttachment depthStencilAttachment = WGPU_RENDER_PASS_DEPTH_STENCIL_ATTACHMENT_INIT;
{{Describe depth/stencil attachment}}
renderPassDesc.depthStencilAttachment = &depthStencilAttachment;
```
````

We must set up clear/store operations for the stencil part as well even if we do not use it:

````{tab} With webgpu.hpp
```{lit} C++, Describe depth/stencil attachment
// Describe depth/stencil attachment

// The view of the depth texture
depthStencilAttachment.view = m_depthTextureView;

// The initial value of the depth buffer, meaning "far"
depthStencilAttachment.depthClearValue = 1.0f;

// Operation settings comparable to the color attachment
depthStencilAttachment.depthLoadOp = LoadOp::Clear;
depthStencilAttachment.depthStoreOp = StoreOp::Store;

// we could turn off writing to the depth buffer globally here
depthStencilAttachment.depthReadOnly = false; // NB: this is the default
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe depth/stencil attachment (for tangle root "Vanilla")
// Describe depth/stencil attachment

// The view of the depth texture
depthStencilAttachment.view = m_depthTextureView;

// The initial value of the depth buffer, meaning "far"
depthStencilAttachment.depthClearValue = 1.0f;

// Operation settings comparable to the color attachment
depthStencilAttachment.depthLoadOp = WGPULoadOp_Clear;
depthStencilAttachment.depthStoreOp = WGPUStoreOp_Store;

// we could turn off writing to the depth buffer globally here
depthStencilAttachment.depthReadOnly = false; // NB: this is the default
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

```{lit} rust, Set vertex out position (hidden, replace, also for tangle root "Vanilla")
let angle = uMyUniforms.time; // you can multiply it go rotate faster
let alpha = cos(angle);
let beta = sin(angle);
var position = vec3f(
	in.position.x,
	alpha * in.position.y + beta * in.position.z,
	alpha * in.position.z - beta * in.position.y,
);
out.position = vec4f(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
//                                     This changes: ^^^^^^^^^^^^^^^^^^^^^^
```

Conclusion
----------

We now **fixed the depth issue**! And with this depth attachment we have set up an important part of the 3D rendering pipeline that we won't have to edit so much. We are now ready for **more 3d transforms**.

```{figure} /images/pyramid-zissue-fixed.png
:align: center
:class: with-shadow
The depth ordering issue is gone!
```

````{tab} With webgpu.hpp
*Resulting code:* [`step052-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla-next)
````
