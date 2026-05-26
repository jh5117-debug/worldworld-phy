def lora_plan(rank: int=16, alpha: int=16, target_modules: list[str]|None=None) -> dict:
    return {'rank':rank,'alpha':alpha,'target_modules':target_modules or ['attention','ffn'],'trainable_scope':'adapter_only'}
