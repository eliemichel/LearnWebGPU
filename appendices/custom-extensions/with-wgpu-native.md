With `wgpu-native` (<span class="bullet">🟠</span>WIP)
==================

*Resulting code:* [`wgpu`](https://github.com/eliemichel/wgpu/tree/eliemichel/foo), [`wgpu-native`](https://github.com/eliemichel/wgpu-native/tree/eliemichel/foo) and [`step030-test-foo-extension`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-test-foo-extension)

Setup
-----

Before modifying any code, we need to set up the **2 repositories** that `wgpu-native` relies on.

### Building `wgpu-native`

Start by building a "regular" `wgpu-native` using [the instructions from their repository](https://github.com/gfx-rs/wgpu-native/wiki/Getting-Started). You need in particular [rust](https://www.rust-lang.org/) and [LLVM/Clang](https://rust-lang.github.io/rust-bindgen/requirements.html). With these installed, building looks like this:

```bash
git clone --recurse-submodules https://github.com/gfx-rs/wgpu-native
cd wgpu-native
set LIBCLANG_PATH=E:/Libraries/libclang/bin
cargo build --release
```

```{important}
Adapt the value of `LIBCLANG_PATH` above to your actual installation of LLVM/Clang.
```

You then find the binaries in `target\release`. If you use the `wgpu-native` based [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution/tree/wgpu) in your end project, simply replace the relevant files in `webgpu/bin`.

### Building `wgpu`

The `wgpu-native` repository is a **thin layer** exposing as a C interface the actual `wgpu` backend. When creating a custom extension, we need to change the backend, and instruct the `wgpu-native` layer to use our custom `wgpu` branch.

```bash
git clone https://github.com/gfx-rs/wgpu
cd wgpu
cargo build --release
```

To point `wgpu-native` to our custom `wgpu`, we can modify its `wgpu-native/Cargo.toml` and add:

```toml
[patch."https://github.com/gfx-rs/wgpu"]
wgpu-core = { path = "../wgpu/wgpu-core" }
wgpu-types = { path = "../wgpu/wgpu-types" }
wgpu-hal = { path = "../wgpu/wgpu-hal" }
naga = { path = "../wgpu/naga" }
```

````{note}
To make sure to reproduce the very same binaries, check out in the `wgpu` directory the commit specified after `rev =` in the `Cargo.toml` of `wgpu-native`.

```bash
cd wgpu
git checkout 011a4e26d04f388ef40e3baee3f19a255b9b5148
```

But since you are writing an extension you may want to use the last version of `wgpu` instead.
````

You may also need to update the rev hash of `[dependencies.naga]` to match what your version of `wgpu` uses.

The Foo Extension
-----------------

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
TODO: I still need to learn better how the code is organized. So far I noticed that:

- `wgpu-native` maps C entry points to the rust API of `wgpu-core`
- `wgpu-core` maintains the common user API, that application based on wgpu use, either through the native wrapper or through `wgpu-rs` (a.k.a. just `wgpu`). Behinds the scenes, it maps instructions to `wgpu-hal`
- `wgpu-hal` is the backend/hardware abstraction layer, it defines the internal API that each backend (Vulkan, Metal, DX12, etc.) must implement
- `wgpu-hal/vulkan` is the Vulkan backend, that implements all of the HAL's requirements
```

The file `wgpu/wgpu-hal/src/lib.rs` defines the interface that each backend must implement. Backends are the subdirectories of `wgpu/wgpu-hal/src` as well as the `empty.rs` file that defines a default behavior that does nothing.

We implement backends one by one, maybe only for the ones that interest us in practice. We must thus make sure that the `Foo` feature is advertised by the adapter only for the backend that we implemented.

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
