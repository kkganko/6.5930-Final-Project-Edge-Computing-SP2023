import os
from pathlib import Path
from yamlwidgets import YamlWidgets
from pytimeloop.app import ModelApp, MapperApp
from pytimeloop.accelergy_interface import invoke_accelergy
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

import logging, sys
logger = logging.getLogger('pytimeloop')
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ConfigRegistry:
    #################################
    # Eyeriss
    #################################
    EYERISS_DIR                     = Path('eyeriss')
    EYERISS_ARCH                    = EYERISS_DIR / 'arch/eyeriss_like-float32.yaml'
    EYERISS_COMPONENTS_DIR          = EYERISS_DIR / 'arch/components'
    EYERISS_OUTPUT_DIR              = EYERISS_DIR / 'output'
    EYERISS_ERT                     = EYERISS_OUTPUT_DIR / 'eyeriss.ERT.yaml'
    EYERISS_ART                     = EYERISS_OUTPUT_DIR / 'eyeriss.ART.yaml'

    EYERISS_CONSTRAINTS_DIR         = EYERISS_DIR / 'constraints'
    EYERISS_ARCH_CONSTRAINTS        = EYERISS_CONSTRAINTS_DIR / 'eyeriss_like_arch_constraints.yaml'
    EYERISS_MAP_CONSTRAINTS         = EYERISS_CONSTRAINTS_DIR / 'eyeriss_like_map_constraints.yaml'
    
    
    #################################
    # PVC
    #################################
    PVC_DIR                         = Path('pvc')
    PVC_ARCH                        = PVC_DIR / 'arch/pvc_like-float32.yaml'
    PVC_COMPONENTS_DIR              = PVC_DIR / 'arch/components'
    PVC_OUTPUT_DIR                  = PVC_DIR / 'output'
    PVC_ERT                         = PVC_OUTPUT_DIR / 'pvc.ERT.yaml'
    PVC_ART                         = PVC_OUTPUT_DIR / 'pvc.ART.yaml'

    PVC_CONSTRAINTS_DIR             = PVC_DIR / 'constraints'
    PVC_ARCH_CONSTRAINTS            = PVC_CONSTRAINTS_DIR / 'pvc_like_arch_constraints.yaml'
    PVC_MAP_CONSTRAINTS             = PVC_CONSTRAINTS_DIR / 'pvc_like_map_constraints.yaml'
    
    

    #################################
    # System Manual
    #################################
    SYSTEM_MANUAL_DIR      = Path('designs/system_manual')
    SYSTEM_1x16_ARCH       = SYSTEM_MANUAL_DIR / 'arch/system_arch_1x16.yaml'
    SYSTEM_2x8_ARCH_WIDGET = SYSTEM_MANUAL_DIR / 'arch/system_arch_2x8-widget.yaml'
    SYSTEM_4x4_ARCH_WIDGET = SYSTEM_MANUAL_DIR / 'arch/system_arch_4x4-widget.yaml'
    SYSTEM_COMPONENTS_DIR  = SYSTEM_MANUAL_DIR / 'arch/components'

    SYSTEM_MANUAL_MAP_WIDGET   = SYSTEM_MANUAL_DIR / 'map/example_mapping_for_1x16-widget.yaml'
    SYSTEM_MANUAL_MAP          = SYSTEM_MANUAL_DIR / 'map/example_mapping_for_1x16.yaml'
    SYSTEM_MANUAL_MAP_TEMPLATE = SYSTEM_MANUAL_DIR / 'map/template_map.yaml'

    #################################
    # System Auto
    #################################
    SYSTEM_AUTO_DIR     = Path('designs/system_auto')
    CONSTRAINTS_DIR     = SYSTEM_AUTO_DIR / 'constraints'
    EXAMPLE_CONSTRAINTS = CONSTRAINTS_DIR / 'example_constraints.yaml'
    RELAXED_CONSTRAINTS = CONSTRAINTS_DIR / 'relaxed_constraints.yaml'
    MAPPER              = SYSTEM_AUTO_DIR / 'mapper/mapper.yaml'

    #################################
    # Mapper Setting
    #################################
    MAPPER_SETTING_DIR = Path('mapper')
    DEFAULT_MAPPER_SETTING = MAPPER_SETTING_DIR / 'mapper.yaml'

    #################################
    # Problems
    #################################
    LAYER_SHAPES_DIR = Path('layer_shapes')
    TINY_LAYER_PROB  = LAYER_SHAPES_DIR / 'tiny_layer.yaml'
    SMALL_LAYER_PROB = LAYER_SHAPES_DIR / 'small_layer.yaml'
    MED_LAYER_PROB   = LAYER_SHAPES_DIR / 'medium_layer.yaml'
    DEPTHWISE_LAYER_PROB = LAYER_SHAPES_DIR / 'depth_wise.yaml'
    POINTWISE_LAYER_PROB = LAYER_SHAPES_DIR / 'point_wise.yaml'

    VGG02_layer5 = LAYER_SHAPES_DIR / 'VGG02_layer5.yaml'

    #################################
    # Models
    #################################
    
    

def load_config(*paths):
    yaml = YAML(typ='safe')
    yaml.version = (1, 2)
    total = None
    def _collect_yaml(yaml_str, total):
        new_stuff = yaml.load(yaml_str)
        if total is None:
            return new_stuff

        for key, value in new_stuff.items():
            if key == 'compound_components' and key in total:
                total['compound_components']['classes'] += value['classes']
            elif key in total:
                raise RuntimeError(f'overlapping key: {key}')
            else:
                total[key] = value
        return total

    for path in paths:
        if isinstance(path, str):
            total = _collect_yaml(path, total)
            continue
        elif path.is_dir():
            for p in path.glob('*.yaml'):
                with p.open() as f:
                    total = _collect_yaml(f.read(), total)
        else:
            with path.open() as f:
                total = _collect_yaml(f.read(), total)
    return total

def load_config_str(*paths):
    total = ''
    for path in paths:
        if isinstance(path, str):
            return path
        elif path.is_dir():
            for p in path.glob('*.yaml'):
                with p.open() as f:
                    total += f.read() + '\n'
            return total
        else:
            with path.open() as f:
                return f.read()

def get_paths(paths):
    all_paths = []
    for path in paths:
        if path.is_dir():
            for p in path.glob('*.yaml'):
                all_paths.append(str(p))
        else:
            all_paths.append(str(path))
    return all_paths

def dump_str(yaml_dict):
    yaml = YAML(typ='safe')
    yaml.version = (1, 2)
    yaml.default_flow_style = False
    stream = StringIO()
    yaml.dump(yaml_dict, stream)
    return stream.getvalue()

def show_config(*paths):
    print(load_config_str(*paths))

def load_widget_config(*paths, title=''):
    widget = YamlWidgets(load_config_str(*paths), title=title)
    widget.display()
    return widget

def run_timeloop_model(*paths):
    yaml_str = dump_str(load_config(*paths))
    model = ModelApp(yaml_str, '.')
    result = model.run_subprocess()
    return result

def run_accelergy(*paths):
    has_str = False
    for path in paths:
        if isinstance(path, str):
            has_str = True
            break
    if has_str:
        yaml_str = dump_str(load_config(*paths))
        with open('tmp-accelergy.yaml', 'w') as f:
            f.write(yaml_str)
        result = invoke_accelergy(['tmp-accelergy.yaml'], '', '.')
        os.remove('tmp-accelergy.yaml')
    else:
        result = invoke_accelergy(get_paths(paths), '', '.')
    return result

def configure_mapping(config_str, mapping, var):
    config = load_config(config_str)
    for key in var:
        for level in config['options']:
            for level_key in level:
                if key == level_key:
                    var[key] = level[level_key]
    with open(mapping, 'r') as f:
        complete_mapping = eval(f.read())
    return complete_mapping

def run_timeloop_mapper(*paths):
    yaml_str = dump_str(load_config(*paths))
    mapper = MapperApp(yaml_str, '.')
    result = mapper.run_subprocess()
    return result
