"""Shared protocol vocabulary and limits; no host state or admission authority."""
MATERIAL_LIMIT = 1024 * 1024
MAX_INPUTS = 16
MAX_BYTES = 8 * 1024 * 1024

ARTIFACTS = {
    'objective_selection': 'objective', 'research': 'research', 'direction': 'direction',
    'definition': 'definition', 'experience': 'experience',
    'visual_exploration': 'visual_direction', 'prototype': 'prototype',
    'implementation': 'implementation', 'review': 'review',
    'validation': 'validation', 'refinement': 'implementation', 'delivery': 'delivery',
}
