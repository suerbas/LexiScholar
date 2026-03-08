"""
PyInstaller hook for PyTorch
Handles DLL loading and ensures proper initialization of PyTorch components.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect PyTorch data files
datas = collect_data_files('torch')

# Collect PyTorch DLLs
binaries = collect_dynamic_libs('torch')

# Set environment variables for proper DLL loading
if sys.platform == 'win32':
    # Windows-specific DLL loading fixes
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

# Hidden imports for PyTorch components
hiddenimports = [
    'torch',
    'torch.cuda',
    'torch.nn',
    'torch.optim',
    'torch.utils.data',
    'torch.backends.cudnn',
    'torch._C',
    'torch._C._nn',
    'torch.serialization',
    'torch.jit',
    'torch.autograd',
    'torch.distributions',
    'torch.nn.functional',
    'torch.optim.lr_scheduler',
    'torch.utils.checkpoint',
    'torch.utils.hooks',
    'torch.utils.model_zoo',
    'torch.profiler',
    'torch.quantization',
    'torch.random',
    'torch.utils.bottleneck',
    'torch.utils.benchmark',
    'torch.utils.mobile_optimizer',
    'torch.utils.tensorboard',
    'torch.utils._triton',
    'torch._inductor',
    'torch._functorch',
    'torch._dynamo',
    'torch._export',
    'torch._guards',
    'torch._logging',
    'torch._monitor',
    'torch._numpy',
    'torch._ops',
    'torch._subclasses',
    'torch._utils',
    'torch.fx',
    'torch.nn.intrinsic',
    'torch.nn.intrinsic.qat',
    'torch.nn.intrinsic.quantized',
    'torch.nn.qat',
    'torch.nn.quantized',
    'torch.quantization',
    'torch.quantization.quantize_fx',
    'torch.testing',
    'torch.testing._internal',
    'torch.types',
]

# Exclude problematic modules if needed
excludes = [
    'torch.distributions._torch_function_fallback_handling',
]

print(f"PyTorch hook: collected {len(datas)} data files and {len(binaries)} binaries")
