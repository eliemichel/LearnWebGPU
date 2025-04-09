RAII <span class="bullet">🟡</span>
====

*Resulting code:* [`gist`](https://gist.github.com/eliemichel/2e154152f981e3f16827ba4d17d1123a)

Ever tired of managing the `foo.release()` to make sure that it matches the `device.createFoo()` and that you don't have dangling resources? This **manual mechanism** is required for a C API, but in C++ we can **wrap** it into a more convenient interface thanks to **destructors**.

The **programming idiom** presented here is called [RAII](https://en.cppreference.com/w/cpp/language/raii), which stands for *"Resource Acquisition Is Initialization"*; it applies to many other non-WebGPU related contexts!

The idea is to write a C++ class that we force **by construction** to be such that the underlying resource it represents exists **if and only if** the instance of the class is still alive.

Motivational examples
---------------------

### Function

Let us start with some examples, where we assume that we have a class `raii::Buffer` that wraps the `wgpu::Buffer` resource using the RAII idiom.

```C++
void foo(Device device) {
	BufferDescriptor bufferDesc = /* ... */;

	// Create an instance of our RAII class, which by construction allocates
	// a new wgpu::Buffer.
	raii::Buffer buffer(device, bufferDesc);

	// [...] Do stuff with `buffer`
}
```

Note how there is no need here to call `buffer.release()`: **as soon as the variable goes out of scope** the buffer it wraps is automatically released.

### Class

If we need the buffer to live longer, we can typically define it as a class member:

```C++
class Foo {
private:
	// Class has a buffer attribute
	raii::Buffer m_buffer;

public:
	// Constructor must initialize m_buffer
	Foo(Device device)
		: m_buffer(device, describeBuffer())
	{}

	void doStuff() {
		// [...] Do stuff with `buffer`
	}

private:
	BufferDescriptor describeBuffer() { /* ... */ }
};
```

This time, the buffer is released whenever the instance of `Foo` is destructed: it automatically calls the destructor of `raii::Buffer`, which releases the buffer resource.

```{important}
Since the `raii::Buffer` cannot exist without an underlying buffer, so it must be initialized by the constructor.
```

### Smart pointers

Sometimes we really want to be able to store a "null" buffer, so the need to initialize it as soon as we define the RAII instance can be annoying. The typical solution is to use the **smart pointers** provided by the standard library:

```C++
#include <memory> // for smart pointers

class Foo {
private:
	// Buffer attribute is a unique smart pointer
	std::unique_ptr<raii::Buffer> m_buffer;

public:
	// No need for a constructor here
	void doStuff(Device device) {
		if (!m_buffer) initBuffer(device);
		// [...] Do stuff with `buffer`
	}

private:
	void initBuffer(Device device) {
		// The make_unique<T> utility function takes the same arguments
		// than the constructor of type T.
		m_buffer = std::make_unique<raii::Buffer>(device, describeBuffer());
	}

	BufferDescriptor describeBuffer() { /* ... */ }
};
```

The smart pointer ensures that the object it points to is destructed when nothing points to it (e.g., when `Foo` gets destructed).

```{note}
The standard type [`std::optional`](https://en.cppreference.com/w/cpp/utility/optional) can also be an interesting option to store a "maybe buffer".
```

Implementation
--------------

So how do we write this `raii::Buffer` wrapper? It looks easy but there are **some caveats to avoid**!

```C++
namespace raii {

// WARNING: This RAII class is not complete.
class Buffer {
public:
	// Whenever a RAII instance is created, we create an underlying resource
	Buffer(wgpu::Device device, const wgpu::BufferDescriptor& bufferDesc)
		: m_raw(device.createBuffer(bufferDesc))
	{}

	// And whenever it gets destroyed, we free the resource
	~Buffer() {
		m_raw.release();
	}

private:
	// Raw resources that is wrapped by the RAII class
	// (Remember that `wgpu::Buffer` is actually just a pointer)
	wgpu::Buffer m_raw;
};

// namespace raii
```

```{caution}
When implementing a RAII idiom, it is very important to keep in mind that, as for any class, **the destructor shall not raise exceptions**! The WebGPU API promises that releasing an object does not causes exception, so we should be fine here.
```

This somehow works... until we meet this kind of scheme:

```C++
raii::Buffer buffer1;

if (something) {
	raii::Buffer buffer2 = buffer1;
}

// Can I still use buffer1 here?
```

At the end of the `if` block, the variable `buffer2` goes out of scope, so its `m_raw` member is released. Except that it was the same `m_raw` as `buffer1` due to the `=` assignment!

This snippet will actually systematically crash with a **double free error** because even if you don't use `buffer1` after the `if`, whenever it gets out of scope on its turn its destructor attempt to release a second time `m_raw`.

### Rule of three

There is a general rule of thumb in C++ that accurately applies in our case, namely the [Rule of three](https://en.cppreference.com/w/cpp/language/rule_of_three). It says in short:

> If a class needs either a user-defined **destructor** (`~Foo()`), a user-defined **copy assignment** operator (`operator=(const Foo& other)` or a user-defined **copy constructor** (`Foo(const Foo& other)`), then it very likely need **the three of them**.

In our case we obviously need a custom destructor, to release the resource, so the rule tells us that we should also manually define **how to copy RAII buffers**.

```C++
// Rule of three
class Buffer {
public:
	// We define a destructor...
	~Buffer();

	// ...so we need a copy assignment operator...
	Buffer& operator=(const Buffer& other);

	// ...and a copy constructor.
	Buffer(const Buffer& other);

	// [...]
};
```

How do we implement these copy operations? We have **three options**:

 - **Option A**: We create a new buffer and copy the content of the previous one.
 - **Option B**: We deactivate the possibility to copy buffers.
 - **Option C**: We count references.

The problem of Option A is that it turns a seemingly innocent line of code like `buffer2 = buffer1` into a time and memory consuming operation. And it requires the buffer object to hold a reference to the `Device` object that must be used to create the new buffer.

Option B make things clearer to the user of the API by forcing the use of a more explicit method (e.g., `buffer.copyFrom(device, other)`). In this case we simply delete the copy operator/constructor:

```C++
// Delete copy semantics
Buffer& operator=(const Buffer& other) = delete;
Buffer(const Buffer& other) = delete;
```

Option C consists in using a counter to keep track of how many different RAII instances use the same `m_raw`, so that we release it only when no body else is using it.

One possibility for this is to implement Option B but then use `std::shared_pointer<raii::Buffer>`, because a shared pointer is precisely a (smart) pointer with a reference counter.

Another possibility is to use the `buffer.reference()` (or `wgpuBufferReference`) procedure to increase an internal counter on the WebGPU backend side.

### Rule of five

Defining custom copy operator/constructor deactivates the automatic creation of **move** operator/constructor. A variant of the Rule of three, called the **Rule of five**, states that should also take care of these move semantics.

These defines what happens when we do, among others, `buffer2 = std::move(buffer1)`, which means that `buffer1` will never be used again. It also enables one to create a function that returns a `raii::Buffer` without performing any copy.

In such a case, we can simply move the value of `m_raw` from `buffer1` to `buffer2`, removing it from `buffer1` so that it can no longer release it.

```C++
Buffer&& operator=(Buffer&& other) {
	m_raw = other.m_raw;
	other.m_raw = nullptr;
}

Buffer(Buffer&& other) {
	m_raw = other.m_raw;
	other.m_raw = nullptr;
}

// And we need to slightly change the destructor:
~Buffer() {
	if (!m_raw) return;
	m_raw.release();
}
```

```{note}
We created a way to have a RAII object that points to no underlying resource, but this is done in a way that follows the C++ lifetime semantics so the compiler can be aware of it.
```

Conclusion
----------

We have seen how to create a RAII wrapper around a WebGPU buffer, and from this one implementing other classes is straightforward (you could even automate it). And keep this design pattern in mind even for other projects, as it is a very common and powerful idiom!

*Resulting code:* [`gist`](https://gist.github.com/eliemichel/2e154152f981e3f16827ba4d17d1123a)
