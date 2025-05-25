Writing a zero-overhead C++ wrapper <span class="bullet">🟠</span>
===================================

*This is a sort of blog-post that gives details about how the `webgpu.hpp` wrapper was developed.*

## Mock Example

In this post, we consider the example of a C API that is build a bit like WebGPU:

```C++
prefixSomethingSomeAction(something, ...)
                          ^^^^^^^^^ // The instance of type 'Something' to act on
               ^^^^^^^^^^ // What to do...
      ^^^^^^^^^ // ...on what type of object
^^^^^^ // (Common prefix to avoid naming collisions)
```

Let's invent one for the sake of illustration, say using a culinary metaphor:

```C++
#include <stdint.h>
// Our library is called "chef"

// It defines some opaque handles for objects:
typedef struct CHEFKitchenImpl* CHEFKitchen;

// Like in WebGPU, we use descriptor structs to hold creation arguments:
typedef struct CHEFKitchenDescriptor {
    const char* label;
} CHEFKitchenDescriptor;

// Then come our procedures:
// We can create a Kitchen object
CHEFKitchen chefCreateKitchen(const CHEFKitchenDescriptor *descriptor);
// And release this object
void chefKitchenRelease(CHEFKitchen kitchen);

// Methods of Kitchen:
// A Kitchen has a given number of stoves, which we can retrieve
uint32_t chefKitchenGetStoveCount(CHEFKitchen kitchen);
// For a valid stove index, we can set it gas strength to turn it on.
uint32_t chefKitchenSetStoveStrength(CHEFKitchen kitchen, uint32_t stoveIndex, float strength);
// When cooking, we may have to wait for something to heat up.
void chefKitchenWait(CHEFKitchen kitchen, uint32_t seconds);
// Get gas the overall consumption (which depends on stove strengths and wait duration).
float chefKitchenGetGasConsumption(CHEFKitchen kitchen);
```

And here is an example of how one can use it:

```C++
int main() {
    // Set up the kitchen
    CHEFKitchenDescriptor desc = { "my kitchen" };
    CHEFKitchen kitchen = chefCreateKitchen(&desc);
    printf("Kitchen: %p\n", kitchen);

    uint32_t stoveCount = chefKitchenGetStoveCount(kitchen);
    printf("Stove count: %d\n", stoveCount);

    if (stoveCount == 0) {
        printf("No stove? What kitchen is that... Aborting.\n");
        return 1;
    }

    // Try out some very basic receipe
    chefKitchenSetStoveStrength(kitchen, 0, 0.5); // heat-up
    chefKitchenWait(kitchen, 3 * 60); // wait for 3 min
    chefKitchenSetStoveStrength(kitchen, 0, 0); // stop stove

    // Measure overall energy consumption of the receipe
    float gazConsumption = chefKitchenGetGasConsumption(kitchen);
    printf("Overall gas consumption: %f\n", gazConsumption);

    chefKitchenRelease(kitchen);
}
```

Our goal is to write a **C++ wrapper** for this library, which makes it **more comfortable** to use while **not changing anything at runtime**!

In order to inspect in details how our wrapper affects compilation, I will be using [GodBolt Compiler Explorer](https://godbolt.org/). I invite you to use it as well while following this article.

```{figure} /images/cpp-wrapper/godbolt.png
:align: center
:class: with-shadow

GodBolt Compiler Explorer is a very handy **online tool** to compare many many compiler, looking at how the resulting assembly looks like.
```

```{note}
Throughout the examples, I will be using the **clang (x86-64)** compiler with a basic level of compilation optimization, namely `-O1`.
```

```{figure} /images/cpp-wrapper/optimize-flag.png
:align: center
:class: with-shadow

We add the `-O1` command line argument to enable a basic level of compile optimization.
```

## Even smaller example

Let's start with an even more minimal main in order to be able to inspect the output in details:

```C++
int main() {
    // Set up the kitchen
    CHEFKitchenDescriptor desc = { "my kitchen" };
    CHEFKitchen kitchen = chefCreateKitchen(&desc);
    printf("Kitchen: %p\n", kitchen);
    chefKitchenRelease(kitchen);
    return 0;
}
```

When building with clang (x86-64) with optimization option `-O1`, we get this assembly:

```asm
main:
        push    rbx
        sub     rsp, 16
        lea     rax, [rip + .L.str]
        mov     qword ptr [rsp + 8], rax
        lea     rdi, [rsp + 8]
        call    chefCreateKitchen(CHEFKitchenDescriptor const*)@PLT
        mov     rbx, rax
        lea     rdi, [rip + .L.str.1]
        mov     rsi, rax
        xor     eax, eax
        call    printf@PLT
        mov     rdi, rbx
        call    chefKitchenRelease(CHEFKitchenImpl*)@PLT
        xor     eax, eax
        add     rsp, 16
        pop     rbx
        ret

.L.str:
        .asciz  "my kitchen"

.L.str.1:
        .asciz  "Kitchen: %p\n"
```

````{note}
If we want to also **link** the program, we must provide an implementation of the part of the API that we are using, for instance:

```C++
typedef struct CHEFKitchenImpl {
    uint32_t stoveCount;
} CHEFKitchenImpl;

CHEFKitchen chefCreateKitchen(const CHEFKitchenDescriptor *) {
    CHEFKitchen kitchen = new CHEFKitchenImpl;
    kitchen->stoveCount = 0;
    return kitchen;
}

void chefKitchenRelease(CHEFKitchen kitchen) {
    delete kitchen;
}
```
````

Let us use this as a **reference** to compare with other results.

## Namespace

The very first thing that we would like to introduce is a `chef` **namespace**, so that we can write `wgpu::Kitchen`, `wgpu::createKitchen`, etc. (and potentially `using namespace chef` to spare us the prefix).

The beginning of a namespace wrapper could look like this:

```C++
// Introducing the 'chef' namespace
namespace chef {
    using Kitchen = CHEFKitchen;
    using KitchenDescriptor = CHEFKitchenDescriptor;

    Kitchen createKitchen(const KitchenDescriptor* descriptor) {
        return chefCreateKitchen(descriptor);
    }
    void kitchenRelease(Kitchen kitchen) {
        chefKitchenRelease(kitchen);
    }
} // namespace chef
```

This is then used like so:

```C++
int main() {
    chef::KitchenDescriptor desc = { "my kitchen" };
    chef::Kitchen kitchen = chef::createKitchen(&desc);
    chef::kitchenRelease(kitchen);
    return 0;
}
```

The `main` section of the resulting assembly is the same as before except that it calls `chef::createKitchen` rather than `chefCreateKitchen`, but this also introduced two **new sections** at the beginning:

```asm
chef::createKitchen(CHEFKitchenDescriptor const*):
        jmp     chefCreateKitchen(CHEFKitchenDescriptor const*)@PLT

chef::kitchenRelease(CHEFKitchenImpl*):
        jmp     chefKitchenRelease(CHEFKitchenImpl*)@PLT

main:
        push    rbx
        sub     rsp, 16
        lea     rax, [rip + .L.str]
        mov     qword ptr [rsp + 8], rax
        lea     rdi, [rsp + 8]
        call    chefCreateKitchen(CHEFKitchenDescriptor const*)@PLT
        mov     rbx, rax
        lea     rdi, [rip + .L.str.1]
        mov     rsi, rax
        xor     eax, eax
        call    printf@PLT
        mov     rdi, rbx
        call    chefKitchenRelease(CHEFKitchenImpl*)@PLT
        xor     eax, eax
        add     rsp, 16
        pop     rbx
        ret

.L.str:
        .asciz  "my kitchen"

.L.str.1:
        .asciz  "Kitchen: %p\n"
```

Two things to notice here:

1. There are these extra `chef::createKitchen(CHEFKitchenDescriptor const*)` and `chef::kitchenRelease(CHEFKitchenImpl*)` sections at the beginning. These corresponds to the lines of code where we define the `chef::createKitchen` function.

2. But as it turns out, the `main` section **does not use them**. The compiler figured that it was worth **inlining** the call.

Explicit use of the `inline` keyword is often considered harmful as the compiler is usually better than us at figuring out when to inline or not.

However, it seems that the compiler still keeps around the extra symbols `chef::createKitchen` and `chef::kitchenRelease`, all the way down to the linked program: I get **31 lines** for the **baseline** (without the namespace wrapper), **44 lines** with the **naive** namespace wrapper.

I then suggest to add explicit `inline` qualifiers:

```C++
// in namespace chef
inline Kitchen createKitchen(const KitchenDescriptor* descriptor) {
    return chefCreateKitchen(descriptor);
}
inline void kitchenRelease(Kitchen kitchen) {
    chefKitchenRelease(kitchen);
}
```

And we are now **back to the very same 31 lines as the baseline** in the linked program!

```{important}
Throughout this article, I use differences in the number of lines in the assembly as a **proxy** of difference in the runtime overhead. It is only a proxy, as we could have the same number of lines but more costly operations or control flow.
```

## Object notation

A nice thing that C++ adds compared to C is the object notation. Any call to `chefKitchenDoSomething(kitchen, ...)` can thus become the more succinct `kitchen.doSomething(...)`.

For this purpose, the `Kitchen` type defined in the `chef` namespace is no longer a simple `using Kitchen = CHEFKitchen` but an actual class:

```C++
// in namespace chef
class Kitchen {
public:
    CHEFKitchen raw;
};
```

We must then modify the functions:

```C++
inline Kitchen createKitchen(const KitchenDescriptor* descriptor) {
    return { chefCreateKitchen(descriptor) };
}
inline void kitchenRelease(Kitchen kitchen) {
    chefKitchenRelease(kitchen.raw);
}
```

So far, it does not change the result of the compilation! Actually, **instead of modifying these functions** we can make things more flexible by adding **conversion operators**:

```C++
class Kitchen {
public:
    CHEFKitchen raw;

    // Convert from CHEFKitchen to Kitchen
    Kitchen(const CHEFKitchen& w) : raw(w) {}
    // Convert from Kitchen to CHEFKitchen (read-only)
    operator const CHEFKitchen&() const { return raw; }
    // Convert from Kitchen to CHEFKitchen (read-write)
    operator CHEFKitchen&() { return raw; }
};
```

````{note}
Our `Kitchen` instances can now transparently be used with the C API as if they were `CHEFKitchen` instances, so we revert the previous change:

```C++
inline Kitchen createKitchen(const KitchenDescriptor* descriptor) {
    return chefCreateKitchen(descriptor);
}
inline void kitchenRelease(Kitchen kitchen) {
    chefKitchenRelease(kitchen);
}
```
````

Again, no change in the result of the compilation. Let us now add a `release` method to this class:

```C++
class Kitchen {
public:
    // [...] (Keep what we had so far in the Kitchen class)

    void release() {
        chefKitchenRelease(raw);
    }
};
```

We use it in the main function:

```C++
//chef::kitchenRelease(kitchen);
kitchen.release();
```

Still no change in the compiled object! We can now remove `chef::kitchenRelease()` by the way.

```{note}
This time, no need to explicitly `inline` the function. Methods defined directly in the header are always inlined.
```

## References

All right, nice, we have namespaces and object methods for free. Another thing that we can add is to pass **arguments by reference** where they were passed as pointers:

```C++
inline Kitchen createKitchen(const KitchenDescriptor& descriptor) {
    //                                              ^ This was a *
    return chefCreateKitchen(&descriptor);
    //                       ^ Convert the reference to a pointer
}
```

We can thus remove the ampersand (`&`) from the main function:

```C++
int main() {
    chef::KitchenDescriptor desc = { "my kitchen" };
    chef::Kitchen kitchen = chef::createKitchen(desc);
    //                                          ^ There used to be a '&' here
    // [...]
}
```

Again, check in GodBolt: no change in the compiled code!

## Const qualifiers

We can keep on adding methods, and even introduce compile-time-only safeguards like `const` qualifiers for methods that are pure getters, e.g.:

```C++
class Kitchen {
public:
    // [...]

    uint32_t getStoveCount() const {
        return chefKitchenGetStoveCount(raw);
    }
};
```

Adding a basic implementation of `chefKitchenGetStoveCount` and using this in `main()`, we're now at 38 lines of assembly in the linked program:

```C++
// in main()
uint32_t stoveCount = kitchen.getStoveCount();
printf("Stove count: %d\n", stoveCount);
```

```C++
// At the end of the file
uint32_t chefKitchenGetStoveCount(CHEFKitchen kitchen) {
    return kitchen->stoveCount;
}
```

## Back to our initial example

I let you implement the C++ wrapper for rest of the mock API introduced at the beginning of this article. You can test it with the following implementation:

```C++
typedef struct CHEFStoveImpl {
    float strength;
} CHEFStoveImpl;

typedef struct CHEFKitchenImpl {
    uint32_t stoveCount;
    CHEFStoveImpl* stoves;
    float gasConsumption;
} CHEFKitchenImpl;

CHEFKitchen chefCreateKitchen(const CHEFKitchenDescriptor *descriptor) {
    CHEFKitchen kitchen = new CHEFKitchenImpl;
    kitchen->stoveCount = 4;
    kitchen->stoves = new CHEFStoveImpl[kitchen->stoveCount];
    for (uint32_t i = 0 ; i < kitchen->stoveCount ; ++i) {
        kitchen->stoves[i].strength = 0.0f;
    }
    kitchen->gasConsumption = 0;
    return kitchen;
}

void chefKitchenRelease(CHEFKitchen kitchen) {
    delete[] kitchen->stoves;
    delete kitchen;
}

uint32_t chefKitchenGetStoveCount(CHEFKitchen kitchen) {
    return kitchen->stoveCount;
}

void chefKitchenSetStoveStrength(CHEFKitchen kitchen, uint32_t stoveIndex, float strength) {
    kitchen->stoves[stoveIndex].strength = strength;
}

void chefKitchenWait(CHEFKitchen kitchen, uint32_t seconds) {
    const float rate = 0.1f;
    const float rateSeconds = rate * seconds;
    for (uint32_t i = 0 ; i < kitchen->stoveCount ; ++i) {
        kitchen->gasConsumption += kitchen->stoves[i].strength * rateSeconds;
    }
}

float chefKitchenGetGasConsumption(CHEFKitchen kitchen) {
    return kitchen->gasConsumption;
}
```

And the following main program:

```C++
// Using the raw C API
int main() {
    // Set up the kitchen
    CHEFKitchenDescriptor desc = { "my kitchen" };
    CHEFKitchen kitchen = chefCreateKitchen(&desc);
    printf("Kitchen: %p\n", kitchen);

    uint32_t stoveCount = chefKitchenGetStoveCount(kitchen);
    printf("Stove count: %d\n", stoveCount);

    if (stoveCount == 0) {
        printf("No stove? What kitchen is that... Aborting.\n");
        return 1;
    }

    // Try out some very basic receipe
    chefKitchenSetStoveStrength(kitchen, 0, 0.5); // heat-up
    chefKitchenWait(kitchen, 3 * 60); // wait for 3 min
    chefKitchenSetStoveStrength(kitchen, 0, 0); // stop stove

    // Measure overall energy consumption of the receipe
    float gazConsumption = chefKitchenGetGasConsumption(kitchen);
    printf("Overall gas consumption: %f\n", gazConsumption);
    chefKitchenRelease(kitchen);
}
```

```C++
// Using the C++ wrapper
int main() {
    // Set up the kitchen
    chef::KitchenDescriptor desc = { "my kitchen" };
    chef::Kitchen kitchen = chef::createKitchen(desc);
    printf("Kitchen: %p\n", kitchen);
    
    uint32_t stoveCount = kitchen.getStoveCount();
    printf("Stove count: %d\n", stoveCount);

    if (stoveCount == 0) {
        printf("No stove? What kitchen is that... Aborting.\n");
        return 1;
    }

    // Try out some very basic receipe
    kitchen.setStoveStrength(0, 0.5); // heat-up
    kitchen.wait(3 * 60); // wait for 3 min
    kitchen.setStoveStrength(0, 0); // stop stove

    // Measure overall energy consumption of the receipe
    float gazConsumption = kitchen.getGasConsumption();
    printf("Overall gas consumption: %f\n", gazConsumption);
    kitchen.release();
    return 0;
}
```

This must output something like this using 129 lines of assembly in the linked program:

```
Kitchen: 0x6278cbc552b0
Stove count: 4
Overall gas consumption: 9.000000
```

Here is a possible implementation of the wrapper:

```C++
namespace chef {
    class Kitchen {
    public:
        CHEFKitchen raw;

        // Conversion functions
        Kitchen(const CHEFKitchen& w) : raw(w) {}
        operator CHEFKitchen&() { return raw; }
        operator const CHEFKitchen&() const { return raw; }

        void release() {
            chefKitchenRelease(raw);
        }

        uint32_t getStoveCount() const {
            return chefKitchenGetStoveCount(raw);
        }

        float getGasConsumption() const {
            return chefKitchenGetGasConsumption(raw);
        }

        void setStoveStrength(uint32_t stoveIndex, float strength) {
            return chefKitchenSetStoveStrength(raw, stoveIndex, strength);
        }

        void wait(uint32_t seconds) const {
            chefKitchenWait(raw, seconds);
        }

        // Here is an extra function!
        // As long as you are not using it, it does not impact the compiled program.
        friend auto operator<<(std::ostream &stream, const Kitchen& self) -> std::ostream & {
            return stream << "<chef::Kitchen " << self.raw << ">";
        }
    };

    using KitchenDescriptor = CHEFKitchenDescriptor;

    inline Kitchen createKitchen(const KitchenDescriptor& descriptor) {
        return chefCreateKitchen(&descriptor);
    }
} // namespace chef
```

```{note}
In the end, we only use a single `inline` keyword because there is **only one function directly under the `chef` namespace**. Without this inline, the compiled program size goes up to 145 lines of assembly.

Testing with `gcc (x86-64)`, I get 101 lines with `inline` and 107 without (its `-O1` flag seems more aggressive than clang's).
```

## Function callbacks

### Example

Let us add to our mock wrapped API a callback mechanism. Say, a callback can be invoked whenever a stove switches from on to off.

```C++
// The callback type, which gets the index of the stove that
// was switched off, plus 2 blind user pointer.
typedef void (*CHEFStoveSwitchedOffCallback)(
    uint32_t stoveIndex,
    void* userdata1,
    void* userdata2
);

// The callback setter, that also takes the two user pointers as argument
void chefKitchenOnStoveSwitchedOff(
    CHEFKitchen kitchen,
    CHEFStoveSwitchedOffCallback callback,
    void* userdata1,
    void* userdata2
);
```

```{note}
I follow WebGPU's approach of providing no less than **2 user pointers**, because it is precisely needed to create zero-overhead wrapper that is compatible with **capturing lambdas**.
```

Let us ignore the user pointers for now when using the callback:

```C++
void onStoveSwitchedOff(
    uint32_t stoveIndex,
    void* /* userdata1 */,
    void* /* userdata2 */
) {
    printf("Stove #%d was turned off!\n", stoveIndex);
}

int main() {
    // [...] Create kitchen

    chefKitchenOnStoveSwitchedOff(kitchen, onStoveSwitchedOff, nullptr, nullptr);

    // [...]
}
```

And here is the actual implementation to be able to test it:

```C++
// Just to keep things organized, we create a struct to group the callback info
// that the kitchen object needs to store
typedef struct CHEFStoveSwitchedOffCallbackInfo {
    CHEFStoveSwitchedOffCallback callback;
    void* userdata1;
    void* userdata2;
} CHEFStoveSwitchedOffCallbackInfo;

typedef struct CHEFKitchenImpl {
    // [...]
    // And we use this struct here:
    CHEFStoveSwitchedOffCallbackInfo stoveSwitchedOffCallbackInfo;
} CHEFKitchenImpl;

// The implementation of the callback setter is thus simply this:
void chefKitchenOnStoveSwitchedOff(
    CHEFKitchen kitchen,
    CHEFStoveSwitchedOffCallback callback,
    void* userdata1,
    void* userdata2
) {
    kitchen->stoveSwitchedOffCallbackInfo.callback = callback;
    kitchen->stoveSwitchedOffCallbackInfo.userdata1 = userdata1;
    kitchen->stoveSwitchedOffCallbackInfo.userdata1 = userdata1;
}

// And we modify (a) the kitchen constructor to initialize this callback info
CHEFKitchen chefCreateKitchen(const CHEFKitchenDescriptor *descriptor) {
    // [...]
    kitchen->stoveSwitchedOffCallbackInfo.callback = nullptr;
    kitchen->stoveSwitchedOffCallbackInfo.userdata1 = nullptr;
    kitchen->stoveSwitchedOffCallbackInfo.userdata1 = nullptr;
    return kitchen;
}

// And (b) the stove strength setter to invoke the callback
void chefKitchenSetStoveStrength(CHEFKitchen kitchen, uint32_t stoveIndex, float strength) {
    bool shouldInvokeCallback = strength == 0.0 && kitchen->stoves[stoveIndex].strength > 0.0;
    kitchen->stoves[stoveIndex].strength = strength;
    if (shouldInvokeCallback && kitchen->stoveSwitchedOffCallbackInfo.callback != nullptr) {
        kitchen->stoveSwitchedOffCallbackInfo.callback(
            stoveIndex,
            kitchen->stoveSwitchedOffCallbackInfo.userdata1,
            kitchen->stoveSwitchedOffCallbackInfo.userdata2
        );
    }
}
```

Okey, the output of the program is now the following, using 169 lines of assembly:

```
Kitchen: 0x55c73c1342b0
Stove count: 4
Stove #0 was turned off!
Overall gas consumption: 9.000000
```

### Wrapper

Switching to the C++ wrapper version, we can start by doing the very same changes of the main function, since our wrapper's conversion operators allows to use the raw C API as well:

```C++
// In the C++ wrapper version
int main() {
    // [...] Create kitchen

    chefKitchenOnStoveSwitchedOff(kitchen, onStoveSwitchedOff, nullptr, nullptr);

    // [...]
}
```

Naturally, we can turn this into a method:

```C++
class Kitchen {
public:
    // [...]

    void onStoveSwitchedOff(
        CHEFStoveSwitchedOffCallback callback,
        void* userdata1,
        void* userdata2
    ) {
        chefKitchenOnStoveSwitchedOff(raw, callback, userdata1, userdata2);
    }
};
```

This leads to:

```C++
// in main()
kitchen.onStoveSwitchedOff(onStoveSwitchedOff, nullptr, nullptr);
```

Still at 169 lines of assembly, so far so good.

But this callback is a bit simplistic, things get a bit more interesting once we start using the user data pointers. Let's say we want to name our stoves, so that the callback prints "The 'foo' stove was turned off" instead of using the stove index. And we want to set the names from the main function (maybe because it'd be a dynamic information in a real scenario), so we pass an array of stove names through the first user data pointer:

```C++
// Using the C API
void onStoveSwitchedOff(
    uint32_t stoveIndex,
    void* userdata1,
    void* /* userdata2 */
) {
    const char** stoveNames = (const char**)userdata1;
    printf("The %s stove was turned off!\n", stoveNames[stoveIndex]);
}

int main() {
    // [...]

    const char* stoveNames[] = {
        "big",
        "top-right",
        "bottom-left",
        "small",
    };

    chefKitchenOnStoveSwitchedOff(kitchen, onStoveSwitchedOff, stoveNames, nullptr);

    // [...]
}
```

Our new baseline is at 176 lines of assembly now (and 151 with gcc), and gives the following output:

```
Kitchen: 0x63729a7d22b0
Stove count: 4
The big stove was turned off!
Overall gas consumption: 9.000000
```

What we would like to do on the C++ side is to use lambda functions instead of handling the user data pointers to pass in some context (it was simple here because we only pass a single variable, but if we want more, we need to create a dedicated context structure, etc.).

Let's start simple and just switch from a regular function to a lambda:

```C++
int main() {
    // [...]

    auto onStoveSwitchedOff = [](
        uint32_t stoveIndex,
        void* userdata1,
        void* /* userdata2 */
    ) {
        const char** stoveNames = (const char**)userdata1;
        printf("The %s stove was turned off!\n", stoveNames[stoveIndex]);
    };

    kitchen.onStoveSwitchedOff(onStoveSwitchedOff, stoveNames, nullptr);

    // [...]
}
```

This changes a bit the assembly, but does not add any extra instruction.

But what we would really like to use, is a **capturing lambda**:

```C++
auto onStoveSwitchedOff = [stoveNames](uint32_t stoveIndex) {
    //                     ^^^^^^^^^^ We capture the stove name array
    //              (which is just a pointer, so we capture it by value here)
    printf("The %s stove was turned off!\n", stoveNames[stoveIndex]);
};

kitchen.onStoveSwitchedOff(onStoveSwitchedOff2);
```

We could repurpose the user data pointer to hold the lambda object instead of explicitly sending a context:

```C++
// Warning: This may crash, see below
template<typename Lambda>
void onStoveSwitchedOff(Lambda cppCallback) {
    auto cCallback = [](
        uint32_t stoveIndex,
        void* userdata1,
        void* /* userdata2 */
    ) {
        auto* cppCallback = reinterpret_cast<Lambda*>(userdata1);
        (*cppCallback)(stoveIndex);
    };
    chefKitchenOnStoveSwitchedOff(raw, cCallback, &cppCallback, nullptr);
}
```

Wait, look how we are **storing a pointer to the local variable `cppCallback`**!

Clang seems to get along with it in this very example, probably thanks to some optimization mechanism that fixes the issue as a byproduct. Let us **switch to gcc (x86-64)** to better see the problem:

```
Kitchen: 0x1924c2b0
Stove count: 4
The (null) stove was turned off!
Overall gas consumption: 9.000000
```

It still doesn't crash (again, an optimization inadvertently helped us here), but we can see that it does not find the captured `stoveNames`.

One thing we can do is to **pass the lambda by reference** instead of copying it:

```C++
template<typename Lambda>
void onStoveSwitchedOff(const Lambda& cppCallback) {
    auto cCallback = [](
        uint32_t stoveIndex,
        void* userdata1,
        void* userdata2
    ) {
        auto* cppCallback = reinterpret_cast<Lambda*>(userdata1);
        (*cppCallback)(stoveIndex);
    };
    chefKitchenOnStoveSwitchedOff(raw, cCallback, (void*)&cppCallback, nullptr);
}
```

```{note}
I've initially made a choice here to pass the lambda **by value** rather than **by reference**. This is a common choice (e.g., the STL does it, Dawn's C++ wrapper does it, etc.) because for lambdas that only capture a small context it makes things easier for the compiler to optimize things. If you intend to use heavy lambdas, it is advised to wrap them inside a shallow one that points to the heavy context by reference.
```

Okey we're back on track (although it added 2 lines in the assembly)... until we decide to define the lambda directly in the call to `onStoveSwitchedOff`:

```C++
kitchen.onStoveSwitchedOff([stoveNames](uint32_t stoveIndex) {
    printf("The %s stove was turned off!\n", stoveNames[stoveIndex]);
});
```

Here, the lambda is released right after the statement is executed, so by the time we invoke the lambda, it no longer exists.

So in the end there is no way around dynamically allocating some room so that we manually manage the callback's memory:

```C++
template<typename Lambda>
void onStoveSwitchedOff(const Lambda& cppCallback) {
    auto* lambda = new Lambda(cppCallback); // allocate a copy here
    auto cCallback = [](
        uint32_t stoveIndex,
        void* userdata1,
        void* userdata2
    ) {
        auto* lambda = reinterpret_cast<Lambda*>(userdata1);
        (*lambda)(stoveIndex);
        delete lambda; // release the copy
    };
    chefKitchenOnStoveSwitchedOff(raw, cCallback, (void*)lambda, nullptr);
}
```

```{important}
Here we make some **key assumptions**:

- The callback will **not be called more than once**! Otherwise, the second time would use the lambda after the first time has deleted it.
- The callback will be **called at least once**! Otherwise the dynamically allocated lambda will never get deleted.
```

In the case of WebGPU, these assumptions are fulfilled for all callbacks because they correspond to JavaScript's Promise mechanism. The callback is invoked when the asynchronous operation is ready, and never again. And all callbacks have a status argument that can be set to `CallbackCancelled` to mean "the operation did not end, but it will never, so here we invoke the callback in case you need to clean things up".

The only **exception** is the **uncaptured error callback**, which can only be set once (at device initialization time) and gets invoked as many times as there are errors.

Our example here is a bit misleading in its wording, because `onStoveSwitchedOff` sounds like a repeatable event, which makes it closer to the uncaptured error callback than to a regular async operation. Anyways, let's assume that it only gets called once for this exercise.

### Robustness to exceptions

There is a case where our solution above can **leak** memory: if the lambda throws an exception, thus never executing the `delete lambda` statement.

The solution is to build a `std::unique_ptr` to wrap the raw lambda pointer into a smart pointer that automatically gets released when going out of scope:

```C++
#include <memory>

// [...]

{ // Previous version:
    auto* lambda = reinterpret_cast<Lambda*>(userdata1);
    (*lambda)(stoveIndex);
    delete lambda;
}
{ // New version
    std::unique_ptr<Lambda> lambda(reinterpret_cast<Lambda*>(userdata1));
    (*lambda)(stoveIndex);
}
```

This adds a couple of lines of assembly (we're now at 179 with clang and 163 with gcc), but is much safer.

### Dynamic allocation or not

Compared to the baseline, we only have 3 extra lines of assembly (with gcc), but these lines include a `new` and a `delete`, which may feel annoying.

A first case we can take special care of is the one of **non capturing lambdas**. Imagine that we are back to our very simple callback:

```C++
kitchen.onStoveSwitchedOff([](uint32_t stoveIndex) {
    printf("A stove was turned off!\n");
});
```

This time, the lambda is no different from a C function, so why bother the complication we just introduced in such a case?

**WIP**

```C++
template<typename Lambda>
void onStoveSwitchedOff(const Lambda& cppCallback) {
    using F = void(uint32_t stoveIndex);

    if constexpr (std::is_convertible_v<Lambda, F*>) {
        auto cCallback = [](
            uint32_t stoveIndex,
            void* userdata1,
            void* userdata2
        ) {
            auto* lambda = reinterpret_cast<F*>(userdata1);
            (*lambda)(stoveIndex);
        };
        chefKitchenOnStoveSwitchedOff(raw, cCallback, (void*)+cppCallback, nullptr);
    } else {
        auto* lambda = new Lambda(cppCallback);
        auto cCallback = [](
            uint32_t stoveIndex,
            void* userdata1,
            void* userdata2
        ) {
            std::unique_ptr<Lambda> lambda(reinterpret_cast<Lambda*>(userdata1));
            (*lambda)(stoveIndex);
        };
        chefKitchenOnStoveSwitchedOff(raw, cCallback, (void*)lambda, nullptr);
    }
}
```

```
(gcc/clang)
Baseline: 145/168
Dynamic: 163/179
New: 149/172
```
