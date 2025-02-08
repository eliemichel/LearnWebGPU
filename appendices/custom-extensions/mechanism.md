The extension mechanism (<span class="bullet">🟠</span>WIP)
=======================

```{admonition} Disclaimer
This section of the guide explores **internal APIs** running behinds the scenes of the official `webgpu.h`. These are highly **subject to changes**, as they are conventions of the developers with themselves, not meant to be documented.

I do my best to update this section from time to time, but the example code **may not work as is** on newer versions. **The overall idea should still hold** anyways, and I invite you to share your experiments on the [Discord server](https://discord.gg/2Tar4Kt564) if you run into trouble!
```

Descriptor extensions
---------------------

You must have noticed this `nextInChain` pointer present in all descriptors. This is a way to **add extra fields to the descriptor**, that may or may not be read by the backend depending on whether they recognize the extension.

### Structure type

When creating a new extension, we first need to pick an extension `SType` ("structure type") identifier. This identifier can be any value that fits in a 32-bit integer, but **some values are reserved**. For instance, the first values correspond to official extensions:

```C++
// The SType identifiers defined in the standard webgpu.h header:
typedef enum WGPUSType {
    WGPUSType_Invalid = 0x00000000,
    WGPUSType_SurfaceDescriptorFromMetalLayer = 0x00000001,
    WGPUSType_SurfaceDescriptorFromWindowsHWND = 0x00000002,
    WGPUSType_SurfaceDescriptorFromXlibWindow = 0x00000003,
    WGPUSType_SurfaceDescriptorFromCanvasHTMLSelector = 0x00000004,
    WGPUSType_ShaderModuleSPIRVDescriptor = 0x00000005,
    WGPUSType_ShaderModuleWGSLDescriptor = 0x00000006,
    WGPUSType_PrimitiveDepthClipControl = 0x00000007,
    WGPUSType_SurfaceDescriptorFromWaylandSurface = 0x00000008,
    WGPUSType_SurfaceDescriptorFromAndroidNativeWindow = 0x00000009,
    WGPUSType_SurfaceDescriptorFromXcbWindow = 0x0000000A,
    WGPUSType_RenderPassDescriptorMaxDrawCount = 0x0000000F,
    WGPUSType_Force32 = 0x7FFFFFFF
} WGPUSType;
```

Each backend picked its own range of values, as far as possible to avoid collisions: `wgpu-native` starts at `0x60000001` (`1610612737`) and Dawn starts at `0x000003E8` (`1000`).

```{note}
In the near future, Dawn will move to `0x20000` (`131072`) and wgpu-native to `0x30000` (`196608`).
```

```C++
// Extensions specific to wgpu-native, defined in wgpu.h
typedef enum WGPUNativeSType {
    // Start at 6 to prevent collisions with webgpu STypes
    WGPUSType_DeviceExtras = 0x60000001,
    WGPUSType_AdapterExtras = 0x60000002,
    WGPUSType_RequiredLimitsExtras = 0x60000003,
    WGPUSType_PipelineLayoutExtras = 0x60000004,
    WGPUSType_ShaderModuleGLSLDescriptor = 0x60000005,
    WGPUSType_SupportedLimitsExtras = 0x60000003,
    WGPUSType_InstanceExtras = 0x60000006,
    WGPUSType_SwapChainDescriptorExtras = 0x60000007,
    WGPUNativeSType_Force32 = 0x7FFFFFFF
} WGPUNativeSType;
```

```C++
// Dawn provides its extensions in its modified webgpu.h
typedef enum WGPUSType {
    WGPUSType_Invalid = 0x00000000,
    //[...] The standard extensions
    WGPUSType_DawnTextureInternalUsageDescriptor = 0x000003E8,
    WGPUSType_DawnTogglesDeviceDescriptor = 0x000003EA,
    WGPUSType_DawnEncoderInternalUsageDescriptor = 0x000003EB,
    WGPUSType_DawnInstanceDescriptor = 0x000003EC,
    WGPUSType_DawnCacheDeviceDescriptor = 0x000003ED,
    WGPUSType_DawnAdapterPropertiesPowerPreference = 0x000003EE,
    WGPUSType_DawnBufferDescriptorErrorInfoFromWireClient = 0x000003EF,
    WGPUSType_DawnTogglesDescriptor = 0x000003F0,
    WGPUSType_DawnShaderModuleSPIRVOptionsDescriptor = 0x000003F1,
    WGPUSType_Force32 = 0x7FFFFFFF
} WGPUSType;
```

> 😐 How should I pick a value for my extension then?

Do **not** use values close **after the ones that already exist**. Each backend and the standard header may add new values just after the ones they already use, so if you used one you will run into a **collision**.

There is no recommended range in particular yet (I guess there will eventually be more guidance but there is little feedback on this extensions mechanism for now). Just pick a base value far enough from others and sequentially add you extensions there.

For the sake of the example, I use `0x40000` (`262144`). In a custom `webgpu-ext-foo.h` I define my extension `SType`. To introduce our new feature "Foo" we may need to add extension to multiple descriptors.

```C++
// In file webgpu-ext-foo.h we define the API of our extension "Foo"

// We give our enum a name that is a variant of WGPUSType
typedef enum WGPUFooSType {
	// Our new extension, for instance to extend the Render Pipeline
	WGPUFooSType_FooRenderPipelineDescriptor = 0x00040001,

	// Force the enum value to be represented on 32-bit integers
	WGPUFooSType_Force32 = 0x7FFFFFFF
} WGPUFooSType; // (set enum name here as well)
```

```{important}
Do not forget the `WGPUNativeSType_Force32 = 0x7FFFFFFF`, which is used to ensure that the C++ compiler does not optimize the representation of the enum's value on less than 32 bits.
```

```{note}
Throughout the next sections, we present here **a very simple and uninteresting extension**, called **foo**, which adds an optional `foo` integer member to the `RenderPipeline` and display it in a debug line whenever `setPipeline` is called on a render pass encoder.
```

### Structure fields

Let us follow the logic of the WebGPU device when it receives a descriptor:

  1. Look at `nextInChain` if it is not null. This has type `WGPUChainedStruct`, which means its first field is another chain pointer `next`, and its second field is an integer called `sType`.
  2. Look at the value `nextInChain->sType` and check that it knows this value.
  3. If it does know it, the device is aware that `nextInChain` actually point to a structure that is **more than just** `WGPUChainedStruct`, but instead a structure that starts in the same way but has **extra fields**.
  4. The device **casts** `nextInChain` to this known structure and reads the extra fields.
  5. Repeat from step 1. by replacing `nextInChain` by `nextInChain->next`.

The heart of the extension lies in step 3. Our extension must provide the definition of this structure that starts like a `WGPUChainedStruct`, that both the user code and the backend code agree on.

To start like `WGPUChainedStruct`, we use the C-idiomatic inheritance mechanism: have **the first attribute** of your struct be of type `WGPUChainedStruct`. This ensure that an instance of your struct can be cast to a `WGPUChainedStruct`:

```C++
// In file webgpu-ext-foo.h
typedef struct WGPUFooRenderPipelineDescriptor {
	// This first field is conventionally called 'chain'
	WGPUChainedStruct chain;

	// Your custom fields here
	uint32_t foo;
} WGPUFooRenderPipelineDescriptor;
```

In the end user code, this would be used as follows:

```C++
WGPUFooRenderPipelineDescriptor fooDesc;
// Set next to NULL or whatever else if you use other extensions as well
fooDesc.chain.next = NULL;

// Always set this to WGPUSType_FooRenderPipelineDescriptor when the struct that
// contains the "chain" field has actually type WGPUFooRenderPipelineDescriptor.
fooDesc.chain.sType = WGPUSType_FooRenderPipelineDescriptor;

// Set Foo description fields
fooDesc.foo = 0;

// Use in the nextInChain of the standard descriptor it targets
WGPURenderPipelineDescriptor desc;
desc.nextInChain = &fooDesc.chain;
```

Adapter features
----------------

When introducing a new extension, we must advertise its availability to the user code by adding a new **feature** in the adapter. Thus at startup when checking adapter capabilities the end user code can figure out whether it is allowed to use the extension of not.

The logic is very similar to `SType`: there are standard ones, and backend-specific ones starting at the same indices than STypes.

```C++
// Standard adapter features
typedef enum WGPUFeatureName {
    WGPUFeatureName_Undefined = 0x00000000,
    WGPUFeatureName_DepthClipControl = 0x00000001,
    WGPUFeatureName_Depth32FloatStencil8 = 0x00000002,
    WGPUFeatureName_TimestampQuery = 0x00000003,
    // [...]
    WGPUFeatureName_Force32 = 0x7FFFFFFF
} WGPUFeatureName;
```

```C++
// Here is wgpu-native's wgpu.h
typedef enum WGPUNativeFeature {
    WGPUNativeFeature_PushConstants = 0x60000001,
    WGPUNativeFeature_TextureAdapterSpecificFormatFeatures = 0x60000002,
    WGPUNativeFeature_MultiDrawIndirect = 0x60000003,
    WGPUNativeFeature_MultiDrawIndirectCount = 0x60000004,
    WGPUNativeFeature_VertexWritableStorage = 0x60000005,
    WGPUNativeFeature_Force32 = 0x7FFFFFFF
} WGPUNativeFeature;
```

```C++
// And here are Dawn features.
typedef enum WGPUFeatureName {
    WGPUFeatureName_Undefined = 0x00000000,
    // [...] The standard feature names
    WGPUFeatureName_DawnShaderFloat16 = 0x000003E9,
    WGPUFeatureName_DawnInternalUsages = 0x000003EA,
    WGPUFeatureName_DawnMultiPlanarFormats = 0x000003EB,
    WGPUFeatureName_DawnNative = 0x000003EC,
    WGPUFeatureName_ChromiumExperimentalDp4a = 0x000003ED,
    WGPUFeatureName_TimestampQueryInsidePasses = 0x000003EE,
    WGPUFeatureName_ImplicitDeviceSynchronization = 0x000003EF,
    WGPUFeatureName_Force32 = 0x7FFFFFFF
} WGPUFeatureName;
```

We can add our own "Foo" feature, still in our `webgpu-ext-foo.h` file:

```C++
// We give our enum a name that is a variant of WGPUFeatureName
typedef enum WGPUFooFeatureName {
	// Our new feature name
	WGPUFooFeatureName_Foo = 0x00040001,

	// Force the enum value to be represented on 32-bit integers
	WGPUFooFeatureName_Force32 = 0x7FFFFFFF
} WGPUFooFeatureName; // (set enum name here as well)
```

The `webgpu-ext-foo.h` file that we have is all we need as an interface between the user code and our modified backend. For the implementation of this header, we need to chose what backend to edit.

The next 2 chapters focus respectively on [`wgpu-native`](with-wgpu-native.md), then [Dawn](with-dawn.md), to show more **internal details** of how to implement this basic Foo extension.
