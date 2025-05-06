Futures and asynchronous operations <span class="bullet">🔴</span>
===================================

**WIP**

## The good way

**To keep track of ongoing asynchronous operations**, each function that starts such an operation **returns a `WGPUFuture`**, which is some sort of internal ID that **identifies the operation**:

```C++
WGPUFuture future;
```

```{note}
Although it is technically just an integer value, the `WGPUFuture` should be treated as an **opaque handle**, i.e., one should not try to deduce anything from the very value of this ID.
```

This *future* can then be passed to `wgpuInstanceWaitAny` to mean "wait until this asynchronous operation completes"! Here is the signature of `wgpuInstanceWaitAny`:

```C++
WGPUWaitStatus wgpuInstanceWaitAny(WGPUInstance instance, size_t futureCount, WGPUFutureWaitInfo * futures, uint64_t timeoutNS);
```

```C++
WGPUFutureWaitInfo futureInfo = { mapBufferFuture };

uint64_t timeoutNS = 200 * 1000; // 200 ms
WGPUWaitStatus status = wgpuInstanceWaitAny(instance, 1, &futureInfo, timeoutNS);
```
