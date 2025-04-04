
# 7B version

import os
import sys
import json
import torch
import safetensors.torch
import argparse

try:
    from ties_merging import do_merging, do_merging_strategy
except:
    print("ties_merging.py not found, couldn't perform ties-merging.")

OUTPUT_PATH = "converted-minicpm2qwen"

CKPT_PATH = {
    "cogvlm_chat": "/yeesuanAI05/thumt/dyy/model/cogvlm-base-490-hf", #"/yeesuanAI05/thumt/dyy/model/cogvlm-chat-hf",
    "cogvlm_grounding": "/yeesuanAI05/thumt/dyy/model/cogvlm-grounding-generalist-hf",
    "llava": "/yeesuanAI05/thumt/dyy/model/llava-v1.5-7b",
    "sharegpt": "/yeesuanAI05/thumt/dyy/model/ShareGPT4V-7B-llava",
    "vicuna-v1.5": "/yeesuanAI05/thumt/cc/checkpoints/vicuna-7b-v1.5",
    "qwen2-7B": "/yeesuanAI05/thumt/dyy/model/qwen2-7b-instruct/Qwen2-7B-Instruct",
    "qwen2_vl":"/yeesuanAI05/thumt/dyy/model/Qwen2-VL-7B-Instruct",
    "llava-onevision-qwen" : "/yeesuanAI05/thumt/dyy/model/llava-onevision-qwen2-7b-si"
}

INDEX_FILENAME = {
    "cogvlm_chat": "model.safetensors.index.json",
    "cogvlm_grounding": "model.safetensors.index.json",
    "llava": "pytorch_model.bin.index.json",
    "sharegpt": "pytorch_model.bin.index.json",
    "vicuna-v1.5": "pytorch_model.bin.index.json",
    "llava-onevision-qwen": "model.safetensors.index.json",
    "qwen2_vl" : "model.safetensors.index.json",
    "qwen2-7B": "model.safetensors.index.json"
}

N = 28 # layers count


def load_pytorch_weights(base_path, file_list):
    weights = {}
    for file in file_list:
        path = os.path.join(base_path, file)
        x = torch.load(path)
        weights.update(x)
    return weights
def load_safetensors_weights(base_path, file_list):
    weights = {}
    for file in file_list:
        path = os.path.join(base_path, file)
        x = safetensors.torch.load_file(path)
        weights.update(x)
    return weights

qwen_file_list = ['model-00001-of-00004.safetensors', 'model-00002-of-00004.safetensors', 'model-00003-of-00004.safetensors', 'model-00004-of-00004.safetensors']
vicuna_file_list = ['pytorch_model-00001-of-00002.bin', 'pytorch_model-00002-of-00002.bin']
llama_file_list = ['pytorch_model-00001-of-00003.bin', 'pytorch_model-00002-of-00003.bin', 'pytorch_model-00003-of-00003.bin']
def load_llama_weights(base_path, file_list=llama_file_list):
    return load_pytorch_weights(base_path, file_list)

def load_qwen_weights(base_path, file_list=qwen_file_list):
    return load_safetensors_weights(base_path, file_list)


llava_file_list = ['pytorch_model-00001-of-00002.bin', 'pytorch_model-00002-of-00002.bin']
def load_llava_weights(base_path, file_list=llava_file_list):
    return load_pytorch_weights(base_path, file_list)

mplug_owl_file_list_template = "pytorch_model-{}-of-33.bin"
mplug_owl_file_list = [mplug_owl_file_list_template.format(str(i+1)) for i in range(33)]
def load_mplug_owl_weights(base_path, file_list=mplug_owl_file_list):
    return load_pytorch_weights(base_path, file_list)

cogvlm_file_list = ['model-00001-of-00008.safetensors', 'model-00002-of-00008.safetensors', 'model-00003-of-00008.safetensors', 'model-00004-of-00008.safetensors', 'model-00005-of-00008.safetensors', 'model-00006-of-00008.safetensors', 'model-00007-of-00008.safetensors', 'model-00008-of-00008.safetensors']
def load_cogvlm_weights(base_path, file_list=cogvlm_file_list):
    return load_safetensors_weights(base_path, file_list)

qwenvl_file_list = ['model-00001-of-00005.safetensors', 'model-00002-of-00005.safetensors', 'model-00003-of-00005.safetensors', 'model-00004-of-00005.safetensors', 'model-00005-of-00005.safetensors']
def load_qwenvl_weights(base_path, file_list=qwenvl_file_list):
    return load_safetensors_weights(base_path, file_list)

llava_onevision_qwen_file_list = ['model-00001-of-00004.safetensors', 'model-00002-of-00004.safetensors', 'model-00003-of-00004.safetensors', 'model-00004-of-00004.safetensors']
def load_minicpm_weights(base_path, file_list=llava_onevision_qwen_file_list):
    return load_safetensors_weights(base_path, file_list)


def need_merge_llava(name:str) -> bool:
    if name in ['lm_head.weight', 'model.embed_tokens.weight' ]:
        return True
    if name in [ 'model.norm.weight']:
        return True   
    if name.startswith("model.layers."):
        if name.endswith(".self_attn.rotary_emb.inv_freq"):
            return False
        return True
    return False
    
def create_soft_link(source_path, link_path):
    # Check if source path exists
    if not os.path.exists(source_path):
        print(f"Error: Source path '{source_path}' does not exist.")
        return

    # Check if link path exists, if not create it
    if not os.path.exists(link_path):
        os.makedirs(link_path)
        print(f"Created directory '{link_path}'")

    # Iterate through all files and directories in the source path
    for item in os.listdir(source_path):
        source_item = os.path.join(source_path, item)
        link_item = os.path.join(link_path, item)

        # Skip files that end with '.bin'
        if item.endswith('.bin'):
            print(f"Skipping '{item}' as it ends with '.bin'")
            continue

        # If it's a file, create a symbolic link
        if os.path.isfile(source_item):
            try:
                os.symlink(source_item, link_item)
                print(f"Created soft link '{link_item}' -> '{source_item}'")
            except OSError as e:
                print(f"Error creating soft link for '{item}': {e}")

        # If it's a directory, ignore it
        elif os.path.isdir(source_item):
            continue

def need_merge(name:str) -> bool:
    if name in ['model.norm.weight']:
        return True
    if name in ['lm_head.weight', 'model.embed_tokens.weight']:
        return False
    if name.startswith("model.layers."):
        if name.endswith(".self_attn.rotary_emb.inv_freq"):
            return False
        return True
    return False

def convert(args):
    global OUTPUT_PATH
    alpha = args.alpha
    interpolation = args.interpolation
    print("interpolation----",interpolation)
    if args.output is not None:
        OUTPUT_PATH = args.output
    else: # when --output is not provided
        # Default path name
        if alpha != 1.0:
            assert alpha != 0
            OUTPUT_PATH = OUTPUT_PATH + f"-alpha-{alpha}"
        if interpolation:
            OUTPUT_PATH = OUTPUT_PATH + "-interpolation"
    print(f"Merging output path: {OUTPUT_PATH}")

    print("Loading...")
    llava = load_qwenvl_weights(CKPT_PATH["qwen2_vl"])
    sharegpt = load_minicpm_weights(CKPT_PATH['llava-onevision-qwen'])

    

    print("Merging...")
    cogvlm_diff={}
    # re-scale by alpha
    if args.strategy:
        vicuna = load_qwen_weights(CKPT_PATH["qwen2-7B"], file_list=qwen_file_list)
        llava_merge = {}
        sharegpt_merge = {}
        for key in llava:
            if need_merge_llava(key):
                llava_merge[key] = llava[key] - vicuna[key]
                sharegpt_merge[key] = sharegpt[key] - vicuna[key]
                # llava_merge[key]=(args.tiesalpha*2) * llava_merge[key]
                # sharegpt_merge[key]=(1 - args.tiesalpha) * 2 * sharegpt_merge[key]
        if args.strategy == 'ties':            
            merged = do_merging([llava_merge, sharegpt_merge], merge_func = "sum",K=args.K, alpha=args.tiesalpha)            
        else:
            merged = do_merging_strategy([llava_merge, sharegpt_merge], args.strategy, K=args.K, alpha=args.tiesalpha)

        for key in llava:
            if need_merge_llava(key):
                llava[key] = merged[key] + vicuna[key]
    elif interpolation:
        for key in sharegpt:
            llava_key=key
            
            if need_merge_llava(llava_key):
                llava[llava_key] *= 1 - alpha
                    
            # cogvlm_diff[key] = (sharegpt[key] * alpha) if need_merge(key) else sharegpt[key]
            cogvlm_diff[key] = (sharegpt[key] * alpha) if need_merge(key) else 0
    
    # save
    print("Saving...")
    metadata = {'format': 'pt'}
    llava_index_path = os.path.join(CKPT_PATH["qwen2_vl"], INDEX_FILENAME["qwen2_vl"])
    with open(llava_index_path, "r") as f:
        llava_index = json.load(f)
        llava_index = llava_index["weight_map"]
    
    split_llava = {}
    for file in qwenvl_file_list:
        split_llava[file] = {}
    for key in llava_index:
        split_llava[llava_index[key]][key] = llava[key]
    for file in qwenvl_file_list:
        if not os.path.isdir(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)
        save_path = os.path.join(OUTPUT_PATH, file)
        safetensors.torch.save_file(split_llava[file], save_path, metadata)
        
    create_soft_link(source_path=CKPT_PATH["qwen2_vl"], link_path=OUTPUT_PATH)

    print("Convert Done.")
    print(save_path)

if __name__ == "__main__":
   
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='/yeesuanAI05/thumt/dyy/model/checkpoints/debug/debug-0.5-llava2qwen/qwen2_vl', help="Output checkpoint path")
    parser.add_argument('--alpha', type=float, default=0.5)
    parser.add_argument('--interpolation',default=False, action='store_true')
    parser.add_argument('--noLN', default=False, action='store_true')    

    # other merging strategies
    parser.add_argument('--strategy', type=str, default='task_arithmetic') 
    parser.add_argument('-K', type=float, default=0.5)
    parser.add_argument('--tiesalpha', type=float, default=0.5)
    
    args = parser.parse_args()
    
    args.output=f"/yeesuanAI05/thumt/dyy/model/checkpoints/debug/{args.strategy}-K-{str(args.K)}-llava2qwen"
    print(args)
    # if args.reverse:
    #     CKPT_PATH['llava'] ="/yeesuanAI05/thumt/dyy/model/ShareGPT4V-7B-llava"
    #     CKPT_PATH['sharegpt'] = "/yeesuanAI05/thumt/dyy/model/llava-v1.5-7b"
    

    convert(args)