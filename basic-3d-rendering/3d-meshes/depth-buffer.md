Depth buffer (WIP)
============

````{tab} With webgpu.hpp
*Resulting code:* [`step052`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla)
````

TODO

Pipeline State
--------------

```C++
DepthStencilState depthStencilState;
depthStencilState.setDefault();
depthStencilState.depthBias = 0;
depthStencilState.depthBiasClamp = 0.0f;
depthStencilState.depthBiasSlopeScale = 1.0f;
depthStencilState.depthCompare = CompareFunction::Less;
depthStencilState.depthWriteEnabled = true;
depthStencilState.format = TextureFormat::Depth24Plus;
depthStencilState.stencilBack.compare = CompareFunction::Never;
depthStencilState.stencilFront.compare = CompareFunction::Never;
depthStencilState.stencilReadMask = 0;
depthStencilState.stencilWriteMask = 0;
pipelineDesc.depthStencil = &depthStencilState;
```

Depth attachment
----------------

```C++
RenderPassDepthStencilAttachment depthStencilAttachment;
depthStencilAttachment.view = depthTextureView;
depthStencilAttachment.depthClearValue = 100.0f;
depthStencilAttachment.depthLoadOp = LoadOp::Clear;
depthStencilAttachment.depthReadOnly = false;
depthStencilAttachment.depthStoreOp = StoreOp::Store;
depthStencilAttachment.stencilClearValue = 0;
depthStencilAttachment.stencilLoadOp = LoadOp::Clear;
depthStencilAttachment.stencilReadOnly = true;
depthStencilAttachment.stencilStoreOp = StoreOp::Store;
```

Depth texture
-------------

I'm going to be quick on this part, as we'll come back on textures later on.

```C++
TextureFormat depthTextureFormat = TextureFormat::Depth24Plus;
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

Shader
------

Temporary hack

```rust
out.position = vec4<f32>(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
```

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step052`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step052-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step052-vanilla)
````
