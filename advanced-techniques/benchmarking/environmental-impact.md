Environmental Impact (<span class="bullet">🔴</span>TODO)
====================

It is important to be able to asses, at least roughly, the environmental impact of an application, if we want to be able to compare with other (potentially non-software based) solution to the problem they address.

GPU-intensive application have an environmental impact through multiple expenses, for instance:

 - The impact of the energy expense while using the application depends on how long computation run, how long the user uses intensive computations in a typical workflow, how intense the computation is.

 - The choice of minimal required limits impacts the need to manufacture new hardware.

Tools for measuring **instant energy** expense depend a lot on the platform. For instance NVidia provides information through the [NVML library](https://developer.nvidia.com/nvidia-management-library-nvml).

The **carbon impact** of this energy depends on the user's location. Several APIs exist to query this information, like [WattTime](https://www.watttime.org/api-documentation).

The **manufacturing impact** is harder to evaluate, especially for non-carbon related, which includes notably the challenging extraction of **rare metals**, which are non-renewable.
