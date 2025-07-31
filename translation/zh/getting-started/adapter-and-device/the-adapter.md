适配器 <span class="bullet">🟢</span>
===========

```{lit-setup}
:tangle-root: zh/005 - 适配器
:parent: zh/001 - Hello WebGPU
```

*结果代码:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)

在我们上手**设备**(device)之前，我们需要选择一**适配器**(adapter)。在同一个宿主系统可多个物理 GPU 时，宿主系统下可以暴露**多个适配器**。也可能存在代表着一个模拟的或虚拟的设备的适配器。

```{note}
对于高端笔记本电脑，包含**两个物理 GPU** 是很常见的，一个**高性能** GPU 和一个 **低功耗** CPU（后者经常集成在 CPU 芯片中）。
```

每个适配器都会提其可支持的可选**功能**和**限制范围**的列表。这些信息用于在**请求设备**前确定系统的整体能力。

> 🤔 为何需要同时存在**适配器**和**设备**这两层抽象？

其设计初衷是为了避免"在我的机器上能跑"（但在其他机器上时却不能）的兼容性问题。**适配器**用于获取用户硬件的**实际能力**，这些信息将决定应用程序在不同代码路径中的具体行为。一旦选定代码路径，系统就会根据**我们选择的能力**创建对应的**设备**。

在应用的后续逻辑中，也只能使用为该设备选择的能力集。通过这种机制，可以从**根本上杜绝开发者无意间依赖特定机器专属能力的情况**。

```{themed-figure} /images/the-adapter/limit-tiers_{theme}.svg
:align: center
在适配器/设备机制的高级用法中，我们可以配置多个限制预设并基于适配器从中进行选择。在我们的示例代码中，我们只有一个预设，如果遇到了兼容性问题就会立刻终止。
```


请求适配器
----------------------

适配器并不是由我们**创建**的，而是通过 `wgpuInstanceRequestAdapater` 函数**请求**获取到的。

````{note}
`webgpu.h` 提供的方法名称始终遵循同样的结构：

```C
wgpuSomethingSomeAction(something, ...)
    ^^^^^^^^^           // 对什么样的对象...
             ^^^^^^^^^^ // ...做什么事情
^^^^                    // (统一的前缀，用于避免命名冲突)
```

函数的第一个参数始终是一个表示这个“Something”对象的“句柄”(一个不透明指针)。
````

根据名称，我们知道了第一个参数是我们在上一章中创建的 `WGPUInstance`。那么的其他的参数呢？

```C++
// webgpu.h 中定义的 wgpuInstanceRequestAdapter 函数签名
void wgpuInstanceRequestAdapter(
	WGPUInstance instance,
	WGPU_NULLABLE WGPURequestAdapterOptions const * options,
	WGPURequestAdapterCallback callback,
	void * userdata
);
```

```{note}
查阅 `webgpu.h` 头文件中的函数定义总是能获得有价值的信息！
```

第二个参数是一些**配置**的集合，它与我们在 `wgpuCreateSomething` 函数中所看到的**描述符**类似，我们会在后面详细说明它。`WGPU_NULLABLE` 标记是一个空定义，仅用于告知读者（也就是我们）在使用**默认配置**时是可以使用 `nullptr` 作为输的入。

### 异步函数

后面两个参数是共同使用的，并且它们揭示了另一个 **WebGPU 惯用设计**。实际上，`wgpuInstanceRequestAdapter` 是一个**异步**函数。它并不直接返回一个 `WGPUAdapter` 对象，而是接受一个**回调函数**，也就是在请求结束时才会被调用的函数。

```{note}
在 WebGPU API 内部多处，只要一个操作需要耗费时间，它们都使用了异步函数，**没有任何一个 WebGPU 函数**会占用时间返回。这样，我们所编写的 CPU 程序永远不会被一个需要耗时的操作所阻塞！
```

为了更好的理解回调机制，我们来看一下 `WGPURequestAdapterCallback` 函数类型的定义：

```C++
// webgpu.h 内定义的 WGPURequestAdapaterCallback 函数类型定义
typedef void (*WGPURequestAdapterCallback)(
	WGPURequestAdapterStatus status,
	WGPUAdapter adapter,
	char const * message,
	void * userdata
);
```

该回调函数是一个接收包括参数为**请求的适配器**、**状态**信息（用于表示请求是否失败与原因）和神秘的 `userdata` **指针**的**函数**。

这个 `userdata` 指针可以是任意数据，WebGPU 不会解析其内容，仅会将其从最初的 `wgpuInstanceRequestAdapter` 调用**透传**至回调函数，作为**共享上下文信息**的载体：

```C++
void onAdapterRequestEnded(
	WGPURequestAdapterStatus status, // 请求状态
	WGPUAdapter adapter, // 返回的适配器
	char const* message, // 错误信息，或 nullptr
	void* userdata // 用户自定义数据，与请求适配器时一致
) {
	// [...] 对适配器进行操作

	// 操作用户信息
	bool* pRequestEnded = reinterpret_cast<bool*>(userdata);
	*pRequestEnded = true;
}

// [...]

// main() 函数:
bool requestEnded = false;
wgpuInstanceRequestAdapter(
	instance /* navigator.gpu 的等价对象 */,
	&options,
	onAdapterRequestEnded,
	&requestEnded // 在本示例中，自定义用户信息是一个简单的布尔值指针
);
```

我们将在下一节中看到针对上下文更高级的用法，它用于在请求结束时恢复适配器。

````{admonition} 笔记 - JavaScript API
:class: foldable note

在 **JavaScript WebGPU API** 中，异步函数使用内置的 [Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) 机制：

```js
const adapterPromise = navigator.gpu.requestAdapter(options);
// promise 目前还没有值，它是一个我们用于连接回调的句柄
adapterPromise.then(onAdapterRequestEnded).catch(onAdapterRequestFailed);

// [...]

// 它使用多个回调函数而不是使用 'status' 参数
function onAdapterRequestEnded(adapter) {
	// 操作 adapter
}
function onAdapterRequestFailed(error) {
	// 显示错误信息
}
```

JavaScript 后期引进了一种名为 [`async` 函数](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function) 的机制，它允许**"等待"**一个异步函数执行完成，而不需要显式地声明一个回调函数。

```js
// 在一个异步函数内
const adapter = await navigator.gpu.requestAdapter(options);
// 操作 adapter
```

现在该机制在其他语言中也存在，比如 [Python](https://docs.python.org/3/library/asyncio-task.html)。C++20 也引入了相同机制的 [coroutines](https://en.cppreference.com/w/cpp/language/coroutines) 特性。

但在本教程中，我会尽量**避免堆砌过多高级抽象**，因此我们不会使用它们（并且对齐 C++17），但高阶的读者可能希望创建依赖 coroutines 的 WebGPU 封装。
````

### Request

We can wrap the whole adapter request in the following `requestAdapterSync()` function, which I provide so that we do not spend too much time on **boilerplate** code (the important part here is that you get the idea of the **asynchronous callback** described above):

```{lit} C++, Includes (append)
#include <cassert>
```

```{lit} C++, Request adapter function
/**
 * Utility function to get a WebGPU adapter, so that
 *     WGPUAdapter adapter = requestAdapterSync(options);
 * is roughly equivalent to
 *     const adapter = await navigator.gpu.requestAdapter(options);
 */
WGPUAdapter requestAdapterSync(WGPUInstance instance, WGPURequestAdapterOptions const * options) {
	// A simple structure holding the local information shared with the
	// onAdapterRequestEnded callback.
	struct UserData {
		WGPUAdapter adapter = nullptr;
		bool requestEnded = false;
	};
	UserData userData;

	// Callback called by wgpuInstanceRequestAdapter when the request returns
	// This is a C++ lambda function, but could be any function defined in the
	// global scope. It must be non-capturing (the brackets [] are empty) so
	// that it behaves like a regular C function pointer, which is what
	// wgpuInstanceRequestAdapter expects (WebGPU being a C API). The workaround
	// is to convey what we want to capture through the pUserData pointer,
	// provided as the last argument of wgpuInstanceRequestAdapter and received
	// by the callback as its last argument.
	auto onAdapterRequestEnded = [](WGPURequestAdapterStatus status, WGPUAdapter adapter, char const * message, void * pUserData) {
		UserData& userData = *reinterpret_cast<UserData*>(pUserData);
		if (status == WGPURequestAdapterStatus_Success) {
			userData.adapter = adapter;
		} else {
			std::cout << "Could not get WebGPU adapter: " << message << std::endl;
		}
		userData.requestEnded = true;
	};

	// Call to the WebGPU request adapter procedure
	wgpuInstanceRequestAdapter(
		instance /* equivalent of navigator.gpu */,
		options,
		onAdapterRequestEnded,
		(void*)&userData
	);

	// We wait until userData.requestEnded gets true
	{{Wait for request to end}}

	assert(userData.requestEnded);

	return userData.adapter;
}
```

```{lit} C++, Utility functions (hidden)
// All utility functions are regrouped here
{{Request adapter function}}
```

In the main function, after creating the WebGPU instance, we can get the adapter:

```{lit} C++, Request adapter
std::cout << "Requesting adapter..." << std::endl;

WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
WGPUAdapter adapter = requestAdapterSync(instance, &adapterOpts);

std::cout << "Got adapter: " << adapter << std::endl;
```

#### Waiting for the request to end

You may have noticed the comment above saying **we need to wait** for the request to end, i.e. for the callback to be invoked, before returning.

When using the **native** API (Dawn or `wgpu-native`), it is in practice **not needed**, we know that when the `wgpuInstanceRequestAdapter` function returns its callback has been called.

However, when using **Emscripten**, we need to hand the control **back to the browser** until the adapter is ready. In JavaScript, this would be using the `await` keyword. Instead, Emscripten provides the `emscripten_sleep` function that interrupts the C++ module for a couple of milliseconds:

```{lit} C++, Wait for request to end
#ifdef __EMSCRIPTEN__
	while (!userData.requestEnded) {
		emscripten_sleep(100);
	}
#endif // __EMSCRIPTEN__
```

In order to use this, we must add a **custom link option** in `CMakeLists.txt`, in the `if (EMSCRIPTEN)` block:

```{lit} CMake, Emscripten-specific options (append)
# Enable the use of emscripten_sleep()
target_link_options(App PRIVATE -sASYNCIFY)
```

Also do not forget to include `emscripten.h` in order to use `emscripten_sleep`:

```{lit} C++, Includes (append)
#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#endif // __EMSCRIPTEN__
```

### Destruction

Like for the WebGPU instance, we must release the adapter:

```{lit} C++, Destroy adapter
wgpuAdapterRelease(adapter);
```

````{note}
We will no longer need to use the `instance` once we have selected our **adapter**, so we can call `wgpuInstanceRelease(instance)` right after the adapter request **instead of at the very end**. The **underlying instance** object will keep on living until the adapter gets released but we do not need to manage this.

```{lit} C++, Create things (hidden)
{{Create WebGPU instance}}
{{Check WebGPU instance}}
{{Request adapter}}
// We no longer need to use the instance once we have the adapter
{{Destroy WebGPU instance}}
```
````

```{lit} C++, file: main.cpp (replace, hidden)
{{Includes}}

{{Utility functions in main.cpp}}

int main() {
	{{Create things}}

	{{Main body}}

	{{Destroy things}}

	return 0;
}
```

```{lit} C++, Utility functions in main.cpp (hidden)
{{Utility functions}}
```

```{lit} C++, Main body (hidden)
```

```{lit} C++, Destroy things (hidden)
{{Destroy adapter}}
```

Inspecting the adapter
----------------------

The adapter object provides **information about the underlying implementation** and hardware, and about what it is able or not to do. It advertises the following information:

 - **Limits** regroup all the **maximum and minimum** values that may limit the behavior of the underlying GPU and its driver. A typical examples is the maximum texture size. Supported limits are retrieved using `wgpuAdapterGetLimits`.
 - **Features** are non-mandatory **extensions** of WebGPU, that adapters may or may not support. They can be listed using `wgpuAdapterEnumerateFeatures` or tested individually with `wgpuAdapterHasFeature`.
 - **Properties** are extra information about the adapter, like its name, vendor, etc. Properties are retrieved using `wgpuAdapterGetProperties`.

```{note}
In the accompanying code, adapter capability inspection is enclosed in the `inspectAdapter()` function.
```

```{lit} C++, Utility functions (append, hidden)
void inspectAdapter(WGPUAdapter adapter) {
	{{Inspect adapter}}
}
```

```{lit} C++, Request adapter (append, hidden)
inspectAdapter(adapter);
```

### Limits

We can first list the limits that our adapter supports with `wgpuAdapterGetLimits`. This function takes as argument a `WGPUSupportedLimits` object where it writes the limits:

```{lit} C++, Inspect adapter
#ifndef __EMSCRIPTEN__
WGPUSupportedLimits supportedLimits = {};
supportedLimits.nextInChain = nullptr;

#ifdef WEBGPU_BACKEND_DAWN
bool success = wgpuAdapterGetLimits(adapter, &supportedLimits) == WGPUStatus_Success;
#else
bool success = wgpuAdapterGetLimits(adapter, &supportedLimits);
#endif

if (success) {
	std::cout << "Adapter limits:" << std::endl;
	std::cout << " - maxTextureDimension1D: " << supportedLimits.limits.maxTextureDimension1D << std::endl;
	std::cout << " - maxTextureDimension2D: " << supportedLimits.limits.maxTextureDimension2D << std::endl;
	std::cout << " - maxTextureDimension3D: " << supportedLimits.limits.maxTextureDimension3D << std::endl;
	std::cout << " - maxTextureArrayLayers: " << supportedLimits.limits.maxTextureArrayLayers << std::endl;
}
#endif // NOT __EMSCRIPTEN__
```

```{admonition} Implementation divergences
The procedure `wgpuAdapterGetLimits` returns a boolean in `wgpu-native` but a `WGPUStatus` in Dawn.

Also, as of April 1st, 2024, `wgpuAdapterGetLimits` is not implemented yet on Google Chrome, hence the `#ifndef __EMSCRIPTEN__` above.
```

Here is an example of what you could see:

```
Adapter limits:
 - maxTextureDimension1D: 32768
 - maxTextureDimension2D: 32768
 - maxTextureDimension3D: 16384
 - maxTextureArrayLayers: 2048
```

This means for instance that my GPU can handle 2D textures up to 32k, 3D textures up to 16k and texture arrays up to 2k layers.

```{note}
There are **many more limits**, that we will progressively introduce in the next chapters. The **full list** is [available in the spec](https://www.w3.org/TR/webgpu/#limits), together with their **default values**, which is also expected to be the minimum for an adapter to claim support for WebGPU.
```

### Features

Let us now focus on the `wgpuAdapterEnumerateFeatures` function, which enumerates the features of the WebGPU implementation, because its usage is very typical from WebGPU native.

We call the function **twice**. The **first time**, we provide a null pointer as the return, and as a consequence the function only returns the **number of features**, but not the features themselves.

We then dynamically **allocate memory** for storing this many items of result, and call the same function a **second time**, this time with a pointer to where the result should store its result.

```{lit} C++, Includes (append)
#include <vector>
```

```{lit} C++, Inspect adapter (append)
std::vector<WGPUFeatureName> features;

// Call the function a first time with a null return address, just to get
// the entry count.
size_t featureCount = wgpuAdapterEnumerateFeatures(adapter, nullptr);

// Allocate memory (could be a new, or a malloc() if this were a C program)
features.resize(featureCount);

// Call the function a second time, with a non-null return address
wgpuAdapterEnumerateFeatures(adapter, features.data());

std::cout << "Adapter features:" << std::endl;
std::cout << std::hex; // Write integers as hexadecimal to ease comparison with webgpu.h literals
for (auto f : features) {
	std::cout << " - 0x" << f << std::endl;
}
std::cout << std::dec; // Restore decimal numbers
```

The features are numbers corresponding to the enum `WGPUFeatureName` defined in `webgpu.h`. We use `std::hex` to display them as hexadecimal values, because this is how they are listed in `webgpu.h`.

You may notice very high numbers apparently not defined in this enum. These are **extensions** provided by our native implementation (e.g., defined in `wgpu.h` instead of `webgpu.h` in the case of `wgpu-native`).

### Properties

Lastly we can have a look at the adapter's properties, that contain information that we may want to display to the end user:

```{lit} C++, Inspect adapter (append)
WGPUAdapterProperties properties = {};
properties.nextInChain = nullptr;
wgpuAdapterGetProperties(adapter, &properties);
std::cout << "Adapter properties:" << std::endl;
std::cout << " - vendorID: " << properties.vendorID << std::endl;
if (properties.vendorName) {
	std::cout << " - vendorName: " << properties.vendorName << std::endl;
}
if (properties.architecture) {
	std::cout << " - architecture: " << properties.architecture << std::endl;
}
std::cout << " - deviceID: " << properties.deviceID << std::endl;
if (properties.name) {
	std::cout << " - name: " << properties.name << std::endl;
}
if (properties.driverDescription) {
	std::cout << " - driverDescription: " << properties.driverDescription << std::endl;
}
std::cout << std::hex;
std::cout << " - adapterType: 0x" << properties.adapterType << std::endl;
std::cout << " - backendType: 0x" << properties.backendType << std::endl;
std::cout << std::dec; // Restore decimal numbers
```

Here is a sample result with my nice Titan RTX:

```
Adapter properties:
 - vendorID: 4318
 - vendorName: NVIDIA
 - architecture:
 - deviceID: 7682
 - name: NVIDIA TITAN RTX
 - driverDescription: 536.23
 - adapterType: 0x0
 - backendType: 0x5
```

Conclusion
----------

 - The very first thing to do with WebGPU is to get the **adapter**.
 - Once we have an adapter, we can inspect its **capabilities** (limits, features) and properties.
 - We learned to use **asynchronous functions** and **double call** enumeration functions.

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)
