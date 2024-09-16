from dataclasses import MISSING, dataclass
from logging import DEBUG
from typing import Any, List
from hydra import compose, initialize
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from logger import log

@dataclass(frozen=True)
class GeneralConfig:
    frame: int = 1000
    float_tol: float = 0.00000024
    id_separator: str = '|'
    max_time_diff: float = 0.1
    debug: bool = False

@dataclass(frozen=True)
class AudacityConfig:
    end_line: str = '\r\n'
    num_separator: str = '.'
    line_separator: str = '\t'
    only_alphabetic_label: bool = True
    non_negative: bool = True
    omit_exceptions: bool = True

@dataclass(frozen=True)
class SampleConfig:
    labels = []
    rev: str = ''
    path: str = '/app/labels'
    ext: str = 'txt'
    default_label: str = 'ZVOID'

@dataclass(frozen=True)
class ChartConfig:
    pass

@dataclass(frozen=True)
class ColorConfig:
    labeling = []
    agreement: str = 'green'
    disagreement: str = 'red'

@dataclass(frozen=True)
class Config:
    general: GeneralConfig = MISSING
    audacity: AudacityConfig = MISSING
    sample: SampleConfig = MISSING
    color: ColorConfig = MISSING
    chart: ChartConfig = MISSING

cs = ConfigStore.instance()
cs.store(name='base_config', node=Config)
cs.store(group='general', name='base_general', node=GeneralConfig)
cs.store(group='audacity', name='base_audacity', node=AudacityConfig)
cs.store(group='sample', name='base_sample', node=SampleConfig)
cs.store(group='chart', name='base_chart', node=ChartConfig)
cs.store(group='color', name='base_color', node=ColorConfig)

with initialize(version_base=None, config_path="conf"):
    config = compose(config_name="config")

if config.general.debug:
    log.setLevel(DEBUG)

log.debug(OmegaConf.to_yaml(config))
