from __future__ import annotations

from cam_physgeo.dpo.winner_anchor_cache_builder import tensor_tree_finite, tensor_tree_shapes


def test_tensor_tree_helpers_on_plain_values():
    assert tensor_tree_finite({"a": [1, 2, 3]})
    assert tensor_tree_shapes({"a": [1, 2]})["a"] == ["int", "int"]
