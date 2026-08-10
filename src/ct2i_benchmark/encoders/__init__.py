"""Encoder registry. Thin per-concept modules keep architecture separation."""
from .base import Encoder, MinMaxScaler01
from .hashing_enc import ColumnAwareHashEncoder, SharedValueHashEncoder
from .homals import HomalsEncoder
from .supervised import OrderedCatBoostEncoder, TargetEncoder, WoEEncoder
from .unsupervised import CountEncoder, LabelEncoder, OneHotEncoder01

REGISTRY = {
    "label": LabelEncoder,
    "onehot": OneHotEncoder01,
    "count": CountEncoder,
    "target": TargetEncoder,
    "woe": WoEEncoder,
    "ordered_catboost": OrderedCatBoostEncoder,
    "hash_column": ColumnAwareHashEncoder,
    "hash_shared": SharedValueHashEncoder,
    "homals": HomalsEncoder,
}

SUPERVISED = {"target", "woe", "ordered_catboost"}

__all__ = [
    "REGISTRY",
    "SUPERVISED",
    "ColumnAwareHashEncoder",
    "CountEncoder",
    "Encoder",
    "HomalsEncoder",
    "LabelEncoder",
    "MinMaxScaler01",
    "OneHotEncoder01",
    "OrderedCatBoostEncoder",
    "SharedValueHashEncoder",
    "TargetEncoder",
    "WoEEncoder",
]
