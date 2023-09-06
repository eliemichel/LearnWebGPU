Benchmarking (🚧WIP)
============

````{tab} With webgpu.hpp
*Resulting code:* [`step095-timestamp-queries`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-timestamp-queries)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-timestamp-queries-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-timestamp-queries-vanilla)
````

Benchmarking consists in measuring the **resources** needed for different tasks, in order for instance to identify **performance bottlenecks** or to compare two approaches to the same problem.

```{warning}
As of September 6, 2023, wgpu-native does not support timestamp queries yet. I suggest you follow this chapter with Dawn only for now.
```

Time
----

### Asynchronicity

We start by **measuring compute time**, which is often the most valuable resource. Importantly, measuring GPU time is **quite different** from measuring CPU time, because as you may recall **we only interact with the GPU through remote calls** issued in our CPU code (C++).

In an imperative CPU code, measuring time looks like this:

```python
# Pseudocode of a simple CPU benchmarking
start_time = get_current_time()
do_on_cpu(something)
end_time = get_current_time()
ellapsed = end_time - start_time
```

But when doing this on the GPU, we only **submit** operations that run on a **different timeline**:

```python
# Pseudocode of a **wrong** GPU benchmarking
start_time = get_current_time()
submit_to_do_on_gpu(something)
end_time = get_current_time()
ellapsed = end_time - start_time # wrong!
```

The "something" may not even have started at this point. What we measure is the time it takes to submit instructions, **not to actually execute them**!

### Timestamp Queries

We must instruct the GPU to run some equivalent of `get_current_time()` on its own timeline. The result of this operation is stored in a dedicated object called a **timestamp query**.

```python
# Pseudocode of a correct GPU benchmarking
start_timestamp_query = create_timestamp_query()
end_timestamp_query = create_timestamp_query()
submit_to_do_on_gpu(write_current_time, start_timestamp_query)
submit_to_do_on_gpu(something)
submit_to_do_on_gpu(write_current_time, end_timestamp_query)
```

We must then **fetch** the timestamp values back to the CPU, through a mapped buffer like we see in [Playing with buffers](../basic-3d-rendering/input-geometry/playing-with-buffers.md#mapping-context).

> 🫡 Okey, got it, so what about actual C++ code?

Whether they measure timestamps or other things, GPU queries are stored in a `QuerySet`. We typically store both the start and end time in the same set:

````{tab} With webgpu.hpp
```C++
// Create timestamp queries
QuerySetDescriptor querySetDesc;
querySetDesc.type = QueryType::Timestamp;
querySetDesc.count = 2; // start and end
QuerySet timestampQueries = device.createQuerySet(querySetDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// Create timestamp queries
WGPUQuerySetDescriptor querySetDesc;
querySetDesc.nextInChain = nullptr;
querySetDesc.type = WGPUQueryType_Timestamp;
querySetDesc.count = 2; // start and end
WGPUQuerySet timestampQueries = wgpuDeviceCreateQuerySet(device, &querySetDesc);
```
````

```{note}
I base this example on [`step095`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095), from chapter [Simple GUI](../basic-3d-rendering/some-interaction/simple-gui.md)
```

However, if you try to add the code block above to your application, you will face an error:

> **Device error:**
> *(Dawn)* Timestamp queries are disallowed because they may expose precise timing information.
> *(wgpu-native)* Features(TIMESTAMP_QUERY) are required but not enabled on the device.

### Enabling Timestamp Feature

#### Dawn toggles

Let us start with Dawn: for **privacy reasons**, Dawn disables timing information. This is relevant when running on the Web, but not in our native application context. Fortunately, **this safeguard can easily be disabled**.

Dawn has a list of so-called "toggles" that can be turned on or off at the scale of the whole WebGPU instance: the list is available in [`Toggles.cpp`](https://dawn.googlesource.com/dawn/+/refs/heads/main/src/dawn/native/Toggles.cpp#33).

To enable toggles, we use the Dawn-specific `DawnTogglesDescriptor` **extension**, which can be chained to the instance descriptor:

````{tab} With webgpu.hpp
```C++
// At the very beginning of onInit()
InstanceDescriptor instanceDesc;
#ifdef WEBGPU_BACKEND_DAWN
// Dawn-specific extension to enable/disable toggles
DawnTogglesDescriptor dawnToggles;
// [...]
instanceDesc.nextInChain = &dawnToggles.chain;
#endif
m_instance = createInstance(instanceDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// At the very beginning of onInit()
WGPUInstanceDescriptor instanceDesc;
#ifdef WEBGPU_BACKEND_DAWN
// Dawn-specific extension to enable/disable toggles
WGPUDawnTogglesDescriptor dawnToggles;
// [...]
instanceDesc.nextInChain = &dawnToggles.chain;
#endif
m_instance = wgpuCreateInstance(&instanceDesc);
```
````

We then specify that we want to enable the `allow_unsafe_apis` feature:

````{tab} With webgpu.hpp
```C++
#ifdef WEBGPU_BACKEND_DAWN
DawnTogglesDescriptor dawnToggles;
dawnToggles.chain.next = nullptr;
dawnToggles.chain.sType = SType::DawnTogglesDescriptor;

std::vector<const char*> enabledToggles = {
    "allow_unsafe_apis",
};
dawnToggles.enabledToggles = enabledToggles.data();
dawnToggles.enabledTogglesCount = enabledToggles.size();
dawnToggles.disabledTogglesCount = 0;

instanceDesc.nextInChain = &dawnToggles.chain;
#endif
```
````

````{tab} Vanilla webgpu.h
```C++
#ifdef WEBGPU_BACKEND_DAWN
WGPUDawnTogglesDescriptor dawnToggles;
dawnToggles.chain.next = nullptr;
dawnToggles.chain.sType = WGPUSType_DawnTogglesDescriptor;

std::vector<const char*> enabledToggles = {
    "allow_unsafe_apis",
};
dawnToggles.enabledToggles = enabledToggles.data();
dawnToggles.enabledTogglesCount = enabledToggles.size();
dawnToggles.disabledTogglesCount = 0;

instanceDesc.nextInChain = &dawnToggles.chain;
#endif
```
````

```{note}
The toggles descriptor can also be used as an extension of the adapter or device request options. In that case, device toggles supersede adapter toggles, which supersede instance toggles.
```

The error message we get is now slightly different:

> **Device error:**
> *(Dawn)* Timestamp query set created without the feature being enabled.

This is in substance the same error than the one reported by `wgpu-native` above, we treat both in the next section.

#### Feature request

When creating our WebGPU device, we mentioned already that we can set up specific limits. But we can also **request specific features** from the `WGPUFeatureName` enum. In particular, we need to enable `FeatureName::TimestampQuery`.

````{tab} With webgpu.hpp
```C++
std::vector<FeatureName> requiredFeatures = {
	FeatureName::TimestampQuery,
};
deviceDesc.requiredFeatures = (const WGPUFeatureName*)requiredFeatures.data();
deviceDesc.requiredFeaturesCount = (uint32_t)requiredFeatures.size();
```
````

````{tab} Vanilla webgpu.h
```C++
std::vector<WGPUFeatureName> requiredFeatures = {
	WGPUFeatureName_TimestampQuery,
};
deviceDesc.requiredFeatures = requiredFeatures.data();
deviceDesc.requiredFeaturesCount = (uint32_t)requiredFeatures.size();
```
````

The error messages should now be fixed! You may also want to check that the adapter, and then the device, support this feature:

````{tab} With webgpu.hpp
```C++
std::vector<FeatureName> requiredFeatures;
if (m_adapter.hasFeature(FeatureName::TimestampQuery)) {
	requiredFeatures.push_back(FeatureName::TimestampQuery);
}
// [...] Create device
if (!m_device.hasFeature(FeatureName::TimestampQuery)) {
	std::cout << "Timestamp queries are not supported!" << std::endl;
}
```
````

````{tab} Vanilla webgpu.h
```C++
std::vector<WGPUFeatureName> requiredFeatures;
if (wgpuAdapterHasFeature(m_adapter, WGPUFeatureName_TimestampQuery)) {
	requiredFeatures.push_back(WGPUFeatureName_TimestampQuery);
}
// [...] Create device
if (!wgpuDeviceHasFeature(m_device, WGPUFeatureName_TimestampQuery)) {
	std::cout << "Timestamp queries are not supported!" << std::endl;
}
```
````

```{note}
Timestamp queries are specified as an explicit feature because some devices/adapters may not support them.
```

#### Writing timestamp queries

There are different ways of writing timestamp into queries. The closest one to our pseudocode above is `commandEncoder.writeTimestamp()`, which writes the GPU-side time into a query whenever the command is executed in the **GPU timeline**.

If you want more specifically to measure the time taken by **a render or compute pass**, you can also pass timestamp queries to the passes descriptor:

````{tab} With webgpu.hpp
```C++
// In Application::onFrame()
std::vector<RenderPassTimestampWrite> timestampWrites(2);
timestampWrites[0].location = RenderPassTimestampLocation::Beginning;
timestampWrites[0].querySet = m_timestampQueries;
timestampWrites[0].queryIndex = 0; // first query = start time
timestampWrites[1].location = RenderPassTimestampLocation::End;
timestampWrites[1].querySet = m_timestampQueries;
timestampWrites[1].queryIndex = 1; // second query = end time

renderPassDesc.timestampWriteCount = (uint32_t)timestampWrites.size();
renderPassDesc.timestampWrites = timestampWrites.data();
RenderPassEncoder renderPass = encoder.beginRenderPass(renderPassDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// In Application::onFrame()
std::vector<WGPURenderPassTimestampWrite> timestampWrites(2);
timestampWrites[0].location = WGPURenderPassTimestampLocation_Beginning;
timestampWrites[0].querySet = m_timestampQueries;
timestampWrites[0].queryIndex = 0; // first query = start time
timestampWrites[1].location = WGPURenderPassTimestampLocation_End;
timestampWrites[1].querySet = m_timestampQueries;
timestampWrites[1].queryIndex = 1; // second query = end time

renderPassDesc.timestampWriteCount = (uint32_t)timestampWrites.size();
renderPassDesc.timestampWrites = timestampWrites.data();
WGPURenderPassEncoder renderPass = wgpuCommandEncoderBeginRenderPass(encoder, &renderPassDesc);
```
````

```{note}
I initialize the query set only once and store it into an attribute `m_timestampQueries` of the `Application` class.
```

#### Retrieving timestamps

Okey, the render pass writes to our first query when it begins, and writes to the second query when it ends. We only need to compute the difference now, right? But the timestamp still **live in the GPU memory**, so we first need to **fetch them back** to the CPU.

WIP

````{tab} With webgpu.hpp
*Resulting code:* [`step095-timestamp-queries`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-timestamp-queries)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-timestamp-queries-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-timestamp-queries-vanilla)
````
