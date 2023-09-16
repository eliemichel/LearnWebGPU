Custom Extensions (🚧WIP)
=================

When using WebGPU in a non-Web context, there is no reason to be limited by the Web requirements. This chapter gives an overview of how to add support for new device features through WebGPU's extension mechanism.

```{note}
I do not use the [`webgpu.hpp`](https://github.com/eliemichel/WebGPU-Cpp) helper here as the extension file must define a C API. The `webgpu.hpp` wrapper can then easily be generalized to your own custom extension by using [`generator.py`](https://github.com/eliemichel/WebGPU-Cpp#custom-generation).
```

The extension mechanism
-----------------------

### Descriptor extensions

You must have noticed this `nextInChain` pointer present in all descriptors. This is a way to **add extra fields to the descriptor**, that may or may not be read by the backend depending on whether they recognize the extension.

#### Structure type

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

For the sake of the example, I use `0x00001000` (`4096`). In a custom `webgpu-ext-foo.h` I define my extension `SType`. To introduce our new feature "Foo" we may need to add extension to multiple descriptors.

```C++
// In file webgpu-ext-foo.h we define the API of our extension "Foo"

// We give our enum a name that is a variant of WGPUSType
typedef enum WGPUFooSType {
	// Our new extension, for instance to extend the Render Pipeline
	WGPUFooSType_FooRenderPipelineDescriptor = 0x00001001,

	// Force the enum value to be represented on 32-bit integers
	WGPUFooSType_Force32 = 0x7FFFFFFF
} WGPUFooSType; // (set enum name here as well)
```

```{important}
Do not forget the `WGPUNativeSType_Force32 = 0x7FFFFFFF`, which is used to ensure that the C++ compiler does not optimize the representation of the enum's value on less than 32 bits.
```

#### Structure fields

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

### Adapter features

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
	WGPUFooFeatureName_Foo = 0x00001001,

	// Force the enum value to be represented on 32-bit integers
	WGPUFooFeatureName_Force32 = 0x7FFFFFFF
} WGPUFooFeatureName; // (set enum name here as well)
```

The `webgpu-ext-foo.h` file that we have is all we need as an interface between the user code and our modified backend. For the implementation of this header, we need to chose what backend to edit.

With `wgpu-native`
------------------

*Resulting code:* [`wgpu`](https://github.com/eliemichel/wgpu/tree/eliemichel/foo), [`wgpu-native`](https://github.com/eliemichel/wgpu-native/tree/eliemichel/foo) and [`step030-test-foo-extension`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-test-foo-extension)

### Building `wgpu-native`

Start by building a "regular" `wgpu-native` using [the instructions from their repository](https://github.com/gfx-rs/wgpu-native/wiki/Getting-Started). You need in particular [rust](https://www.rust-lang.org/) and [LLVM/Clang](https://rust-lang.github.io/rust-bindgen/requirements.html). With these installed, building looks like this:

```bash
git clone --recurse-submodules https://github.com/gfx-rs/wgpu-native
cd wgpu-native
set LIBCLANG_PATH=E:/Libraries/libclang/bin
cargo build --release
```

You then find the binaries in `target\release`. If you use the `wgpu-native` based [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution/tree/wgpu) in your end project, simply replace the relevant files in `webgpu/bin`.

### Building `wgpu`

The `wgpu-native` repository is a thin layer exposing as a C interface the actual `wgpu` backend. When creating a custom extension, we need to change the backend, and instruct the `wgpu-native` layer to use our custom `wgpu` branch.

```bash
git clone https://github.com/gfx-rs/wgpu
cd wgpu
cargo build --release
```

To point `wgpu-native` to our custom `wgpu`, we can modify its `Cargo.toml` and add:

```toml
[patch."https://github.com/gfx-rs/wgpu"]
wgpu-core = { path = "../wgpu/wgpu-core" }
wgpu-types = { path = "../wgpu/wgpu-types" }
```

````{note}
To make sure to reproduce the very same binaries, check out in the `wgpu` directory the commit specified after `rev =` in the `Cargo.toml` of `wgpu-native`.

```bash
cd wgpu
git checkout 011a4e26d04f388ef40e3baee3f19a255b9b5148
```

But since you are writing an extension you may want to use the last version of `wgpu` instead.
````

### Extending types

We can copy our `webgpu-ext-foo.h` header in the `wgpu-native/ffi/` directory, next to `wgpu.h`. In order to have rust's build system parse these files, we add our custom header to `build.rs`:

```rust
let mut builder = bindgen::Builder::default()
    .header("ffi/webgpu-headers/webgpu.h")
    .header("ffi/wgpu.h")
    .header("ffi/webgpu-ext-foo.h") // <-- Here is our custom file
    // [...]
```

This defines in rust's `native` namespace symbols that are equivalent to what the C header files expose. We must also modify some existing types in `wgpu-types/src/lib.rs`. At least to add our new adapter feature:

```rust
bitflags::bitflags! {
	// [...]
	pub struct Features: u64 {
		// [...]
		const SHADER_EARLY_DEPTH_TEST = 1 << 62;

		// Our feature as a bitflag
		const FOO = 1 << 63;
	}
}
```

In our running example, we want to add a field `foo` to the render pipeline. We thus modify the `RenderPipelineDescriptor` in `wgpu/wgpu-core/src/pipeline.rs`:

```rust
pub struct RenderPipelineDescriptor<'a> {
	// [...]
	/// our custom new field
    pub foo: Option<u32>,
}
```

````{note}
When trying to build from the `wgpu` root, do not try to build the whole project, we only use `wgpu-core` and `wgpu-types` (which the former depends on), so try building with:

```bash
wgpu$ cargo build --package wgpu-core
```

But more likely you will build from the `wgpu-native` projects:

```bash
wgpu-native$ cargo build
```

If you want your extension to also be available to rust users, you must also adapt the `wgpu` package, but I will not cover it here.
````

### Extending native wrapper

Conversion utilities to link rust-side types defined in `wgpu/wgpu-types` with the `native` defines that follow the C header. Add your feature name to `features_to_native` and `map_feature` in `wgpu-native/src/conv.rs`:

```rust
pub fn features_to_native(features: wgt::Features) -> Vec<native::WGPUFeatureName> {
    // [...]
    if features.contains(wgt::Features::FOO) {
        temp.push(native::WGPUFeatureName_Foo);
    }
    temp
}

pub fn map_feature(feature: native::WGPUFeatureName) -> Option<wgt::Features> {
    use wgt::Features;
    match feature {
        // [...]
        native::WGPUFeatureName_Foo => Some(Features::FOO),
        // [...]
    }
}
```

In order to recognize our `SType` when it is passed in the extension chain of a `RenderPipelineDescriptor`, we modify the `wgpuDeviceCreateRenderPipeline` procedure in `wgpu-native/src/lib.rs`:

```rust
pub unsafe extern "C" fn wgpuDeviceCreateRenderPipeline(
    device: native::WGPUDevice,
    descriptor: Option<&native::WGPURenderPipelineDescriptor>,
) -> native::WGPURenderPipeline {
    let (device, context) = device.unwrap_handle();
    let descriptor = descriptor.expect("invalid descriptor");

    let desc = wgc::pipeline::RenderPipelineDescriptor {
        // [...]

        // Iteratively explore the extension chain until it finds an extension
        // of our type, cast to WGPUFooRenderPipelineDescriptor and retrieve
        // the value of foo.
        foo: follow_chain!(
            map_render_pipeline_descriptor(
                descriptor,
                WGPUFooSType_FooRenderPipelineDescriptor => native::WGPUFooRenderPipelineDescriptor)
        ),
    };
}
```

This calls a `map_render_pipeline_descriptor` that we create in `conv.rs`:

```rust
pub unsafe fn map_render_pipeline_descriptor<'a>(
    _: &native::WGPURenderPipelineDescriptor,
    foo: Option<&native::WGPUFooRenderPipelineDescriptor>,
) -> Option<u32> {
    foo.map(|x| x.foo)
}
```

```{note}
Do not forget to add `map_render_pipeline_descriptor` to the `use conv::{...}` line at the beginning of `lib.rs`.
```

### Extending core

If your extension is shallow enough not to affect the backends, you should only have to modify `wgpu/wgpu-core`. But if you take the time to write a custom extension, it likely requires to modify one or multiple backends.

### Extending backends

```{warning}
TODO: I still need to learn better how the code is organized.
```

The file `wgpu/wgpu-hal/src/lib.rs` defines the interface that each backend must implement. Backends are the subdirectories of `wgpu/wgpu-hal/src` as well as the `empty.rs` file that defines a default behavior that does nothing.

We implement backends one by one, maybe only for the ones that interest us in practice. We must thus make sure that the `Foo` feature is advertised by the adapter only for the backend that we implemented.

```C++
TODO
```

Let's start with the Vulkan backend. We first advertise that the adapter (a.k.a. *physical device* in Vulkan wording) supports our feature.

```{note}
Of course you may inspect the actual physical device properties to conditionally list the `FOO` feature only if the mechanism you want to implement is indeed supported.
```

```rust
// in wgpu/wgpu-hal/src/vulkan/adapter.rs
impl PhysicalDeviceFeatures {
    // [...]
    fn to_wgpu(
        /* [...] */
    ) -> (wgt::Features, wgt::DownlevelFlags) {
        // [...]
        let mut features = F::empty()
            | F::SPIRV_SHADER_PASSTHROUGH
            | F::MAPPABLE_PRIMARY_BUFFERS
            // [...]
            | F::FOO; // our extension here!
    }
    // [...]
}
```

Now in DirectX 12 backend:

```rust
// in wgpu/wgpu-hal/src/dx12/adapter.rs
impl super::Adapter {
    // [...]
    pub(super) fn expose(
        /* [...] */
    ) -> Option<crate::ExposedAdapter<super::Api>> {
        // [...]
        let mut features = wgt::Features::empty()
            | wgt::Features::DEPTH_CLIP_CONTROL
            | wgt::Features::DEPTH32FLOAT_STENCIL8
            // [...]
            | wgt::Features::FOO; // our extension here!
    }
    // [...]
}
```

```{note}
We focus only on the Vulkan backend in the remainder of this section.
```

We can now check that the feature is correctly made available in our application code. I start from the [`step030-headless`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless) branch.

```C++
if (wgpuAdapterHasFeature(adapter, (WGPUFeatureName)WGPUFeatureName_Foo)) {
    std::cout << "Feature 'Foo' supported by adapter" << std::endl;
}
else {
    std::cout << "Feature 'Foo' NOT supported by adapter" << std::endl;
}
```

After you copy the DLL and headers of your custom `wgpu-native`, you should see the Foo feature supported.

````{note}
You can force a particular backend by playing with the **instance extras** extension of `wgpu-native` in the instance descriptor:

```C++
WGPUInstanceExtras instanceExtras = {};
instanceExtras.chain.next = nullptr;
instanceExtras.chain.sType = (WGPUSType)WGPUSType_InstanceExtras;
instanceExtras.backends = WGPUInstanceBackend_Vulkan; // We only accept Vulkan adapters here!
WGPUInstanceDescriptor instanceDesc = {};
instanceDesc.nextInChain = &instanceExtras.chain;

Instance instance = createInstance(instanceDesc);
```
````

Do not forget to also request the feature when creating your device:

```C++
WGPUFeatureName featureFoo = (WGPUFeatureName)WGPUFeatureName_Foo;
deviceDesc.requiredFeaturesCount = 1;
deviceDesc.requiredFeatures = &featureFoo;
// [...]

if (wgpuDeviceHasFeature(device, (WGPUFeatureName)WGPUFeatureName_Foo)) {
    std::cout << "Feature 'Foo' supported by device" << std::endl;
}
else {
    std::cout << "Feature 'Foo' NOT supported by device" << std::endl;
}
```

We can then try extending the render pipeline:

```C++
RenderPipelineDescriptor pipelineDesc;
// [...]

WGPUFooRenderPipelineDescriptor fooRenderPipelineDesc;
fooRenderPipelineDesc.chain.next = nullptr;
fooRenderPipelineDesc.chain.sType = (WGPUSType)WGPUFooSType_FooRenderPipelineDescriptor;
fooRenderPipelineDesc.foo = 42; // some test value here.
pipelineDesc.nextInChain = &fooRenderPipelineDesc.chain;

RenderPipeline pipeline = device.createRenderPipeline(pipelineDesc);
```

In order to test that the value is correctly propagated, we just print a log line whenever `setPipeline` is called for this pipeline:

```rust
// In wgpu/wgpu-hal/src/vulkan/command.rs
unsafe fn set_render_pipeline(&mut self, pipeline: &super::RenderPipeline) {
    // Debug print
    if let Some(foo) = pipeline.foo {
        println!("DEBUG of FOO feature: foo={:?}", foo);
    }

    // [...]
}
```

We need for this to add a `foo` field to the RenderPipeline (we only added it to the descriptor for now):

```rust
// In wgpu/wgpu-hal/src/vulkan/mod.rs
#[derive(Debug)]
pub struct RenderPipeline {
    raw: vk::Pipeline,
    foo: Option<u32>, // add this
}
```

And we propagate from the descriptor when creating the render pipeline:

```rust
// In wgpu/wgpu-hal/src/vulkan/device.rs
unsafe fn create_render_pipeline(
    &self,
    desc: &crate::RenderPipelineDescriptor<super::Api>,
) -> Result<super::RenderPipeline, crate::PipelineError> {
    // [...]
    let foo = desc.foo;

    Ok(super::RenderPipeline { raw, foo })
}
```

But, as you may notice, this is **yet another** taste of `RenderPipelineDescriptor` type (defined in `wgpu-hal/lib.rs`). As this is getting quite confusing, let me summarize with a figure:

```{image} /images/extension/wgpu-architecture-light.svg
:align: center
:class: only-light
```

```{image} /images/extension/wgpu-architecture-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>The architecture of the wgpu-native project.</em></span>
</p>

```rust
// In wgpu/wgpu-hal/lib.rs
#[derive(Clone, Debug)]
pub struct RenderPipelineDescriptor<'a, A: Api> {
    // [...]
    /// Our custom FOO extension
    pub foo: Option<u32>,
}

// In wgpu/wgpu-core/src/device/resource.rs
pub(super) fn create_render_pipeline<G: GlobalIdentityHandlerFactory>(
    /* [...] */
) -> Result<pipeline::RenderPipeline<A>, pipeline::CreateRenderPipelineError> {
    // [...]
    let pipeline_desc = hal::RenderPipelineDescriptor {
        // [...]
        multiview: desc.multiview,
        foo: desc.foo, // forward our custom member here
    };
    // [...]
}
```

At this stage, if you build `wgpu-native`, update the DLL in your C++ application and run that application, it should eventually display the test log line:

```
DEBUG of FOO feature: foo=42
```

**Congratulation**, you have your first extension of `wgpu-native`! Of course it does not do much, and it only does so on the Vulkan backend. But we have explored the architecture of the project. What remains now depends highly on what exact extension you want to implement!

*Resulting code:* [`wgpu`](https://github.com/eliemichel/wgpu/tree/eliemichel/foo), [`wgpu-native`](https://github.com/eliemichel/wgpu-native/tree/eliemichel/foo) and [`step030-test-foo-extension`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-test-foo-extension)

With Dawn
---------

TODO
