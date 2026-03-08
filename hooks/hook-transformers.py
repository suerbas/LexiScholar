"""
PyInstaller hook for Transformers library
Handles proper loading of HuggingFace Transformers components.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect Transformers data files
datas = collect_data_files('transformers')

# Collect Transformers binaries
binaries = collect_dynamic_libs('transformers')

# Hidden imports for Transformers components
hiddenimports = [
    'transformers',
    'transformers.models',
    'transformers.models.auto',
    'transformers.models.bert',
    'transformers.models.gpt2',
    'transformers.models.roberta',
    'transformers.models.t5',
    'transformers.models.distilbert',
    'transformers.models.xlm_roberta',
    'transformers.tokenization',
    'transformers.tokenization_auto',
    'transformers.tokenization_utils_base',
    'transformers.configuration_utils',
    'transformers.generation_utils',
    'transformers.generation',
    'transformers.pipelines',
    'transformers.pipelines.base',
    'transformers.pipelines.feature_extraction',
    'transformers.pipelines.fill_mask',
    'transformers.pipelines.text_classification',
    'transformers.pipelines.token_classification',
    'transformers.pipelines.question_answering',
    'transformers.pipelines.text2text_generation',
    'transformers.pipelines.text_generation',
    'transformers.pipelines.conversational',
    'transformers.utils',
    'transformers.utils.generic',
    'transformers.utils.hub',
    'transformers.file_utils',
    'transformers.modelcard',
    'transformers.models.configuration_utils',
    'transformers.models.tokenization_utils',
    'transformers.models.utils',
    'transformers.models.model_outputs',
    'transformers.deepspeed',
    'transformers.integrations',
    'transformers.onnx',
    'transformers.tf_utils',
    'transformers.trainer',
    'transformers.trainer_callback',
    'transformers.trainer_seq2seq',
    'transformers.trainer_utils',
    'transformers.training_args',
    'transformers.data',
    'transformers.data.data_collator',
    'transformers.data.datasets',
    'transformers.data.processors',
    'transformers.sagemaker',
    'transformers.spark',
    'transformers.testing_utils',
    'transformers.utils.logging',
]

print(f"Transformers hook: collected {len(datas)} data files and {len(binaries)} binaries")
