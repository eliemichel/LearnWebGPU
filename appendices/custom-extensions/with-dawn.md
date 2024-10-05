With Dawn (<span class="bullet">🟠</span>WIP)
=========

*Resulting code:* [`dawn:eliemichel/foo`](https://github.com/eliemichel/Dawn/tree/eliemichel/foo) and [`step030-test-foo-extension-dawn`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-test-foo-extension-dawn)

```{note}
If you have not already, don't forget to read the introduction of the [Extension Mechanism](mechanism.md).
```

Setup
-----

Instead of fetching Dawn source at configuration time and have it lost in `build/_deps`, we clone Dawn as a git submodule (or just copy it) in our source tree.

```{note}
I start from the [`step030-headless`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless) branch to have a minimalistic version of the test app (and strip down the `save_image` part).
```

```bash
# Setup Dawn in a dawn/ subdirectory
git submodule add https://dawn.googlesource.com/dawn dawn

cd dawn

# Fetch the release tag of your choice (in a shallow way)
git fetch origin chromium/5869
git reset --hard FETCH_HEAD

# Create your new custom branch from this tag
git checkout -b eliemichel/foo
```

Update `webgpu/webgpu.cmake` to use the local Dawn submodule (simply copy from [here](https://github.com/eliemichel/LearnWebGPU-Code/blob/step030-test-foo-extension-dawn/webgpu/webgpu.cmake)).

```{note}
I also copied [`webgpu.hpp`](https://github.com/eliemichel/WebGPU-Cpp/blob/main/dawn/webgpu.hpp) into `webgpu/include/webgpu/`.
```

New feature
-----------

### Public API

We start by updating the descriptor structs to handle our new Foo extension. Contrary to `wgpu-native`, we do **not directly write the extension header** (that we called `webgpu-ext-foo.h`), because Dawn's `webgpu.h` is **auto-generated**.

The source of this generation is the large `dawn.json` file, at the root of Dawn's repo. Locate for instance `"feature name": {` to add our Foo feature:

```json
"feature name": {
    "category": "enum",
    "values": [
        {"value": 0, "name": "undefined", "jsrepr": "undefined"},
        {"value": 1, "name": "depth clip control"},
        /* [...] */
        {"value": 1010, "name": "MSAA render to single sampled", "tags": ["dawn"]},
        /* We add our custom extension here: */
        {"value": 4097, "name": "Foo", "tags": ["native"]}
    ]
},
```

```{note}
We add the tag `native` to mean that this feature must only be generated for native builds, not for web-based setups.
```

```{caution}
Do not forget to add a comma (`,`) at the end of the previous line, before our custom one.
```

We can now check that the feature is indeed supported:

```C++
if (wgpuAdapterHasFeature(adapter, WGPUFeatureName_Foo)) {
	std::cout << "Feature 'Foo' supported by adapter" << std::endl;
}
else {
	std::cout << "Feature 'Foo' NOT supported by adapter" << std::endl;
}
```

> 😡 It is **not** supported here!

The code that was auto-generated from the json file above describes the **public API** of the Dawn library. We now need to manually modify the **internal `dawn::native` API** that is used to dialog with the different backends (Vulkan, DirectX, Metal, etc.).

### Internal API

We add our feature to the internal `Feature` enum:

```C++
// In dawn/src/dawn/native/Features.h
enum class Feature {
	// [...]
	MSAARenderToSingleSampled,

    // Our custom feature here
    Foo,

    EnumCount,
    InvalidEnum = EnumCount,
    FeatureMin = TextureCompressionBC,
};
```

```{admonition} Update
I wrote this on an earlier version of Dawn, lately this has been moved to the auto-generated version so no need to worry about it!
```

We then specify in `Features.cpp` how to convert back and forth between the public and internal APIs:

```C++
// In dawn/src/dawn/native/Features.cpp
Feature FromAPIFeature(wgpu::FeatureName feature) {
	switch (feature) {
		// [...]
		// Add a case for our new feature
		case wgpu::FeatureName::Foo:
			return Feature::Foo;
	}
	return Feature::InvalidEnum;
}

wgpu::FeatureName ToAPIFeature(Feature feature) {
	switch (feature) {
		// [...]
		// Add a case for our new feature
		case Feature::Foo:
			return wgpu::FeatureName::Foo;

		case Feature::EnumCount:
			break;
	}
	UNREACHABLE();
}
```

Finally, we add some information about this feature:

```C++
// In dawn/src/dawn/native/Features.cpp
static constexpr FeatureEnumAndInfoList kFeatureNameAndInfoList = {{
    // [...]
    // We add info about our new feature
    {Feature::Foo,
     {"foo",
      "Support our custom FOO feature on render pipelines.",
      "https://eliemichel.github.io/LearnWebGPU/appendices/custom-extensions.html", FeatureInfo::FeatureState::Stable}},
}};
```

```{note}
I leave the feature state to `Stable` for the sake of simplicity. If you want to set it to `Experimental`, you must make sure to enable the `allow_unsafe_apis` toggle in your application code.
```

### Backend change (Vulkan)

Okay, now our feature is correctly wired up in the internal API, but so far **none of the backends support it**! At this stage we must focus on **a single one at a time**.

We start with **Vulkan**, looking inside `dawn/src/dawn/native/vulkan`. So let's first force the Vulkan backend in our application:

```C++
RequestAdapterOptions adapterOpts = Default;
// Force Vulkan backend
adapterOpts.backendType = BackendType::Vulkan;
Adapter adapter = instance.requestAdapter(adapterOpts);
```

In Vulkan wording (and also in Dawn's internal), the available feature set is provided by a `PhysicalDevice`.

In `vulkan/PhysicalDeviceVk.h`, we can see that the `PhysicalDevice` class, specific to this backend, inherits from the `PhysicalDeviceBase` class, defined by the internal backend-agnostic `dawn::native` API.

This base class contains a protected method `void EnableFeature(Feature feature)`, that the child class may call to enable a particular feature. **In practice** this is done in `InitializeSupportedFeaturesImpl()`, where we add our feature:

```C++
// In native/vulkan/PhysicalDeviceVk.cpp
void PhysicalDevice::InitializeSupportedFeaturesImpl() {
	// [...]
	// Our feature is always enabled on Vulkan backend:
	EnableFeature(Feature::Foo);
}
```

You should now see the feature supported:

```
Feature 'Foo' supported by adapter
```

Add it to the list of `requiredFeatures` of the **device descriptor** and you can then check that `wgpuDeviceHasFeature(device, WGPUFeatureName_Foo)` is true!

Render pipeline
---------------

### Public API

Let us now actually add some behavior to this extension. We create an extension of the `RenderPipelineDescriptor`, thus we create a type that can be chained to this descriptor.

The **public API** is handled in `dawn.json`: we define the extension chained struct by adding anywhere in the root scope (at the end for instance), the following entry:

```json
"foo render pipeline descriptor": {
    "category": "structure",
    "chained": "in",
    "chain roots": ["render pipeline descriptor"],
    "tags": ["native"],
    "members": [
        {"name": "foo", "type": "uint32_t"}
    ]
},
```

And we must also add **the very name of this struct** to the SType enum:

```json
"s type": {
    "category": "enum",
    "emscripten_no_enum_table": true,
    "values": [
        {"value": 0, "name": "invalid", "valid": false},
        {"value": 1, "name": "surface descriptor from metal layer", "tags": ["native"]},
        /* [...] */
        {"value": 1013, "name": "dawn render pass color attachment render to single sampled", "tags": ["dawn"]},
        /* We add our custom extension here: */
        {"value": 4097, "name": "foo render pipeline descriptor", "tags": ["native"]}
    ]
},
```

We can now try to use this new struct in our application:

```C++
RenderPipelineDescriptor pipelineDesc;
// [...]

// Our custom extension in use in our main.cpp
WGPUFooRenderPipelineDescriptor fooRenderPipelineDesc;
fooRenderPipelineDesc.chain.next = nullptr;
fooRenderPipelineDesc.chain.sType = WGPUSType_FooRenderPipelineDescriptor;
fooRenderPipelineDesc.foo = 42; // some arbitrary value here
pipelineDesc.nextInChain = &fooRenderPipelineDesc.chain;

RenderPipeline pipeline = device.createRenderPipeline(pipelineDesc);
```

````{important}
Since so far the render pipeline descriptor was not extended by any feature, a sanity check in `ValidateRenderPipelineDescriptor` ensures that there is no chained data in the descriptor. We must remove that and check instead the validity of the chain:

```C++
// In dawn/src/dawn/native/RenderPipeline.cpp
MaybeError ValidateRenderPipelineDescriptor(DeviceBase* device,
                                            const RenderPipelineDescriptor* descriptor) {
    // Commend that out:
    //DAWN_INVALID_IF(descriptor->nextInChain != nullptr, "nextInChain must be nullptr.");
    // And add this check:
    DAWN_TRY(ValidateSTypes(descriptor->nextInChain, {{wgpu::SType::FooRenderPipelineDescriptor}}));
    // [...]
}
```
````

Our application now runs correctly, but does nothing special.

### Internal API

This time, the internal version of `RenderPipelineDescriptor` is identical to the public one (it has a different type name, but is `reinterpret_cast`-ed). So we can directly proceed to the backend change.

### Backend change (agnostic)

Our example feature is **so simple** that it can actually be implemented in the `RenderPipelineBase` class, which is **agnostic to the backend**!

We add in the struct **two private attributes**, storing the value of "foo" provided by our extension of the descriptor, and a boolean telling whether it was provided:

```C++
// In dawn/src/dawn/native/RenderPipeline.h
class RenderPipelineBase : public PipelineBase {
	// [...]

	// Foo extension
    bool mUseFoo = false;
    uint32_t mFoo;
};
```

We then **modify the constructor** to read these values from the descriptor. The handy `FindInChain` utility function **recursively inspects the extension chain**, looking for the right SType:

```C++
// In dawn/src/dawn/native/RenderPipeline.cpp
RenderPipelineBase::RenderPipelineBase(/* [...] */) : /* [...] */ {
	// [...]

	// Handle foo info, if provided
    const FooRenderPipelineDescriptor* fooDesc = nullptr;
    FindInChain(descriptor->nextInChain, &fooDesc);
    if (fooDesc != nullptr) {
        mUseFoo = true;
        mFoo = fooDesc->foo;
    }
}
```

We also define a `DoTestFoo` method that emits our test log line:

```C++
// In RenderPipeline.h, in RenderPipelineBase class definition
public:
	// Display a debug log line with the value of foo, is enabled
	void DoTestFoo() const;

// In RenderPipeline.cpp
#include <iostream>
// [...]
void RenderPipelineBase::DoTestFoo() const {
    if (mUseFoo) {
        std::cout << "DEBUG of FOO feature: foo=" << mFoo << std::endl;
    }
}
```

In order to trigger this line whenever `setPipeline` is called, we go to the definition of the `RenderEncoderBase` class:

```C++
// In dawn/src/dawn/native/RenderEncoderBase.cpp
void RenderEncoderBase::APISetPipeline(RenderPipelineBase* pipeline) {
    pipeline->DoTestFoo();
    // [...]
}
```

```{note}
Method names that start with `API` directly correspond to calls to the public API. The mapping is auto-generated.
```

And tadam! We were able to create a custom extension, and propagate the extra "foo" information from our application code all the way to Dawn's internals.

```
DEBUG of FOO feature: foo=42
```

Of course this was only a basic example, but from there on changes highly depend on the actual extension you want to implement!

*Resulting code:* [`dawn:eliemichel/foo`](https://github.com/eliemichel/Dawn/tree/eliemichel/foo) and [`step030-test-foo-extension-dawn`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-test-foo-extension-dawn)
