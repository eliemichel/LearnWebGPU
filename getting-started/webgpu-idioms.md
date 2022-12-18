WebGPU idioms
=============

Before diving into the specifics, I briefly introduce here the **common structure** that most functions provided by the WebGPU API follow.

All functions are prefixed with `wgpu`, and all structures with `WGPU`. This is a C API, so it could not use namespaces.

```C++
wgpuInstanceRequestAdapter(
	NULL,
	&adapterOpts,
	request_adapter_callback,
	(void*)&adapter
);

typedef struct WGPURequestAdapterOptions {
    WGPUChainedStruct const * nextInChain;
    WGPUSurface compatibleSurface; // nullable
    WGPUPowerPreference powerPreference;
    bool forceFallbackAdapter;
} WGPURequestAdapterOptions;
wgpuInstanceRequestAdapter(WGPUInstance instance, WGPURequestAdapterOptions const * options /* nullable */, WGPURequestAdapterCallback callback, void * userdata);
```

There is likely more resources available about the JavaScript binding of WebGPU, so here is how to port a JavaScript snippet into a C++ one:

```js
const opts = {
	powerPreference: "low-power",
	forceFallbackAdapter: false,
};
const adapter = gpu.requestAdapter(opts);
```

```C++
WGPURequestAdapterOptions opts;
opts.nextInChain = NULL;
opts.compatibleSurface = glfwGetWGPUSurface(window);
opts.powerPreference = "low-power";
opts.forceFallbackAdapter = false;

WGPUAdapter adapter;
wgpuInstanceRequestAdapter(NULL, opts, callback, (void*)&adapter);
```

```C++
WGPURequestAdapterOptions opts = {
	.powerPreference = "low-power",
	.forceFallbackAdapter = false,
};

WGPUAdapter adapter;
wgpuInstanceRequestAdapter(NULL, opts, callback, (void*)&adapter);
```

Promises
--------

Operations that may take time do not directly return. In JavaScript, this is handled by returning a [*Promise*](#). Each time the JavaScript API returns a Promise, it is replace in the C API by taking two extra arguments:

 - **callback**, a function that is called when the operation is done (whether it is a success or not).
 - **userdata**, an arbitrary pointer that is forwarded to the callback. This is the way the callback communicates with your code.

```C++
void callback(
	WGPURequestAdapterStatus status,
	WGPUxxx received,
	const char* message,
	void* userdata
) {
	// Do something depending on the status
}

wgpuXXX(NULL, opts, callback, (void*)&userdata);
```


Slots
-----

Chained Struct
--------------

`WGPUChainedStruct`
